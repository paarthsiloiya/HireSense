"""
Unit tests for new Manager/Employee models.
"""
import pytest
from datetime import datetime
from app.models import (
    Department, Skill, Project, ProjectSkill, ProjectAssignment,
    UserSkill, Resume, LearningPath, User
)


class TestDepartmentModel:
    """Tests for Department model."""

    def test_department_creation(self, db_session):
        """Test creating a department."""
        dept = Department(name="Engineering")
        db_session.add(dept)
        db_session.commit()

        assert dept.id is not None
        assert dept.name == "Engineering"
        assert dept.created_at is not None

    def test_department_unique_name(self, db_session, department):
        """Test that department names must be unique."""
        from sqlalchemy.exc import IntegrityError

        dept2 = Department(name="Engineering")
        db_session.add(dept2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestSkillModel:
    """Tests for Skill model."""

    def test_skill_creation(self, db_session):
        """Test creating a skill."""
        skill = Skill(name="Python", category="technical")
        db_session.add(skill)
        db_session.commit()

        assert skill.id is not None
        assert skill.name == "Python"
        assert skill.category == "technical"

    def test_skill_unique_name(self, db_session):
        """Test that skill names must be unique."""
        from sqlalchemy.exc import IntegrityError

        skill1 = Skill(name="Python", category="technical")
        db_session.add(skill1)
        db_session.commit()

        skill2 = Skill(name="Python", category="programming")
        db_session.add(skill2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestProjectModel:
    """Tests for Project model."""

    def test_project_creation(self, db_session, manager_user):
        """Test creating a project."""
        project = Project(
            title="Test Project",
            description="Test description",
            status="planning",
            manager_id=manager_user.id,
        )
        db_session.add(project)
        db_session.commit()

        assert project.id is not None
        assert project.title == "Test Project"
        assert project.status == "planning"
        assert project.manager_id == manager_user.id
        assert project.manager == manager_user

    def test_project_manager_relationship(self, db_session, manager_user):
        """Test project-manager relationship."""
        project = Project(
            title="Test Project",
            manager_id=manager_user.id,
        )
        db_session.add(project)
        db_session.commit()

        assert project in manager_user.managed_projects.all()


class TestProjectSkillModel:
    """Tests for ProjectSkill model."""

    def test_project_skill_creation(self, db_session, project, skills):
        """Test adding skills to a project."""
        ps = ProjectSkill(
            project_id=project.id,
            skill_id=skills[0].id,
            is_mandatory=True,
            minimum_proficiency=3,
        )
        db_session.add(ps)
        db_session.commit()

        assert ps.id is not None
        assert ps.is_mandatory is True
        assert ps.minimum_proficiency == 3
        assert ps.skill == skills[0]
        assert ps.project == project


class TestProjectAssignmentModel:
    """Tests for ProjectAssignment model."""

    def test_assignment_creation(self, db_session, project, employee_user):
        """Test creating an assignment."""
        assignment = ProjectAssignment(
            project_id=project.id,
            user_id=employee_user.id,
            role_in_project="Developer",
        )
        db_session.add(assignment)
        db_session.commit()

        assert assignment.id is not None
        assert assignment.status == "active"
        assert assignment.user == employee_user
        assert assignment.project == project

    def test_assignment_unique_constraint(self, db_session, assignment):
        """Test that user can only be assigned once per project."""
        from sqlalchemy.exc import IntegrityError

        duplicate = ProjectAssignment(
            project_id=assignment.project_id,
            user_id=assignment.user_id,
        )
        db_session.add(duplicate)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestUserSkillModel:
    """Tests for UserSkill model."""

    def test_user_skill_creation(self, db_session, employee_user, skills):
        """Test adding a skill to a user."""
        us = UserSkill(
            user_id=employee_user.id,
            skill_id=skills[0].id,
            proficiency_level=3,
        )
        db_session.add(us)
        db_session.commit()

        assert us.id is not None
        assert us.proficiency_level == 3
        assert us.is_verified is False
        assert us.skill == skills[0]

    def test_user_skill_unique_constraint(self, db_session, employee_with_skills, skills):
        """Test that user can only have one entry per skill."""
        from sqlalchemy.exc import IntegrityError

        duplicate = UserSkill(
            user_id=employee_with_skills.id,
            skill_id=skills[0].id,  
            proficiency_level=1,
        )
        db_session.add(duplicate)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestResumeModel:
    """Tests for Resume model."""

    def test_resume_creation(self, db_session, employee_user):
        """Test creating a resume record."""
        resume = Resume(
            user_id=employee_user.id,
            file_path="uploads/resumes/test.pdf",
            original_filename="my_resume.pdf",
        )
        db_session.add(resume)
        db_session.commit()

        assert resume.id is not None
        assert resume.user == employee_user
        assert resume.last_updated is not None


class TestLearningPathModel:
    """Tests for LearningPath model."""

    def test_learning_path_creation(self, db_session, employee_user):
        """Test creating a learning path."""
        import json
        content = {"recommendations": []}
        path = LearningPath(
            user_id=employee_user.id,
            target_role="senior_developer",
            generated_content=json.dumps(content),
        )
        db_session.add(path)
        db_session.commit()

        assert path.id is not None
        assert path.status == "active"
        assert path.user == employee_user


class TestUserModelExtensions:
    """Tests for User model extensions."""

    def test_user_department_relationship(self, db_session, employee_user, department):
        """Test user-department relationship."""
        employee_user.department_id = department.id
        db_session.commit()

        assert employee_user.department == department
        assert employee_user in department.users.all()

    def test_user_job_title(self, db_session, employee_user):
        """Test user job title field."""
        employee_user.job_title = "Senior Developer"
        db_session.commit()

        assert employee_user.job_title == "Senior Developer"
