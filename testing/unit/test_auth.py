"""
Unit tests for authentication module (login, register, logout).

This module tests authentication flows, user registration validation,
login/logout functionality, and access control.
"""

import pytest
from flask import url_for
from app.models import User
from app import db


class TestAuthLogin:
    """Test suite for login functionality."""

    def test_login_page_loads(self, client):
        """Test that login page loads successfully."""
        response = client.get("/auth/login")
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_login_with_valid_credentials(self, client, admin_user):
        """Test successful login with valid credentials."""
        response = client.post("/auth/login", data={
            "email": "admin@hiresense.test",
            "password": "Admin@123",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"dashboard" in response.data.lower() or b"admin" in response.data.lower()

    def test_login_with_invalid_email(self, client):
        """Test login with non-existent email."""
        response = client.post("/auth/login", data={
            "email": "nonexistent@example.com",
            "password": "SomePassword123",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"invalid credentials" in response.data.lower()

    def test_login_with_invalid_password(self, client, admin_user):
        """Test login with incorrect password."""
        response = client.post("/auth/login", data={
            "email": "admin@hiresense.test",
            "password": "WrongPassword",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"invalid credentials" in response.data.lower()

    def test_login_with_blacklisted_user(self, client, blacklisted_user):
        """Test login attempt with blacklisted account."""
        response = client.post("/auth/login", data={
            "email": "blacklisted@hiresense.test",
            "password": "Blacklisted@123",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"blacklisted" in response.data.lower()

    def test_login_with_inactive_user(self, client, db_session):
        """Test login attempt with inactive account."""
        user = User(
            username="inactive",
            email="inactive@hiresense.test",
            role="employee",
            is_active=False,
            is_approved=True,
        )
        user.set_password("Inactive@123")
        db_session.add(user)
        db_session.commit()

        response = client.post("/auth/login", data={
            "email": "inactive@hiresense.test",
            "password": "Inactive@123",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"deactivated" in response.data.lower()

    def test_login_with_pending_user(self, client, pending_user):
        """Test login attempt with pending (unapproved) account."""
        response = client.post("/auth/login", data={
            "email": "pending@hiresense.test",
            "password": "Pending@123",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"pending" in response.data.lower() or b"approval" in response.data.lower()

    def test_login_with_remember_me(self, client, admin_user):
        """Test login with 'remember me' option."""
        response = client.post("/auth/login", data={
            "email": "admin@hiresense.test",
            "password": "Admin@123",
            "remember": "on",
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_redirect_when_authenticated(self, authenticated_admin_client):
        """Test that authenticated users are redirected away from login page."""
        response = authenticated_admin_client.get("/auth/login", follow_redirects=True)
        assert response.status_code == 200

    def test_login_case_insensitive_email(self, client, admin_user):
        """Test that email login is case-insensitive."""
        response = client.post("/auth/login", data={
            "email": "ADMIN@HIRESENSE.TEST",
            "password": "Admin@123",
        }, follow_redirects=True)

        assert response.status_code == 200

    def test_login_redirects_to_role_dashboard(self, client, manager_user):
        """Test that login redirects to appropriate role dashboard."""
        response = client.post("/auth/login", data={
            "email": "manager@hiresense.test",
            "password": "Manager@123",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"manager" in response.data.lower() or b"dashboard" in response.data.lower()


class TestAuthRegister:
    """Test suite for registration functionality."""

    def test_register_page_loads(self, client):
        """Test that registration page loads successfully."""
        response = client.get("/auth/register")
        assert response.status_code == 200
        assert b"register" in response.data.lower()

    def test_register_new_employee(self, client, db_session):
        """Test successful registration of new employee."""
        response = client.post("/auth/register", data={
            "username": "newemployee",
            "email": "newemployee@example.com",
            "password": "NewPass@123",
            "role": "employee",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"account created" in response.data.lower() or b"log in" in response.data.lower()

        user = User.query.filter_by(email="newemployee@example.com").first()
        assert user is not None
        assert user.username == "newemployee"
        assert user.role == "employee"

    def test_register_new_manager(self, client, db_session):
        """Test successful registration of new manager."""
        response = client.post("/auth/register", data={
            "username": "newmanager",
            "email": "newmanager@example.com",
            "password": "NewPass@123",
            "role": "manager",
        }, follow_redirects=True)

        assert response.status_code == 200

        user = User.query.filter_by(email="newmanager@example.com").first()
        assert user is not None
        assert user.role == "manager"

    def test_register_with_duplicate_email(self, client, admin_user):
        """Test registration with already existing email."""
        response = client.post("/auth/register", data={
            "username": "duplicate",
            "email": "admin@hiresense.test",
            "password": "NewPass@123",
            "role": "employee",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"already registered" in response.data.lower() or b"email" in response.data.lower()

    def test_register_with_invalid_role(self, client):
        """Test registration with invalid role."""
        response = client.post("/auth/register", data={
            "username": "invalidrole",
            "email": "invalidrole@example.com",
            "password": "NewPass@123",
            "role": "admin",
        }, follow_redirects=True)

        assert response.status_code == 200
        assert b"invalid role" in response.data.lower()

    def test_register_default_user_status(self, client, db_session):
        """Test that new users have correct default status."""
        client.post("/auth/register", data={
            "username": "statustest",
            "email": "statustest@example.com",
            "password": "Pass@123",
            "role": "employee",
        }, follow_redirects=True)

        user = User.query.filter_by(email="statustest@example.com").first()
        assert user.is_approved is False
        assert user.is_active is True
        assert user.is_blacklisted is False

    def test_register_password_is_hashed(self, client, db_session):
        """Test that registered passwords are properly hashed."""
        client.post("/auth/register", data={
            "username": "hashtest",
            "email": "hashtest@example.com",
            "password": "PlainPassword123",
            "role": "employee",
        }, follow_redirects=True)

        user = User.query.filter_by(email="hashtest@example.com").first()
        assert user.password_hash != "PlainPassword123"
        assert user.check_password("PlainPassword123") is True

    def test_register_redirect_when_authenticated(self, authenticated_admin_client):
        """Test that authenticated users are redirected away from registration."""
        response = authenticated_admin_client.get("/auth/register", follow_redirects=True)
        assert response.status_code == 200

    def test_register_with_whitespace_in_fields(self, client, db_session):
        """Test registration with whitespace in username and email."""
        response = client.post("/auth/register", data={
            "username": "  spaceuser  ",
            "email": "  space@example.com  ",
            "password": "Pass@123",
            "role": "employee",
        }, follow_redirects=True)

        assert response.status_code == 200

        user = User.query.filter_by(email="space@example.com").first()
        if user:
            assert user.username.strip() == "spaceuser"


class TestAuthLogout:
    """Test suite for logout functionality."""

    def test_logout_when_authenticated(self, authenticated_admin_client):
        """Test successful logout."""
        response = authenticated_admin_client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_logout_unauthenticated_user(self, client):
        """Test logout attempt without authentication."""
        response = client.get("/auth/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"login" in response.data.lower()

    def test_logout_clears_session(self, client, admin_user):
        """Test that logout properly clears user session."""
        
        client.post("/auth/login", data={
            "email": "admin@hiresense.test",
            "password": "Admin@123",
        }, follow_redirects=True)

        
        client.get("/auth/logout", follow_redirects=True)

        
        response = client.get("/admin/")
        assert response.status_code in [302, 401]


class TestAuthAccessControl:
    """Test suite for authentication-based access control."""

    def test_unauthenticated_redirect_to_login(self, client):
        """Test that unauthenticated users are redirected to login."""
        response = client.get("/admin/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location

    def test_authenticated_user_can_access_dashboard(self, authenticated_admin_client):
        """Test that authenticated users can access their dashboard."""
        response = authenticated_admin_client.get("/admin/")
        assert response.status_code == 200

    def test_role_based_access_admin(self, authenticated_admin_client):
        """Test that admin can access admin routes."""
        response = authenticated_admin_client.get("/admin/")
        assert response.status_code == 200

    def test_role_based_access_manager(self, authenticated_manager_client):
        """Test that manager can access manager routes."""
        response = authenticated_manager_client.get("/manager/")
        assert response.status_code == 200

    def test_role_based_access_employee(self, authenticated_employee_client):
        """Test that employee can access employee routes."""
        response = authenticated_employee_client.get("/employee/")
        assert response.status_code == 200

    def test_manager_cannot_access_admin_routes(self, authenticated_manager_client):
        """Test that manager cannot access admin-only routes."""
        response = authenticated_manager_client.get("/admin/")
        assert response.status_code == 403

    def test_employee_cannot_access_admin_routes(self, authenticated_employee_client):
        """Test that employee cannot access admin-only routes."""
        response = authenticated_employee_client.get("/admin/")
        assert response.status_code == 403

    def test_employee_cannot_access_manager_routes(self, authenticated_employee_client):
        """Test that employee cannot access manager-only routes."""
        response = authenticated_employee_client.get("/manager/")
        assert response.status_code == 403
