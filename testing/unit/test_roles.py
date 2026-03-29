"""
Unit tests for manager and employee modules.

This module tests role-specific dashboard access and functionality
for manager and employee roles.
"""

import pytest
from app.models import User


class TestManagerModule:
    """Test suite for manager module functionality."""

    def test_manager_dashboard_loads(self, authenticated_manager_client):
        """Test that manager dashboard loads successfully."""
        response = authenticated_manager_client.get("/manager/")
        assert response.status_code == 200
        assert b"manager" in response.data.lower() or b"dashboard" in response.data.lower()

    def test_manager_dashboard_requires_authentication(self, client):
        """Test that unauthenticated users cannot access manager dashboard."""
        response = client.get("/manager/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_manager_dashboard_requires_manager_role(self, authenticated_employee_client):
        """Test that non-manager users cannot access manager dashboard."""
        response = authenticated_employee_client.get("/manager/")
        assert response.status_code == 403

    def test_admin_cannot_access_manager_dashboard(self, authenticated_admin_client):
        """Test that admin cannot access manager dashboard without proper role."""
        response = authenticated_admin_client.get("/manager/")
        assert response.status_code == 403

    def test_manager_can_access_manager_dashboard(self, authenticated_manager_client):
        """Test that manager role can access manager dashboard."""
        response = authenticated_manager_client.get("/manager/")
        assert response.status_code == 200

    def test_manager_decorator_functionality(self, client, manager_user):
        """Test that manager_required decorator works correctly."""
        
        client.post("/auth/login", data={
            "email": manager_user.email,
            "password": "Manager@123",
        }, follow_redirects=True)

        response = client.get("/manager/")
        assert response.status_code == 200

    def test_manager_decorator_blocks_other_roles(self, client, employee_user):
        """Test that manager_required decorator blocks non-manager users."""
        
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        response = client.get("/manager/")
        assert response.status_code == 403


class TestEmployeeModule:
    """Test suite for employee module functionality."""

    def test_employee_dashboard_loads(self, authenticated_employee_client):
        """Test that employee dashboard loads successfully."""
        response = authenticated_employee_client.get("/employee/")
        assert response.status_code == 200
        assert b"employee" in response.data.lower() or b"dashboard" in response.data.lower()

    def test_employee_dashboard_requires_authentication(self, client):
        """Test that unauthenticated users cannot access employee dashboard."""
        response = client.get("/employee/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_employee_dashboard_requires_employee_role(self, authenticated_manager_client):
        """Test that non-employee users cannot access employee dashboard."""
        response = authenticated_manager_client.get("/employee/")
        assert response.status_code == 403

    def test_admin_cannot_access_employee_dashboard(self, authenticated_admin_client):
        """Test that admin cannot access employee dashboard without proper role."""
        response = authenticated_admin_client.get("/employee/")
        assert response.status_code == 403

    def test_employee_can_access_employee_dashboard(self, authenticated_employee_client):
        """Test that employee role can access employee dashboard."""
        response = authenticated_employee_client.get("/employee/")
        assert response.status_code == 200

    def test_employee_decorator_functionality(self, client, employee_user):
        """Test that employee_required decorator works correctly."""
        
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        response = client.get("/employee/")
        assert response.status_code == 200

    def test_employee_decorator_blocks_other_roles(self, client, manager_user):
        """Test that employee_required decorator blocks non-employee users."""
        
        client.post("/auth/login", data={
            "email": manager_user.email,
            "password": "Manager@123",
        }, follow_redirects=True)

        response = client.get("/employee/")
        assert response.status_code == 403


class TestViewsModule:
    """Test suite for views module (main routing)."""

    def test_root_redirect_for_admin(self, authenticated_admin_client):
        """Test that root path redirects admin to admin dashboard."""
        response = authenticated_admin_client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"admin" in response.data.lower() or b"dashboard" in response.data.lower()

    def test_root_redirect_for_manager(self, authenticated_manager_client):
        """Test that root path redirects manager to manager dashboard."""
        response = authenticated_manager_client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"manager" in response.data.lower() or b"dashboard" in response.data.lower()

    def test_root_redirect_for_employee(self, authenticated_employee_client):
        """Test that root path redirects employee to employee dashboard."""
        response = authenticated_employee_client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"employee" in response.data.lower() or b"dashboard" in response.data.lower()

    def test_root_requires_authentication(self, client):
        """Test that unauthenticated users are redirected from root."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_role_dashboard_url_helper_admin(self, client, admin_user):
        """Test role-based dashboard URL resolution for admin."""
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/admin" in response.location

    def test_role_dashboard_url_helper_manager(self, client, manager_user):
        """Test role-based dashboard URL resolution for manager."""
        client.post("/auth/login", data={
            "email": manager_user.email,
            "password": "Manager@123",
        }, follow_redirects=True)

        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/manager" in response.location

    def test_role_dashboard_url_helper_employee(self, client, employee_user):
        """Test role-based dashboard URL resolution for employee."""
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        response = client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/employee" in response.location


class TestRoleBasedAccessControl:
    """Test suite for comprehensive role-based access control."""

    def test_admin_role_access_permissions(self, authenticated_admin_client):
        """Test that admin can access admin routes but not manager/employee routes."""
        admin_response = authenticated_admin_client.get("/admin/")
        manager_response = authenticated_admin_client.get("/manager/")
        employee_response = authenticated_admin_client.get("/employee/")

        assert admin_response.status_code == 200
        assert manager_response.status_code == 403
        assert employee_response.status_code == 403

    def test_manager_role_access_permissions(self, authenticated_manager_client):
        """Test that manager can access manager routes but not admin/employee routes."""
        admin_response = authenticated_manager_client.get("/admin/")
        manager_response = authenticated_manager_client.get("/manager/")
        employee_response = authenticated_manager_client.get("/employee/")

        assert admin_response.status_code == 403
        assert manager_response.status_code == 200
        assert employee_response.status_code == 403

    def test_employee_role_access_permissions(self, authenticated_employee_client):
        """Test that employee can access employee routes but not admin/manager routes."""
        admin_response = authenticated_employee_client.get("/admin/")
        manager_response = authenticated_employee_client.get("/manager/")
        employee_response = authenticated_employee_client.get("/employee/")

        assert admin_response.status_code == 403
        assert manager_response.status_code == 403
        assert employee_response.status_code == 200

    def test_role_hierarchy_enforcement(self, client, db_session):
        """Test that role hierarchy is properly enforced."""
        
        users = [
            User(username="test_admin", email="test_admin@test.com", role="admin", is_approved=True, is_active=True),
            User(username="test_manager", email="test_manager@test.com", role="manager", is_approved=True, is_active=True),
            User(username="test_employee", email="test_employee@test.com", role="employee", is_approved=True, is_active=True),
        ]

        for user in users:
            user.set_password("Test@123")
            db_session.add(user)
        db_session.commit()

        
        for user in users:
            client.post("/auth/login", data={
                "email": user.email,
                "password": "Test@123",
            }, follow_redirects=True)

            if user.role == "admin":
                assert client.get("/admin/").status_code == 200
                assert client.get("/manager/").status_code == 403
                assert client.get("/employee/").status_code == 403
            elif user.role == "manager":
                assert client.get("/admin/").status_code == 403
                assert client.get("/manager/").status_code == 200
                assert client.get("/employee/").status_code == 403
            elif user.role == "employee":
                assert client.get("/admin/").status_code == 403
                assert client.get("/manager/").status_code == 403
                assert client.get("/employee/").status_code == 200

            client.get("/auth/logout")
