"""
app/employee.py

Employee Blueprint - Routes for employee-specific functionality.

Handles project assignments, skill management, resume uploads,
and learning path features for employees.

NLP integration points
──────────────────────
• upload_resume()  – after a successful upload the NLP pipeline is
  triggered automatically via ResumeService.parse_resume_skills().
  Extracted skills are immediately synced to the user's profile via
  ResumeService.sync_parsed_skills_to_profile().

• view_resume()    – displays parsed skills from Resume.parsed_content
  (if available) so the employee can review what was extracted.
"""

import json
import logging
import os
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.models import ProjectAssignment, Skill, User, UserSkill
from app.services.learning_path_service import LearningPathService
from app.services.project_service import ProjectService
from app.services.resume_service import ResumeService
from app.services.skill_service import SkillService

logger = logging.getLogger(__name__)

employee_bp = Blueprint("employee", __name__, url_prefix="/employee")







def employee_required(f):
    """Restrict route to authenticated users with the 'employee' role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "employee":
            abort(403)
        return f(*args, **kwargs)
    return decorated







@employee_bp.route("/")
@employee_required
def dashboard():
    """Employee dashboard: active assignments, skills, resume, learning path."""
    assignments = ProjectService.get_employee_assignments(current_user.id, status="active")
    skills      = SkillService.get_user_skills(current_user.id)
    active_path = LearningPathService.get_active_learning_path(current_user.id)
    resume      = ResumeService.get_user_resume(current_user.id)

    
    path_progress = None
    if active_path:
        path_progress = LearningPathService.get_path_progress(active_path)

    return render_template(
        "employee/dashboard.html",
        assignments=assignments,
        skills=skills,
        active_path=active_path,
        path_progress=path_progress,
        resume=resume,
    )







@employee_bp.route("/assignments")
@employee_required
def list_assignments():
    """List all project assignments for the current employee."""
    status_filter = request.args.get("status", "")
    assignments = ProjectService.get_employee_assignments(
        current_user.id, status=status_filter or None
    )
    return render_template(
        "employee/assignments.html",
        assignments=assignments,
        status_filter=status_filter,
    )


@employee_bp.route("/assignments/<int:assignment_id>")
@employee_required
def view_assignment(assignment_id):
    """Detail view for a single assignment – shows project skill comparison."""
    assignment = ProjectService.get_assignment_by_id(assignment_id)
    if not assignment or assignment.user_id != current_user.id:
        abort(404)

    skill_requirements = SkillService.get_project_skill_requirements(
        assignment.project_id
    )
    my_skills    = SkillService.get_user_skills(current_user.id)
    my_skill_ids = {s["skill_id"] for s in my_skills}

    return render_template(
        "employee/assignment_detail.html",
        assignment=assignment,
        skill_requirements=skill_requirements,
        my_skills=my_skills,
        my_skill_ids=my_skill_ids,
    )







@employee_bp.route("/profile")
@employee_required
def profile():
    """Employee's own profile page."""
    skills      = SkillService.get_user_skills(current_user.id)
    resume      = ResumeService.get_user_resume(current_user.id)
    active_path = LearningPathService.get_active_learning_path(current_user.id)

    return render_template(
        "employee/profile.html",
        user=current_user,
        skills=skills,
        resume=resume,
        active_path=active_path,
    )







@employee_bp.route("/resume")
@employee_required
def view_resume():
    """
    Resume overview page.

    Passes parsed NLP content (extracted_skills, experience, education,
    contact) to the template when available so the employee can review
    what the parser found.
    """
    resume = ResumeService.get_user_resume(current_user.id)

    parsed_data = {}
    if resume and resume.parsed_content:
        try:
            parsed_data = json.loads(resume.parsed_content)
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                "Could not decode parsed_content for resume id=%s",
                resume.id if resume else "N/A",
            )

    return render_template(
        "employee/resume.html",
        resume=resume,
        parsed_data=parsed_data,
    )


@employee_bp.route("/resume/upload", methods=["GET", "POST"])
@employee_required
def upload_resume():
    """
    Upload or replace the employee's resume.

    On a successful upload the NLP pipeline is triggered automatically:
      1. ResumeService.parse_resume_skills()        – runs full NLP parse.
      2. ResumeService.sync_parsed_skills_to_profile() – adds new skills
         found in the resume to the user's skill profile (proficiency=2,
         unverified – a manager can verify later).

    NLP errors are caught and logged; the upload itself is still marked
    as successful so a parsing failure never blocks the user.
    """
    if request.method == "POST":
        if "resume_file" not in request.files:
            flash("No file selected.", "danger")
            return redirect(url_for("employee.view_resume"))

        file = request.files["resume_file"]
        if not file.filename:
            flash("No file selected.", "danger")
            return redirect(url_for("employee.view_resume"))

        try:
            resume = ResumeService.upload_resume(current_user.id, file)
            flash("Resume uploaded successfully.", "success")

            
            try:
                parsed = ResumeService.parse_resume_skills(resume.id)
                extracted_skills = parsed.get("extracted_skills", [])

                if extracted_skills:
                    added = ResumeService.sync_parsed_skills_to_profile(
                        current_user.id, extracted_skills, default_proficiency=2
                    )
                    if added:
                        flash(
                            f"NLP extracted {len(extracted_skills)} skill(s) from your "
                            f"resume and added {added} new skill(s) to your profile.",
                            "info",
                        )
                    else:
                        flash(
                            f"NLP extracted {len(extracted_skills)} skill(s) "
                            "(all already in your profile).",
                            "info",
                        )
                else:
                    flash(
                        "Resume uploaded. No skills could be auto-extracted; "
                        "please add them manually.",
                        "info",
                    )
            except Exception as nlp_exc:  
                
                logger.error(
                    "NLP parsing failed for resume id=%s: %s", resume.id, nlp_exc
                )
                flash(
                    "Resume uploaded, but automatic skill extraction failed. "
                    "Please add your skills manually.",
                    "warning",
                )

            return redirect(url_for("employee.view_resume"))

        except ValueError as e:
            flash(str(e), "danger")

    return render_template("employee/resume_upload.html")


@employee_bp.route("/resume/download")
@employee_required
def download_resume():
    """Serve the employee's own resume file as a download."""
    resume = ResumeService.get_user_resume(current_user.id)
    if not resume or not resume.file_path:
        abort(404)

    if not os.path.exists(resume.file_path):
        flash("Resume file not found on server.", "danger")
        return redirect(url_for("employee.view_resume"))

    return send_file(
        resume.file_path,
        as_attachment=True,
        download_name=resume.original_filename or "resume",
    )


@employee_bp.route("/resume/delete", methods=["POST"])
@employee_required
def delete_resume():
    """Delete the employee's own resume."""
    if ResumeService.delete_resume(current_user.id):
        flash("Resume deleted.", "success")
    else:
        flash("No resume to delete.", "info")
    return redirect(url_for("employee.view_resume"))







@employee_bp.route("/skills")
@employee_required
def my_skills():
    """Skill management page."""
    skills          = SkillService.get_user_skills(current_user.id)
    all_skills      = SkillService.get_all_skills()
    added_skill_ids = {s["skill_id"] for s in skills}
    available       = [s for s in all_skills if s.id not in added_skill_ids]

    
    skill_distribution = _calculate_skill_distribution(skills)

    return render_template(
        "employee/skills.html",
        skills=skills,
        available_skills=available,
        skill_distribution=skill_distribution,
    )


def _calculate_skill_distribution(skills):
    """Calculate skill distribution percentages by category."""
    if not skills:
        return {"technical": 0, "soft": 0, "domain": 0}

    
    categories = {"technical": [], "soft": [], "domain": []}
    for skill in skills:
        category = (skill.get("category") or "technical").lower()
        if category in categories:
            categories[category].append(skill["proficiency_level"])
        else:
            categories["technical"].append(skill["proficiency_level"])

    
    distribution = {}
    for cat, levels in categories.items():
        if levels:
            avg = sum(levels) / len(levels)
            distribution[cat] = int((avg / 5) * 100)
        else:
            distribution[cat] = 0

    return distribution


@employee_bp.route("/skills/add", methods=["POST"])
@employee_required
def add_skill():
    """Add a skill to the employee's profile."""
    skill_id   = request.form.get("skill_id", type=int)
    proficiency = request.form.get("proficiency_level", type=int, default=1)

    if not skill_id:
        flash("Please select a skill.", "danger")
        return redirect(url_for("employee.my_skills"))

    try:
        SkillService.add_user_skill(current_user.id, skill_id, proficiency)
        flash("Skill added.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.my_skills"))


@employee_bp.route("/skills/update", methods=["POST"])
@employee_required
def update_skill():
    """Update proficiency for an existing skill."""
    skill_id    = request.form.get("skill_id", type=int)
    proficiency = request.form.get("proficiency_level", type=int)

    if not skill_id or not proficiency:
        flash("Invalid request.", "danger")
        return redirect(url_for("employee.my_skills"))

    try:
        SkillService.update_user_skill(current_user.id, skill_id, proficiency)
        flash("Skill updated.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.my_skills"))


@employee_bp.route("/skills/remove", methods=["POST"])
@employee_required
def remove_skill():
    """Remove a skill from the employee's profile."""
    skill_id = request.form.get("skill_id", type=int)

    if SkillService.remove_user_skill(current_user.id, skill_id):
        flash("Skill removed.", "success")
    else:
        flash("Skill not found.", "danger")

    return redirect(url_for("employee.my_skills"))







@employee_bp.route("/compare")
@employee_required
def compare_roles():
    """Compare the employee's current profile against a target role."""
    target_role     = request.args.get("target_role", "")
    available_roles = LearningPathService.get_available_target_roles()
    comparison      = None

    if target_role:
        try:
            comparison = LearningPathService.compare_roles(current_user.id, target_role)
        except ValueError as e:
            flash(str(e), "danger")

    return render_template(
        "employee/compare.html",
        available_roles=available_roles,
        selected_role=target_role,
        comparison=comparison,
    )







@employee_bp.route("/learning-paths")
@employee_required
def learning_paths():
    """List all learning paths for the employee."""
    paths           = LearningPathService.get_user_learning_paths(current_user.id)
    available_roles = LearningPathService.get_available_target_roles()

    return render_template(
        "employee/learning_paths.html",
        paths=paths,
        available_roles=available_roles,
    )


@employee_bp.route("/learning-paths/generate", methods=["POST"])
@employee_required
def generate_learning_path():
    """Generate a new learning path for a chosen target role."""
    target_role = request.form.get("target_role", "").strip()

    if not target_role:
        flash("Please select a target role.", "danger")
        return redirect(url_for("employee.learning_paths"))

    try:
        path = LearningPathService.generate_learning_path(current_user.id, target_role)
        flash("Learning path generated successfully.", "success")
        return redirect(url_for("employee.view_learning_path", path_id=path.id))
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.learning_paths"))


@employee_bp.route("/learning-paths/<int:path_id>")
@employee_required
def view_learning_path(path_id):
    """Detail view for a specific learning path."""
    path = LearningPathService.get_learning_path_by_id(path_id)
    if not path or path.user_id != current_user.id:
        abort(404)

    content = json.loads(path.generated_content) if path.generated_content else {}
    progress = LearningPathService.get_path_progress(path)

    return render_template(
        "employee/learning_path_detail.html",
        path=path,
        content=content,
        progress=progress,
    )


@employee_bp.route("/learning-paths/<int:path_id>/complete", methods=["POST"])
@employee_required
def complete_learning_path(path_id):
    """Mark a learning path as completed."""
    path = LearningPathService.get_learning_path_by_id(path_id)
    if not path or path.user_id != current_user.id:
        abort(404)

    try:
        LearningPathService.update_learning_path_status(path_id, "completed")
        flash("Learning path marked as completed.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.learning_paths"))


@employee_bp.route("/learning-paths/<int:path_id>/complete-skill", methods=["POST"])
@employee_required
def complete_skill(path_id):
    """Mark a skill as completed within a learning path."""
    path = LearningPathService.get_learning_path_by_id(path_id)
    if not path or path.user_id != current_user.id:
        abort(404)

    skill_name = request.form.get("skill_name", "").strip()
    if not skill_name:
        flash("Skill name is required.", "danger")
        return redirect(url_for("employee.view_learning_path", path_id=path_id))

    try:
        LearningPathService.mark_skill_complete(path_id, skill_name, current_user.id)
        flash(f"Skill '{skill_name}' marked as completed!", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.view_learning_path", path_id=path_id))


@employee_bp.route("/learning-paths/<int:path_id>/archive", methods=["POST"])
@employee_required
def archive_learning_path(path_id):
    """Archive a learning path."""
    path = LearningPathService.get_learning_path_by_id(path_id)
    if not path or path.user_id != current_user.id:
        abort(404)

    try:
        LearningPathService.update_learning_path_status(path_id, "archived")
        flash("Learning path archived.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.learning_paths"))