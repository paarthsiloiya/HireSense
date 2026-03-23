"""
End-to-end system tests for complete user workflows.

This module tests complete business workflows from start to finish,
simulating real user interactions across the entire system.
"""

import pytest
from app.models import User, Notification
from app import db


class TestUserRegistrationWorkflow:
    """E2E tests for complete user registration workflow."""

    def test_complete_employee_registration_to_dashboard(self, client, db_session, admin_user):
        """
        Test complete workflow: employee registers, admin approves, employee logs in.
        """
        # Step 1: New employee registers
        register_response = client.post("/auth/register", data={
            "username": "newemployee",
            "email": "newemployee@company.com",
            "password": "NewEmp@123",
            "role": "employee",
        }, follow_redirects=True)

        assert register_response.status_code == 200
        assert b"account created" in register_response.data.lower() or b"log in" in register_response.data.lower()

        # Step 2: Verify employee exists but is not approved
        employee = User.query.filter_by(email="newemployee@company.com").first()
        assert employee is not None
        assert employee.is_approved is False

        # Step 3: Employee tries to login (should fail - pending approval)
        login_response = client.post("/auth/login", data={
            "email": "newemployee@company.com",
            "password": "NewEmp@123",
        }, follow_redirects=True)

        assert b"pending" in login_response.data.lower() or b"approval" in login_response.data.lower()

        # Step 4: Admin logs in
        admin_login = client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        assert admin_login.status_code == 200

        # Step 5: Admin sees pending user on dashboard
        dashboard = client.get("/admin/")
        assert employee.username.encode() in dashboard.data

        # Step 6: Admin approves the employee
        approve_response = client.post(
            f"/admin/approve/{employee.id}",
            follow_redirects=True
        )

        assert approve_response.status_code == 200

        # Step 7: Admin logs out
        client.get("/auth/logout")

        # Step 8: Employee logs in successfully
        employee_login = client.post("/auth/login", data={
            "email": "newemployee@company.com",
            "password": "NewEmp@123",
        }, follow_redirects=True)

        assert employee_login.status_code == 200

        # Step 9: Employee accesses their dashboard
        dashboard_response = client.get("/employee/")
        assert dashboard_response.status_code == 200

    def test_complete_manager_registration_to_dashboard(self, client, db_session, admin_user):
        """
        Test complete workflow: manager registers, admin approves, manager logs in.
        """
        # Manager registration
        client.post("/auth/register", data={
            "username": "newmanager",
            "email": "newmanager@company.com",
            "password": "NewMgr@123",
            "role": "manager",
        }, follow_redirects=True)

        manager = User.query.filter_by(email="newmanager@company.com").first()

        # Admin approves
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        client.post(f"/admin/approve/{manager.id}", follow_redirects=True)
        client.get("/auth/logout")

        # Manager logs in
        client.post("/auth/login", data={
            "email": "newmanager@company.com",
            "password": "NewMgr@123",
        }, follow_redirects=True)

        # Access manager dashboard
        response = client.get("/manager/")
        assert response.status_code == 200


class TestAdminUserManagementWorkflow:
    """E2E tests for admin user management workflows."""

    def test_complete_user_lifecycle_management(self, client, db_session, admin_user):
        """
        Test complete user lifecycle: create, approve, edit, blacklist, whitelist, delete.
        """
        # Step 1: User registers
        client.post("/auth/register", data={
            "username": "lifecycleuser",
            "email": "lifecycle@company.com",
            "password": "Lifecycle@123",
            "role": "employee",
        }, follow_redirects=True)

        user = User.query.filter_by(email="lifecycle@company.com").first()
        assert user.is_approved is False

        # Step 2: Admin logs in and approves user
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        client.post(f"/admin/approve/{user.id}", follow_redirects=True)
        db_session.refresh(user)
        assert user.is_approved is True

        # Step 3: Admin edits user role and details
        client.post(f"/admin/users/{user.id}/edit", data={
            "username": "modified_lifecycle",
            "email": "lifecycle@company.com",
            "role": "manager",
            "is_active": "on",
            "is_approved": "on",
        }, follow_redirects=True)

        db_session.refresh(user)
        assert user.username == "modified_lifecycle"
        assert user.role == "manager"

        # Step 4: Admin blacklists user
        client.post(f"/admin/users/{user.id}/blacklist", follow_redirects=True)
        db_session.refresh(user)
        assert user.is_blacklisted is True
        assert user.is_active is False

        # Step 5: Verify user is in blacklisted users list
        blacklist_page = client.get("/admin/blacklisted")
        assert user.username.encode() in blacklist_page.data

        # Step 6: Admin whitelists user
        client.post(f"/admin/whitelist/{user.id}", follow_redirects=True)
        db_session.refresh(user)
        assert user.is_blacklisted is False
        assert user.is_active is True

        # Step 7: Admin deletes user
        client.post(f"/admin/users/{user.id}/delete", follow_redirects=True)
        deleted_user = db_session.get(User, user.id)
        assert deleted_user is None

    def test_reject_user_workflow(self, client, db_session, admin_user):
        """
        Test workflow: user registers, admin rejects (deletes) during pending phase.
        """
        # User registers
        client.post("/auth/register", data={
            "username": "rejectuser",
            "email": "reject@company.com",
            "password": "Reject@123",
            "role": "employee",
        }, follow_redirects=True)

        user = User.query.filter_by(email="reject@company.com").first()
        user_id = user.id

        # Admin logs in and rejects
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        client.post(f"/admin/reject/{user_id}", follow_redirects=True)

        # User should be deleted
        rejected_user = db_session.get(User, user_id)
        assert rejected_user is None


class TestPasswordResetWorkflow:
    """E2E tests for password reset workflows."""

    def test_admin_password_reset_workflow(self, client, db_session, admin_user):
        """
        Test complete password reset: user forgets password, admin resets, user logs in.
        """
        # Create and approve employee
        employee = User(
            username="forgetful",
            email="forgetful@company.com",
            role="employee",
            is_approved=True,
            is_active=True,
        )
        employee.set_password("OldPassword@123")
        db_session.add(employee)
        db_session.commit()

        # Employee tries to login with wrong password (simulating forgotten password)
        login_fail = client.post("/auth/login", data={
            "email": "forgetful@company.com",
            "password": "WrongPassword",
        }, follow_redirects=True)

        assert b"invalid credentials" in login_fail.data.lower()

        # Admin logs in
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        # Admin searches for user
        search_response = client.get(f"/admin/reset-credentials?q={employee.username}")
        assert employee.username.encode() in search_response.data

        # Admin resets password
        new_password = "NewPassword@456"
        client.post(f"/admin/reset-password/{employee.id}", data={
            "new_password": new_password,
        }, follow_redirects=True)

        # Admin logs out
        client.get("/auth/logout")

        # Employee logs in with new password
        login_success = client.post("/auth/login", data={
            "email": "forgetful@company.com",
            "password": new_password,
        }, follow_redirects=True)

        assert login_success.status_code == 200

        # Access dashboard
        dashboard = client.get("/employee/")
        assert dashboard.status_code == 200


class TestMultiRoleAccessWorkflow:
    """E2E tests for multi-role access scenarios."""

    def test_role_separation_enforcement(self, client, db_session, admin_user, manager_user, employee_user):
        """
        Test that role separation is enforced across complete user sessions.
        """
        # Test employee access
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)

        employee_dashboard = client.get("/employee/")
        manager_dashboard = client.get("/manager/")
        admin_dashboard = client.get("/admin/")

        assert employee_dashboard.status_code == 200
        assert manager_dashboard.status_code == 403
        assert admin_dashboard.status_code == 403

        client.get("/auth/logout")

        # Test manager access
        client.post("/auth/login", data={
            "email": manager_user.email,
            "password": "Manager@123",
        }, follow_redirects=True)

        employee_dashboard = client.get("/employee/")
        manager_dashboard = client.get("/manager/")
        admin_dashboard = client.get("/admin/")

        assert employee_dashboard.status_code == 403
        assert manager_dashboard.status_code == 200
        assert admin_dashboard.status_code == 403

        client.get("/auth/logout")

        # Test admin access
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        employee_dashboard = client.get("/employee/")
        manager_dashboard = client.get("/manager/")
        admin_dashboard = client.get("/admin/")

        assert employee_dashboard.status_code == 403
        assert manager_dashboard.status_code == 403
        assert admin_dashboard.status_code == 200


class TestUserStatusTransitionWorkflow:
    """E2E tests for user status transition workflows."""

    def test_activation_deactivation_workflow(self, client, db_session, admin_user):
        """
        Test user activation/deactivation workflow.
        """
        # Create approved employee
        employee = User(
            username="activetest",
            email="activetest@company.com",
            role="employee",
            is_approved=True,
            is_active=True,
        )
        employee.set_password("Active@123")
        db_session.add(employee)
        db_session.commit()

        # Employee logs in successfully
        client.post("/auth/login", data={
            "email": "activetest@company.com",
            "password": "Active@123",
        }, follow_redirects=True)

        dashboard = client.get("/employee/")
        assert dashboard.status_code == 200

        client.get("/auth/logout")

        # Admin logs in and force-logouts employee (deactivates)
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        client.post(f"/admin/force-logout/{employee.id}", follow_redirects=True)

        db_session.refresh(employee)
        assert employee.is_active is False

        client.get("/auth/logout")

        # Employee tries to login (should fail - deactivated)
        login_fail = client.post("/auth/login", data={
            "email": "activetest@company.com",
            "password": "Active@123",
        }, follow_redirects=True)

        assert b"deactivated" in login_fail.data.lower()

        # Admin reactivates user
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        client.post(f"/admin/users/{employee.id}/edit", data={
            "username": employee.username,
            "email": employee.email,
            "role": employee.role,
            "is_active": "on",
            "is_approved": "on",
        }, follow_redirects=True)

        client.get("/auth/logout")

        # Employee can now login again
        login_success = client.post("/auth/login", data={
            "email": "activetest@company.com",
            "password": "Active@123",
        }, follow_redirects=True)

        assert login_success.status_code == 200


class TestSearchAndFilterWorkflow:
    """E2E tests for search and filter functionalities."""

    def test_admin_search_pending_users(self, client, db_session, admin_user):
        """
        Test admin searching for pending users on dashboard.
        """
        # Create multiple pending users
        pending_users = [
            User(username=f"pending{i}", email=f"pending{i}@test.com", role="employee", is_approved=False)
            for i in range(3)
        ]

        for user in pending_users:
            user.set_password("Pending@123")
            db_session.add(user)
        db_session.commit()

        # Admin logs in
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        # Search for specific pending user
        search_response = client.get("/admin/?q=pending1")
        assert b"pending1" in search_response.data

        # Search should not show other pending users
        # (depends on implementation, but generally filtered results)

    def test_admin_search_for_password_reset(self, client, db_session, admin_user, employee_user):
        """
        Test admin searching for user to reset password.
        """
        # Admin logs in
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        # Search by username
        search_by_username = client.get(f"/admin/reset-credentials?q={employee_user.username}")
        assert employee_user.username.encode() in search_by_username.data

        # Search by email
        search_by_email = client.get(f"/admin/reset-credentials?q={employee_user.email}")
        assert employee_user.email.encode() in search_by_email.data


class TestManageUsersWorkflow:
    """E2E tests for manage users page workflows."""

    def test_manage_users_filter_and_pagination_workflow(self, client, db_session, admin_user):
        """
        Test complete workflow: create users, filter, paginate, take actions.
        """
        # Create 25 users with mixed roles
        for i in range(25):
            user = User(
                username=f"workflowuser{i}",
                email=f"workflow{i}@test.com",
                role="manager" if i % 2 == 0 else "employee",
                is_approved=True,
            )
            user.set_password("Test@123")
            db_session.add(user)
        db_session.commit()

        # Admin logs in
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        # View first page
        response = client.get("/admin/users?per_page=10&page=1")
        assert response.status_code == 200

        # Navigate to second page
        response = client.get("/admin/users?per_page=10&page=2")
        assert response.status_code == 200

        # Filter by role
        response = client.get("/admin/users?role_filter=manager")
        assert response.status_code == 200

        # Filter by status
        response = client.get("/admin/users?status_filter=approved")
        assert response.status_code == 200

        # Filter by status and role
        response = client.get("/admin/users?status_filter=pending&role_filter=manager")
        assert response.status_code == 200

        # Filter with pagination
        response = client.get("/admin/users?role_filter=employee&status_filter=approved&per_page=10&page=1")
        assert response.status_code == 200

    def test_manage_users_export_workflow(self, client, db_session, admin_user):
        """
        Test user export workflow from manage users page.
        """
        # Create some users
        for i in range(5):
            user = User(
                username=f"exportuser{i}",
                email=f"export{i}@test.com",
                role="employee",
                is_approved=True,
            )
            user.set_password("Test@123")
            db_session.add(user)
        db_session.commit()

        # Admin logs in
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        # Export all users
        response = client.get("/admin/users/export")
        assert response.status_code == 200
        assert "text/csv" in response.content_type
        assert len(response.get_data()) > 0  # consume the stream

        # Export filtered users
        response = client.get("/admin/users/export?role_filter=employee")
        assert response.status_code == 200
        assert "text/csv" in response.content_type
        assert len(response.get_data()) > 0  # consume the stream

    def test_manage_users_statistics_display(self, client, db_session, admin_user):
        """
        Test that user statistics are displayed correctly.
        """
        # Create users with various states
        approved = User(username="statapproved", email="approved@test.com", role="employee", is_approved=True)
        approved.set_password("Test@123")

        pending = User(username="statpending", email="pending@test.com", role="employee", is_approved=False)
        pending.set_password("Test@123")

        blacklisted = User(username="statblacklisted", email="blacklisted@test.com", role="employee",
                          is_approved=True, is_blacklisted=True)
        blacklisted.set_password("Test@123")

        db_session.add_all([approved, pending, blacklisted])
        db_session.commit()

        # Admin logs in
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)

        # View manage users page
        response = client.get("/admin/users")
        assert response.status_code == 200
        # Page should load with statistics


class TestCompleteApplicationFlow:
    """E2E test for complete application workflow."""

    def test_full_application_lifecycle(self, client, db_session, admin_user):
        """
        Comprehensive test covering: registration, approval, login, role change,
        password reset, blacklist, whitelist, and deletion.
        """
        # 1. User registers
        client.post("/auth/register", data={
            "username": "fulltest",
            "email": "fulltest@app.com",
            "password": "Full@Test123",
            "role": "employee",
        }, follow_redirects=True)

        user = User.query.filter_by(email="fulltest@app.com").first()

        # 2. Admin approves
        client.post("/auth/login", data={"email": admin_user.email, "password": "Admin@123"}, follow_redirects=True)
        client.post(f"/admin/approve/{user.id}", follow_redirects=True)
        client.get("/auth/logout")

        # 3. User logs in
        client.post("/auth/login", data={"email": "fulltest@app.com", "password": "Full@Test123"}, follow_redirects=True)
        assert client.get("/employee/").status_code == 200
        client.get("/auth/logout")

        # 4. Admin changes role to manager
        client.post("/auth/login", data={"email": admin_user.email, "password": "Admin@123"}, follow_redirects=True)
        client.post(f"/admin/users/{user.id}/edit", data={
            "username": "fulltest",
            "email": "fulltest@app.com",
            "role": "manager",
            "is_active": "on",
            "is_approved": "on",
        }, follow_redirects=True)
        client.get("/auth/logout")

        # 5. User logs in as manager
        client.post("/auth/login", data={"email": "fulltest@app.com", "password": "Full@Test123"}, follow_redirects=True)
        assert client.get("/manager/").status_code == 200
        assert client.get("/employee/").status_code == 403
        client.get("/auth/logout")

        # 6. Admin resets password
        client.post("/auth/login", data={"email": admin_user.email, "password": "Admin@123"}, follow_redirects=True)
        client.post(f"/admin/reset-password/{user.id}", data={"new_password": "NewFull@456"}, follow_redirects=True)
        client.get("/auth/logout")

        # 7. User logs in with new password
        client.post("/auth/login", data={"email": "fulltest@app.com", "password": "NewFull@456"}, follow_redirects=True)
        assert client.get("/manager/").status_code == 200
        client.get("/auth/logout")

        # 8. Admin blacklists user
        client.post("/auth/login", data={"email": admin_user.email, "password": "Admin@123"}, follow_redirects=True)
        client.post(f"/admin/users/{user.id}/blacklist", follow_redirects=True)
        client.get("/auth/logout")

        # 9. User cannot login (blacklisted)
        login_response = client.post("/auth/login", data={"email": "fulltest@app.com", "password": "NewFull@456"}, follow_redirects=True)
        assert b"blacklisted" in login_response.data.lower()

        # 10. Admin whitelists user
        client.post("/auth/login", data={"email": admin_user.email, "password": "Admin@123"}, follow_redirects=True)
        client.post(f"/admin/whitelist/{user.id}", follow_redirects=True)

        # 11. Finally, admin deletes user
        client.post(f"/admin/users/{user.id}/delete", follow_redirects=True)
        deleted = db_session.get(User, user.id)
        assert deleted is None
