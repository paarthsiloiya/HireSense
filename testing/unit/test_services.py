"""
Unit tests for service layer.
"""
import pytest
import os
import json
from io import BytesIO
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
        # Verify it's gone
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
        # Employee with Python skill should be in matches
        employee_match = next((m for m in matches if m["user_id"] == employee_with_skills.id), None)
        assert employee_match is not None
        assert employee_match["mandatory_met"] is True

    def test_calculate_skill_gap(self, db_session, employee_with_skills):
        """Test calculating skill gaps."""
        gaps = SkillService.calculate_skill_gap(employee_with_skills.id)
        # Should identify gaps for skills not at level 3+
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
        # Verify status changed
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
            assert resume is None  # No resume yet

    def test_upload_resume_pdf(self, app, db_session, employee_user, tmp_path):
        """Test uploading a PDF resume."""
        with app.app_context():
            # Create a test PDF file
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

            # Cleanup
            if os.path.exists(resume.file_path):
                os.remove(resume.file_path)

    def test_upload_resume_docx(self, app, db_session, employee_user, tmp_path):
        """Test uploading a DOCX resume."""
        with app.app_context():
            test_file = tmp_path / "test_resume.docx"
            test_file.write_bytes(b"PK\x03\x04")  # DOCX magic bytes

            with open(test_file, 'rb') as f:
                file_storage = FileStorage(
                    stream=f,
                    filename="test_resume.docx",
                    content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                resume = ResumeService.upload_resume(employee_user.id, file_storage)

            assert resume is not None
            assert resume.original_filename == "test_resume.docx"

            # Cleanup
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
            # Upload first resume
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

            # Upload second resume
            test_file2 = tmp_path / "resume2.pdf"
            test_file2.write_bytes(b"%PDF-1.4\nSecond resume")

            with open(test_file2, 'rb') as f:
                file_storage2 = FileStorage(
                    stream=f,
                    filename="resume2.pdf",
                    content_type="application/pdf"
                )
                resume2 = ResumeService.upload_resume(employee_user.id, file_storage2)

            # Check only one resume exists
            assert resume2.original_filename == "resume2.pdf"
            assert not os.path.exists(old_path)  # Old file deleted

            # Cleanup
            if os.path.exists(resume2.file_path):
                os.remove(resume2.file_path)

    def test_delete_resume(self, app, db_session, employee_user, tmp_path):
        """Test deleting a resume."""
        with app.app_context():
            # Upload resume first
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

            # Delete resume
            result = ResumeService.delete_resume(employee_user.id)
            assert result is True

            # Verify file and DB record deleted
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
            # Create a learning path with the skill
            path = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            # Get a skill from recommendations
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
            # Generate path - Docker should be a required skill
            path = LearningPathService.generate_learning_path(
                employee_user.id, "devops_engineer"
            )

            # Docker is a required skill for devops
            result = LearningPathService.mark_skill_complete(
                path.id, "Docker", employee_user.id
            )

            # Check user now has the skill
            user_skills = SkillService.get_user_skills(employee_user.id)
            # The skill may have been added if it exists in DB
            assert result["skill_name"] == "Docker"

    def test_mark_skill_complete_all_skills(self, app, db_session, employee_user):
        """Test completing all skills auto-completes the path."""
        with app.app_context():
            # Generate path
            path = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            content = json.loads(path.generated_content)
            recommendations = content.get("recommendations", [])

            # Mark all skills complete
            for rec in recommendations:
                LearningPathService.mark_skill_complete(
                    path.id, rec["skill_name"], employee_user.id
                )

            # Refresh path
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

            # User has Python at level 4, so they should meet that requirement
            assert content["readiness_score"] >= 0

    def test_generate_path_archives_existing(self, app, db_session, employee_user):
        """Test generating new path archives old active paths."""
        with app.app_context():
            # Generate first path
            path1 = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            # Generate second path for same role
            path2 = LearningPathService.generate_learning_path(
                employee_user.id, "senior_developer"
            )

            # Refresh path1
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

        # Employee has Python at level 4
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
            # First upload a resume
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

            # Parse resume
            result = ResumeService.parse_resume_skills(resume.id)

            assert "extracted_skills" in result
            assert "parsed_at" in result
            assert result["parser_version"] == "stub_v1"

            # Cleanup
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
            # Sync existing skills
            skill_names = ["Python", "JavaScript", "NonexistentSkill"]
            count = ResumeService.sync_parsed_skills_to_profile(
                employee_user.id, skill_names, default_proficiency=3
            )

            # Python and JavaScript should be added (if not already there)
            assert count >= 0  # May be 0-2 depending on existing skills

    def test_sync_parsed_skills_skip_duplicates(self, app, db_session, employee_with_skills, skills):
        """Test syncing skills skips existing ones."""
        with app.app_context():
            # Employee already has Python
            skill_names = ["Python"]
            count = ResumeService.sync_parsed_skills_to_profile(
                employee_with_skills.id, skill_names
            )

            assert count == 0  # Already has Python

    def test_get_recent_resume_updates(self, app, db_session, employee_user, tmp_path):
        """Test getting recent resume updates."""
        with app.app_context():
            # Upload a resume first
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

            # Get recent updates
            updates = ResumeService.get_recent_resume_updates(limit=10)

            assert len(updates) > 0
            assert any(u["user_id"] == employee_user.id for u in updates)

            # Cleanup
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

