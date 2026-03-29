"""
Skill Service - Business logic for skill matching and gap analysis.

Handles skill management, employee-project matching, and skill gap calculations.
"""

from typing import List, Dict, Tuple, Optional
from app import db
from app.models import User, Skill, UserSkill, Project, ProjectSkill


class SkillService:
    """Service class for skill-related operations."""

    @staticmethod
    def get_all_skills() -> List[Skill]:
        """Get all skills in the system."""
        return Skill.query.order_by(Skill.name).all()

    @staticmethod
    def get_skills_by_category(category: str) -> List[Skill]:
        """Get skills filtered by category."""
        return Skill.query.filter_by(category=category).order_by(Skill.name).all()

    @staticmethod
    def get_skill_by_id(skill_id: int) -> Optional[Skill]:
        """Get a skill by its ID."""
        return db.session.get(Skill, skill_id)

    @staticmethod
    def create_skill(name: str, category: str = None) -> Skill:
        """Create a new skill."""
        existing = Skill.query.filter_by(name=name).first()
        if existing:
            raise ValueError(f"Skill '{name}' already exists")

        skill = Skill(name=name, category=category)
        db.session.add(skill)
        db.session.commit()
        return skill

    @staticmethod
    def get_user_skills(user_id: int) -> List[Dict]:
        """Get all skills for a user with proficiency levels."""
        user_skills = UserSkill.query.filter_by(user_id=user_id).all()
        return [
            {
                "id": us.id,
                "skill_id": us.skill_id,
                "skill_name": us.skill.name,
                "category": us.skill.category,
                "proficiency_level": us.proficiency_level,
                "is_verified": us.is_verified,
                "acquired_date": us.acquired_date,
                "last_used_date": us.last_used_date,
            }
            for us in user_skills
        ]

    @staticmethod
    def add_user_skill(user_id: int, skill_id: int, proficiency_level: int = 1) -> UserSkill:
        """Add a skill to a user's profile."""
        if proficiency_level < 1 or proficiency_level > 5:
            raise ValueError("Proficiency level must be between 1 and 5")
            
        skill = db.session.get(Skill, skill_id)
        if not skill:
            raise ValueError("Skill not found")

        existing = UserSkill.query.filter_by(user_id=user_id, skill_id=skill_id).first()
        if existing:
            raise ValueError("User already has this skill")

        user_skill = UserSkill(
            user_id=user_id,
            skill_id=skill_id,
            proficiency_level=proficiency_level,
            is_verified=False,
        )
        db.session.add(user_skill)
        db.session.commit()
        return user_skill

    @staticmethod
    def update_user_skill(user_id: int, skill_id: int, proficiency_level: int) -> UserSkill:
        """Update a user's skill proficiency level."""
        if proficiency_level < 1 or proficiency_level > 5:
            raise ValueError("Proficiency level must be between 1 and 5")

        user_skill = UserSkill.query.filter_by(user_id=user_id, skill_id=skill_id).first()
        if not user_skill:
            raise ValueError("User does not have this skill")

        user_skill.proficiency_level = proficiency_level
        user_skill.is_verified = False  # Reset verification on update
        db.session.commit()
        return user_skill

    @staticmethod
    def remove_user_skill(user_id: int, skill_id: int) -> bool:
        """Remove a skill from a user's profile."""
        user_skill = UserSkill.query.filter_by(user_id=user_id, skill_id=skill_id).first()
        if not user_skill:
            return False

        db.session.delete(user_skill)
        db.session.commit()
        return True

    @staticmethod
    def verify_user_skill(user_id: int, skill_id: int) -> UserSkill:
        """Mark a user's skill as verified (manager action)."""
        user_skill = UserSkill.query.filter_by(user_id=user_id, skill_id=skill_id).first()
        if not user_skill:
            raise ValueError("User skill not found")

        user_skill.is_verified = True
        db.session.commit()
        return user_skill

    @staticmethod
    def get_project_skill_requirements(project_id: int) -> List[Dict]:
        """Get required skills for a project."""
        project_skills = ProjectSkill.query.filter_by(project_id=project_id).all()
        return [
            {
                "id": ps.id,
                "skill_id": ps.skill_id,
                "skill_name": ps.skill.name,
                "category": ps.skill.category,
                "is_mandatory": ps.is_mandatory,
                "minimum_proficiency": ps.minimum_proficiency,
            }
            for ps in project_skills
        ]

    @staticmethod
    def match_employees_to_project(project_id: int) -> List[Dict]:
        """
        Find employees matching project skill requirements.

        Returns ranked list of employees with match scores.

        :param project_id: ID of the project.
        :type project_id: int
        :returns: List of matching employees.
        :rtype: List[Dict]
        """
        project_skills = ProjectSkill.query.filter_by(project_id=project_id).all()
        if not project_skills:
            return []

        # Get all approved, active employees
        employees = User.query.filter_by(
            role="employee", is_approved=True, is_active=True
        ).all()

        matches = []
        for employee in employees:
            score, details = SkillService._calculate_match_score(
                employee.id, project_skills
            )
            matches.append(
                {
                    "user_id": employee.id,
                    "username": employee.username,
                    "email": employee.email,
                    "department": employee.department.name if employee.department else None,
                    "job_title": employee.job_title,
                    "match_score": score,
                    "mandatory_met": details["mandatory_met"],
                    "mandatory_count": details["mandatory_count"],
                    "optional_matched": details["optional_matched"],
                    "optional_count": details["optional_count"],
                    "skill_details": details["skill_details"],
                }
            )

        # Sort by mandatory skills met first, then by score
        matches.sort(key=lambda x: (x["mandatory_met"], x["match_score"]), reverse=True)
        return matches

    @staticmethod
    def _calculate_match_score(
        user_id: int, project_skills: List[ProjectSkill]
    ) -> Tuple[float, Dict]:
        """Calculate skill match score for a user against project requirements."""
        user_skills = {
            us.skill_id: us.proficiency_level
            for us in UserSkill.query.filter_by(user_id=user_id).all()
        }

        mandatory_required = 0
        mandatory_met = 0
        optional_count = 0
        optional_matched = 0
        total_proficiency_score = 0
        skill_details = []

        for ps in project_skills:
            has_skill = ps.skill_id in user_skills
            meets_min = has_skill and user_skills[ps.skill_id] >= ps.minimum_proficiency
            user_level = user_skills.get(ps.skill_id, 0)

            skill_details.append({
                "skill_name": ps.skill.name,
                "required_level": ps.minimum_proficiency,
                "user_level": user_level,
                "is_mandatory": ps.is_mandatory,
                "met": meets_min,
            })

            if ps.is_mandatory:
                mandatory_required += 1
                if meets_min:
                    mandatory_met += 1
                    total_proficiency_score += user_level
            else:
                optional_count += 1
                if has_skill:
                    optional_matched += 1
                    total_proficiency_score += user_level

        # Calculate weighted score
        all_mandatory_met = mandatory_met == mandatory_required if mandatory_required > 0 else True
        base_score = (mandatory_met * 10) + (optional_matched * 5) + total_proficiency_score

        return base_score, {
            "mandatory_met": all_mandatory_met,
            "mandatory_count": f"{mandatory_met}/{mandatory_required}",
            "optional_matched": optional_matched,
            "optional_count": optional_count,
            "skill_details": skill_details,
        }

    @staticmethod
    def calculate_skill_gap(user_id: int, target_role: str = None) -> List[Dict]:
        """
        Calculate skill gaps for career progression.
        Returns skills the user is missing or has low proficiency in.
        """
        user_skills = {
            us.skill_id: us.proficiency_level
            for us in UserSkill.query.filter_by(user_id=user_id).all()
        }

        # Get all skills and identify gaps
        all_skills = Skill.query.all()
        gaps = []

        for skill in all_skills:
            user_level = user_skills.get(skill.id, 0)
            # Consider a gap if user doesn't have skill or has low proficiency
            recommended_level = 3  # Intermediate level as baseline
            if user_level < recommended_level:
                gaps.append(
                    {
                        "skill_id": skill.id,
                        "skill_name": skill.name,
                        "category": skill.category,
                        "current_level": user_level,
                        "recommended_level": recommended_level,
                        "gap": recommended_level - user_level,
                    }
                )

        return sorted(gaps, key=lambda x: x["gap"], reverse=True)

    @staticmethod
    def get_recent_skill_updates(limit: int = 20) -> List[Dict]:
        """Get recent skill updates across all employees."""
        recent_skills = (
            UserSkill.query
            .join(User)
            .filter(User.role == "employee")
            .order_by(UserSkill.updated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "user_id": us.user_id,
                "username": us.user.username,
                "skill_name": us.skill.name,
                "proficiency_level": us.proficiency_level,
                "is_verified": us.is_verified,
                "updated_at": us.updated_at,
            }
            for us in recent_skills
        ]
