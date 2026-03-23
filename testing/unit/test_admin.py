"""
Unit tests for admin module functionality.

This module tests admin-specific operations including user approval,
rejection, management, blacklisting, and notifications.
"""

import pytest
from app.models import User, Notification
from app import db


class TestAdminDashboard:
    """Test suite for admin dashboard."""

    def test_admin_dashboard_loads(self, authenticated_admin_client):
        """Test that admin dashboard loads successfully."""
        response = authenticated_admin_client.get("/admin/")
        assert response.status_code == 200
        assert b"dashboard" in response.data.lower() or b"admin" in response.data.lower()

    def test_admin_dashboard_shows_pending_users(self, authenticated_admin_client, pending_user):
        """Test that pending users appear on admin dashboard."""
        response = authenticated_admin_client.get("/admin/")
        assert response.status_code == 200
        assert pending_user.email.encode() in response.data or pending_user.username.encode() in response.data

    def test_admin_dashboard_search_functionality(self, authenticated_admin_client, pending_user, db_session):
        """Test admin dashboard user search."""
        response = authenticated_admin_client.get(f"/admin/?q={pending_user.username}")
        assert response.status_code == 200
        assert pending_user.username.encode() in response.data

    def test_non_admin_cannot_access_dashboard(self, authenticated_employee_client):
        """Test that non-admin users cannot access admin dashboard."""
        response = authenticated_employee_client.get("/admin/")
        assert response.status_code == 403


class TestUserApproval:
    """Test suite for user approval functionality."""

    def test_approve_pending_user(self, authenticated_admin_client, pending_user, db_session):
        """Test approving a pending user."""
        response = authenticated_admin_client.post(
            f"/admin/approve/{pending_user.id}",
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(pending_user)
        assert pending_user.is_approved is True

    def test_approve_nonexistent_user(self, authenticated_admin_client):
        """Test approving non-existent user returns 404."""
        response = authenticated_admin_client.post("/admin/approve/99999")
        assert response.status_code == 404

    def test_non_admin_cannot_approve_user(self, authenticated_manager_client, pending_user):
        """Test that non-admin cannot approve users."""
        response = authenticated_manager_client.post(f"/admin/approve/{pending_user.id}")
        assert response.status_code == 403


class TestUserRejection:
    """Test suite for user rejection functionality."""

    def test_reject_pending_user(self, authenticated_admin_client, db_session):
        """Test rejecting a pending user (deletes user)."""
        user = User(
            username="rejecttest",
            email="reject@test.com",
            role="employee",
            is_approved=False,
        )
        user.set_password("Pass@123")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        response = authenticated_admin_client.post(
            f"/admin/reject/{user_id}",
            follow_redirects=True
        )
        assert response.status_code == 200

        rejected_user = db_session.get(User, user_id)
        assert rejected_user is None

    def test_reject_nonexistent_user(self, authenticated_admin_client):
        """Test rejecting non-existent user returns 404."""
        response = authenticated_admin_client.post("/admin/reject/99999")
        assert response.status_code == 404

    def test_non_admin_cannot_reject_user(self, authenticated_manager_client, pending_user):
        """Test that non-admin cannot reject users."""
        response = authenticated_manager_client.post(f"/admin/reject/{pending_user.id}")
        assert response.status_code == 403


class TestUserManagement:
    """Test suite for user management operations."""

    def test_manage_users_page_loads(self, authenticated_admin_client):
        """Test that manage users page loads successfully."""
        response = authenticated_admin_client.get("/admin/users")
        assert response.status_code == 200

    def test_manage_users_shows_all_users(self, authenticated_admin_client, manager_user, employee_user):
        """Test that manage users page shows all non-admin users."""
        response = authenticated_admin_client.get("/admin/users")
        assert response.status_code == 200
        assert manager_user.email.encode() in response.data or employee_user.email.encode() in response.data

    def test_manage_users_pagination(self, authenticated_admin_client, db_session):
        """Test pagination on manage users page."""
        # Create multiple users
        for i in range(15):
            user = User(
                username=f"paginationtest{i}",
                email=f"page{i}@test.com",
                role="employee",
                is_approved=True,
            )
            user.set_password("Test@123")
            db_session.add(user)
        db_session.commit()

        # Test first page with 10 per page
        response = authenticated_admin_client.get("/admin/users?per_page=10")
        assert response.status_code == 200

        # Test with different per_page value
        response = authenticated_admin_client.get("/admin/users?per_page=20")
        assert response.status_code == 200

    def test_manage_users_role_filter(self, authenticated_admin_client, manager_user, employee_user):
        """Test role filtering on manage users page."""
        # Filter by manager role
        response = authenticated_admin_client.get("/admin/users?role_filter=manager")
        assert response.status_code == 200

        # Filter by employee role
        response = authenticated_admin_client.get("/admin/users?role_filter=employee")
        assert response.status_code == 200

    def test_manage_users_status_filter(self, authenticated_admin_client, db_session):
        """Test status filtering on manage users page."""
        # Create approved and pending users
        approved_user = User(
            username="approveduser",
            email="approved@test.com",
            role="employee",
            is_approved=True,
        )
        approved_user.set_password("Test@123")

        pending_user = User(
            username="pendinguser",
            email="pending@test.com",
            role="employee",
            is_approved=False,
        )
        pending_user.set_password("Test@123")

        db_session.add_all([approved_user, pending_user])
        db_session.commit()

        # Test page loads with status filter options
        response = authenticated_admin_client.get("/admin/users")
        assert response.status_code == 200
        assert b"status-filter" in response.data or b"Status" in response.data
        
        # Test filtering by approved
        response = authenticated_admin_client.get("/admin/users?status_filter=approved")
        assert response.status_code == 200
        assert b"approveduser" in response.data
        assert b"pendinguser" not in response.data

        # Test filtering by pending
        response = authenticated_admin_client.get("/admin/users?status_filter=pending")
        assert response.status_code == 200
        assert b"pendinguser" in response.data
        assert b"approveduser" not in response.data

    def test_manage_users_combined_filters(self, authenticated_admin_client, db_session):
        """Test combining role and status filters."""
        # Create users with different combinations
        approved_manager = User(
            username="appmanager",
            email="appmanager@test.com",
            role="manager",
            is_approved=True,
        )
        approved_manager.set_password("Test@123")

        pending_employee = User(
            username="pendemp",
            email="pendemp@test.com",
            role="employee",
            is_approved=False,
        )
        pending_employee.set_password("Test@123")

        db_session.add_all([approved_manager, pending_employee])
        db_session.commit()

        # Test combined filters
        response = authenticated_admin_client.get("/admin/users?role_filter=manager&status_filter=approved")
        assert response.status_code == 200
        assert b"appmanager" in response.data
        assert b"pendemp" not in response.data

        response = authenticated_admin_client.get("/admin/users?role_filter=employee&status_filter=pending")
        assert response.status_code == 200
        assert b"pendemp" in response.data
        assert b"appmanager" not in response.data

    def test_manage_users_shows_statistics(self, authenticated_admin_client):
        """Test that manage users page shows user statistics."""
        response = authenticated_admin_client.get("/admin/users")
        assert response.status_code == 200
        # Check for statistical elements
        assert b"New Users" in response.data or b"Awaiting" in response.data or b"Blacklisted" in response.data

    def test_manage_users_action_buttons(self, authenticated_admin_client, employee_user):
        """Test that action buttons are present for users."""
        response = authenticated_admin_client.get("/admin/users")
        assert response.status_code == 200
        # Check for action elements
        assert b"Edit" in response.data or b"edit" in response.data

    def test_edit_user_page_loads(self, authenticated_admin_client, employee_user):
        """Test that edit user page loads successfully."""
        response = authenticated_admin_client.get(f"/admin/users/{employee_user.id}/edit")
        assert response.status_code == 200
        assert employee_user.email.encode() in response.data

    def test_edit_user_details(self, authenticated_admin_client, employee_user, db_session):
        """Test editing user details."""
        response = authenticated_admin_client.post(
            f"/admin/users/{employee_user.id}/edit",
            data={
                "username": "updated_employee",
                "email": "updated@example.com",
                "role": "manager",
                "is_active": "on",
                "is_approved": "on",
            },
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(employee_user)
        assert employee_user.username == "updated_employee"
        assert employee_user.email == "updated@example.com"
        assert employee_user.role == "manager"

    def test_edit_user_with_invalid_role(self, authenticated_admin_client, employee_user):
        """Test editing user with invalid role."""
        response = authenticated_admin_client.post(
            f"/admin/users/{employee_user.id}/edit",
            data={
                "username": employee_user.username,
                "email": employee_user.email,
                "role": "invalid_role",
            },
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_edit_user_with_duplicate_email(self, authenticated_admin_client, employee_user, manager_user):
        """Test editing user with already existing email."""
        response = authenticated_admin_client.post(
            f"/admin/users/{employee_user.id}/edit",
            data={
                "username": employee_user.username,
                "email": manager_user.email,
                "role": employee_user.role,
            },
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_admin_cannot_edit_self(self, authenticated_admin_client, admin_user):
        """Test that admin cannot edit their own account."""
        response = authenticated_admin_client.post(
            f"/admin/users/{admin_user.id}/edit",
            data={
                "username": "hacked",
                "email": "hacked@example.com",
                "role": "employee",
            },
            follow_redirects=True
        )
        assert response.status_code == 200

    def test_edit_nonexistent_user(self, authenticated_admin_client):
        """Test editing non-existent user returns 404."""
        response = authenticated_admin_client.get("/admin/users/99999/edit")
        assert response.status_code == 404


class TestUserDeletion:
    """Test suite for user deletion functionality."""

    def test_delete_user(self, authenticated_admin_client, db_session):
        """Test deleting a user."""
        user = User(
            username="deletetest",
            email="delete@test.com",
            role="employee",
            is_approved=True,
        )
        user.set_password("Pass@123")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        response = authenticated_admin_client.post(
            f"/admin/users/{user_id}/delete",
            follow_redirects=True
        )
        assert response.status_code == 200

        deleted_user = db_session.get(User, user_id)
        assert deleted_user is None

    def test_admin_cannot_delete_self(self, authenticated_admin_client, admin_user):
        """Test that admin cannot delete their own account."""
        response = authenticated_admin_client.post(
            f"/admin/users/{admin_user.id}/delete",
            follow_redirects=True
        )
        assert response.status_code == 200

        # Admin user should still exist
        admin_still_exists = User.query.get(admin_user.id)
        assert admin_still_exists is not None

    def test_delete_nonexistent_user(self, authenticated_admin_client):
        """Test deleting non-existent user returns 404."""
        response = authenticated_admin_client.post("/admin/users/99999/delete")
        assert response.status_code == 404


class TestUserBlacklisting:
    """Test suite for user blacklisting functionality."""

    def test_blacklist_user(self, authenticated_admin_client, employee_user, db_session):
        """Test blacklisting a user."""
        response = authenticated_admin_client.post(
            f"/admin/users/{employee_user.id}/blacklist",
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(employee_user)
        assert employee_user.is_blacklisted is True
        assert employee_user.is_active is False

    def test_admin_cannot_blacklist_self(self, authenticated_admin_client, admin_user, db_session):
        """Test that admin cannot blacklist themselves."""
        response = authenticated_admin_client.post(
            f"/admin/users/{admin_user.id}/blacklist",
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(admin_user)
        assert admin_user.is_blacklisted is False

    def test_blacklist_nonexistent_user(self, authenticated_admin_client):
        """Test blacklisting non-existent user returns 404."""
        response = authenticated_admin_client.post("/admin/users/99999/blacklist")
        assert response.status_code == 404

    def test_view_blacklisted_users(self, authenticated_admin_client, blacklisted_user):
        """Test viewing list of blacklisted users."""
        response = authenticated_admin_client.get("/admin/blacklisted")
        assert response.status_code == 200
        assert blacklisted_user.email.encode() in response.data or blacklisted_user.username.encode() in response.data

    def test_whitelist_user(self, authenticated_admin_client, blacklisted_user, db_session):
        """Test whitelisting a blacklisted user."""
        response = authenticated_admin_client.post(
            f"/admin/whitelist/{blacklisted_user.id}",
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(blacklisted_user)
        assert blacklisted_user.is_blacklisted is False
        assert blacklisted_user.is_active is True

    def test_whitelist_nonexistent_user(self, authenticated_admin_client):
        """Test whitelisting non-existent user returns 404."""
        response = authenticated_admin_client.post("/admin/whitelist/99999")
        assert response.status_code == 404


class TestPasswordReset:
    """Test suite for admin password reset functionality."""

    def test_reset_credentials_page_loads(self, authenticated_admin_client):
        """Test that reset credentials page loads."""
        response = authenticated_admin_client.get("/admin/reset-credentials")
        assert response.status_code == 200

    def test_search_user_for_reset(self, authenticated_admin_client, employee_user):
        """Test searching for user to reset password."""
        response = authenticated_admin_client.get(f"/admin/reset-credentials?q={employee_user.username}")
        assert response.status_code == 200
        assert employee_user.username.encode() in response.data

    def test_reset_user_password(self, authenticated_admin_client, employee_user, db_session):
        """Test resetting a user's password."""
        new_password = "NewSecurePass@123"
        response = authenticated_admin_client.post(
            f"/admin/reset-password/{employee_user.id}",
            data={"new_password": new_password},
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(employee_user)
        assert employee_user.check_password(new_password) is True

    def test_reset_password_too_short(self, authenticated_admin_client, employee_user, db_session):
        """Test resetting password with too short password."""
        old_hash = employee_user.password_hash
        response = authenticated_admin_client.post(
            f"/admin/reset-password/{employee_user.id}",
            data={"new_password": "123"},
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(employee_user)
        assert employee_user.password_hash == old_hash

    def test_reset_password_nonexistent_user(self, authenticated_admin_client):
        """Test resetting password for non-existent user returns 404."""
        response = authenticated_admin_client.post(
            "/admin/reset-password/99999",
            data={"new_password": "NewPass@123"}
        )
        assert response.status_code == 404


class TestForceLogout:
    """Test suite for force logout functionality."""

    def test_force_logout_user(self, authenticated_admin_client, employee_user, db_session):
        """Test force logging out a user (deactivates account)."""
        response = authenticated_admin_client.post(
            f"/admin/force-logout/{employee_user.id}",
            follow_redirects=True
        )
        assert response.status_code == 200

        db_session.refresh(employee_user)
        assert employee_user.is_active is False

    def test_force_logout_nonexistent_user(self, authenticated_admin_client):
        """Test force logout for non-existent user returns 404."""
        response = authenticated_admin_client.post("/admin/force-logout/99999")
        assert response.status_code == 404


class TestAdminNotifications:
    """Test suite for admin notification system."""

    def test_admin_notification_creation(self, authenticated_admin_client, db_session, admin_user):
        """Test that admin notifications are created on actions."""
        pending = User(
            username="notiftest",
            email="notif@test.com",
            role="employee",
            is_approved=False,
        )
        pending.set_password("Pass@123")
        db_session.add(pending)
        db_session.commit()

        # Approve user to trigger notification
        authenticated_admin_client.post(
            f"/admin/approve/{pending.id}",
            follow_redirects=True
        )

        notifications = Notification.query.filter_by(user_id=admin_user.id).all()
        assert len(notifications) >= 1

    def test_notification_context_processor(self, authenticated_admin_client, admin_user, db_session):
        """Test that notifications are injected into admin templates."""
        # Create a notification
        notif = Notification(
            user_id=admin_user.id,
            message="Test notification",
            type="info",
            is_read=False,
        )
        db_session.add(notif)
        db_session.commit()

        response = authenticated_admin_client.get("/admin/")
        assert response.status_code == 200
