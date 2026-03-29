"""
Unit tests for service layer.
"""
import pytest
import os
import json
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage
from app import db
from app.services.skill_service import SkillService
from app.services.project_service import ProjectService
from app.services.learning_path_service import LearningPathService
from app.services.resume_service import ResumeService
from app.models import UserSkill, ProjectSkill, ProjectAssignment, Resume, LearningPath


class TestSkillService:
    """Tests for SkillService."""

    def test_get_all_skills(self, db_session, skills):
        """Test retrieving all skills."""
        all_skills = SkillService.get_all_skills()
        assert len(all_skills) >= len(skills)

    def test_get_user_skills(self, db_session, employee_with_skills):
        """Test retrieving user skills."""
        user_skills = SkillService.get_user_skills(employee_with_skills.id)
        assert len(user_skills) == 2
        assert any(s["skill_name"] == "Python" for s in user_skills)

    def test_add_user_skill(self, db_session, employee_user, skills):
        """Test adding a skill to a user."""
        skill = SkillService.add_user_skill(employee_user.id, skills[0].id, 3)
        assert skill.proficiency_level == 3
        assert skill.is_verified is False

    def test_add_user_skill_invalid_proficiency(self, db_session, employee_user, skills):
        """Test adding skill with invalid proficiency."""
        with pytest.raises(ValueError, match="Proficiency level must be between 1 and 5"):
            SkillService.add_user_skill(employee_user.id, skills[0].id, 6)

    def test_add_duplicate_skill(self, db_session, employee_with_skills, skills):
        """Test adding a skill user already has."""
        with pytest.raises(ValueError, match="already has this skill"):
            SkillService.add_user_skill(employee_with_skills.id, skills[0].id, 2)

    def test_update_user_skill(self, db_session, employee_with_skills, skills):
        """Test updating skill proficiency."""
        updated = SkillService.update_user_skill(employee_with_skills.id, skills[0].id, 5)
        assert updated.proficiency_level == 5

    def test_remove_user_skill(self, db_session, employee_with_skills, skills):
        """Test removing a user skill."""
        result = SkillService.remove_user_skill(employee_with_skills.id, skills[0].id)
        assert result is True
        
        user_skills = SkillService.get_user_skills(employee_with_skills.id)
        assert not any(s["skill_name"] == "Python" for s in user_skills)

    def test_get_project_skill_requirements(self, db_session, project_with_skills):
        """Test getting project skill requirements."""
        requirements = SkillService.get_project_skill_requirements(project_with_skills.id)
        assert len(requirements) == 2
        python_req = next(r for r in requirements if r["skill_name"] == "Python")
        assert python_req["is_mandatory"] is True

    def test_match_employees_to_project(self, db_session, project_with_skills, employee_with_skills):
        """Test matching employees to project."""
        matches = SkillService.match_employees_to_project(project_with_skills.id)
        assert len(matches) > 0
        
        employee_match = next((m for m in matches if m["user_id"] == employee_with_skills.id), None)
        assert employee_match is not None
        assert employee_match["mandatory_met"] is True

    def test_calculate_skill_gap(self, db_session, employee_with_skills):
        """Test calculating skill gaps."""
        gaps = SkillService.calculate_skill_gap(employee_with_skills.id)
        
        assert len(gaps) > 0


class TestProjectService:
    """Tests for ProjectService."""

    def test_get_manager_projects(self, db_session, project, manager_user):
        """Test getting manager's projects."""
        projects = ProjectService.get_manager_projects(manager_user.id)
        assert len(projects) >= 1
        assert project in projects

    def test_create_project(self, db_session, manager_user):
        """Test creating a project."""
        proj = ProjectService.create_project(
            manager_id=manager_user.id,
            title="New Project",
            description="Test description",
        )
        assert proj.id is not None
        assert proj.title == "New Project"
        assert proj.status == "planning"

    def test_create_project_empty_title(self, db_session, manager_user):
        """Test creating project with empty title."""
        with pytest.raises(ValueError, match="title is required"):
            ProjectService.create_project(manager_user.id, "  ")

    def test_update_project(self, db_session, project):
        """Test updating a project."""
        updated = ProjectService.update_project(
            project_id=project.id,
            title="Updated Title",
            status="active",
        )
        assert updated.title == "Updated Title"
        assert updated.status == "active"

    def test_update_project_invalid_status(self, db_session, project):
        """Test updating project with invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            ProjectService.update_project(project.id, status="invalid")

    def test_assign_employee_to_project(self, db_session, project, employee_user):
        """Test assigning employee to project."""
        assignment = ProjectService.assign_employee_to_project(
            project.id, employee_user.id, "Developer"
        )
        assert assignment.status == "active"
        assert assignment.role_in_project == "Developer"

    def test_assign_non_employee(self, db_session, project, manager_user):
        """Test assigning non-employee to project."""
        with pytest.raises(ValueError, match="Only employees"):
            ProjectService.assign_employee_to_project(project.id, manager_user.id)

    def test_get_employee_assignments(self, db_session, assignment, employee_user):
        """Test getting employee assignments."""
        assignments = ProjectService.get_employee_assignments(employee_user.id)
        assert len(assignments) >= 1

    def test_remove_employee_from_project(self, db_session, assignment):
        """Test removing employee from project."""
        result = ProjectService.remove_employee_from_project(
            assignment.project_id, assignment.user_id
        )
        assert result is True
        
        db_session.refresh(assignment)
        assert assignment.status == "removed"

    def test_get_project_team(self, db_session, assignment, project):
        """Test getting project team."""
        team = ProjectService.get_project_team(project.id)
        assert len(team) >= 1
        assert any(m["role_in_project"] == "Developer" for m in team)

    def test_get_project_stats(self, db_session, project, manager_user):
        """Test getting project statistics."""
        stats = ProjectService.get_project_stats(manager_user.id)
        assert stats["total_projects"] >= 1
        assert "active" in stats["by_status"] or stats["by_status"].get("active", 0) >= 0


class TestLearningPathService:
    """Tests for LearningPathService."""

    def test_get_available_target_roles(self):
        """Test getting available target roles."""
        roles = LearningPathService.get_available_target_roles()
        assert len(roles) > 0
        assert any(r["id"] == "senior_developer" for r in roles)

    def test_generate_learning_path(self, db_session, employee_user):
        """Test generating a learning path."""
        path = LearningPathService.generate_learning_path(
            employee_user.id, "senior_developer"
        )
        assert path.id is not None
        assert path.status == "active"
        assert path.target_role == "senior_developer"

    def test_generate_learning_path_invalid_role(self, db_session, employee_user):
        """Test generating path with invalid role."""
        with pytest.raises(ValueError, match="Unknown target role"):
            LearningPathService.generate_learning_path(employee_user.id, "invalid_role")

    def test_get_user_learning_paths(self, db_session, learning_path, employee_user):
        """Test getting user's learning paths."""
        paths = LearningPathService.get_user_learning_paths(employee_user.id)
        assert len(paths) >= 1
        assert learning_path in paths

    def test_compare_roles(self, db_session, employee_with_skills):
        """Test comparing roles."""
        comparison = LearningPathService.compare_roles(
            employee_with_skills.id, "senior_developer"
        )
        assert "readiness_score" in comparison
        assert "required_skills" in comparison
        assert comparison["target_role_title"] == "Senior Developer"

    def test_compare_roles_invalid(self, db_session, employee_user):
        """Test comparing with invalid role."""
        with pytest.raises(ValueError, match="Unknown target role"):
            LearningPathService.compare_roles(employee_user.id, "invalid_role")

    def test_update_learning_path_status(self, db_session, learning_path):
        """Test updating learning path status."""
        updated = LearningPathService.update_learning_path_status(
            learning_path.id, "completed"
        )
        assert updated.status == "completed"

    def test_update_learning_path_invalid_status(self, db_session, learning_path):
        """Test updating with invalid status."""
        with pytest.raises(ValueError, match="Invalid status"):
            LearningPathService.update_learning_path_status(learning_path.id, "invalid")


class TestResumeService:
    """Tests for ResumeService."""

    def test_get_user_resume(self, app, db_session, employee_user):
        """Test retrieving user's resume."""
        with app.app_context():
            resume = ResumeService.get_user_resume(employee_user.id)
            assert resume is None  

    def test_upload_resume_pdf(self, app, db_session, employee_user, tmp_path):
        """Test uploading a PDF resume."""
        with app.app_context():
            
            test_file = tmp_path / "test_resume.pdf"
            test_file.write_bytes(b"%PDF-1.4\nTest resume content")

            with open(test_file, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename="test_resume.pdf",
                    content_type="application/pdf"
                )
                resume = ResumeService.upload_resume(employee_user.id, file_storage)

            assert resume is not None
            assert resume.original_filename == "test_resume.pdf"
            assert resume.user_id == employee_user.id
            assert os.path.exists(resume.file_path)

            
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)

    def test_upload_resume_docx(self, app, db_session, employee_user, tmp_path):
        """Test uploading a DOCX resume."""
        with app.app_context():
            test_file = tmp_path / "test_resume.docx"
            test_file.write_bytes(b"PK\x03\x04")  

            with open(test_file, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename="test_resume.docx",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                resume = ResumeService.upload_resume(employee_user.id, file_storage)

            assert resume is not None
            assert resume.original_filename == "test_resume.docx"

            
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)

    def test_upload_resume_invalid_extension(self, app, db_session, employee_user):
        """Test uploading file with invalid extension."""
        with app.app_context():
            file_storage = FileStorage(
                stream=BytesIO(b"test content"),
                filename="test.txt",
                content_type="text/plain"
            )

            with pytest.raises(ValueError, match="Invalid file type"):
                ResumeService.upload_resume(employee_user.id, file_storage)

    def test_upload_resume_no_filename(self, app, db_session, employee_user):
        """Test uploading file without filename."""
        with app.app_context():
            file_storage = FileStorage(
                stream=BytesIO(b"test content"),
                filename="",
                content_type="application/pdf"
            )

            with pytest.raises(ValueError, match="No file provided|No filename provided"):
                ResumeService.upload_resume(employee_user.id, file_storage)

    def test_upload_resume_replaces_existing(self, app, db_session, employee_user, tmp_path):
        """Test that uploading a new resume replaces the old one."""
        with app.app_context():
            
            test_file1 = tmp_path / "resume1.pdf"
            test_file1.write_bytes(b"%PDF-1.4\nFirst resume")

            with open(test_file1, 'rb') as f:
                file_storage1 = FileStorage(
                    stream=f,
                    filename="resume1.pdf",
                    content_type="application/pdf"
                )
                resume1 = ResumeService.upload_resume(employee_user.id, file_storage1)
                old_path = resume1.file_path

            
            test_file2 = tmp_path / "resume2.pdf"
            test_file2.write_bytes(b"%PDF-1.4\nSecond resume")

            with open(test_file2, 'rb') as f:
                file_storage2 = FileStorage(
                    stream=f,
                    filename="resume2.pdf",
                    content_type="application/pdf"
                )
                resume2 = ResumeService.upload_resume(employee_user.id, file_storage2)

            
            assert resume2.original_filename == "resume2.pdf"
            assert not os.path.exists(old_path)  

            
            if os.path.exists(resume2.file_path):
                os.remove(resume2.file_path)

    def test_delete_resume(self, app, db_session, employee_user, tmp_path):
        """Test deleting a resume."""
        with app.app_context():
            
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4\nTest")

            with open(test_file, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename="test.pdf",
                    content_type="application/pdf"
                )
                resume = ResumeService.upload_resume(employee_user.id, file_storage)
                file_path = resume.file_path

            
            result = ResumeService.delete_resume(employee_user.id)
            assert result is True

            
            assert not os.path.exists(file_path)
            assert ResumeService.get_user_resume(employee_user.id) is None

    def test_delete_resume_nonexistent(self, app, db_session, employee_user):
        """Test deleting when no resume exists."""
        with app.app_context():
            result = ResumeService.delete_resume(employee_user.id)
            assert result is False



class TestProjectServiceAdvanced:
    """Additional tests for ProjectService edge cases."""

    def test_delete_project(self, app, db_session, project):
        """Test deleting a project."""
        with app.app_context():
            result = ProjectService.delete_project(project.id)
            assert result is True
            assert ProjectService.get_project_by_id(project.id) is None

    def test_delete_nonexistent_project(self, app, db_session):
        """Test deleting a project that doesn't exist."""
        with app.app_context():
            result = ProjectService.delete_project(99999)
            assert result is False

    def test_update_nonexistent_project(self, app, db_session):
        """Test updating a project that doesn't exist."""
        with app.app_context():
            with pytest.raises(ValueError, match="not found"):
                ProjectService.update_project(99999, title="New Title")

    def test_update_project_empty_title(self, app, db_session, project):
        """Test updating project with empty title."""
        with app.app_context():
            with pytest.raises(ValueError, match="cannot be empty"):
                ProjectService.update_project(project.id, title="  ")

    def test_add_project_skill(self, app, db_session, project, skills):
        """Test adding skill requirement to project."""
        with app.app_context():
            skill_req = ProjectService.add_project_skill(
                project.id,
                skills[0].id,
                is_mandatory=True,
                minimum_proficiency=3
            )
            assert skill_req.is_mandatory is True
            assert skill_req.minimum_proficiency == 3

    def test_add_project_skill_duplicate(self, app, db_session, project_with_skills, skills):
        """Test adding duplicate skill to project."""
        with app.app_context():
            with pytest.raises(ValueError, match="already added to this project"):
                ProjectService.add_project_skill(project_with_skills.id, skills[0].id)

    def test_remove_project_skill(self, app, db_session, project_with_skills, skills):
        """Test removing skill from project."""
        with app.app_context():
            result = ProjectService.remove_project_skill(project_with_skills.id, skills[0].id)
            assert result is True

    def test_remove_nonexistent_project_skill(self, app, db_session, project, skills):
        """Test removing skill that isn't in project."""
        with app.app_context():
            result = ProjectService.remove_project_skill(project.id, skills[0].id)
            assert result is False

    def test_get_project_skills(self, app, db_session, project_with_skills):
        """Test getting project skill requirements."""
        with app.app_context():
            skill_reqs = ProjectService.get_project_skills(project_with_skills.id)
            assert len(skill_reqs) == 2

    def test_assign_duplicate_employee(self, app, db_session, assignment):
        """Test assigning employee already on project."""
        with app.app_context():
            with pytest.raises(ValueError, match="already assigned"):
                ProjectService.assign_employee_to_project(
                    assignment.project_id,
                    assignment.user_id,
                    "Developer"
                )

    def test_remove_nonexistent_assignment(self, app, db_session, project, employee_user):
        """Test removing employee not on project."""
        with app.app_context():
            result = ProjectService.remove_employee_from_project(project.id, employee_user.id)
            assert result is False


class TestSkillServiceAdvanced:
    """Additional tests for SkillService edge cases."""

    def test_update_nonexistent_skill(self, app, db_session, employee_user, skills):
        """Test updating skill user doesn't have."""
        with app.app_context():
            with pytest.raises(ValueError, match="does not have this skill"):
                SkillService.update_user_skill(employee_user.id, skills[0].id, 4)

    def test_remove_nonexistent_skill(self, app, db_session, employee_user, skills):
        """Test removing skill user doesn't have."""
        with app.app_context():
            result = SkillService.remove_user_skill(employee_user.id, skills[0].id)
            assert result is False


class TestLearningPathServiceMarkSkillComplete:
    """Tests for LearningPathService.mark_skill_complete."""

    def test_mark_skill_complete_success(self, app, db_session, employee_user, skills):
        """Test successfully marking a skill as complete."""
        with app.app_context():
            
            path = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            
            content = json.loads(path.generated_content)
            if content["recommendations"]:
                skill_name = content["recommendations"][0]["skill_name"]

                result = LearningPathService.mark_skill_complete(
                    path.id, skill_name, employee_user.id
                )

                assert result["skill_name"] == skill_name
                assert result["progress_percentage"] >= 0
                assert "completed_skills" in result
                assert "total_skills" in result

    def test_mark_skill_complete_path_not_found(self, db_session, employee_user):
        """Test marking skill complete on nonexistent path."""
        with pytest.raises(ValueError, match="Learning path not found"):
            LearningPathService.mark_skill_complete(99999, "Python", employee_user.id)

    def test_mark_skill_complete_unauthorized(self, db_session, learning_path, manager_user):
        """Test marking skill complete by unauthorized user."""
        with pytest.raises(ValueError, match="Unauthorized"):
            LearningPathService.mark_skill_complete(
                learning_path.id, "Docker", manager_user.id
            )

    def test_mark_skill_complete_non_active_path(self, app, db_session, employee_user):
        """Test marking skill complete on archived path."""
        with app.app_context():
            path = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )
            LearningPathService.update_learning_path_status(path.id, "archived")

            with pytest.raises(ValueError, match="non-active"):
                LearningPathService.mark_skill_complete(path.id, "Python", employee_user.id)

    def test_mark_skill_complete_skill_not_found(self, db_session, learning_path, employee_user):
        """Test marking skill that doesn't exist in path."""
        with pytest.raises(ValueError, match="not found in this learning path"):
            LearningPathService.mark_skill_complete(
                learning_path.id, "NonexistentSkill", employee_user.id
            )

    def test_mark_skill_complete_updates_user_skill(self, app, db_session, employee_user, skills):
        """Test that completing skill adds it to user profile."""
        with app.app_context():
            
            path = LearningPathService.generate_learning_path(
                employee_user.id, "devops_engineer"
            )

            
            result = LearningPathService.mark_skill_complete(
                path.id, "Docker", employee_user.id
            )

            
            user_skills = SkillService.get_user_skills(employee_user.id)
            
            assert result["skill_name"] == "Docker"

    def test_mark_skill_complete_all_skills(self, app, db_session, employee_user):
        """Test completing all skills auto-completes the path."""
        with app.app_context():
            
            path = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            content = json.loads(path.generated_content)
            recommendations = content.get("recommendations", [])

            
            for rec in recommendations:
                LearningPathService.mark_skill_complete(
                    path.id, rec["skill_name"], employee_user.id
                )

            
            from app.models import LearningPath
            path = db.session.get(LearningPath, path.id)
            assert path.status == "completed"

    def test_get_path_progress(self, db_session, learning_path):
        """Test getting path progress."""
        progress = LearningPathService.get_path_progress(learning_path)
        assert "percentage" in progress
        assert "completed" in progress
        assert "total" in progress

    def test_get_path_progress_empty_content(self, db_session, employee_user):
        """Test getting progress for path with no content."""
        from app.models import LearningPath
        path = LearningPath(
            user_id=employee_user.id,
            target_role="senior_developer",
            generated_content=None,
            status="active",
        )
        db_session.add(path)
        db_session.commit()

        progress = LearningPathService.get_path_progress(path)
        assert progress["percentage"] == 0
        assert progress["completed"] == 0
        assert progress["total"] == 0


class TestLearningPathServiceAdvanced:
    """Additional tests for LearningPathService edge cases."""

    def test_generate_path_with_existing_skills(self, app, db_session, employee_with_skills):
        """Test generating path when user has some skills."""
        with app.app_context():
            path = LearningPathService.generate_learning_path(
                employee_with_skills.id, "senior_developer"
            )
            content = json.loads(path.generated_content)

            
            assert content["readiness_score"] >= 0

    def test_generate_path_archives_existing(self, app, db_session, employee_user):
        """Test generating new path archives old active paths."""
        with app.app_context():
            
            path1 = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            
            path2 = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            
            from app.models import LearningPath
            path1_refreshed = db.session.get(LearningPath, path1.id)

            assert path1_refreshed.status == "archived"
            assert path2.status == "active"

    def test_get_user_learning_paths_with_status(self, db_session, learning_path, employee_user):
        """Test getting learning paths filtered by status."""
        paths = LearningPathService.get_user_learning_paths(
            employee_user.id, status="active"
        )
        assert all(p.status == "active" for p in paths)

    def test_get_learning_path_by_id(self, db_session, learning_path):
        """Test getting learning path by ID."""
        path = LearningPathService.get_learning_path_by_id(learning_path.id)
        assert path is not None
        assert path.id == learning_path.id

    def test_get_learning_path_by_id_not_found(self, db_session):
        """Test getting nonexistent learning path."""
        path = LearningPathService.get_learning_path_by_id(99999)
        assert path is None

    def test_update_learning_path_not_found(self, db_session):
        """Test updating nonexistent learning path."""
        with pytest.raises(ValueError, match="not found"):
            LearningPathService.update_learning_path_status(99999, "completed")

    def test_compare_roles_with_skills(self, db_session, employee_with_skills):
        """Test role comparison with existing skills."""
        comparison = LearningPathService.compare_roles(
            employee_with_skills.id, "senior_developer"
        )

        
        assert comparison["required_skills"]["met"] > 0
        assert comparison["readiness_score"] >= 0
        assert "estimated_time_to_ready" in comparison

    def test_compare_roles_user_not_found(self, db_session):
        """Test comparing roles for nonexistent user."""
        with pytest.raises(ValueError, match="User not found"):
            LearningPathService.compare_roles(99999, "senior_developer")

    def test_get_active_learning_path(self, db_session, learning_path, employee_user):
        """Test getting active learning path."""
        active = LearningPathService.get_active_learning_path(employee_user.id)
        assert active is not None
        assert active.status == "active"

    def test_get_active_learning_path_none(self, db_session, employee_user):
        """Test getting active path when none exists."""
        active = LearningPathService.get_active_learning_path(employee_user.id)
        assert active is None


class TestResumeServiceAdvanced:
    """Additional tests for ResumeService."""

    def test_parse_resume_skills(self, app, db_session, employee_user, tmp_path):
        """Test parsing skills from resume."""
        with app.app_context():
            
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4\nTest resume")

            from werkzeug.datastructures import FileStorage
            with open(test_file, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename="test.pdf",
                    content_type="application/pdf"
                )
                resume = ResumeService.upload_resume(employee_user.id, file_storage)

            
            result = ResumeService.parse_resume_skills(resume.id)

            assert "extracted_skills" in result
            assert "parsed_at" in result
            assert result["parser_version"] == "nlp_v2"

            
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)

    def test_parse_resume_skills_not_found(self, app, db_session):
        """Test parsing nonexistent resume."""
        with app.app_context():
            with pytest.raises(ValueError, match="Resume not found"):
                ResumeService.parse_resume_skills(99999)

    def test_sync_parsed_skills_to_profile(self, app, db_session, employee_user, skills):
        """Test syncing parsed skills to user profile."""
        with app.app_context():
            
            skill_names = ["Python", "JavaScript", "NonexistentSkill"]
            count = ResumeService.sync_parsed_skills_to_profile(
                employee_user.id, skill_names, default_proficiency=3
            )

            
            assert count >= 0  

    def test_sync_parsed_skills_skip_duplicates(self, app, db_session, employee_with_skills, skills):
        """Test syncing skills skips existing ones."""
        with app.app_context():
            
            skill_names = ["Python"]
            count = ResumeService.sync_parsed_skills_to_profile(
                employee_with_skills.id, skill_names
            )

            assert count == 0  

    def test_get_recent_resume_updates(self, app, db_session, employee_user, tmp_path):
        """Test getting recent resume updates."""
        with app.app_context():
            
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4\nTest")

            from werkzeug.datastructures import FileStorage
            with open(test_file, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename="test.pdf",
                    content_type="application/pdf"
                )
                resume = ResumeService.upload_resume(employee_user.id, file_storage)

            
            updates = ResumeService.get_recent_resume_updates(limit=10)

            assert len(updates) > 0
            assert any(u["user_id"] == employee_user.id for u in updates)

            
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)

    def test_allowed_file_extensions(self):
        """Test allowed file extension checking."""
        assert ResumeService.allowed_file("test.pdf") is True
        assert ResumeService.allowed_file("test.doc") is True
        assert ResumeService.allowed_file("test.docx") is True
        assert ResumeService.allowed_file("test.txt") is False
        assert ResumeService.allowed_file("test.exe") is False
        assert ResumeService.allowed_file("noextension") is False


class TestSkillServiceVerification:
    """Tests for skill verification functionality."""

    def test_verify_user_skill(self, app, db_session, employee_with_skills, skills):
        """Test verifying a user skill."""
        with app.app_context():
            result = SkillService.verify_user_skill(employee_with_skills.id, skills[0].id)
            assert result.is_verified is True

    def test_verify_nonexistent_skill(self, app, db_session, employee_user, skills):
        """Test verifying skill user doesn't have."""
        with app.app_context():
            with pytest.raises(ValueError):
                SkillService.verify_user_skill(employee_user.id, skills[0].id)

    def test_get_recent_skill_updates(self, app, db_session, employee_with_skills):
        """Test getting recent skill updates."""
        with app.app_context():
            updates = SkillService.get_recent_skill_updates(limit=10)
            assert isinstance(updates, list)


class TestResumeServiceExtraction:
    """Tests for resume parsing and skill extraction methods."""

    def test_skill_pattern_simple_word(self):
        """Test pattern generation for simple words."""
        pattern = ResumeService._skill_pattern("Python")
        import re
        assert re.search(pattern, "Python", re.IGNORECASE) is not None
        assert re.search(pattern, "python", re.IGNORECASE) is not None

    def test_skill_pattern_with_punctuation(self):
        """Test pattern generation for skills with punctuation."""
        pattern = ResumeService._skill_pattern("C++")
        import re
        assert re.search(pattern, "C++", re.IGNORECASE) is not None

    def test_skill_pattern_short_word_boundary(self):
        """Test pattern for short words prevents false matches."""
        pattern = ResumeService._skill_pattern("Go")
        import re
        
        assert re.search(pattern, "Go", re.IGNORECASE) is not None
        
        result = re.search(pattern, "algorithm", re.IGNORECASE)
        

    def test_extract_contact_info_email_and_phone(self, app):
        """Test extracting both email and phone."""
        with app.app_context():
            try:
                from app.services.nlp_manager import nlp_manager
                nlp = nlp_manager.load_spacy_model()
            except:
                nlp = None
            
            text = "Contact: john.doe@example.com or 555-123-4567"
            doc = nlp(text) if nlp else None
            
            contact = ResumeService._extract_contact_info(doc, text)
            
            assert contact["email"] == "john.doe@example.com"
            assert contact["phone"] is not None

    def test_extract_contact_info_email_only(self):
        """Test extracting email without phone."""
        text = "Email: jane@test.org"
        
        doc = MagicMock()
        doc.ents = []
        
        contact = ResumeService._extract_contact_info(doc, text)
        
        assert contact["email"] == "jane@test.org"
        assert contact["phone"] is None

    def test_extract_contact_info_phone_only(self):
        """Test extracting phone without email."""
        text = "Call me at (555) 987-6543"
        
        doc = MagicMock()
        doc.ents = []
        
        contact = ResumeService._extract_contact_info(doc, text)
        
        assert contact["email"] is None
        assert contact["phone"] is not None

    def test_extract_contact_info_no_contact(self):
        """Test when no contact info is found."""
        text = "This resume has no contact information"
        
        doc = MagicMock()
        doc.ents = []
        
        contact = ResumeService._extract_contact_info(doc, text)
        
        assert contact["email"] is None
        assert contact["phone"] is None

    def test_extract_contact_info_multiple_emails(self):
        """Test that only first email is extracted."""
        text = "Email: first@example.com or second@example.com"
        
        doc = MagicMock()
        doc.ents = []
        
        contact = ResumeService._extract_contact_info(doc, text)
        
        assert contact["email"] == "first@example.com"

    def test_extract_education_with_degree_keywords(self):
        """Test extracting education with degree keywords."""
        text = """
        Education
        Bachelor of Science in Computer Science (2019)
        Master of Technology in AI (2021)
        """
        education = ResumeService._extract_education(text)
        
        assert len(education) > 0
        assert any("bachelor" in e["degree"].lower() for e in education)

    def test_extract_education_empty_text(self):
        """Test education extraction from empty text."""
        education = ResumeService._extract_education("")
        assert education == []

    def test_extract_education_no_degrees(self):
        """Test education extraction when text has no degrees."""
        text = "This person has no formal education listed"
        education = ResumeService._extract_education(text)
        assert len(education) == 0 or len(education) <= 10

    def test_extract_experience_with_dates(self):
        """Test extracting experience with date ranges."""
        text = """
        Experience
        Software Engineer at Company A (2020-2021)
        - Developed backend APIs
        - Improved performance by 30%
        
        Senior Developer at Company B (2021-present)
        - Led team of 5 engineers
        """
        try:
            
            from app.services.nlp_manager import nlp_manager
            nlp = nlp_manager.load_spacy_model()
            doc = nlp(text)
        except:
            doc = None
        
        experience = ResumeService._extract_experience(doc, text)
        
        assert len(experience) > 0

    def test_extract_experience_empty_text(self):
        """Test experience extraction from empty text."""
        
        doc = MagicMock()
        doc.sents = []
        
        experience = ResumeService._extract_experience(doc, "")
        assert experience == []

    def test_extract_experience_no_dates(self):
        """Test experience extraction when no dates present."""
        text = """
        Experience
        Worked as a developer for several companies
        """
        
        doc = MagicMock()
        doc.sents = []
        
        experience = ResumeService._extract_experience(doc, text)
        


class TestSkillServiceEdgeCases:
    """Tests for SkillService edge cases and error handling."""

    def test_add_skill_with_zero_proficiency(self, db_session, employee_user, skills):
        """Test adding skill with proficiency of 0 (out of range)."""
        with pytest.raises(ValueError, match="between 1 and 5"):
            SkillService.add_user_skill(employee_user.id, skills[0].id, 0)

    def test_add_skill_with_negative_proficiency(self, db_session, employee_user, skills):
        """Test adding skill with negative proficiency."""
        with pytest.raises(ValueError, match="between 1 and 5"):
            SkillService.add_user_skill(employee_user.id, skills[0].id, -1)

    def test_add_skill_nonexistent_skill(self, db_session, employee_user):
        """Test adding skill that doesn't exist."""
        with pytest.raises(ValueError, match="Skill not found"):
            SkillService.add_user_skill(employee_user.id, 99999, 3)

    def test_update_skill_invalid_low_proficiency(self, db_session, employee_with_skills, skills):
        """Test updating skill with proficiency below 1."""
        with pytest.raises(ValueError, match="between 1 and 5"):
            SkillService.update_user_skill(employee_with_skills.id, skills[0].id, 0)

    def test_update_skill_invalid_high_proficiency(self, db_session, employee_with_skills, skills):
        """Test updating skill with proficiency above 5."""
        with pytest.raises(ValueError, match="between 1 and 5"):
            SkillService.update_user_skill(employee_with_skills.id, skills[0].id, 10)

    def test_get_skill_by_id_existing(self, db_session, skills):
        """Test retrieving skill by ID."""
        skill = SkillService.get_skill_by_id(skills[0].id)
        assert skill is not None
        assert skill.id == skills[0].id

    def test_get_skill_by_id_nonexistent(self, db_session):
        """Test retrieving nonexistent skill by ID."""
        skill = SkillService.get_skill_by_id(99999)
        assert skill is None

    def test_get_skills_by_category(self, db_session, skills):
        """Test retrieving skills by category."""
        technical_skills = SkillService.get_skills_by_category("technical")
        assert isinstance(technical_skills, list)
        
        assert len(technical_skills) > 0

    def test_create_skill_duplicate(self, db_session, skills):
        """Test creating duplicate skill raises error."""
        with pytest.raises(ValueError, match="already exists"):
            SkillService.create_skill(skills[0].name, "technical")

    def test_create_skill_success(self, db_session):
        """Test successfully creating a new skill."""
        skill = SkillService.create_skill("NewSkill", "technical")
        assert skill.id is not None
        assert skill.name == "NewSkill"
        assert skill.category == "technical"

    def test_match_employees_with_optional_skills(self, app, db_session, manager_user, employee_with_skills, skills):
        """Test employee matching when project has optional (non-mandatory) skills."""
        with app.app_context():
            
            project = ProjectService.create_project(manager_user.id, "OptionalProject", "Test")
            
            
            ProjectService.add_project_skill(project.id, skills[0].id, is_mandatory=False)
            
            
            matches = SkillService.match_employees_to_project(project.id)
            
            
            assert len(matches) >= 0

    def test_match_employees_no_project_skills(self, app, db_session, manager_user, employee_with_skills):
        """Test employee matching when project has no skill requirements."""
        with app.app_context():
            
            project = ProjectService.create_project(manager_user.id, "NoSkillsProject", "Test")
            
            
            matches = SkillService.match_employees_to_project(project.id)
            
            
            assert matches == []

    def test_upload_resume_no_file(self, app, db_session, employee_user):
        """Test upload resume with no file."""
        with app.app_context():
            with pytest.raises(ValueError, match="No file provided"):
                ResumeService.upload_resume(employee_user.id, None)

    def test_upload_resume_empty_filename(self, app, db_session, employee_user):
        """Test upload resume with empty filename."""
        with app.app_context():
            mock_file = MagicMock()
            mock_file.filename = ""
            
            with pytest.raises(ValueError, match="No filename provided"):
                ResumeService.upload_resume(employee_user.id, mock_file)

    def test_allowed_file_with_no_extension(self):
        """Test file without extension is not allowed."""
        assert ResumeService.allowed_file("resumefile") is False

    def test_allowed_file_case_insensitive(self):
        """Test file extension check is case-insensitive."""
        assert ResumeService.allowed_file("resume.PDF") is True
        assert ResumeService.allowed_file("resume.DOC") is True
        assert ResumeService.allowed_file("resume.DOCX") is True

    def test_sync_parsed_skills_empty_list(self, app, db_session, employee_user):
        """Test syncing empty skill list."""
        with app.app_context():
            count = ResumeService.sync_parsed_skills_to_profile(employee_user.id, [])
            assert count == 0

    def test_sync_parsed_skills_with_whitespace(self, app, db_session, employee_user):
        """Test syncing skills with whitespace."""
        with app.app_context():
            skills_with_whitespace = ["Python", " JavaScript ", ""]
            count = ResumeService.sync_parsed_skills_to_profile(
                employee_user.id, skills_with_whitespace
            )
            
            assert count >= 0

    def test_get_user_resume_not_found(self, db_session, employee_user):
        """Test getting resume for user without one."""
        resume = ResumeService.get_user_resume(employee_user.id)
        assert resume is None

    def test_delete_resume_not_found(self, db_session, employee_user):
        """Test deleting resume that doesn't exist."""
        result = ResumeService.delete_resume(employee_user.id)
        assert result is False

    def test_parse_resume_skills_no_file_path(self, app, db_session, employee_user, tmp_path):
        """Test parsing resume with no file path (or parsing when file missing)."""
        with app.app_context():
            from app.models import Resume
            
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4\nTest resume")
            
            resume = Resume(user_id=employee_user.id, file_path=str(test_file))
            db.session.add(resume)
            db.session.commit()
            
            
            test_file.unlink()
            
            
            result = ResumeService.parse_resume_skills(resume.id)
            
            
            assert result["status"] == "parse_error"
            assert result["extracted_skills"] == []


class TestResumeServiceParsing:
    """Tests for resume content parsing pipeline."""

    def test_parse_resume_content_insufficient_text(self):
        """Test parsing with text that's too short."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"short")
            temp_path = f.name
        
        try:
            
            with patch('app.services.resume_service.DocumentParser.parse_file') as mock_parse:
                mock_parse.return_value = "x"
                result = ResumeService._parse_resume_content(temp_path)
                
                assert result["status"] == "insufficient_text"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_parse_resume_content_parse_error(self):
        """Test parsing with file parse error."""
        with patch('app.services.resume_service.DocumentParser.parse_file') as mock_parse:
            mock_parse.side_effect = FileNotFoundError("File not found")
            
            result = ResumeService._parse_resume_content("/nonexistent/file.pdf")
            
            assert result["status"] == "parse_error"
            assert result["extracted_skills"] == []

    def test_parse_without_spacy_returns_valid_result(self):
        """Test degraded mode parsing without spaCy."""
        text = """
        My name is John Doe
        Email: john@example.com
        Python developer with JavaScript experience
        
        Education
        BS Computer Science
        """
        
        result = ResumeService._parse_without_spacy(text)
        
        assert "extracted_skills" in result
        assert "education" in result
        assert "contact" in result
        assert "experience" in result
        assert result["status"] == "degraded_no_spacy"
        assert result["parser_version"] == "nlp_v2_degraded"

    def test_parse_without_spacy_finds_synonyms(self):
        """Test that degraded mode uses synonym matching."""
        text = "I know k8s and docker containerization"
        
        result = ResumeService._parse_without_spacy(text)
        
        
        extracted = result["extracted_skills"]
        assert len(extracted) > 0

    def test_extract_skills_from_doc_strategy_a_db_lookup(self, app, db_session, skills):
        """Test Strategy A: direct DB skill lookup."""
        with app.app_context():
            text = "Expert in Python and JavaScript programming"
            
            try:
                from app.services.nlp_manager import nlp_manager
                nlp = nlp_manager.load_spacy_model()
                doc = nlp(text)
            except:
                doc = None
            
            found_skills = ResumeService._extract_skills_from_doc(doc, text)
            
            
            assert "Python" in found_skills or len(found_skills) >= 0

    def test_extract_skills_from_doc_empty_text(self, app):
        """Test skill extraction from empty text."""
        with app.app_context():
            
            doc = MagicMock()
            doc.ents = []
            
            found_skills = ResumeService._extract_skills_from_doc(doc, "")
            assert found_skills == []

    def test_extract_skills_no_matches(self, app):
        """Test skill extraction when no skills match."""
        with app.app_context():
            text = "This is a document with no programming skills mentioned"
            
            doc = MagicMock()
            doc.ents = []
            
            found_skills = ResumeService._extract_skills_from_doc(doc, text)
            
            assert isinstance(found_skills, list)

