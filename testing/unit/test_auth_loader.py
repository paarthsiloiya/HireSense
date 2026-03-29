"""
Tests for load_user function and authentication utilities.
"""

import pytest
from app import db
from app.models import User, load_user


class TestLoginManager:
    """Tests for Flask-Login integration."""

    def test_load_user_existing(self, db_session, app):
        """Test loading an existing user by ID."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com", role="employee")
            user.set_password("Test@123")
            db_session.add(user)
            db_session.commit()
            user_id = user.id
            
        
        with app.app_context():
            loaded_user = load_user(str(user_id))
            assert loaded_user is not None
            assert loaded_user.id == user_id

    def test_load_user_nonexistent(self, db_session, app):
        """Test loading a nonexistent user."""
        with app.app_context():
            loaded_user = load_user("99999")
            assert loaded_user is None
