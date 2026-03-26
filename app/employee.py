"""
Employee Blueprint - Routes for employee-specific functionality.

Handles project assignments, skill management, resume uploads,
and learning path features for employees.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import current_user, login_required
from functools import wraps
import json
import os

from . import db
from .models import User, ProjectAssignment, Skill, UserSkill
from .services.project_service import ProjectService
from .services.skill_service import SkillService
from .services.resume_service import ResumeService
from .services.learning_path_service import LearningPathService


employee_bp = Blueprint("employee", __name__, url_prefix="/employee")


def employee_required(f):
    """Decorator to require employee role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "employee":
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ============================================
# DASHBOARD
# ============================================

@employee_bp.route("/")
@employee_required
def dashboard():
    """Employee dashboard with assignments overview."""
    assignments = ProjectService.get_employee_assignments(current_user.id, status="active")
    skills = SkillService.get_user_skills(current_user.id)
    active_path = LearningPathService.get_active_learning_path(current_user.id)
    resume = ResumeService.get_user_resume(current_user.id)

    return render_template(
        "employee/dashboard.html",
        assignments=assignments,
        skills=skills,
        active_path=active_path,
        resume=resume,
        active_page="Dashboard",
    )


# ============================================
# PROJECT ASSIGNMENTS (REQ-12: View Assigned Work)
# ============================================

@employee_bp.route("/assignments")
@employee_required
def list_assignments():
    """List all project assignments for the employee."""
    status_filter = request.args.get("status", "")

    if status_filter:
        assignments = ProjectService.get_employee_assignments(current_user.id, status=status_filter)
    else:
        assignments = ProjectService.get_employee_assignments(current_user.id)

    return render_template(
        "employee/assignments.html",
        assignments=assignments,
        status_filter=status_filter,
        active_page="Assignments",
    )


@employee_bp.route("/assignments/<int:assignment_id>")
@employee_required
def view_assignment(assignment_id):
    """View assignment details."""
    assignment = ProjectService.get_assignment_by_id(assignment_id)
    if not assignment or assignment.user_id != current_user.id:
        abort(404)

    # Get project skill requirements
    skill_requirements = SkillService.get_project_skill_requirements(assignment.project_id)

    # Get employee's skills for comparison
    my_skills = SkillService.get_user_skills(current_user.id)
    my_skill_ids = {s["skill_id"] for s in my_skills}

    return render_template(
        "employee/assignment_detail.html",
        assignment=assignment,
        skill_requirements=skill_requirements,
        my_skills=my_skills,
        my_skill_ids=my_skill_ids,
        active_page="Assignments",
    )


# ============================================
# PROFILE
# ============================================

@employee_bp.route("/profile")
@employee_required
def profile():
    """View employee's own profile."""
    skills = SkillService.get_user_skills(current_user.id)
    resume = ResumeService.get_user_resume(current_user.id)
    active_path = LearningPathService.get_active_learning_path(current_user.id)

    return render_template(
        "employee/profile.html",
        user=current_user,
        skills=skills,
        resume=resume,
        active_path=active_path,
        active_page="Profile",
    )


# ============================================
# RESUME MANAGEMENT (REQ-13: Update Resume)
# ============================================

@employee_bp.route("/resume")
@employee_required
def view_resume():
    """View resume upload page."""
    resume = ResumeService.get_user_resume(current_user.id)

    return render_template(
        "employee/resume.html",
        resume=resume,
        active_page="Resume",
    )


@employee_bp.route("/resume/upload", methods=["GET", "POST"])
@employee_required
def upload_resume():
    """Upload or update resume."""
    if request.method == "POST":
        if "resume_file" not in request.files:
            flash("No file selected.", "danger")
            return redirect(url_for("employee.view_resume"))

        file = request.files["resume_file"]
        if file.filename == "":
            flash("No file selected.", "danger")
            return redirect(url_for("employee.view_resume"))

        try:
            resume = ResumeService.upload_resume(current_user.id, file)
            flash("Resume uploaded successfully.", "success")
            return redirect(url_for("employee.view_resume"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("employee/resume_upload.html", active_page="Resume")


@employee_bp.route("/resume/download")
@employee_required
def download_resume():
    """Download own resume file."""
    resume = ResumeService.get_user_resume(current_user.id)
    if not resume or not resume.file_path:
        abort(404)

    if not os.path.exists(resume.file_path):
        flash("Resume file not found.", "danger")
        return redirect(url_for("employee.view_resume"))

    return send_file(
        resume.file_path,
        as_attachment=True,
        download_name=resume.original_filename or "resume",
    )


@employee_bp.route("/resume/delete", methods=["POST"])
@employee_required
def delete_resume():
    """Delete own resume."""
    if ResumeService.delete_resume(current_user.id):
        flash("Resume deleted.", "success")
    else:
        flash("No resume to delete.", "info")

    return redirect(url_for("employee.view_resume"))


# ============================================
# SKILL MANAGEMENT (REQ-13: Update Skills)
# ============================================

@employee_bp.route("/skills")
@employee_required
def my_skills():
    """View and manage employee's skills."""
    skills = SkillService.get_user_skills(current_user.id)
    all_skills = SkillService.get_all_skills()

    # Filter out already added skills
    added_skill_ids = {s["skill_id"] for s in skills}
    available_skills = [s for s in all_skills if s.id not in added_skill_ids]

    return render_template(
        "employee/skills.html",
        skills=skills,
        available_skills=available_skills,
        active_page="Skills",
    )


@employee_bp.route("/skills/add", methods=["POST"])
@employee_required
def add_skill():
    """Add a skill to employee's profile."""
    skill_id = request.form.get("skill_id", type=int)
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
    """Update proficiency for a skill."""
    skill_id = request.form.get("skill_id", type=int)
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
    """Remove a skill from employee's profile."""
    skill_id = request.form.get("skill_id", type=int)

    if SkillService.remove_user_skill(current_user.id, skill_id):
        flash("Skill removed.", "success")
    else:
        flash("Skill not found.", "danger")

    return redirect(url_for("employee.my_skills"))


# ============================================
# ROLE COMPARISON (REQ-14: Compare with Higher Roles)
# ============================================

@employee_bp.route("/compare")
@employee_required
def compare_roles():
    """Compare current profile with target roles."""
    target_role = request.args.get("target_role", "")
    available_roles = LearningPathService.get_available_target_roles()
    comparison = None

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
        active_page="Compare Roles",
    )


# ============================================
# LEARNING PATHS (REQ-14: Access Learning Paths)
# ============================================

@employee_bp.route("/learning-paths")
@employee_required
def learning_paths():
    """View employee's learning paths."""
    paths = LearningPathService.get_user_learning_paths(current_user.id)
    available_roles = LearningPathService.get_available_target_roles()

    # Calculate progress for each path
    path_progress = {}
    for path in paths:
        path_progress[path.id] = LearningPathService.get_path_progress(path)

    return render_template(
        "employee/learning_paths.html",
        paths=paths,
        available_roles=available_roles,
        path_progress=path_progress,
        active_page="Learning Paths",
    )


@employee_bp.route("/learning-paths/generate", methods=["POST"])
@employee_required
def generate_learning_path():
    """Generate a new learning path."""
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
    """View a specific learning path."""
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
        active_page="Learning Paths",
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


@employee_bp.route("/learning-paths/<int:path_id>/skill/complete", methods=["POST"])
@employee_required
def complete_skill(path_id):
    """Mark a skill as completed in a learning path."""
    skill_name = request.form.get("skill_name", "").strip()

    if not skill_name:
        flash("Skill name is required.", "danger")
        return redirect(url_for("employee.view_learning_path", path_id=path_id))

    try:
        result = LearningPathService.mark_skill_complete(
            path_id=path_id,
            skill_name=skill_name,
            user_id=current_user.id
        )

        if result["path_completed"]:
            flash(f"Congratulations! You've completed all skills in this learning path!", "success")
        else:
            flash(f"Skill '{skill_name}' marked as complete. Progress: {result['progress_percentage']}%", "success")

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("employee.view_learning_path", path_id=path_id))
