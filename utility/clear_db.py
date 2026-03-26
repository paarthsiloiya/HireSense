"""
Utility script to clear database tables for HireSense.

Provides a safe way to clear all data while preserving the admin user.
"""

import click
from flask.cli import with_appcontext


@click.command("clear-db")
@click.option("--confirm", is_flag=True, help="Confirm database clearing (required)")
@with_appcontext
def clear_db(confirm: bool):
    """Clear all database tables (preserves admin user).

    Usage:
        flask clear-db --confirm

    WARNING: This will delete ALL data except the admin user.
    """
    from app import db
    from app.models import (
        User, Department, Skill, Project, ProjectSkill,
        ProjectAssignment, UserSkill, Resume, LearningPath, Notification
    )

    # Safety check
    if not confirm:
        click.echo(click.style("WARNING: This will delete ALL data from the database!", fg="red", bold=True))
        click.echo("   Preserved: admin@hiresense.local")
        click.echo("\nTo proceed, run: ", nl=False)
        click.echo(click.style("flask clear-db --confirm", fg="yellow", bold=True))
        return

    # Deletion order (respects foreign keys)
    deletion_order = [
        ("Notifications", Notification),
        ("Project Assignments", ProjectAssignment),
        ("Project Skills", ProjectSkill),
        ("User Skills", UserSkill),
        ("Learning Paths", LearningPath),
        ("Resumes", Resume),
        ("Projects", Project),
        ("Users (except admin)", User),
        ("Skills", Skill),
        ("Departments", Department),
    ]

    click.echo("\n" + click.style("Clearing database...", fg="cyan", bold=True))
    click.echo()

    try:
        for name, model in deletion_order:
            if model == User:
                # Special handling: preserve admin
                count = model.query.filter(
                    model.email != "admin@hiresense.local"
                ).delete(synchronize_session='fetch')
            else:
                count = model.query.delete(synchronize_session='fetch')

            click.echo(f"  ✓ {name}: ", nl=False)
            click.echo(click.style(f"{count} deleted", fg="yellow"))

        db.session.commit()

        click.echo()
        click.echo(click.style("Database cleared successfully!", fg="green", bold=True))

        # Show preserved items
        admin = User.query.filter_by(email="admin@hiresense.local").first()
        click.echo("\n" + click.style("Preserved:", fg="cyan"))
        click.echo(f"  - Admin user: {admin.email if admin else 'NOT FOUND'}")

        # Current state
        click.echo("\n" + click.style("Current Database State:", fg="cyan"))
        click.echo(f"  - Users: {User.query.count()}")
        click.echo(f"  - Projects: {Project.query.count()}")
        click.echo(f"  - Skills: {Skill.query.count()}")
        click.echo(f"  - Departments: {Department.query.count()}")

    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"\n❌ Error clearing database: {str(e)}", fg="red"))
        return
