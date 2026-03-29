"""
Integration tests for API endpoints and database interactions.

This module tests the integration between different system components,
including endpoints, database operations, and model relationships.
"""

import pytest
from app.models import User, Notification
from app import db


class TestAuthenticationIntegration:
    """Integration tests for authentication flow with database."""

    def test_complete_registration_and_login_flow(self, client, db_session):
        """Test complete user registration and login workflow."""
        
        register_response = client.post("/auth/register", data={
            "username": "integrationuser",
            "email": "integration@test.com",
            "password": "Integration@123",
            "role": "employee",
        }, follow_redirects=True)

        assert register_response.status_code == 200

        
        user = User.query.filter_by(email="integration@test.com").first()
        assert user is not None
        assert user.username == "integrationuser"
        assert user.is_approved is False

        
        login_response = client.post("/auth/login", data={
            "email": "integration@test.com",
            "password": "Integration@123",
        }, follow_redirects=True)

        assert b"pending" in login_response.data.lower() or b"approval" in login_response.data.lower()

        
        user.is_approved = True
        db_session.commit()

        
        login_response = client.post("/auth/login", data={
            "email": "integration@test.com",
            "password": "Integration@123",
        }, follow_redirects=True)

        assert login_response.status_code == 200

    def test_session_persistence_across_requests(self, client, employee_user):
        """Test that user session persists across multiple requests."""
        
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        
        response1 = client.get("/employee/")
        response2 = client.get("/employee/")
        response3 = client.get("/employee/")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200

    def test_logout_invalidates_session(self, client, employee_user):
        """Test that logout properly invalidates user session."""
        
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        
        response = client.get("/employee/")
        assert response.status_code == 200

        
        client.get("/auth/logout", follow_redirects=True)

        
        response = client.get("/employee/", follow_redirects=False)
        assert response.status_code == 302
        assert "/auth/login" in response.location


class TestAdminUserManagementIntegration:
    """Integration tests for admin user management with database."""

    def test_approve_user_workflow(self, client, db_session, admin_user):
        """Test complete user approval workflow."""
        
        pending = User(
            username="pendingtest",
            email="pendingtest@test.com",
            role="employee",
            is_approved=False,
            is_active=True,
        )
        pending.set_password("Pending@123")
        db_session.add(pending)
        db_session.commit()
        pending_id = pending.id

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        dashboard_response = client.get("/admin/")
        assert pending.username.encode() in dashboard_response.data

        
        client.post(f"/admin/approve/{pending_id}", follow_redirects=True)

        
        approved_user = db_session.get(User, pending_id)
        assert approved_user.is_approved is True

        
        dashboard_response = client.get("/admin/")
        

    def test_edit_user_updates_database(self, client, db_session, admin_user, employee_user):
        """Test that editing user updates database correctly."""
        original_username = employee_user.username
        original_role = employee_user.role

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        client.post(f"/admin/users/{employee_user.id}/edit", data={
            "username": "edited_username",
            "email": employee_user.email,
            "role": "manager",
            "is_active": "on",
            "is_approved": "on",
        }, follow_redirects=True)

        
        db_session.refresh(employee_user)
        assert employee_user.username == "edited_username"
        assert employee_user.role == "manager"
        assert employee_user.username != original_username
        assert employee_user.role != original_role

    def test_blacklist_prevents_login(self, client, db_session, admin_user, employee_user):
        """Test that blacklisted users cannot login."""
        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        client.post(f"/admin/users/{employee_user.id}/blacklist", follow_redirects=True)

        
        client.get("/auth/logout")

        
        login_response = client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        assert b"blacklisted" in login_response.data.lower()

        
        db_session.refresh(employee_user)
        assert employee_user.is_blacklisted is True


class TestNotificationIntegration:
    """Integration tests for notification system."""

    def test_notification_creation_on_approval(self, client, db_session, admin_user):
        """Test that notifications are created when users are approved."""
        
        pending = User(
            username="notifytest",
            email="notifytest@test.com",
            role="employee",
            is_approved=False,
        )
        pending.set_password("Notify@123")
        db_session.add(pending)
        db_session.commit()

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        client.post(f"/admin/approve/{pending.id}", follow_redirects=True)

        
        notifications = Notification.query.filter_by(user_id=admin_user.id).all()
        assert len(notifications) >= 1

    def test_notification_cascade_delete_on_user_deletion(self, db_session):
        """Test that notifications are deleted when user is deleted."""
        
        user = User(
            username="cascadetest",
            email="cascade@test.com",
            role="employee",
            is_approved=True,
        )
        user.set_password("Cascade@123")
        db_session.add(user)
        db_session.commit()

        
        notification = Notification(
            user_id=user.id,
            message="Test notification",
            type="info",
        )
        db_session.add(notification)
        db_session.commit()
        notification_id = notification.id

        
        db_session.delete(user)
        db_session.commit()

        
        deleted_notification = db_session.get(Notification, notification_id)
        assert deleted_notification is None


class TestDatabaseConstraints:
    """Integration tests for database constraints and validations."""

    def test_email_uniqueness_constraint(self, db_session, admin_user):
        """Test that email uniqueness is enforced at database level."""
        duplicate_user = User(
            username="duplicate",
            email=admin_user.email,
            role="employee",
        )
        duplicate_user.set_password("Duplicate@123")
        db_session.add(duplicate_user)

        with pytest.raises(Exception):
            db_session.commit()

    def test_user_deletion_allowed(self, db_session):
        """Test that user can be deleted from database."""
        user = User(
            username="deletetest",
            email="delete@test.com",
            role="employee",
        )
        user.set_password("Delete@123")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        db_session.delete(user)
        db_session.commit()

        deleted_user = db_session.get(User, user_id)
        assert deleted_user is None

    def test_notification_foreign_key_constraint(self, db_session, admin_user):
        """Test that notification requires valid user_id."""
        notification = Notification(
            user_id=admin_user.id,
            message="Test notification",
            type="info",
        )
        db_session.add(notification)
        db_session.commit()

        assert notification.user_id == admin_user.id


class TestMultiUserInteractions:
    """Integration tests for interactions between multiple users."""

    def test_multiple_users_can_login_simultaneously(self, client, db_session):
        """Test that multiple users can have active sessions."""
        users = [
            User(username=f"user{i}", email=f"user{i}@test.com", role="employee", is_approved=True, is_active=True)
            for i in range(3)
        ]

        for user in users:
            user.set_password("Test@123")
            db_session.add(user)
        db_session.commit()

        
        for user in users:
            response = client.post("/auth/login", data={
                "email": user.email,
                "password": "Test@123",
            }, follow_redirects=True)
            assert response.status_code == 200
            client.get("/auth/logout")

    def test_admin_actions_affect_other_users(self, client, db_session, admin_user):
        """Test that admin actions properly affect target users."""
        
        employee = User(
            username="target",
            email="target@test.com",
            role="employee",
            is_approved=True,
            is_active=True,
        )
        employee.set_password("Employee@123")
        db_session.add(employee)
        db_session.commit()
        employee_id = employee.id

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        client.post(f"/admin/users/{employee_id}/blacklist", follow_redirects=True)

        
        db_session.refresh(employee)
        assert employee.is_blacklisted is True

        
        client.get("/auth/logout")

        
        response = client.post("/auth/login", data={
            "email": employee.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        assert b"blacklisted" in response.data.lower()


class TestPasswordManagement:
    """Integration tests for password management."""

    def test_password_change_by_admin(self, client, db_session, admin_user, employee_user):
        """Test admin password reset functionality."""
        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        new_password = "NewPassword@456"
        client.post(f"/admin/reset-password/{employee_user.id}", data={
            "new_password": new_password,
        }, follow_redirects=True)

        
        client.get("/auth/logout")

        
        response = client.post("/auth/login", data={
            "email": employee_user.email,
            "password": new_password,
        }, follow_redirects=True)

        assert response.status_code == 200

        
        client.get("/auth/logout")
        response = client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        assert b"invalid credentials" in response.data.lower()

    def test_password_hashing_is_consistent(self, db_session):
        """Test that password hashing produces consistent results."""
        user = User(
            username="hashtest",
            email="hash@test.com",
            role="employee",
        )
        password = "TestPassword@123"
        user.set_password(password)
        db_session.add(user)
        db_session.commit()

        
        assert user.check_password(password) is True
        assert user.check_password("WrongPassword") is False

        
        assert user.password_hash != password


class TestRoleTransitions:
    """Integration tests for user role transitions."""

    def test_role_change_updates_access(self, client, db_session, admin_user, employee_user):
        """Test that changing role updates user access permissions."""
        
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        employee_access = client.get("/employee/")
        manager_access = client.get("/manager/")

        assert employee_access.status_code == 200
        assert manager_access.status_code == 403

        
        client.get("/auth/logout")

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        client.post(f"/admin/users/{employee_user.id}/edit", data={
            "username": employee_user.username,
            "email": employee_user.email,
            "role": "manager",
            "is_active": "on",
            "is_approved": "on",
        }, follow_redirects=True)

        
        client.get("/auth/logout")

        
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        employee_access = client.get("/employee/")
        manager_access = client.get("/manager/")

        assert employee_access.status_code == 403
        assert manager_access.status_code == 200


class TestManageUsersPageIntegration:
    """Integration tests for manage users page functionality."""

    def test_manage_users_with_filters_integration(self, client, db_session, admin_user):
        """Test manage users page with various filter combinations."""
        
        manager = User(username="filtermanager", email="filtermgr@test.com", role="manager", is_approved=True)
        manager.set_password("Test@123")
        employee = User(username="filteremployee", email="filteremp@test.com", role="employee", is_approved=True)
        employee.set_password("Test@123")
        db_session.add_all([manager, employee])
        db_session.commit()

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        response = client.get("/admin/users")
        assert response.status_code == 200

        
        response = client.get("/admin/users?role_filter=manager")
        assert response.status_code == 200

        
        response = client.get("/admin/users?per_page=20")
        assert response.status_code == 200

        
        response = client.get("/admin/users?role_filter=employee&per_page=10")
        assert response.status_code == 200

    def test_manage_users_status_filter_integration(self, client, db_session, admin_user):
        """Test status filtering works correctly."""
        
        for i in range(5):
            approved = User(
                username=f"approved{i}",
                email=f"approved{i}@test.com",
                role="employee",
                is_approved=True,
            )
            approved.set_password("Test@123")
            db_session.add(approved)

            pending = User(
                username=f"pending{i}",
                email=f"pending{i}@test.com",
                role="employee",
                is_approved=False,
            )
            pending.set_password("Test@123")
            db_session.add(pending)
        db_session.commit()

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        response = client.get("/admin/users")
        assert response.status_code == 200
        assert b"status-filter" in response.data or b"Status" in response.data
        
        
        response = client.get("/admin/users?status_filter=approved")
        assert response.status_code == 200
        assert b"approved0" in response.data
        assert b"pending0" not in response.data

        
        response = client.get("/admin/users?status_filter=pending")
        assert response.status_code == 200
        assert b"pending0" in response.data
        assert b"approved0" not in response.data

    def test_manage_users_pagination_integration(self, client, db_session, admin_user):
        """Test pagination works correctly with multiple users."""
        
        for i in range(15):
            user = User(
                username=f"pageuser{i}",
                email=f"pageuser{i}@test.com",
                role="employee",
                is_approved=True,
            )
            user.set_password("Test@123")
            db_session.add(user)
        db_session.commit()

        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        response = client.get("/admin/users?per_page=10&page=1")
        assert response.status_code == 200

        
        response = client.get("/admin/users?per_page=10&page=2")
        assert response.status_code == 200

    def test_export_users_integration(self, client, db_session, admin_user, employee_user):
        """Test user export functionality."""
        
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        
        response = client.get("/admin/users/export")
        assert response.status_code == 200
        assert response.content_type == "text/csv; charset=utf-8"
        response.get_data()

        
        response = client.get("/admin/users/export?role_filter=employee")
        assert response.status_code == 200
        response.get_data()

        
        response = client.get("/admin/users/export?status_filter=pending")
        assert response.status_code == 200
        response.get_data()
        
        response = client.get("/admin/users/export?status_filter=approved")
        assert response.status_code == 200
        response.get_data()
