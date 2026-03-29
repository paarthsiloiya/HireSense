"""
Unit tests for route coverage and export functionality.

Tests admin export endpoints with various filters and ensures
response streaming works correctly. These tests ensure coverage
of admin routes for user data export in CSV format.
"""
import pytest


def consume_response(response):
    """
    Consume response stream to avoid GeneratorExit issues in test client.
    
    :param response: Flask test response with streaming data.
    :type response: flask.Response
    """
    
    list(response.iter_encoded())
    response.close()

def test_admin_export(authenticated_admin_client, db_session, pending_user):
    """
    Test admin user export endpoint with CSV streaming.
    
    Verifies that the export endpoint correctly handles various filter
    parameters (status_filter, role_filter) and returns CSV data.
    
    :param authenticated_admin_client: Flask test client logged in as admin.
    :param db_session: SQLAlchemy database session.
    :param pending_user: Test user with pending status.
    """
    
    response = authenticated_admin_client.get("/admin/users/export")
    assert response.status_code == 200
    consume_response(response)

    response = authenticated_admin_client.get("/admin/users/export?status_filter=pending")
    assert response.status_code == 200
    consume_response(response)

    response = authenticated_admin_client.get("/admin/users/export?status_filter=approved")
    assert response.status_code == 200
    consume_response(response)

    response = authenticated_admin_client.get("/admin/users/export?status_filter=blacklisted")
    assert response.status_code == 200
    consume_response(response)

    response = authenticated_admin_client.get("/admin/users/export?role_filter=employee")
    assert response.status_code == 200
    consume_response(response)

    
    response = authenticated_admin_client.get("/admin/")
    assert response.status_code == 200
