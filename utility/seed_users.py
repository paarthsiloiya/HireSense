"""
User seeding utility for HireSense.

This script provides a Flask CLI command to generate fake users for testing
and development purposes. It uses the Faker library to create realistic
user data with various roles and approval statuses.

Usage:
    flask seed-users          # Seeds 30 users (default)
    flask seed-users 50       # Seeds 50 users
    flask seed-users --help   # Show help

Example:
    $ flask seed-users
    Seeding 30 users...
    Successfully added 30 fake users.
"""

import click
import random
from flask.cli import with_appcontext


@click.command("seed-users")
@click.argument("number", default=30, type=int)
@click.option("--approved/--pending", default=True, help="Create approved or pending users")
@click.option("--role", type=click.Choice(["manager", "employee", "mixed"]), default="mixed", help="Role for seeded users")
@with_appcontext
def seed_users(number: int, approved: bool, role: str):
    """
    Seed the database with fake users for testing.

    NUMBER: The number of users to create (default: 30)
    """
    from faker import Faker
    from app import db
    from app.models import User

    fake = Faker()
    roles = ["manager", "employee"] if role == "mixed" else [role]

    click.echo(f"Seeding {number} users...")

    created = 0
    skipped = 0

    for _ in range(number):
        username = fake.user_name()
        email = fake.unique.email()
        user_role = random.choice(roles)
        is_approved = approved if approved else random.choice([True, False])

        # Check for existing email
        if User.query.filter_by(email=email).first():
            skipped += 1
            continue

        user = User(
            username=username,
            email=email,
            role=user_role,
            is_approved=is_approved,
            is_active=True,
        )
        user.set_password("password123")

        db.session.add(user)
        created += 1

    try:
        db.session.commit()
        click.echo(click.style(f"Successfully added {created} fake users.", fg="green"))
    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"Error: {str(e)}", fg="red"))
        return
    if skipped:
        click.echo(click.style(f"Skipped {skipped} users (duplicate emails).", fg="yellow"))

    # Show summary
    click.echo("\nUser Summary:")
    click.echo(f"  - Total users in DB: {User.query.count()}")
    click.echo(f"  - Approved: {User.query.filter_by(is_approved=True).count()}")
    click.echo(f"  - Pending: {User.query.filter_by(is_approved=False).count()}")
    click.echo(f"  - Managers: {User.query.filter_by(role='manager').count()}")
    click.echo(f"  - Employees: {User.query.filter_by(role='employee').count()}")
