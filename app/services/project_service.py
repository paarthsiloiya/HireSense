"""
Project Service - Business logic for project management operations.

Handles project CRUD, team assignments, and project skill requirements.
"""

from typing import List, Dict, Optional
from datetime import datetime, date
from app import db
from app.models import User, Project, ProjectAssignment, ProjectSkill, Skill


class ProjectService:
    """Service class for project-related operations."""

    @staticmethod
    def get_all_projects() -> List[Project]:
        """Get all projects in the system."""
        return Project.query.order_by(Project.created_at.desc()).all()

    @staticmethod
    def get_manager_projects(manager_id: int) -> List[Project]:
        """Get all projects managed by a specific manager."""
        return (
            Project.query.filter_by(manager_id=manager_id)
            .order_by(Project.created_at.desc())
            .all()
        )

    @staticmethod
    def get_project_by_id(project_id: int) -> Optional[Project]:
        """Get a project by its ID."""
        return db.session.get(Project, project_id)

    @staticmethod
    def create_project(
        manager_id: int,
        title: str,
        description: str = None,
        start_date: date = None,
        end_date: date = None,
    ) -> Project:
        """
        Create a new project.

        :param manager_id: ID of the manager creating the project.
        :type manager_id: int
        :param title: Title of the project.
        :type title: str
        :param description: Description of the project.
        :type description: str or None
        :param start_date: Start date of the project.
        :type start_date: date or None
        :param end_date: End date of the project.
        :type end_date: date or None
        :returns: Created project.
        :rtype: Project
        """
        if not title or not title.strip():
            raise ValueError("Project title is required")

        project = Project(
            title=title.strip(),
            description=description,
            manager_id=manager_id,
            status="planning",
            start_date=start_date,
            end_date=end_date,
        )
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def update_project(
        project_id: int,
        title: str = None,
        description: str = None,
        status: str = None,
        start_date: date = None,
        end_date: date = None,
    ) -> Project:
        """Update project details."""
        project = db.session.get(Project, project_id)
        if not project:
            raise ValueError("Project not found")

        if title is not None:
            if not title.strip():
                raise ValueError("Project title cannot be empty")
            project.title = title.strip()
        if description is not None:
            project.description = description
        if status is not None:
            valid_statuses = ["planning", "active", "completed", "on_hold"]
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")
            project.status = status
        if start_date is not None:
            project.start_date = start_date
        if end_date is not None:
            project.end_date = end_date

        db.session.commit()
        return project

    @staticmethod
    def delete_project(project_id: int) -> bool:
        """Delete a project and all related data."""
        project = db.session.get(Project, project_id)
        if not project:
            return False

        db.session.delete(project)
        db.session.commit()
        return True

    @staticmethod
    def add_project_skill(
        project_id: int,
        skill_id: int,
        is_mandatory: bool = True,
        minimum_proficiency: int = 1,
    ) -> ProjectSkill:
        """Add a skill requirement to a project."""
        if minimum_proficiency < 1 or minimum_proficiency > 5:
            raise ValueError("Minimum proficiency must be between 1 and 5")

        existing = ProjectSkill.query.filter_by(
            project_id=project_id, skill_id=skill_id
        ).first()
        if existing:
            raise ValueError("Skill already added to this project")

        project_skill = ProjectSkill(
            project_id=project_id,
            skill_id=skill_id,
            is_mandatory=is_mandatory,
            minimum_proficiency=minimum_proficiency,
        )
        db.session.add(project_skill)
        db.session.commit()
        return project_skill

    @staticmethod
    def get_project_skills(project_id: int) -> List[ProjectSkill]:
        """Get all skill requirements for a project."""
        return ProjectSkill.query.filter_by(project_id=project_id).all()

    @staticmethod
    def remove_project_skill(project_id: int, skill_id: int) -> bool:
        """Remove a skill requirement from a project."""
        project_skill = ProjectSkill.query.filter_by(
            project_id=project_id, skill_id=skill_id
        ).first()
        if not project_skill:
            return False

        db.session.delete(project_skill)
        db.session.commit()
        return True

    @staticmethod
    def get_employee_assignments(user_id: int, status: str = None) -> List[Dict]:
        """Get all project assignments for an employee."""
        query = ProjectAssignment.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)

        assignments = query.order_by(ProjectAssignment.allotted_date.desc()).all()
        return [
            {
                "assignment_id": a.id,
                "project_id": a.project.id,
                "project_title": a.project.title,
                "project_description": a.project.description,
                "project_status": a.project.status,
                "manager_id": a.project.manager_id,
                "manager_name": a.project.manager.username,
                "role_in_project": a.role_in_project,
                "allotted_date": a.allotted_date,
                "assignment_status": a.status,
            }
            for a in assignments
        ]

    @staticmethod
    def get_assignment_by_id(assignment_id: int) -> Optional[ProjectAssignment]:
        """Get an assignment by its ID."""
        return db.session.get(ProjectAssignment, assignment_id)

    @staticmethod
    def assign_employee_to_project(
        project_id: int, user_id: int, role: str = None
    ) -> ProjectAssignment:
        """Assign an employee to a project."""
        # Verify the user is an employee
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")
        if user.role != "employee":
            raise ValueError("Only employees can be assigned to projects")

        # Check for existing assignment
        existing = ProjectAssignment.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()

        if existing:
            if existing.status == "removed":
                # Reactivate the assignment
                existing.status = "active"
                existing.allotted_date = datetime.utcnow()
                existing.role_in_project = role
                db.session.commit()
                return existing
            raise ValueError("Employee already assigned to this project")

        assignment = ProjectAssignment(
            project_id=project_id,
            user_id=user_id,
            role_in_project=role,
            status="active",
        )
        db.session.add(assignment)
        db.session.commit()
        return assignment

    @staticmethod
    def remove_employee_from_project(project_id: int, user_id: int) -> bool:
        """Remove an employee from a project (soft delete)."""
        assignment = ProjectAssignment.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()

        if not assignment:
            return False

        assignment.status = "removed"
        db.session.commit()
        return True

    @staticmethod
    def get_project_team(project_id: int) -> List[Dict]:
        """Get all active team members for a project."""
        assignments = ProjectAssignment.query.filter_by(
            project_id=project_id, status="active"
        ).all()

        return [
            {
                "assignment_id": a.id,
                "user_id": a.user.id,
                "username": a.user.username,
                "email": a.user.email,
                "department": a.user.department.name if a.user.department else None,
                "job_title": a.user.job_title,
                "role_in_project": a.role_in_project,
                "allotted_date": a.allotted_date,
            }
            for a in assignments
        ]

    @staticmethod
    def get_project_stats(manager_id: int) -> Dict:
        """Get project statistics for a manager."""
        projects = Project.query.filter_by(manager_id=manager_id).all()

        total = len(projects)
        by_status = {}
        total_team_members = 0

        for project in projects:
            status = project.status
            by_status[status] = by_status.get(status, 0) + 1
            total_team_members += (
                ProjectAssignment.query.filter_by(
                    project_id=project.id, status="active"
                ).count()
            )

        return {
            "total_projects": total,
            "by_status": by_status,
            "total_team_members": total_team_members,
            "planning": by_status.get("planning", 0),
            "active": by_status.get("active", 0),
            "completed": by_status.get("completed", 0),
            "on_hold": by_status.get("on_hold", 0),
        }
