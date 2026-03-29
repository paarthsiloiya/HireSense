"""
Learning Path Service - Business logic for learning path generation.

Handles learning path creation, role comparison, and skill gap analysis.
"""

import json
from typing import List, Dict, Optional
from datetime import datetime
from app import db
from app.models import User, LearningPath, Skill, UserSkill
from app.services.skill_service import SkillService


class LearningPathService:
    """Service class for learning path operations."""

    # Predefined role templates with expected skills
    # In production, this would be stored in the database
    ROLE_TEMPLATES = {
        "senior_developer": {
            "title": "Senior Developer",
            "required_skills": ["Python", "JavaScript", "SQL", "Git", "Docker"],
            "recommended_skills": ["AWS", "Kubernetes", "CI/CD", "System Design"],
        },
        "tech_lead": {
            "title": "Tech Lead",
            "required_skills": ["Python", "System Design", "Code Review", "Mentoring"],
            "recommended_skills": ["Project Management", "Agile", "Communication"],
        },
        "devops_engineer": {
            "title": "DevOps Engineer",
            "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Linux"],
            "recommended_skills": ["Terraform", "Ansible", "Monitoring", "Python"],
        },
        "data_scientist": {
            "title": "Data Scientist",
            "required_skills": ["Python", "SQL", "Machine Learning", "Statistics"],
            "recommended_skills": ["Deep Learning", "NLP", "Data Visualization"],
        },
        "qa_engineer": {
            "title": "QA Engineer",
            "required_skills": ["Testing", "Automation", "SQL", "Git"],
            "recommended_skills": ["Selenium", "Performance Testing", "API Testing"],
        },
        "security_analyst": {
            "title": "Security Analyst",
            "required_skills": ["Cybersecurity", "Network Security", "Linux"],
            "recommended_skills": ["Penetration Testing", "SIEM", "Compliance"],
        },
    }

    @staticmethod
    def get_available_target_roles() -> List[Dict]:
        """Get list of available target roles for career progression."""
        return [
            {"id": role_id, "title": role_data["title"]}
            for role_id, role_data in LearningPathService.ROLE_TEMPLATES.items()
        ]

    @staticmethod
    def generate_learning_path(user_id: int, target_role: str) -> LearningPath:
        """
        Generate a learning path for career progression.

        Analyzes skill gaps and creates recommendations.

        :param user_id: ID of the user.
        :type user_id: int
        :param target_role: Target role for progression.
        :type target_role: str
        :returns: Created learning path.
        :rtype: LearningPath
        """
        if target_role not in LearningPathService.ROLE_TEMPLATES:
            raise ValueError(f"Unknown target role: {target_role}")

        role_template = LearningPathService.ROLE_TEMPLATES[target_role]
        user_skills = SkillService.get_user_skills(user_id)
        user_skill_names = {s["skill_name"].lower() for s in user_skills}

        # Analyze skill gaps
        recommendations = []

        # Check required skills
        for skill_name in role_template["required_skills"]:
            skill_lower = skill_name.lower()
            user_has_skill = any(
                s["skill_name"].lower() == skill_lower for s in user_skills
            )

            if not user_has_skill:
                recommendations.append({
                    "skill_name": skill_name,
                    "priority": "high",
                    "current_level": 0,
                    "target_level": 3,
                    "is_required": True,
                    "resources": LearningPathService._get_learning_resources(skill_name),
                })
            else:
                # Check if proficiency needs improvement
                user_skill = next(
                    s for s in user_skills if s["skill_name"].lower() == skill_lower
                )
                if user_skill["proficiency_level"] < 3:
                    recommendations.append({
                        "skill_name": skill_name,
                        "priority": "medium",
                        "current_level": user_skill["proficiency_level"],
                        "target_level": 4,
                        "is_required": True,
                        "resources": LearningPathService._get_learning_resources(skill_name),
                    })

        # Check recommended skills
        for skill_name in role_template.get("recommended_skills", []):
            skill_lower = skill_name.lower()
            user_has_skill = any(
                s["skill_name"].lower() == skill_lower for s in user_skills
            )

            if not user_has_skill:
                recommendations.append({
                    "skill_name": skill_name,
                    "priority": "low",
                    "current_level": 0,
                    "target_level": 2,
                    "is_required": False,
                    "resources": LearningPathService._get_learning_resources(skill_name),
                })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order[x["priority"]])

        # Calculate readiness score
        required_count = len(role_template["required_skills"])
        met_count = sum(
            1 for skill in role_template["required_skills"]
            if skill.lower() in user_skill_names
        )
        readiness_score = int((met_count / required_count * 100)) if required_count > 0 else 100

        content = {
            "target_role": target_role,
            "target_role_title": role_template["title"],
            "generated_at": datetime.utcnow().isoformat(),
            "readiness_score": readiness_score,
            "total_skills_to_learn": len([r for r in recommendations if r["current_level"] == 0]),
            "skills_to_improve": len([r for r in recommendations if r["current_level"] > 0]),
            "recommendations": recommendations,
        }

        # Archive any existing active paths for the same target role
        existing_paths = LearningPath.query.filter_by(
            user_id=user_id, target_role=target_role, status="active"
        ).all()
        for path in existing_paths:
            path.status = "archived"

        learning_path = LearningPath(
            user_id=user_id,
            target_role=target_role,
            generated_content=json.dumps(content),
            status="active",
        )
        db.session.add(learning_path)
        db.session.commit()
        return learning_path

    @staticmethod
    def _get_learning_resources(skill_name: str) -> List[Dict]:
        """
        Get recommended learning resources for a skill.

        This is a placeholder. In production, integrate with learning platforms
        or maintain a database of resources.
        """
        return [
            {
                "type": "course",
                "title": f"Introduction to {skill_name}",
                "platform": "Internal LMS",
                "url": None,
            },
            {
                "type": "documentation",
                "title": f"{skill_name} Best Practices Guide",
                "platform": "Company Wiki",
                "url": None,
            },
        ]

    @staticmethod
    def get_user_learning_paths(user_id: int, status: str = None) -> List[LearningPath]:
        """Get all learning paths for a user."""
        query = LearningPath.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        return query.order_by(LearningPath.created_at.desc()).all()

    @staticmethod
    def get_learning_path_by_id(path_id: int) -> Optional[LearningPath]:
        """Get a learning path by its ID."""
        return db.session.get(LearningPath, path_id)

    @staticmethod
    def get_active_learning_path(user_id: int) -> Optional[LearningPath]:
        """Get the most recent active learning path for a user."""
        return (
            LearningPath.query
            .filter_by(user_id=user_id, status="active")
            .order_by(LearningPath.created_at.desc())
            .first()
        )

    @staticmethod
    def update_learning_path_status(path_id: int, status: str) -> LearningPath:
        """Update learning path status."""
        valid_statuses = ["active", "completed", "archived"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        path = db.session.get(LearningPath, path_id)
        if not path:
            raise ValueError("Learning path not found")

        path.status = status
        db.session.commit()
        return path

    @staticmethod
    def compare_roles(user_id: int, target_role: str) -> Dict:
        """
        Compare user's current profile with requirements for a target role.

        Used for role-switch analysis.

        :param user_id: ID of the user.
        :type user_id: int
        :param target_role: Target role to compare against.
        :type target_role: str
        :returns: Comparison results.
        :rtype: Dict
        """
        if target_role not in LearningPathService.ROLE_TEMPLATES:
            raise ValueError(f"Unknown target role: {target_role}")

        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("User not found")

        role_template = LearningPathService.ROLE_TEMPLATES[target_role]
        user_skills = SkillService.get_user_skills(user_id)
        user_skill_names = {s["skill_name"].lower() for s in user_skills}

        # Analyze required skills
        required_skills = role_template["required_skills"]
        met_required = []
        missing_required = []

        for skill in required_skills:
            if skill.lower() in user_skill_names:
                user_skill = next(
                    s for s in user_skills if s["skill_name"].lower() == skill.lower()
                )
                met_required.append({
                    "skill_name": skill,
                    "proficiency": user_skill["proficiency_level"],
                })
            else:
                missing_required.append(skill)

        # Analyze recommended skills
        recommended_skills = role_template.get("recommended_skills", [])
        met_recommended = []
        missing_recommended = []

        for skill in recommended_skills:
            if skill.lower() in user_skill_names:
                user_skill = next(
                    s for s in user_skills if s["skill_name"].lower() == skill.lower()
                )
                met_recommended.append({
                    "skill_name": skill,
                    "proficiency": user_skill["proficiency_level"],
                })
            else:
                missing_recommended.append(skill)

        # Calculate readiness
        required_count = len(required_skills)
        met_count = len(met_required)
        readiness_score = int((met_count / required_count * 100)) if required_count > 0 else 100

        return {
            "user_id": user_id,
            "current_role": user.job_title or user.role,
            "target_role": target_role,
            "target_role_title": role_template["title"],
            "readiness_score": readiness_score,
            "required_skills": {
                "total": required_count,
                "met": len(met_required),
                "missing": len(missing_required),
                "met_list": met_required,
                "missing_list": missing_required,
            },
            "recommended_skills": {
                "total": len(recommended_skills),
                "met": len(met_recommended),
                "missing": len(missing_recommended),
                "met_list": met_recommended,
                "missing_list": missing_recommended,
            },
            "total_skills": len(user_skills),
            "estimated_time_to_ready": LearningPathService._estimate_learning_time(
                missing_required, missing_recommended
            ),
        }

    @staticmethod
    def _estimate_learning_time(missing_required: List[str], missing_recommended: List[str]) -> str:
        """
        Estimate time needed to acquire missing skills.

        This is a simplified placeholder. In production, use more sophisticated
        estimation based on skill complexity and learning data.
        """
        total_missing = len(missing_required) + len(missing_recommended)

        if total_missing == 0:
            return "Ready now"
        elif total_missing <= 2:
            return "1-2 months"
        elif total_missing <= 4:
            return "3-6 months"
        elif total_missing <= 6:
            return "6-12 months"
        else:
            return "12+ months"

    @staticmethod
    def mark_skill_complete(path_id: int, skill_name: str, user_id: int) -> Dict:
        """
        Mark a skill as completed in a learning path.

        This will:
        1. Update the generated_content JSON to mark the skill as completed
        2. Add/update the skill in the user's profile (UserSkill)
        3. Recalculate and return the new progress percentage
        """
        path = db.session.get(LearningPath, path_id)
        if not path:
            raise ValueError("Learning path not found")

        if path.user_id != user_id:
            raise ValueError("Unauthorized access to learning path")

        if path.status != "active":
            raise ValueError("Cannot modify a non-active learning path")

        # Parse existing content
        content = json.loads(path.generated_content) if path.generated_content else {}
        recommendations = content.get("recommendations", [])

        # Find and update the skill
        skill_found = False
        for rec in recommendations:
            if rec["skill_name"].lower() == skill_name.lower():
                rec["completed"] = True
                rec["completed_at"] = datetime.utcnow().isoformat()
                skill_found = True
                break

        if not skill_found:
            raise ValueError(f"Skill '{skill_name}' not found in this learning path")

        # Add skill to user's profile if not already present
        skill = Skill.query.filter(
            db.func.lower(Skill.name) == skill_name.lower()
        ).first()

        if skill:
            existing_user_skill = UserSkill.query.filter_by(
                user_id=user_id, skill_id=skill.id
            ).first()

            if existing_user_skill:
                # Update proficiency to target level if current is less
                target_level = next(
                    (r["target_level"] for r in recommendations
                     if r["skill_name"].lower() == skill_name.lower()),
                    3
                )
                if existing_user_skill.proficiency_level < target_level:
                    existing_user_skill.proficiency_level = target_level
                    existing_user_skill.is_verified = False
            else:
                # Add new skill with target proficiency level
                target_level = next(
                    (r["target_level"] for r in recommendations
                     if r["skill_name"].lower() == skill_name.lower()),
                    3
                )
                new_user_skill = UserSkill(
                    user_id=user_id,
                    skill_id=skill.id,
                    proficiency_level=target_level,
                    is_verified=False,
                )
                db.session.add(new_user_skill)

        # Calculate new progress
        total_skills = len(recommendations)
        completed_skills = sum(1 for r in recommendations if r.get("completed", False))
        progress_percentage = int((completed_skills / total_skills * 100)) if total_skills > 0 else 0

        # Update content with new progress
        content["recommendations"] = recommendations
        content["progress_percentage"] = progress_percentage
        content["completed_skills_count"] = completed_skills
        content["total_skills_count"] = total_skills

        # Auto-complete learning path if all skills are done
        if progress_percentage == 100:
            path.status = "completed"

        path.generated_content = json.dumps(content)
        db.session.commit()

        return {
            "skill_name": skill_name,
            "progress_percentage": progress_percentage,
            "completed_skills": completed_skills,
            "total_skills": total_skills,
            "path_completed": progress_percentage == 100,
        }

    @staticmethod
    def get_path_progress(path: LearningPath) -> Dict:
        """
        Get the progress information for a learning path.
        """
        if not path.generated_content:
            return {"percentage": 0, "completed": 0, "total": 0}

        content = json.loads(path.generated_content)
        recommendations = content.get("recommendations", [])

        # Check if progress is already calculated
        if "progress_percentage" in content:
            return {
                "percentage": content["progress_percentage"],
                "completed": content.get("completed_skills_count", 0),
                "total": content.get("total_skills_count", len(recommendations)),
            }

        # Calculate progress from recommendations
        total_skills = len(recommendations)
        completed_skills = sum(1 for r in recommendations if r.get("completed", False))
        progress_percentage = int((completed_skills / total_skills * 100)) if total_skills > 0 else 0

        return {
            "percentage": progress_percentage,
            "completed": completed_skills,
            "total": total_skills,
        }
