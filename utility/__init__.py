"""
HireSense Utility Package

This package contains utility scripts and CLI commands for managing the
HireSense application, including database seeding, maintenance tasks,
and development helpers.

Available commands:
    - seed-users: Generate fake users for testing
    - seed-data: Seed departments, skills, and projects
    - seed-projects: Generate projects with skills and assignments
    - clear-db: Clear all database tables (with safety checks)
"""

from .seed_users import seed_users, seed_data
from .seed_projects import seed_projects
from .clear_db import clear_db

__all__ = ["seed_users", "seed_data", "seed_projects", "clear_db"]
