"""
Manager Blueprint - Routes for manager-specific functionality.

Handles project management, employee skill matching, team assignments,
and manager self-service features (learning paths, skill development).
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user, login_required
from functools import wraps
from datetime import datetime

from . import db
from .models import User, Project, ProjectAssignment, ProjectSkill, Skill, Notification, UserSkill
from .services.project_service import ProjectService
from .services.skill_service import SkillService
from .services.resume_service import ResumeService
from .services.learning_path_service import LearningPathService


manager_bp = Blueprint("manager", __name__, url_prefix="/manager")


def manager_required(f):
    """Decorator to require manager role."""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if current_user.role != "manager":
            abort(403)
        return f(*args, **kwargs)
    return decorated






@manager_bp.route("/")
@manager_required
def dashboard():
    """Manager dashboard with project overview and stats."""
    stats = ProjectService.get_project_stats(current_user.id)
    projects = ProjectService.get_manager_projects(current_user.id)[:5]  

    
    recent_updates = SkillService.get_recent_skill_updates(limit=10)

    return render_template(
        "manager/dashboard.html",
        stats=stats,
        projects=projects,
        recent_updates=recent_updates,
        active_page="Dashboard"
    )






@manager_bp.route("/projects")
@manager_required
def list_projects():
    """List all projects managed by current user."""
    status_filter = request.args.get("status", "")
    projects = ProjectService.get_manager_projects(current_user.id)

    if status_filter:
        projects = [p for p in projects if p.status == status_filter]

    return render_template(
        "manager/projects.html",
        projects=projects,
        status_filter=status_filter,
        active_page="Projects"
    )


@manager_bp.route("/projects/create", methods=["GET", "POST"])
@manager_required
def create_project():
    """Create a new project."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        start_date_str = request.form.get("start_date", "")
        end_date_str = request.form.get("end_date", "")

        if not title:
            flash("Project title is required.", "danger")
            return render_template("manager/project_form.html", project=None)

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

            project = ProjectService.create_project(
                manager_id=current_user.id,
                title=title,
                description=description,
                start_date=start_date,
                end_date=end_date,
            )
            flash(f"Project '{project.title}' created successfully.", "success")
            return redirect(url_for("manager.view_project", project_id=project.id))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("manager/project_form.html", project=None)


@manager_bp.route("/projects/<int:project_id>")
@manager_required
def view_project(project_id):
    """View project details."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    team = ProjectService.get_project_team(project_id)
    skill_requirements = SkillService.get_project_skill_requirements(project_id)

    return render_template(
        "manager/project_detail.html",
        project=project,
        team=team,
        skill_requirements=skill_requirements,
    )


@manager_bp.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
@manager_required
def edit_project(project_id):
    """Edit project details."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "")
        start_date_str = request.form.get("start_date", "")
        end_date_str = request.form.get("end_date", "")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None

            ProjectService.update_project(
                project_id=project_id,
                title=title,
                description=description,
                status=status,
                start_date=start_date,
                end_date=end_date,
            )
            flash("Project updated successfully.", "success")
            return redirect(url_for("manager.view_project", project_id=project_id))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("manager/project_form.html", project=project)


@manager_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
@manager_required
def delete_project(project_id):
    """Delete a project."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    title = project.title
    if ProjectService.delete_project(project_id):
        flash(f"Project '{title}' deleted successfully.", "success")
    else:
        flash("Failed to delete project.", "danger")

    return redirect(url_for("manager.list_projects"))






@manager_bp.route("/projects/<int:project_id>/skills")
@manager_required
def project_skills(project_id):
    """View and manage skill requirements for a project."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    skill_requirements = SkillService.get_project_skill_requirements(project_id)
    all_skills = SkillService.get_all_skills()

    
    added_skill_ids = {s["skill_id"] for s in skill_requirements}
    available_skills = [s for s in all_skills if s.id not in added_skill_ids]

    return render_template(
        "manager/project_skills.html",
        project=project,
        skill_requirements=skill_requirements,
        available_skills=available_skills,
    )


@manager_bp.route("/projects/<int:project_id>/skills/add", methods=["POST"])
@manager_required
def add_project_skill(project_id):
    """Add a skill requirement to a project."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    skill_id = request.form.get("skill_id", type=int)
    is_mandatory = request.form.get("is_mandatory") == "on"
    min_proficiency = request.form.get("minimum_proficiency", type=int, default=1)

    if not skill_id:
        flash("Please select a skill.", "danger")
        return redirect(url_for("manager.project_skills", project_id=project_id))

    try:
        ProjectService.add_project_skill(
            project_id=project_id,
            skill_id=skill_id,
            is_mandatory=is_mandatory,
            minimum_proficiency=min_proficiency,
        )
        flash("Skill requirement added.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("manager.project_skills", project_id=project_id))


@manager_bp.route("/projects/<int:project_id>/skills/remove", methods=["POST"])
@manager_required
def remove_project_skill(project_id):
    """Remove a skill requirement from a project."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    skill_id = request.form.get("skill_id", type=int)

    if ProjectService.remove_project_skill(project_id, skill_id):
        flash("Skill requirement removed.", "success")
    else:
        flash("Skill not found.", "danger")

    return redirect(url_for("manager.project_skills", project_id=project_id))






@manager_bp.route("/projects/<int:project_id>/match")
@manager_required
def match_employees(project_id):
    """Find employees matching project skill requirements."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    matches = SkillService.match_employees_to_project(project_id)
    skill_requirements = SkillService.get_project_skill_requirements(project_id)

    
    current_team = ProjectService.get_project_team(project_id)
    current_team_ids = {m["user_id"] for m in current_team}

    
    available_matches = [m for m in matches if m["user_id"] not in current_team_ids]

    return render_template(
        "manager/employee_match.html",
        project=project,
        matches=available_matches,
        skill_requirements=skill_requirements,
    )


@manager_bp.route("/projects/<int:project_id>/assign", methods=["POST"])
@manager_required
def assign_employee(project_id):
    """Assign an employee to a project."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    user_id = request.form.get("user_id", type=int)
    role_in_project = request.form.get("role_in_project", "").strip()

    if not user_id:
        flash("Please select an employee.", "danger")
        return redirect(url_for("manager.match_employees", project_id=project_id))

    try:
        assignment = ProjectService.assign_employee_to_project(
            project_id=project_id,
            user_id=user_id,
            role=role_in_project or None,
        )
        user = db.session.get(User, user_id)
        flash(f"Assigned {user.username} to the project.", "success")

        
        notification = Notification(
            user_id=user_id,
            message=f"You have been assigned to project: {project.title}",
            type="info",
        )
        db.session.add(notification)
        db.session.commit()

    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("manager.project_team", project_id=project_id))


@manager_bp.route("/projects/<int:project_id>/team")
@manager_required
def project_team(project_id):
    """View project team members."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    team = ProjectService.get_project_team(project_id)

    return render_template(
        "manager/project_team.html",
        project=project,
        team=team,
    )


@manager_bp.route("/projects/<int:project_id>/unassign/<int:user_id>", methods=["POST"])
@manager_required
def unassign_employee(project_id, user_id):
    """Remove an employee from a project."""
    project = ProjectService.get_project_by_id(project_id)
    if not project or project.manager_id != current_user.id:
        abort(404)

    if ProjectService.remove_employee_from_project(project_id, user_id):
        user = db.session.get(User, user_id)
        flash(f"Removed {user.username} from the project.", "success")

        
        notification = Notification(
            user_id=user_id,
            message=f"You have been removed from project: {project.title}",
            type="info",
        )
        db.session.add(notification)
        db.session.commit()
    else:
        flash("Employee not found in project.", "danger")

    return redirect(url_for("manager.project_team", project_id=project_id))






@manager_bp.route("/updates")
@manager_required
def view_updates():
    """View recent skill and resume changes across employees."""
    skill_updates = SkillService.get_recent_skill_updates(limit=20)
    resume_updates = ResumeService.get_recent_resume_updates(limit=20)

    return render_template(
        "manager/updates.html",
        skill_updates=skill_updates,
        resume_updates=resume_updates,
        active_page="Updates"
    )


@manager_bp.route("/employees/<int:user_id>/skills")
@manager_required
def view_employee_skills(user_id):
    """View an employee's skills (no PII exposed per RBAC)."""
    employee = db.session.get(User, user_id)
    if not employee or employee.role != "employee":
        abort(404)

    skills = SkillService.get_user_skills(user_id)

    return render_template(
        "manager/employee_skills.html",
        employee=employee,
        skills=skills,
    )


@manager_bp.route("/employees/<int:user_id>/skills/verify", methods=["POST"])
@manager_required
def verify_employee_skill(user_id):
    """Verify an employee's skill."""
    employee = db.session.get(User, user_id)
    if not employee or employee.role != "employee":
        abort(404)

    skill_id = request.form.get("skill_id", type=int)
    if not skill_id:
        flash("Invalid skill.", "danger")
        return redirect(url_for("manager.view_employee_skills", user_id=user_id))

    try:
        SkillService.verify_user_skill(user_id, skill_id)
        flash("Skill verified.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("manager.view_employee_skills", user_id=user_id))






@manager_bp.route("/profile")
@manager_required
def profile():
    """View manager's own profile."""
    skills = SkillService.get_user_skills(current_user.id)
    active_path = LearningPathService.get_active_learning_path(current_user.id)

    return render_template(
        "manager/profile.html",
        user=current_user,
        skills=skills,
        active_path=active_path,
        active_page="My Profile"
    )


@manager_bp.route("/skills")
@manager_required
def my_skills():
    """View and manage manager's own skills."""
    skills = SkillService.get_user_skills(current_user.id)
    all_skills = SkillService.get_all_skills()

    
    added_skill_ids = {s["skill_id"] for s in skills}
    available_skills = [s for s in all_skills if s.id not in added_skill_ids]

    
    skill_distribution = _calculate_skill_distribution(skills)

    return render_template(
        "manager/skills.html",
        skills=skills,
        available_skills=available_skills,
        skill_distribution=skill_distribution,
        active_page="My Skills"
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


@manager_bp.route("/skills/add", methods=["POST"])
@manager_required
def add_my_skill():
    """Add a skill to manager's own profile."""
    skill_id = request.form.get("skill_id", type=int)
    proficiency = request.form.get("proficiency_level", type=int, default=1)

    if not skill_id:
        flash("Please select a skill.", "danger")
        return redirect(url_for("manager.my_skills"))

    try:
        SkillService.add_user_skill(current_user.id, skill_id, proficiency)
        flash("Skill added.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("manager.my_skills"))


@manager_bp.route("/skills/update", methods=["POST"])
@manager_required
def update_my_skill():
    """Update proficiency for manager's own skill."""
    skill_id = request.form.get("skill_id", type=int)
    proficiency = request.form.get("proficiency_level", type=int)

    if not skill_id or not proficiency:
        flash("Invalid request.", "danger")
        return redirect(url_for("manager.my_skills"))

    try:
        SkillService.update_user_skill(current_user.id, skill_id, proficiency)
        flash("Skill updated.", "success")
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("manager.my_skills"))


@manager_bp.route("/skills/remove", methods=["POST"])
@manager_required
def remove_my_skill():
    """Remove a skill from manager's own profile."""
    skill_id = request.form.get("skill_id", type=int)

    if SkillService.remove_user_skill(current_user.id, skill_id):
        flash("Skill removed.", "success")
    else:
        flash("Skill not found.", "danger")

    return redirect(url_for("manager.my_skills"))


@manager_bp.route("/learning-paths")
@manager_required
def learning_paths():
    """View manager's learning paths."""
    paths = LearningPathService.get_user_learning_paths(current_user.id)
    available_roles = LearningPathService.get_available_target_roles()

    return render_template(
        "manager/learning_paths.html",
        paths=paths,
        available_roles=available_roles,
        active_page="Learning Paths"
    )


@manager_bp.route("/learning-paths/generate", methods=["POST"])
@manager_required
def generate_learning_path():
    """Generate a new learning path."""
    target_role = request.form.get("target_role", "").strip()

    if not target_role:
        flash("Please select a target role.", "danger")
        return redirect(url_for("manager.learning_paths"))

    try:
        path = LearningPathService.generate_learning_path(current_user.id, target_role)
        flash("Learning path generated successfully.", "success")
        return redirect(url_for("manager.view_learning_path", path_id=path.id))
    except ValueError as e:
        flash(str(e), "danger")

    return redirect(url_for("manager.learning_paths"))


@manager_bp.route("/learning-paths/<int:path_id>")
@manager_required
def view_learning_path(path_id):
    """View a specific learning path."""
    path = LearningPathService.get_learning_path_by_id(path_id)
    if not path or path.user_id != current_user.id:
        abort(404)

    import json
    content = json.loads(path.generated_content) if path.generated_content else {}

    progress = LearningPathService.get_path_progress(path)
    return render_template(
        "manager/learning_path_detail.html",
        path=path,
        content=content,
        progress=progress,
    )


@manager_bp.route("/compare")
@manager_required
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
        "manager/compare.html",
        available_roles=available_roles,
        selected_role=target_role,
        comparison=comparison,
        active_page="Compare Roles"
    )
