"""
app/services/nlp_manager.py

NLP Manager - Centralized NLP model management for HireSense.

Implements the singleton pattern to ensure models are loaded only once
per Flask worker process, preventing memory overhead during request handling.

Usage (from any service or blueprint):
    from app.services.nlp_manager import nlp_manager

    nlp   = nlp_manager.load_spacy_model()
    model = nlp_manager.load_sentence_transformer()

Environment variables (set in .env):
    NLP_ENABLED                  – "true" / "false"  (default: "true")
    SPACY_MODEL                  – spaCy model name   (default: "en_core_web_lg")
    SENTENCE_TRANSFORMER_MODEL   – ST model name      (default: "sentence-transformers/all-MiniLM-L6-v2")
    BERT_MODEL                   – BERT model name    (default: "bert-base-uncased")
"""

import logging
import os
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class NLPManager:
    """
    Singleton NLP model manager.

    All three model loaders are lazy: nothing is downloaded or loaded until
    the first call to the respective load_*() method.  This keeps Flask
    startup time fast when NLP features are not immediately exercised.
    """

    _instance: Optional["NLPManager"] = None

    def __new__(cls) -> "NLPManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        # Lazy model references – populated on first use
        self._spacy_model = None
        self._sentence_transformer = None
        self._bert_tokenizer = None
        self._bert_model = None

        # Config (read from environment with sensible defaults)
        self.nlp_enabled: bool = os.getenv("NLP_ENABLED", "true").lower() == "true"
        self.spacy_model_name: str = os.getenv("SPACY_MODEL", "en_core_web_lg")
        self.sentence_transformer_name: str = os.getenv(
            "SENTENCE_TRANSFORMER_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        self.bert_model_name: str = os.getenv("BERT_MODEL", "bert-base-uncased")

        self._initialized = True
        logger.info("NLPManager initialised (models deferred until first use).")

    # ------------------------------------------------------------------
    # Model loaders
    # ------------------------------------------------------------------

    def load_spacy_model(self):
        """
        Load and cache the spaCy language model.

        Fallback chain:
            configured model  →  en_core_web_md  →  en_core_web_sm  →  auto-download sm

        :returns: spacy.Language instance.
        :rtype: spacy.Language
        :raises RuntimeError: if no spaCy model can be loaded at all.
        """
        if self._spacy_model is not None:
            return self._spacy_model

        import spacy  # noqa: PLC0415 – deferred to avoid mandatory dep at import

        fallback_chain = [
            self.spacy_model_name,
            "en_core_web_md",
            "en_core_web_sm",
        ]

        for model_name in fallback_chain:
            try:
                self._spacy_model = spacy.load(model_name)
                logger.info("Loaded spaCy model: %s", model_name)
                return self._spacy_model
            except OSError:
                logger.warning(
                    "spaCy model '%s' not found – trying next in chain.", model_name
                )

        # Final attempt: download the small model
        logger.warning("Attempting to download 'en_core_web_sm' …")
        os.system("python -m spacy download en_core_web_sm")  # noqa: S605
        try:
            self._spacy_model = spacy.load("en_core_web_sm")
            logger.info("Downloaded and loaded: en_core_web_sm")
            return self._spacy_model
        except OSError as exc:
            raise RuntimeError(
                "No spaCy model could be loaded. "
                "Run: python -m spacy download en_core_web_lg"
            ) from exc

    def load_sentence_transformer(self):
        """
        Load and cache the Sentence-Transformer model.

        Used by SkillService.compute_semantic_similarity() and
        LearningPathService._generate_ai_learning_path().

        :returns: SentenceTransformer instance.
        :rtype: SentenceTransformer
        :raises ImportError: if sentence-transformers is not installed.
        """
        if self._sentence_transformer is not None:
            return self._sentence_transformer

        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc

        self._sentence_transformer = SentenceTransformer(
            self.sentence_transformer_name
        )
        logger.info("Loaded Sentence-Transformer: %s", self.sentence_transformer_name)
        return self._sentence_transformer

    def load_bert_model(self) -> Tuple:
        """
        Load and cache (tokenizer, model) for the configured BERT model.

        Prefer load_sentence_transformer() for similarity tasks – this is
        only needed for token-level classification or fine-tuned workflows.

        Returns:
            Tuple of (AutoTokenizer, AutoModel).

        Raises:
            ImportError: if transformers / torch are not installed.
        """
        if self._bert_model is not None:
            return self._bert_tokenizer, self._bert_model

        try:
            from transformers import AutoModel, AutoTokenizer  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "transformers is not installed. "
                "Run: pip install transformers torch"
            ) from exc

        self._bert_tokenizer = AutoTokenizer.from_pretrained(self.bert_model_name)
        self._bert_model = AutoModel.from_pretrained(self.bert_model_name)
        logger.info("Loaded BERT model: %s", self.bert_model_name)
        return self._bert_tokenizer, self._bert_model

    # ------------------------------------------------------------------
    # Skill synonym dictionary
    # ------------------------------------------------------------------

    def get_skill_synonyms(self) -> Dict[str, List[str]]:
        """
        Return a canonical → variants synonym map used for fuzzy matching.

        Keys are lower-cased canonical names (should align with Skill.name
        in the database, case-insensitively).  Extend this dict as the
        skills catalogue grows.
        """
        return {
            # Programming Languages
            "python": ["python3", "py", "python programming", "python2"],
            "javascript": ["js", "ecmascript", "es6", "es2015", "es2020", "vanilla js"],
            "typescript": ["ts"],
            "java": ["java se", "java ee", "jvm"],
            "c#": ["csharp", "c sharp", ".net c#"],
            "c++": ["cpp", "c plus plus"],
            "ruby": ["ruby on rails", "ror"],
            "php": ["php7", "php8"],
            "go": ["golang"],
            "rust": ["rust lang"],
            "kotlin": [],
            "swift": ["swift programming"],
            "scala": [],
            "r": ["r programming", "r language"],
            # Web frameworks / libraries
            "react": ["reactjs", "react.js", "react js"],
            "angular": ["angularjs", "angular.js", "angular 2+"],
            "vue": ["vuejs", "vue.js", "vue js"],
            "django": ["django rest framework", "drf"],
            "flask": ["flask python"],
            "fastapi": ["fast api"],
            "spring": ["spring boot", "spring framework"],
            "express": ["expressjs", "express.js"],
            "next.js": ["nextjs", "next js"],
            # Databases
            "sql": ["structured query language"],
            "postgresql": ["postgres", "psql"],
            "mysql": [],
            "mongodb": ["mongo", "mongo db"],
            "redis": [],
            "elasticsearch": ["elastic search", "es"],
            "sqlite": [],
            "oracle": ["oracle db", "oracle database"],
            # DevOps / Cloud
            "docker": ["containerization", "containers", "dockerfile"],
            "kubernetes": ["k8s", "k8", "kube"],
            "aws": ["amazon web services", "amazon aws"],
            "azure": ["microsoft azure", "ms azure"],
            "gcp": ["google cloud", "google cloud platform"],
            "terraform": ["tf"],
            "ansible": [],
            "jenkins": [],
            "git": ["github", "gitlab", "bitbucket", "version control"],
            "ci/cd": [
                "continuous integration",
                "continuous deployment",
                "continuous delivery",
                "github actions",
                "gitlab ci",
                "circleci",
            ],
            "linux": ["unix", "bash scripting", "shell scripting", "ubuntu"],
            # Data / ML
            "machine learning": ["ml", "predictive modelling", "predictive modeling"],
            "deep learning": ["dl", "neural networks", "neural network"],
            "nlp": ["natural language processing", "text analytics", "text mining"],
            "data visualization": [
                "tableau", "power bi", "matplotlib", "seaborn", "d3.js",
            ],
            "statistics": ["statistical analysis", "stats"],
            # Methodologies / soft skills
            "agile": ["scrum", "kanban", "sprint planning"],
            "system design": ["systems design", "architecture", "software architecture"],
            "code review": ["peer review", "pull requests", "pr review"],
            "mentoring": ["coaching", "mentorship"],
            "project management": ["pm", "pmp"],
            "communication": ["written communication", "verbal communication"],
            # Security
            "cybersecurity": ["information security", "infosec", "cyber security"],
            "network security": ["network defence", "network defense"],
            "penetration testing": ["pen testing", "pentesting", "ethical hacking"],
            # Testing
            "testing": ["qa", "quality assurance", "software testing"],
            "automation": ["test automation", "automated testing"],
            "selenium": ["selenium webdriver"],
            "api testing": ["rest api testing", "postman"],
        }

    def get_skill_category(self, canonical: str) -> str:
        """
        Return the category string for a canonical skill name.

        Used when auto-creating Skill catalogue rows from NLP extraction so
        that every new row has a meaningful category rather than NULL.

        Returns one of: "technical", "soft", "domain".
        Defaults to "technical" for anything not explicitly mapped.
        """
        _SOFT_SKILLS = {
            "agile", "scrum", "kanban", "communication",
            "mentoring", "project management",
        }
        _DOMAIN_SKILLS = {
            "statistics", "data visualization", "machine learning",
            "deep learning", "nlp", "cybersecurity",
            "network security", "penetration testing",
        }
        lower = canonical.lower()
        if lower in _SOFT_SKILLS:
            return "soft"
        if lower in _DOMAIN_SKILLS:
            return "domain"
        return "technical"

    def get_skill_concept_map(self) -> Dict[str, List[str]]:
        """
        Return a map of canonical skill names to natural-language concept
        descriptions used for semantic (contextual) skill inference.

        Each entry is a list of phrases that describe how that skill appears
        in practice — NOT the skill name itself.  This allows the semantic
        extractor to infer "Docker" from "containerized deployment" or
        "Kubernetes" from "orchestrated microservices at scale", even when
        the skill name is never written in the resume.

        These descriptions are embedded once and compared against embeddings
        of each resume sentence via cosine similarity.
        """
        return {
            # ── Infrastructure & DevOps ──────────────────────────────────
            "Docker": [
                "containerized deployment",
                "container images and registries",
                "packaging applications in containers",
                "built and shipped docker containers",
                "ran services inside isolated containers",
                "used containerization for deployment",
                "wrote Dockerfiles for microservices",
            ],
            "Kubernetes": [
                "orchestrated microservices at scale",
                "managed container clusters",
                "deployed workloads on a container orchestration platform",
                "horizontal pod autoscaling",
                "configured ingress controllers and service meshes",
                "rolling deployments with zero downtime",
                "managed distributed containerized workloads",
            ],
            "AWS": [
                "deployed infrastructure on the cloud",
                "used managed cloud services for storage and compute",
                "hosted applications on Amazon cloud",
                "leveraged cloud-native services for scalability",
                "provisioned EC2 instances and S3 buckets",
                "used Lambda for serverless compute",
                "configured VPCs and IAM roles",
            ],
            "Terraform": [
                "infrastructure as code",
                "provisioned cloud resources declaratively",
                "automated infrastructure provisioning",
                "managed cloud environments with configuration files",
                "used IaC to version-control infrastructure",
            ],
            "CI/CD": [
                "set up automated build and deployment pipelines",
                "continuous integration and continuous delivery",
                "automated testing and deployment workflows",
                "pushed code through automated release pipelines",
                "used pipeline tools to ship code continuously",
                "configured automated deployment on every merge",
            ],
            "Linux": [
                "administered Linux servers",
                "managed Unix-based systems",
                "wrote shell scripts to automate server tasks",
                "configured and maintained Linux environments",
                "deployed on bare-metal and virtual Linux machines",
            ],
            # ── Programming Languages ────────────────────────────────────
            "Python": [
                "wrote backend services in a scripting language",
                "automated data processing pipelines",
                "built REST APIs using a dynamically typed language",
                "scripted automation and tooling",
                "used a high-level language for data analysis",
            ],
            "JavaScript": [
                "built interactive web interfaces",
                "developed client-side logic for browsers",
                "implemented dynamic frontend behavior",
                "created single-page applications",
                "wrote asynchronous event-driven code for the web",
            ],
            "TypeScript": [
                "added static typing to a JavaScript codebase",
                "used a typed superset of JavaScript",
                "improved code reliability with compile-time type checks",
            ],
            "Java": [
                "built enterprise backend services",
                "developed high-throughput JVM applications",
                "wrote object-oriented backend systems",
                "used a statically typed JVM language for large-scale systems",
            ],
            # ── Web Frameworks ───────────────────────────────────────────
            "React": [
                "built component-based user interfaces",
                "developed single-page applications with a frontend library",
                "managed application state with hooks",
                "created reusable UI components for a web app",
            ],
            "Django": [
                "built full-stack web applications with a Python framework",
                "implemented MVC web applications in Python",
                "used an ORM for database access in a web framework",
            ],
            "Flask": [
                "built lightweight REST APIs in Python",
                "developed microservices using a minimal Python web framework",
                "created RESTful endpoints with a Python micro-framework",
            ],
            "Spring": [
                "built enterprise Java web applications",
                "used dependency injection for a Java backend",
                "developed REST APIs with a Java framework",
            ],
            # ── Databases ────────────────────────────────────────────────
            "PostgreSQL": [
                "designed and queried relational databases",
                "optimised complex SQL queries",
                "managed relational data with an open-source RDBMS",
                "wrote stored procedures and database migrations",
            ],
            "MongoDB": [
                "stored unstructured data in a document database",
                "used a NoSQL database for flexible schema storage",
                "queried JSON-like documents at scale",
            ],
            "Redis": [
                "implemented in-memory caching to improve performance",
                "used a key-value store for session management",
                "reduced database load with a caching layer",
            ],
            "SQL": [
                "wrote complex queries to extract and transform data",
                "designed normalized relational schemas",
                "performed joins aggregations and subqueries",
                "optimised database query performance",
            ],
            # ── Architecture & System Design ─────────────────────────────
            "System Design": [
                "designed microservices architecture",
                "architected distributed systems for high availability",
                "designed scalable backend systems",
                "led technical design of multi-tier applications",
                "defined API contracts and service boundaries",
                "designed event-driven architectures",
                "broke a monolith into independent services",
            ],
            "Machine Learning": [
                "trained predictive models on structured data",
                "built and evaluated classification and regression models",
                "applied supervised learning to business problems",
                "feature engineering and model selection",
                "deployed ML models to production",
            ],
            "Deep Learning": [
                "trained neural networks for computer vision or NLP tasks",
                "fine-tuned transformer models",
                "used convolutional or recurrent neural networks",
                "built and trained multi-layer neural architectures",
            ],
            "NLP": [
                "processed and analysed unstructured text data",
                "built text classification or named entity recognition systems",
                "used language models for document understanding",
                "extracted information from natural language text",
            ],
            # ── Methodologies ────────────────────────────────────────────
            "Agile": [
                "worked in two-week sprint cycles",
                "participated in daily standups and retrospectives",
                "collaborated with cross-functional agile teams",
                "delivered features iteratively using scrum",
                "used a kanban board to manage work in progress",
            ],
            "Code Review": [
                "reviewed pull requests and provided technical feedback",
                "ensured code quality through peer review",
                "approved and merged developer contributions",
                "gave constructive feedback on code changes",
            ],
            "Mentoring": [
                "guided junior developers in best practices",
                "onboarded and mentored new engineers",
                "coached team members on technical skills",
                "supported professional growth of junior staff",
            ],
            # ── Security ─────────────────────────────────────────────────
            "Cybersecurity": [
                "implemented security controls and vulnerability mitigations",
                "conducted threat modelling and risk assessments",
                "hardened systems against common attack vectors",
                "ensured compliance with security standards",
            ],
            "Penetration Testing": [
                "performed ethical hacking and security audits",
                "tested systems for vulnerabilities and exploits",
                "conducted red-team exercises",
                "identified and reported security weaknesses",
            ],
            # ── Testing ──────────────────────────────────────────────────
            "Testing": [
                "wrote unit integration and end-to-end tests",
                "ensured software quality through automated testing",
                "achieved high test coverage for critical code paths",
                "used test-driven development",
            ],
            "Selenium": [
                "automated browser-based UI tests",
                "wrote end-to-end test scripts for web interfaces",
                "used a browser automation framework for regression testing",
            ],
            # ── Git / Version Control ────────────────────────────────────
            "Git": [
                "managed source code with version control",
                "used branching strategies like gitflow",
                "collaborated through pull requests and code merges",
                "maintained a clean commit history",
            ],
        }

    def extract_skills_semantically(
        self,
        sentences: List[str],
        candidate_skills: List[str],
        threshold: float = 0.40,
    ) -> Dict[str, float]:
        """
        Infer skills from resume sentences using semantic similarity.

        For each candidate skill this method checks whether any sentence
        in the resume is semantically close enough to any of that skill's
        concept descriptions (from get_skill_concept_map).  If the maximum
        cosine similarity across all sentence-concept pairs exceeds
        `threshold`, the skill is considered inferred.

        Args:
            sentences:        List of individual sentences from the resume.
            candidate_skills: Skill names to test (typically the keys of
                              get_skill_concept_map()).
            threshold:        Cosine similarity cut-off (0–1).  Default 0.40
                              balances recall vs. precision well in practice.
                              Lower → more skills inferred (higher recall,
                              more false positives).
                              Higher → fewer but more confident inferences.

        Returns:
            Dict mapping inferred skill name → best similarity score found.
            Only skills that exceed the threshold are included.
        """
        if not sentences or not candidate_skills:
            return {}

        try:
            model = self.load_sentence_transformer()
        except (ImportError, Exception) as exc:  # noqa: BLE001
            logger.warning(
                "Sentence-Transformer unavailable; skipping semantic extraction: %s",
                exc,
            )
            return {}

        concept_map = self.get_skill_concept_map()
        inferred: Dict[str, float] = {}

        # Embed all resume sentences in a single batched call (fast)
        try:
            import numpy as np  # noqa: PLC0415
            sentence_embeddings = model.encode(
                sentences, batch_size=64, show_progress_bar=False, normalize_embeddings=True
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Sentence embedding failed: %s", exc)
            return {}

        for skill_name in candidate_skills:
            concepts = concept_map.get(skill_name)
            if not concepts:
                continue

            # Embed all concept phrases for this skill in one batched call
            try:
                concept_embeddings = model.encode(
                    concepts,
                    batch_size=64,
                    show_progress_bar=False,
                    normalize_embeddings=True,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Concept embedding failed for skill '%s': %s", skill_name, exc
                )
                continue

            # Cosine similarity matrix: shape (num_sentences, num_concepts)
            # Since embeddings are L2-normalised, dot product == cosine similarity
            similarity_matrix = np.dot(sentence_embeddings, concept_embeddings.T)

            best_score = float(similarity_matrix.max())
            if best_score >= threshold:
                inferred[skill_name] = round(best_score, 4)
                logger.debug(
                    "Semantic inference: '%s' scored %.4f (threshold=%.2f)",
                    skill_name, best_score, threshold,
                )

        logger.info(
            "Semantic extraction: %d/%d candidate skills inferred above threshold=%.2f",
            len(inferred), len(candidate_skills), threshold,
        )
        return inferred

    def resolve_to_canonical(self, term: str) -> Optional[str]:
        """
        Map an extracted term to its canonical skill name via the synonym dict.

        Returns title-cased canonical if found, else None.

        Example:
            resolve_to_canonical("k8s")  →  "Kubernetes"
        """
        term_lower = term.lower().strip()
        for canonical, variants in self.get_skill_synonyms().items():
            all_forms = [canonical] + [v.lower() for v in variants]
            if term_lower in all_forms:
                return canonical.title()
        return None


# ── Module-level singleton ──────────────────────────────────────────────────
# Import this object everywhere NLP models are needed:
#   from app.services.nlp_manager import nlp_manager
nlp_manager = NLPManager()