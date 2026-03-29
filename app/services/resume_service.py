"""
app/services/resume_service.py

Resume Service - Business logic for resume management.

Handles resume uploads, storage, and NLP-powered parsing.

NLP Pipeline
────────────
1. DocumentParser  extracts raw text from the uploaded PDF / DOCX.
2. spaCy (via NLPManager) tokenises the text and runs Named Entity
   Recognition (NER).
3. Skill extraction applies four complementary strategies:
      a. Direct substring match against the app's Skill catalogue (DB).
      b. spaCy NER labels (ORG, PRODUCT) aligned with known skills.
      c. Synonym / alias resolution via NLPManager.get_skill_synonyms().
      d. Semantic / contextual inference via Sentence-Transformers —
         infers skills that are implied but never explicitly named, e.g.
         "containerized deployment" → Docker.
4. Experience, education, and contact info are extracted with regex
   patterns supplemented by spaCy NER.
5. Results are JSON-serialised into Resume.parsed_content.

Integration
───────────
Called from:
  • app/employee.py  – upload_resume(), parse_resume_skills() on upload
  • app/manager.py   – get_recent_resume_updates() on the updates dashboard
  • app/admin.py     – (optional) audit / statistics hooks

Import pattern:
    from app.services.resume_service import ResumeService
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# ── Internal app imports (relative to the app package) ─────────────────────
from app import db
from app.models import Resume, Skill, UserSkill
from app.services.document_parser import DocumentParser
from app.services.nlp_manager import nlp_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level compiled regex patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
_PHONE_RE = re.compile(
    r"(?:\+?[\d][\d\s\-().]{7,14}[\d])"
)
_DATE_RANGE_RE = re.compile(
    r"""
    (?:
        (?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|
           jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|
           oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)
        [\s,]*
    )?
    (?:19|20)\d{2}
    (?:
        \s*[-\u2013\u2014to]+\s*
        (?:
            (?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|
               jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|
               oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)
            [\s,]*
        )?
        (?:(?:19|20)\d{2}|present|current|now)
    )?
    """,
    re.IGNORECASE | re.VERBOSE,
)

_DEGREE_KEYWORDS: tuple = (
    "bachelor", "master", "b.sc", "m.sc", "b.tech", "m.tech",
    "b.e.", "m.e.", "phd", "ph.d", "doctorate", "mba", "diploma",
    "associate", "degree", "b.a.", "m.a.", "b.com", "m.com",
)
_EXPERIENCE_HEADERS: tuple = (
    "experience", "work experience", "employment history",
    "professional experience", "career history", "work history",
)
_EDUCATION_HEADERS: tuple = (
    "education", "academic background", "qualifications",
    "academic qualifications", "educational background",
)


# ---------------------------------------------------------------------------
# ResumeService
# ---------------------------------------------------------------------------


class ResumeService:
    """Service class for resume upload, storage, and NLP-based parsing."""

    ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}
    UPLOAD_FOLDER = "uploads/resumes"

    # ------------------------------------------------------------------ #
    # File-type helper                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Return True if the file extension is in the allowed set."""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in ResumeService.ALLOWED_EXTENSIONS
        )

    # ------------------------------------------------------------------ #
    # CRUD operations                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_user_resume(user_id: int) -> Optional[Resume]:
        """Fetch the Resume record for a given user (or None)."""
        return Resume.query.filter_by(user_id=user_id).first()

    @staticmethod
    def upload_resume(user_id: int, file: FileStorage) -> Resume:
        """
        Validate, save, and register an uploaded resume file.

        If the user already has a resume the old file is deleted and the
        database record is updated in-place.  Otherwise a new record is
        created.

        Args:
            user_id: ID of the authenticated user.
            file:    Werkzeug FileStorage object from request.files.

        Returns:
            The saved Resume ORM instance.

        Raises:
            ValueError: Validation failure (missing file, bad extension).
        """
        if not file:
            raise ValueError("No file provided")
        if not file.filename:
            raise ValueError("No filename provided")
        if not ResumeService.allowed_file(file.filename):
            raise ValueError("Invalid file type. Allowed: PDF, DOC, DOCX")

        # Resolve upload directory relative to the Flask app root
        from flask import current_app  # noqa: PLC0415 – deferred Flask import

        base_dir = (
            os.path.dirname(current_app.root_path)
            if current_app
            else os.path.abspath(".")
        )
        upload_folder = os.path.join(base_dir, ResumeService.UPLOAD_FOLDER)
        os.makedirs(upload_folder, exist_ok=True)

        original_filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{user_id}_{timestamp}_{original_filename}"
        filepath = os.path.join(upload_folder, filename)

        existing = Resume.query.filter_by(user_id=user_id).first()
        if existing:
            # Remove the old physical file
            if existing.file_path and os.path.exists(existing.file_path):
                try:
                    os.remove(existing.file_path)
                except OSError:
                    pass  # Non-fatal – log if needed

            file.save(filepath)
            existing.file_path = filepath
            existing.original_filename = original_filename
            existing.parsed_content = None   # Invalidate stale parse
            existing.last_updated = datetime.utcnow()
            db.session.commit()
            return existing

        file.save(filepath)
        resume = Resume(
            user_id=user_id,
            file_path=filepath,
            original_filename=original_filename,
        )
        db.session.add(resume)
        db.session.commit()
        return resume

    @staticmethod
    def delete_resume(user_id: int) -> bool:
        """
        Delete a user's resume record and the associated file on disk.

        Returns True if deleted, False if no resume existed.
        """
        resume = Resume.query.filter_by(user_id=user_id).first()
        if not resume:
            return False

        if resume.file_path and os.path.exists(resume.file_path):
            try:
                os.remove(resume.file_path)
            except OSError:
                pass

        db.session.delete(resume)
        db.session.commit()
        return True

    # ------------------------------------------------------------------ #
    # NLP Parsing – public entry-point                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def parse_resume_skills(resume_id: int) -> Dict:
        """
        Run the full NLP pipeline on a stored resume and persist results.

        Called from:
          • app/employee.py  after a successful upload
          • Any background task / admin trigger

        Workflow:
          1. Fetch Resume record from DB.
          2. Extract raw text via DocumentParser.
          3. Run _parse_resume_content() (spaCy + regex pipeline).
          4. Write JSON-serialised result to Resume.parsed_content.
          5. Return the parsed dict for immediate use by the caller.

        :param resume_id: ID of the resume to parse.
        :type resume_id: int
        :returns: Parsed content dict.
        :rtype: Dict
        :raises ValueError: Resume record not found.
        """
        resume = db.session.get(Resume, resume_id)
        if not resume:
            raise ValueError("Resume not found")

        if not resume.file_path:
            result = ResumeService._empty_result("no_file_path")
            resume.parsed_content = json.dumps(result)
            db.session.commit()
            return result

        result = ResumeService._parse_resume_content(resume.file_path)
        resume.parsed_content = json.dumps(result)
        db.session.commit()
        return result

    # ------------------------------------------------------------------ #
    # NLP Parsing – internal pipeline                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_resume_content(file_path: str) -> Dict:
        """
        Core NLP extraction pipeline.

        Stages:
          1. DocumentParser   → raw text
          2. DocumentParser.clean_text()  → normalised text
          3. nlp_manager.load_spacy_model()  → spaCy Doc
          4. _extract_skills_from_doc()   → skill list
          5. _extract_experience()        → experience list
          6. _extract_education()         → education list
          7. _extract_contact_info()      → contact dict

        Degrades gracefully:
          - If the file cannot be read → returns empty result.
          - If text is too short (image PDF) → returns empty result.
          - If spaCy is unavailable → falls back to _parse_without_spacy().

        Args:
            file_path: Absolute path to the resume file on disk.

        Returns:
            Parsed content dict (always valid, never raises).
        """
        # ── 1. Extract raw text ─────────────────────────────────────────
        try:
            raw_text = DocumentParser.parse_file(file_path)
            text = DocumentParser.clean_text(raw_text)
        except (FileNotFoundError, ValueError, NotImplementedError) as exc:
            logger.error("Document parsing failed for '%s': %s", file_path, exc)
            return ResumeService._empty_result("parse_error")

        if not text or len(text) < 30:
            logger.warning(
                "Extracted text too short (%d chars) for '%s'. "
                "Possibly a scanned/image PDF.",
                len(text),
                file_path,
            )
            return ResumeService._empty_result("insufficient_text")

        # ── 2. Load spaCy ───────────────────────────────────────────────
        try:
            nlp = nlp_manager.load_spacy_model()
        except RuntimeError as exc:
            logger.error("spaCy unavailable – running degraded parse: %s", exc)
            return ResumeService._parse_without_spacy(text)

        # ── 3. Run spaCy ────────────────────────────────────────────────
        doc = nlp(text)

        # Collect sentences once here — reused by both skill extraction
        # (Strategy D) and experience extraction to avoid re-tokenising.
        sentences: List[str] = [
            sent.text.strip() for sent in doc.sents if sent.text.strip()
        ]

        # ── 4–7. Extract structured fields ─────────────────────────────
        return {
            "extracted_skills": ResumeService._extract_skills_from_doc(doc, text, sentences),
            "experience":        ResumeService._extract_experience(doc, text),
            "education":         ResumeService._extract_education(text),
            "contact":           ResumeService._extract_contact_info(doc, text),
            "summary":           text[:500],
            "parsed_at":         datetime.utcnow().isoformat(),
            "parser_version":    "nlp_v3",
            "status":            "success",
        }

    # ------------------------------------------------------------------ #
    # Extraction helpers                                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _skill_pattern(term: str) -> str:
        """
        Build a regex pattern that matches `term` as a whole token.

        Standard word-boundary \\b fails for skill names that start or end
        with non-word characters (e.g. "C++", "CI/CD", ".NET", "Next.js").
        This helper uses a lookahead / lookbehind that only checks for the
        absence of an alphanumeric character on each side, which works
        correctly for both plain words and punctuation-heavy skill names.

        Additionally, for purely alphabetic short terms (length ≤ 3, e.g.
        "Go", "R", "C") a tighter check is applied so that common
        substrings don't generate false positives (e.g. "go" inside
        "algorithm" or "google").
        """
        escaped = re.escape(term.lower())
        # For short purely-alpha terms use strict word boundaries
        if len(term) <= 3 and re.fullmatch(r"[a-zA-Z]+", term):
            return r"\b" + escaped + r"\b"
        # For all other terms (including those with +, /, ., #, etc.)
        # use a lookaround that ignores surrounding non-alpha characters.
        return r"(?<![a-zA-Z])" + escaped + r"(?![a-zA-Z])"

    @staticmethod
    def _extract_skills_from_doc(doc, text: str, sentences: List[str] = None) -> List[str]:
        """
        Extract skills via four complementary strategies.

        Strategy A – DB catalogue match
            Token-aware regex search for every Skill.name in the database.
            Handles punctuation-heavy names ("C++", "CI/CD", "Next.js").

        Strategy B – spaCy NER
            ORG and PRODUCT entities recognised by spaCy that also appear
            in the DB catalogue (case-insensitive) are promoted to skills.

        Strategy C – Synonym / alias resolution
            Maps known aliases ("k8s" → "Kubernetes", "reactjs" → "React")
            via NLPManager.get_skill_synonyms().

        Strategy D – Semantic / contextual inference  ◀ NEW
            Uses Sentence-Transformers to compare each resume sentence
            against natural-language concept descriptions for every skill
            in NLPManager.get_skill_concept_map().  This catches skills
            that are implied but never explicitly named, e.g.:
              • "Designed microservices architecture using containerized
                 deployment" → Docker, Kubernetes, System Design
              • "Automated build and release pipelines" → CI/CD
              • "Reviewed pull requests and mentored junior engineers"
                → Code Review, Mentoring
            Inferred skills are tagged with their confidence score in the
            debug log and included in the result set at the same weight
            as explicitly matched skills.

        Returns:
            Sorted, deduplicated list of skill name strings.
        """
        found: set[str] = set()
        text_lower = text.lower()

        # ── A: DB catalogue ─────────────────────────────────────────────
        try:
            db_skills: List[Skill] = Skill.query.all()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skill catalogue query failed: %s", exc)
            db_skills = []

        db_lookup: Dict[str, str] = {s.name.lower(): s.name for s in db_skills}

        for skill in db_skills:
            pattern = ResumeService._skill_pattern(skill.name)
            if re.search(pattern, text_lower, re.IGNORECASE):
                found.add(skill.name)

        # ── B: spaCy NER ─────────────────────────────────────────────────
        for ent in doc.ents:
            if ent.label_ in {"ORG", "PRODUCT"} and len(ent.text.strip()) > 1:
                db_name = db_lookup.get(ent.text.lower().strip())
                if db_name:
                    found.add(db_name)

        # ── C: Synonym / alias resolution ───────────────────────────────
        synonyms = nlp_manager.get_skill_synonyms()
        for canonical, variants in synonyms.items():
            canonical_lower = canonical.lower()
            for term in [canonical] + variants:
                pattern = ResumeService._skill_pattern(term)
                if re.search(pattern, text_lower, re.IGNORECASE):
                    db_name = db_lookup.get(canonical_lower)
                    found.add(db_name if db_name else canonical.title())
                    break

        # ── D: Semantic / contextual inference ──────────────────────────
        # Only runs when sentences are provided (full spaCy pipeline path)
        # and sentence-transformers is installed.  Skips skills already
        # found by A/B/C to avoid redundant embedding work.
        if sentences:
            concept_map = nlp_manager.get_skill_concept_map()
            # Only test skills not already captured by literal strategies
            already_found_lower = {s.lower() for s in found}
            candidates = [
                skill for skill in concept_map
                if skill.lower() not in already_found_lower
            ]

            if candidates:
                inferred = nlp_manager.extract_skills_semantically(
                    sentences=sentences,
                    candidate_skills=candidates,
                    threshold=0.40,
                )
                for skill_name, score in inferred.items():
                    # Prefer DB-canonical name if it exists, else use the
                    # concept map key directly (it will be auto-created on sync)
                    db_name = db_lookup.get(skill_name.lower())
                    resolved = db_name if db_name else skill_name
                    found.add(resolved)
                    logger.info(
                        "Contextually inferred skill: '%s' (score=%.4f)", resolved, score
                    )

        logger.debug(
            "_extract_skills_from_doc: db_skills=%d, synonyms_checked=%d, "
            "semantic_candidates=%d, total_found=%d",
            len(db_skills),
            len(synonyms),
            len(concept_map) if sentences else 0,
            len(found),
        )
        return sorted(found)

    @staticmethod
    def _extract_experience(doc, text: str) -> List[Dict]:
        """
        Extract work-experience entries.

        Algorithm:
          1. Detect the 'Experience' section header in the raw text.
          2. Within that section, find lines containing date ranges.
          3. Treat the next non-blank line as the role/company description.
          4. Supplement with spaCy DATE + ORG co-occurrences per sentence.

        Returns:
            List of {'period': str, 'description': str} dicts (max 20).
        """
        experiences: List[Dict] = []
        seen: set[str] = set()
        lines = text.splitlines()

        # Locate experience section
        in_section = False
        section_lines: List[str] = []
        for line in lines:
            lower = line.strip().lower()
            if any(h in lower for h in _EXPERIENCE_HEADERS):
                in_section = True
                continue
            if in_section and any(h in lower for h in _EDUCATION_HEADERS):
                in_section = False
            if in_section and line.strip():
                section_lines.append(line.strip())

        target = section_lines if section_lines else lines

        for i, line in enumerate(target):
            matches = _DATE_RANGE_RE.findall(line)
            if not matches:
                continue
            period = " | ".join(m.strip() for m in matches if m.strip())
            if not period or period in seen:
                continue
            seen.add(period)

            description = ""
            for j in range(i + 1, min(i + 4, len(target))):
                candidate = target[j].strip()
                if candidate and not _DATE_RANGE_RE.search(candidate):
                    description = candidate
                    break

            experiences.append({"period": period, "description": description})

        # Supplement with spaCy sentence-level DATE + ORG pairs
        for sent in doc.sents:
            dates = [e.text for e in sent.ents if e.label_ == "DATE"]
            orgs  = [e.text for e in sent.ents if e.label_ == "ORG"]
            if dates and orgs and dates[0] not in seen:
                seen.add(dates[0])
                experiences.append(
                    {"period": dates[0], "description": ", ".join(orgs)}
                )

        return experiences[:20]

    @staticmethod
    def _extract_education(text: str) -> List[Dict]:
        """
        Extract education entries by scanning for degree keywords.

        Returns:
            List of {'degree': str, 'details': str} dicts (max 10).
        """
        education: List[Dict] = []
        lines = text.splitlines()

        in_section = False
        section_lines: List[str] = []
        for line in lines:
            lower = line.strip().lower()
            if any(h in lower for h in _EDUCATION_HEADERS):
                in_section = True
                continue
            if in_section and any(h in lower for h in _EXPERIENCE_HEADERS):
                in_section = False
            if in_section and line.strip():
                section_lines.append(line.strip())

        target = section_lines if section_lines else lines

        for i, line in enumerate(target):
            if any(kw in line.lower() for kw in _DEGREE_KEYWORDS):
                details = target[i + 1].strip() if i + 1 < len(target) else ""
                education.append({"degree": line.strip(), "details": details})

        return education[:10]

    @staticmethod
    def _extract_contact_info(doc, text: str) -> Dict[str, Optional[str]]:
        """
        Extract email and phone from resume text.

        Strategy: regex for email (reliable), spaCy NER for phone with
        regex as fallback.

        Returns:
            {'email': str|None, 'phone': str|None}
        """
        contact: Dict[str, Optional[str]] = {"email": None, "phone": None}

        emails = _EMAIL_RE.findall(text)
        if emails:
            contact["email"] = emails[0]

        # spaCy phone entity (not all models support this label)
        for ent in doc.ents:
            if ent.label_ in {"PHONE_NUMBER", "PHONE"}:
                contact["phone"] = ent.text.strip()
                break

        if contact["phone"] is None:
            for candidate in _PHONE_RE.findall(text):
                if len(re.sub(r"\D", "", candidate)) >= 7:
                    contact["phone"] = candidate.strip()
                    break

        return contact

    # ------------------------------------------------------------------ #
    # Degraded-mode fallback (no spaCy)                                   #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_without_spacy(text: str) -> Dict:
        """
        Minimal extraction using only regex and synonym matching.

        Used when spaCy cannot be loaded at runtime.  Returns a valid
        result dict with reduced accuracy and status='degraded_no_spacy'.
        """
        logger.warning("Running resume parsing in degraded mode (spaCy unavailable).")

        skills: set[str] = set()
        text_lower = text.lower()
        synonyms = nlp_manager.get_skill_synonyms()

        # Build DB lookup even in degraded mode so canonical names resolve
        try:
            db_skills_deg: List[Skill] = Skill.query.all()
            db_lookup = {s.name.lower(): s.name for s in db_skills_deg}
        except Exception:  # noqa: BLE001
            db_lookup = {}

        for canonical, variants in synonyms.items():
            canonical_lower = canonical.lower()
            for term in [canonical] + variants:
                pattern = ResumeService._skill_pattern(term)
                if re.search(pattern, text_lower, re.IGNORECASE):
                    db_name = db_lookup.get(canonical_lower) if db_lookup else None
                    skills.add(db_name if db_name else canonical.title())
                    break

        contact: Dict[str, Optional[str]] = {"email": None, "phone": None}
        emails = _EMAIL_RE.findall(text)
        if emails:
            contact["email"] = emails[0]
        for candidate in _PHONE_RE.findall(text):
            if len(re.sub(r"\D", "", candidate)) >= 7:
                contact["phone"] = candidate.strip()
                break

        return {
            "extracted_skills": sorted(skills),
            "experience":        [],
            "education":         ResumeService._extract_education(text),
            "contact":           contact,
            "summary":           text[:500],
            "parsed_at":         datetime.utcnow().isoformat(),
            "parser_version":    "nlp_v2_degraded",
            "status":            "degraded_no_spacy",
        }

    # ------------------------------------------------------------------ #
    # Skill sync helper                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def sync_parsed_skills_to_profile(
        user_id: int,
        skill_names: List[str],
        default_proficiency: int = 2,
    ) -> int:
        """
        Add NLP-extracted skills to the user's skill profile.

        For each skill name in the list:
          1. Look up the Skill row in the catalogue (case-insensitive).
          2. If no row exists, CREATE one automatically so the skill is
             persisted to the `skills` table and becomes available
             system-wide (visible in the skills catalogue, assignable to
             projects, etc.).
          3. Skip if the user already has a UserSkill entry for that skill.
          4. Otherwise create a UserSkill row (unverified, default proficiency).

        Args:
            user_id:             Target user.
            skill_names:         List of skill name strings from parse result.
            default_proficiency: Initial proficiency level (1-5). Default 2.

        Returns:
            Number of newly added UserSkill records.
        """
        count = 0
        for skill_name in skill_names:
            if not skill_name or not skill_name.strip():
                continue

            # ── 1. Find or create the Skill catalogue row ───────────────
            skill = Skill.query.filter(
                db.func.lower(Skill.name) == skill_name.lower()
            ).first()

            if not skill:
                # Auto-create: assign a sensible category via the NLP manager
                category = nlp_manager.get_skill_category(skill_name)
                skill = Skill(name=skill_name.strip(), category=category)
                db.session.add(skill)
                db.session.flush()   # Populate skill.id without a full commit
                logger.info(
                    "Auto-created Skill catalogue entry: '%s' (category=%s)",
                    skill_name, category,
                )

            # ── 2. Skip if user already has this skill ──────────────────
            if UserSkill.query.filter_by(
                user_id=user_id, skill_id=skill.id
            ).first():
                continue

            # ── 3. Create the UserSkill row ─────────────────────────────
            db.session.add(
                UserSkill(
                    user_id=user_id,
                    skill_id=skill.id,
                    proficiency_level=default_proficiency,
                    is_verified=False,
                )
            )
            count += 1

        # Single commit covers both new Skill rows and new UserSkill rows
        db.session.commit()
        if count:
            logger.info(
                "Synced %d new skill(s) to profile for user_id=%d.", count, user_id
            )
        return count

    # ------------------------------------------------------------------ #
    # Manager / admin read helpers                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_recent_resume_updates(limit: int = 20) -> List[Dict]:
        """
        Return the most recently updated resumes across all employees.

        Used by:
          • app/manager.py → view_updates()
          • app/admin.py   → any audit dashboard

        Returns:
            List of dicts: {user_id, username, original_filename, last_updated}.
        """
        resumes = (
            Resume.query.join(Resume.user)
            .order_by(Resume.last_updated.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "user_id":           r.user_id,
                "username":          r.user.username,
                "original_filename": r.original_filename,
                "last_updated":      r.last_updated,
            }
            for r in resumes
        ]

    # ------------------------------------------------------------------ #
    # Private utilities                                                    #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _empty_result(status: str) -> Dict:
        """Return a structurally valid but empty parsed-content dict."""
        return {
            "extracted_skills": [],
            "experience":        [],
            "education":         [],
            "contact":           {"email": None, "phone": None},
            "summary":           "",
            "parsed_at":         datetime.utcnow().isoformat(),
            "parser_version":    "nlp_v2",
            "status":            status,
        }