"""
Pytest configuration and shared fixtures for HireSense testing suite.

This module provides reusable fixtures for database setup, test clients,
and authenticated user sessions across all test modules.
"""

import os
import sys
import pytest
from flask import Flask
from flask.testing import FlaskClient
from typing import Generator
from sqlalchemy import event
from sqlalchemy.engine import Engine


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["ADMIN_PASSWORD"] = "TestAdmin@123"
os.environ["FLASK_DEBUG"] = "false"

from app import create_app, db
from app.models import User, Notification, Department, Skill, Project, ProjectSkill, ProjectAssignment, UserSkill, Resume, LearningPath



@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite connections."""
    if hasattr(dbapi_conn, 'execute'):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture(scope="session")
def app() -> Generator[Flask, None, None]:
    """
    Create and configure a Flask application instance for testing.
    Uses in-memory SQLite database to avoid affecting production data.

    Yields:
        Flask: Configured Flask application instance.
    """
    test_app = create_app(port=5010)
    test_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": False,
    })

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def client(app: Flask) -> Generator[FlaskClient, None, None]:
    """
    Provide a test client for making HTTP requests.

    Args:
        app: Flask application fixture.

    Yields:
        FlaskClient: Test client for the application.
    """
    return app.test_client()


@pytest.fixture(scope="function")
def db_session(app: Flask) -> Generator:
    """
    Provide a clean database session for each test.
    Automatically rolls back changes after each test.

    Args:
        app: Flask application fixture.

    Yields:
        SQLAlchemy session object.
    """
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.session.remove()
        
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture(scope="function")
def admin_user(db_session) -> User:
    """
    Create and return an admin user for testing.

    Args:
        db_session: Database session fixture.

    Returns:
        User: Admin user instance.
    """
    user = User(
        username="admin",
        email="admin@hiresense.test",
        role="admin",
        is_approved=True,
        is_active=True,
    )
    user.set_password("Admin@123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def manager_user(db_session) -> User:
    """
    Create and return a manager user for testing.

    Args:
        db_session: Database session fixture.

    Returns:
        User: Manager user instance.
    """
    user = User(
        username="manager",
        email="manager@hiresense.test",
        role="manager",
        is_approved=True,
        is_active=True,
    )
    user.set_password("Manager@123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def employee_user(db_session) -> User:
    """
    Create and return an employee user for testing.

    Args:
        db_session: Database session fixture.

    Returns:
        User: Employee user instance.
    """
    user = User(
        username="employee",
        email="employee@hiresense.test",
        role="employee",
        is_approved=True,
        is_active=True,
    )
    user.set_password("Employee@123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def pending_user(db_session) -> User:
    """
    Create and return a pending (unapproved) user for testing.

    Args:
        db_session: Database session fixture.

    Returns:
        User: Pending user instance.
    """
    user = User(
        username="pending",
        email="pending@hiresense.test",
        role="employee",
        is_approved=False,
        is_active=True,
    )
    user.set_password("Pending@123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def blacklisted_user(db_session) -> User:
    """
    Create and return a blacklisted user for testing.

    Args:
        db_session: Database session fixture.

    Returns:
        User: Blacklisted user instance.
    """
    user = User(
        username="blacklisted",
        email="blacklisted@hiresense.test",
        role="employee",
        is_approved=True,
        is_active=False,
        is_blacklisted=True,
    )
    user.set_password("Blacklisted@123")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture(scope="function")
def authenticated_admin_client(client: FlaskClient, admin_user: User) -> FlaskClient:
    """
    Provide a test client with an authenticated admin session.

    Args:
        client: Test client fixture.
        admin_user: Admin user fixture.

    Returns:
        FlaskClient: Authenticated test client.
    """
    with client:
        client.post("/auth/login", data={
            "email": admin_user.email,
            "password": "Admin@123",
        }, follow_redirects=True)
        yield client


@pytest.fixture(scope="function")
def authenticated_manager_client(client: FlaskClient, manager_user: User) -> FlaskClient:
    """
    Provide a test client with an authenticated manager session.

    Args:
        client: Test client fixture.
        manager_user: Manager user fixture.

    Returns:
        FlaskClient: Authenticated test client.
    """
    with client:
        client.post("/auth/login", data={
            "email": manager_user.email,
            "password": "Manager@123",
        }, follow_redirects=True)
        yield client


@pytest.fixture(scope="function")
def authenticated_employee_client(client: FlaskClient, employee_user: User) -> FlaskClient:
    """
    Provide a test client with an authenticated employee session.

    Args:
        client: Test client fixture.
        employee_user: Employee user fixture.

    Returns:
        FlaskClient: Authenticated test client.
    """
    with client:
        client.post("/auth/login", data={
            "email": employee_user.email,
            "password": "Employee@123",
        }, follow_redirects=True)
        yield client


@pytest.fixture(scope="function")
def sample_notification(db_session, admin_user: User) -> Notification:
    """
    Create and return a sample notification for testing.

    Args:
        db_session: Database session fixture.
        admin_user: Admin user fixture.

    Returns:
        Notification: Sample notification instance.
    """
    notification = Notification(
        user_id=admin_user.id,
        message="Test notification message",
        type="info",
        is_read=False,
    )
    db_session.add(notification)
    db_session.commit()
    return notification






@pytest.fixture(scope="function")
def department(db_session) -> Department:
    """Create a sample department for testing."""
    dept = Department(name="Engineering")
    db_session.add(dept)
    db_session.commit()
    return dept


@pytest.fixture(scope="function")
def skills(db_session) -> list:
    """Create sample skills for testing."""
    skill_data = [
        ("Python", "technical"),
        ("JavaScript", "technical"),
        ("SQL", "technical"),
        ("Docker", "technical"),
        ("AWS", "technical"),
        ("Git", "technical"),
        ("Communication", "soft"),
        ("Project Management", "soft"),
    ]
    skills = []
    for name, category in skill_data:
        skill = Skill(name=name, category=category)
        db_session.add(skill)
        skills.append(skill)
    db_session.commit()
    return skills


@pytest.fixture(scope="function")
def project(db_session, manager_user: User) -> Project:
    """Create a sample project for testing."""
    proj = Project(
        title="Test Project",
        description="A test project for unit testing",
        status="active",
        manager_id=manager_user.id,
    )
    db_session.add(proj)
    db_session.commit()
    return proj


@pytest.fixture(scope="function")
def project_with_skills(db_session, project: Project, skills: list) -> Project:
    """Create a project with skill requirements."""
    
    ps1 = ProjectSkill(
        project_id=project.id,
        skill_id=skills[0].id,  
        is_mandatory=True,
        minimum_proficiency=3,
    )
    ps2 = ProjectSkill(
        project_id=project.id,
        skill_id=skills[1].id,  
        is_mandatory=False,
        minimum_proficiency=2,
    )
    db_session.add_all([ps1, ps2])
    db_session.commit()
    return project


@pytest.fixture(scope="function")
def employee_with_skills(db_session, employee_user: User, skills: list) -> User:
    """Create an employee with skills."""
    
    us1 = UserSkill(
        user_id=employee_user.id,
        skill_id=skills[0].id,  
        proficiency_level=4,
        is_verified=True,
    )
    us2 = UserSkill(
        user_id=employee_user.id,
        skill_id=skills[2].id,  
        proficiency_level=3,
        is_verified=False,
    )
    db_session.add_all([us1, us2])
    db_session.commit()
    return employee_user


@pytest.fixture(scope="function")
def assignment(db_session, project: Project, employee_user: User) -> ProjectAssignment:
    """Create a project assignment for testing."""
    assign = ProjectAssignment(
        project_id=project.id,
        user_id=employee_user.id,
        role_in_project="Developer",
        status="active",
    )
    db_session.add(assign)
    db_session.commit()
    return assign


@pytest.fixture(scope="function")
def learning_path(db_session, employee_user: User) -> LearningPath:
    """Create a learning path for testing."""
    import json
    content = {
        "target_role": "senior_developer",
        "target_role_title": "Senior Developer",
        "readiness_score": 60,
        "recommendations": [
            {"skill_name": "Docker", "priority": "high", "current_level": 0, "target_level": 3}
        ],
    }
    path = LearningPath(
        user_id=employee_user.id,
        target_role="senior_developer",
        generated_content=json.dumps(content),
        status="active",
    )
    db_session.add(path)
    db_session.commit()
    return path
