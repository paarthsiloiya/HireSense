"""
Project seeding utility for HireSense.

This script provides a Flask CLI command to generate realistic projects
with skill requirements and employee assignments for testing and development.

Usage:
    flask seed-projects             # Seeds 20 projects (default)
    flask seed-projects --count 50  # Seeds 50 projects
    flask seed-projects --help      # Show help

Example:
    $ flask seed-projects --count 10
    Seeding 10 projects...
    ✓ Created project: "Customer Platform" (Manager: john_doe, 5 skills, 4 employees)
    Successfully created 10 projects!
"""

import click
import random
from datetime import date, timedelta
from flask.cli import with_appcontext


@click.command("seed-projects")
@click.option("--count", default=20, type=int, help="Number of projects to create")
@with_appcontext
def seed_projects(count: int):
    """Generate projects with skills and employee assignments.

    Generates realistic projects with:
    - Valid manager assignments (required)
    - 3-8 random skill requirements per project
    - 2-6 employee assignments per project
    - Realistic dates, status distribution, and roles

    COUNT: Number of projects to create (default: 20)
    """
    from faker import Faker
    from app import db
    from app.models import User, Skill, Project, ProjectSkill, ProjectAssignment

    fake = Faker()

    # Validation: Check count
    if count <= 0:
        click.echo(click.style("❌ Error: Count must be positive", fg="red"))
        return

    # Validation: Check if managers exist
    managers = User.query.filter_by(role='manager', is_approved=True, is_active=True).all()
    if not managers:
        click.echo(click.style("❌ Error: No managers found in database.", fg="red"))
        click.echo("   Run 'flask seed-users --role manager' first.")
        return

    # Validation: Check if skills exist
    skills = Skill.query.all()
    if not skills:
        click.echo(click.style("❌ Error: No skills found in database.", fg="red"))
        click.echo("   Run 'flask seed-data' first.")
        return

    # Validation: Check if employees exist
    employees = User.query.filter_by(role='employee', is_approved=True, is_active=True).all()
    if not employees:
        click.echo(click.style("❌ Error: No employees found in database.", fg="red"))
        click.echo("   Run 'flask seed-users --role employee' first.")
        return

    click.echo(f"\n{click.style('Seeding ' + str(count) + ' projects...', fg='cyan', bold=True)}")
    click.echo()

    # Project title templates for variety
    title_templates = [
        lambda: f"{fake.bs().title()} Platform",
        lambda: f"{fake.catch_phrase()} System",
        lambda: f"{random.choice(['Customer', 'Enterprise', 'Mobile', 'Cloud'])} {random.choice(['Portal', 'Platform', 'Solution', 'Application'])}",
        lambda: f"{random.choice(['AI', 'ML', 'Data', 'Security'])} {random.choice(['Pipeline', 'Framework', 'Infrastructure', 'Service'])}",
        lambda: f"{fake.company()} {random.choice(['Integration', 'Migration', 'Upgrade', 'Redesign'])}",
    ]

    # Role templates for assignments
    role_templates = [
        "Lead Developer",
        "Senior Developer",
        "Developer",
        "Analyst",
        "Tester",
        "Quality Assurance Engineer",
        "Technical Lead",
        "System Architect",
    ]

    projects_created = 0
    total_skills = 0
    total_assignments = 0

    for i in range(count):
        try:
            # Generate project data
            title = random.choice(title_templates)()
            description = fake.paragraph(nb_sentences=3)

            # Weighted status distribution
            status = random.choices(
                ['active', 'planning', 'completed', 'on hold'],
                weights=[60, 20, 15, 5],
                k=1
            )[0]

            # Generate realistic dates
            start_date = fake.date_between(start_date='-6m', end_date='today')
            duration_days = random.randint(90, 365)
            end_date = start_date + timedelta(days=duration_days)

            # Random manager
            manager = random.choice(managers)

            # Create project
            project = Project(
                title=title,
                description=description,
                status=status,
                manager_id=manager.id,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(project)
            db.session.flush()  # Get project.id before adding related records

            # Add skill requirements (3-8 skills per project)
            num_skills = random.randint(3, 8)
            selected_skills = random.sample(skills, min(num_skills, len(skills)))

            project_skills_count = 0
            for skill in selected_skills:
                # Weighted proficiency (bell curve centered at 3)
                min_proficiency = random.choices(
                    [1, 2, 3, 4, 5],
                    weights=[10, 20, 40, 20, 10],
                    k=1
                )[0]

                # 70% mandatory, 30% optional
                is_mandatory = random.random() < 0.7

                project_skill = ProjectSkill(
                    project_id=project.id,
                    skill_id=skill.id,
                    is_mandatory=is_mandatory,
                    minimum_proficiency=min_proficiency
                )
                db.session.add(project_skill)
                project_skills_count += 1

            total_skills += project_skills_count

            # Add employee assignments (2-6 employees per project)
            num_employees = random.randint(2, min(6, len(employees)))
            selected_employees = random.sample(employees, num_employees)

            project_assignments_count = 0
            for employee in selected_employees:
                # Random role
                role_in_project = random.choice(role_templates)

                # Status matches project status
                if status == 'active':
                    assignment_status = 'active'
                elif status == 'completed':
                    assignment_status = 'completed'
                elif status == 'on hold':
                    assignment_status = random.choice(['active', 'removed'])
                else:  # planning
                    assignment_status = 'active'

                # Allotted date between project start and today
                if start_date > date.today():
                    allotted_date = start_date
                else:
                    allotted_date = fake.date_between(
                        start_date=start_date,
                        end_date=min(date.today(), end_date)
                    )

                assignment = ProjectAssignment(
                    project_id=project.id,
                    user_id=employee.id,
                    role_in_project=role_in_project,
                    status=assignment_status,
                    allotted_date=allotted_date
                )
                db.session.add(assignment)
                project_assignments_count += 1

            total_assignments += project_assignments_count

            db.session.commit()
            projects_created += 1

            # Show progress
            click.echo(
                f"  {click.style('✓', fg='green')} Created project: "
                f"{click.style(title, fg='cyan')} "
                f"(Manager: {manager.username}, {project_skills_count} skills, {project_assignments_count} employees)"
            )

        except Exception as e:
            db.session.rollback()
            click.echo(click.style(f"  ✗ Error creating project {i+1}: {str(e)}", fg="red"))
            continue

    # Summary statistics
    click.echo()
    click.echo(click.style(f"✅ Successfully created {projects_created} projects!", fg="green", bold=True))

    click.echo("\n" + click.style("Project Summary:", fg="cyan", bold=True))
    click.echo(f"  - Total projects in DB: {Project.query.count()}")
    click.echo(f"  - Active: {Project.query.filter_by(status='active').count()}")
    click.echo(f"  - Planning: {Project.query.filter_by(status='planning').count()}")
    click.echo(f"  - Completed: {Project.query.filter_by(status='completed').count()}")
    click.echo(f"  - On Hold: {Project.query.filter_by(status='on hold').count()}")
    click.echo(f"  - Total skill requirements: {ProjectSkill.query.count()}")
    click.echo(f"  - Total assignments: {ProjectAssignment.query.count()}")
