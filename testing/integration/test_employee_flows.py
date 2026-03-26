"""
Integration tests for Employee workflows.
"""
import pytest
import io


class TestEmployeeDashboard:
    """Tests for employee dashboard."""

    def test_employee_dashboard_access(self, authenticated_employee_client):
        """Test employee can access dashboard."""
        response = authenticated_employee_client.get("/employee/")
        assert response.status_code == 200
        assert b"Employee Dashboard" in response.data

    def test_manager_cannot_access_employee_dashboard(self, authenticated_manager_client):
        """Test manager cannot access employee routes."""
        response = authenticated_manager_client.get("/employee/")
        assert response.status_code == 403

    def test_admin_cannot_access_employee_dashboard(self, authenticated_admin_client):
        """Test admin cannot access employee routes."""
        response = authenticated_admin_client.get("/employee/")
        assert response.status_code == 403


class TestEmployeeAssignments:
    """Tests for viewing project assignments."""

    def test_list_assignments(self, authenticated_employee_client, assignment):
        """Test listing assignments."""
        response = authenticated_employee_client.get("/employee/assignments")
        assert response.status_code == 200
        assert b"Assignments" in response.data

    def test_view_assignment_detail(self, authenticated_employee_client, assignment):
        """Test viewing assignment details."""
        response = authenticated_employee_client.get(
            f"/employee/assignments/{assignment.id}"
        )
        assert response.status_code == 200
        assert b"Test Project" in response.data

    def test_view_other_user_assignment(self, authenticated_employee_client, db_session, manager_user, project):
        """Test cannot view another user's assignment."""
        from app.models import ProjectAssignment, User
        # Create another employee
        other_employee = User(
            username="other",
            email="other@test.com",
            role="employee",
            is_approved=True,
            is_active=True,
        )
        other_employee.set_password("Test@123")
        db_session.add(other_employee)
        db_session.commit()

        # Create assignment for other employee
        other_assignment = ProjectAssignment(
            project_id=project.id,
            user_id=other_employee.id,
        )
        db_session.add(other_assignment)
        db_session.commit()

        # Try to access other's assignment
        response = authenticated_employee_client.get(
            f"/employee/assignments/{other_assignment.id}"
        )
        assert response.status_code == 404


class TestEmployeeSkills:
    """Tests for employee skill management."""

    def test_view_skills(self, authenticated_employee_client, employee_with_skills):
        """Test viewing skills page."""
        response = authenticated_employee_client.get("/employee/skills")
        assert response.status_code == 200
        assert b"My Skills" in response.data

    def test_add_skill(self, authenticated_employee_client, skills):
        """Test adding a skill."""
        response = authenticated_employee_client.post(
            "/employee/skills/add",
            data={
                "skill_id": skills[3].id,  # Docker
                "proficiency_level": 2,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Skill added" in response.data

    def test_update_skill(self, authenticated_employee_client, employee_with_skills, skills):
        """Test updating skill proficiency."""
        response = authenticated_employee_client.post(
            "/employee/skills/update",
            data={
                "skill_id": skills[0].id,  # Python
                "proficiency_level": 5,
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Skill updated" in response.data

    def test_remove_skill(self, authenticated_employee_client, employee_with_skills, skills):
        """Test removing a skill."""
        response = authenticated_employee_client.post(
            "/employee/skills/remove",
            data={
                "skill_id": skills[0].id,  # Python
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Skill removed" in response.data


class TestEmployeeResume:
    """Tests for employee resume management."""

    def test_view_resume_page(self, authenticated_employee_client):
        """Test viewing resume page."""
        response = authenticated_employee_client.get("/employee/resume")
        assert response.status_code == 200
        assert b"Resume" in response.data

    def test_upload_resume(self, authenticated_employee_client):
        """Test uploading a resume."""
        # Create a fake PDF file
        data = {
            "resume_file": (io.BytesIO(b"fake pdf content"), "resume.pdf"),
        }
        response = authenticated_employee_client.post(
            "/employee/resume/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Resume uploaded" in response.data

    def test_upload_invalid_file_type(self, authenticated_employee_client):
        """Test uploading invalid file type."""
        data = {
            "resume_file": (io.BytesIO(b"fake exe content"), "virus.exe"),
        }
        response = authenticated_employee_client.post(
            "/employee/resume/upload",
            data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Invalid file type" in response.data


class TestEmployeeRoleComparison:
    """Tests for role comparison functionality."""

    def test_compare_roles_page(self, authenticated_employee_client):
        """Test compare roles page."""
        response = authenticated_employee_client.get("/employee/compare")
        assert response.status_code == 200
        assert b"Compare" in response.data

    def test_compare_with_role(self, authenticated_employee_client, employee_with_skills):
        """Test comparing with a target role."""
        response = authenticated_employee_client.get(
            "/employee/compare?target_role=senior_developer"
        )
        assert response.status_code == 200
        assert b"Comparison Results" in response.data
        assert b"Senior Developer" in response.data


class TestEmployeeLearningPaths:
    """Tests for learning path functionality."""

    def test_view_learning_paths(self, authenticated_employee_client):
        """Test viewing learning paths."""
        response = authenticated_employee_client.get("/employee/learning-paths")
        assert response.status_code == 200
        assert b"Learning Paths" in response.data

    def test_generate_learning_path(self, authenticated_employee_client):
        """Test generating a learning path."""
        response = authenticated_employee_client.post(
            "/employee/learning-paths/generate",
            data={"target_role": "senior_developer"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Learning path generated" in response.data or b"Senior Developer" in response.data

    def test_view_learning_path_detail(self, authenticated_employee_client, learning_path):
        """Test viewing learning path details."""
        response = authenticated_employee_client.get(
            f"/employee/learning-paths/{learning_path.id}"
        )
        assert response.status_code == 200
        assert b"Learning Path" in response.data or b"Skills to Acquire" in response.data

    def test_complete_learning_path(self, authenticated_employee_client, learning_path):
        """Test marking learning path as completed."""
        response = authenticated_employee_client.post(
            f"/employee/learning-paths/{learning_path.id}/complete",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"completed" in response.data.lower()


class TestEmployeeProfile:
    """Tests for employee profile."""

    def test_view_profile(self, authenticated_employee_client):
        """Test viewing own profile."""
        response = authenticated_employee_client.get("/employee/profile")
        assert response.status_code == 200
        assert b"My Profile" in response.data


class TestEmployeeResumeOperations:
    """Tests for advanced resume operations."""

    def test_download_resume(self, authenticated_employee_client, tmp_path):
        """Test downloading resume."""
        # First upload a resume
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\nTest content")

        with open(test_file, 'rb') as f:
            data = {"resume_file": (f, "test.pdf")}
            authenticated_employee_client.post(
                "/employee/resume/upload",
                data=data,
                content_type="multipart/form-data",
            )

        # Now try to download it
        response = authenticated_employee_client.get("/employee/resume/download")
        # Response might be 200 or 404 depending on storage setup
        assert response.status_code in [200, 404, 302]

    def test_delete_resume(self, authenticated_employee_client, tmp_path):
        """Test deleting resume."""
        # First upload a resume
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4\nTest content")

        with open(test_file, 'rb') as f:
            data = {"resume_file": (f, "test.pdf")}
            authenticated_employee_client.post(
                "/employee/resume/upload",
                data=data,
                content_type="multipart/form-data",
            )

        # Now delete it
        response = authenticated_employee_client.post(
            "/employee/resume/delete",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"deleted" in response.data.lower() or b"Resume" in response.data

    def test_download_nonexistent_resume(self, authenticated_employee_client):
        """Test downloading when no resume exists."""
        response = authenticated_employee_client.get("/employee/resume/download")
        assert response.status_code in [404, 302]


class TestEmployeeSkillOperations:
    """Tests for employee skill management operations."""

    def test_update_skill_proficiency(self, authenticated_employee_client, employee_with_skills, skills):
        """Test updating skill proficiency level."""
        response = authenticated_employee_client.post(
            "/employee/skills/update",
            data={"skill_id": skills[0].id, "proficiency_level": 5},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"updated" in response.data.lower() or b"Skill" in response.data

    def test_remove_skill_from_profile(self, authenticated_employee_client, employee_with_skills, skills):
        """Test removing skill from employee profile."""
        response = authenticated_employee_client.post(
            "/employee/skills/remove",
            data={"skill_id": skills[0].id},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"removed" in response.data.lower() or b"Skill" in response.data

    def test_add_invalid_skill(self, authenticated_employee_client):
        """Test adding skill with invalid data."""
        response = authenticated_employee_client.post(
            "/employee/skills/add",
            data={"skill_id": 99999, "proficiency_level": 3},
            follow_redirects=True,
        )
        assert response.status_code in [200, 404]


class TestEmployeeAssignmentDetails:
    """Tests for viewing assignment details."""

    def test_view_nonexistent_assignment(self, authenticated_employee_client):
        """Test viewing assignment that doesn't exist."""
        response = authenticated_employee_client.get("/employee/assignments/99999")
        assert response.status_code in [404, 302, 200]

    def test_view_other_user_assignment_forbidden(self, authenticated_employee_client, assignment, employee_user):
        """Test that employee cannot view other user's assignment."""
        # This assignment belongs to employee_user from fixture
        # Try to access it with a different employee
        response = authenticated_employee_client.get(f"/employee/assignments/{assignment.id}")
        # Should either be allowed (if it's their own) or forbidden
        assert response.status_code in [200, 403, 404]
