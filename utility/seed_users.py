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
from datetime import date, timedelta
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

        
        users = User.query.filter(User.email !=  "admin@hiresense.local").all()

    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"Error: {str(e)}", fg="red"))
        return
    if skipped:
        click.echo(click.style(f"Skipped {skipped} users (duplicate emails).", fg="yellow"))

    
    if role in ["employee", "mixed"]:
        from app.models import Skill, UserSkill

        click.echo("\n" + click.style("Seeding skills for employees...", fg="cyan", bold=True))
        employees = [u for u in users if u.role == "employee"]
        all_skills = Skill.query.all()

        if all_skills:
            try:
                skills_count = _seed_user_skills(employees, all_skills)
                db.session.commit()

                click.echo(click.style(f"✓ Successfully added {skills_count} user skills!", fg="green"))

                
                verified_count = UserSkill.query.filter_by(is_verified=True).count()
                avg_skills = skills_count / len(employees) if employees else 0

                click.echo("\n" + click.style("Skills Summary:", fg="cyan", bold=True))
                click.echo(f"  - Total user skills: {skills_count}")
                click.echo(f"  - Average skills per employee: {avg_skills:.1f}")
                click.echo(f"  - Verified skills: {verified_count} ({verified_count*100//skills_count if skills_count else 0}%)")
            except Exception as e:
                db.session.rollback()
                click.echo(click.style(f"⚠️  Error seeding skills: {str(e)}", fg="yellow"))
        else:
            click.echo(click.style("⚠️  No skills in database. Run 'flask seed-data' first.", fg="yellow"))

    
    click.echo("\n" + click.style("User Summary:", fg="cyan", bold=True))
    click.echo(f"  - Total users in DB: {User.query.count()}")
    click.echo(f"  - Approved: {User.query.filter_by(is_approved=True).count()}")
    click.echo(f"  - Pending: {User.query.filter_by(is_approved=False).count()}")
    click.echo(f"  - Managers: {User.query.filter_by(role='manager').count()}")
    click.echo(f"  - Employees: {User.query.filter_by(role='employee').count()}")


def _seed_user_skills(employees, skills):
    """Seed skills for employees with realistic proficiency levels."""
    from faker import Faker
    from app import db
    from app.models import UserSkill

    fake = Faker()

    if not skills:
        click.echo(click.style("⚠️  No skills found. Skipping user skills.", fg="yellow"))
        return 0

    user_skills_created = 0

    for employee in employees:
        
        num_skills = random.randint(3, 7)
        selected_skills = random.sample(skills, min(num_skills, len(skills)))

        for skill in selected_skills:
            
            proficiency = random.choices([1, 2, 3, 4, 5], weights=[10, 20, 40, 20, 10])[0]

            
            is_verified = random.random() < 0.3

            
            acquired_date = fake.date_between(
                start_date=date.today() - timedelta(days=730),
                end_date=date.today()
            )

            
            last_used_date = fake.date_between(
                start_date=max(acquired_date, date.today() - timedelta(days=180)),
                end_date=date.today()
            )

            user_skill = UserSkill(
                user_id=employee.id,
                skill_id=skill.id,
                proficiency_level=proficiency,
                is_verified=is_verified,
                acquired_date=acquired_date,
                last_used_date=last_used_date
            )
            db.session.add(user_skill)
            user_skills_created += 1

    return user_skills_created


@click.command("seed-data")
@click.option("--full", is_flag=True, help="Include user skills and project assignments")
@with_appcontext
def seed_data(full: bool):
    """
    Seed the database with departments, skills, and sample projects.

    This populates the system with test data for Manager and Employee features.
    """
    from app import db
    from app.models import Department, Skill, User, Project, ProjectSkill, UserSkill, ProjectAssignment

    click.echo("Seeding departments, skills, and projects...")

    
    departments_data = [
        "Engineering",
        "Quality Assurance",
        "Security",
        "Data Science",
        "DevOps",
        "Product Management",
    ]

    departments = {}
    for name in departments_data:
        existing = Department.query.filter_by(name=name).first()
        if not existing:
            dept = Department(name=name)
            db.session.add(dept)
            departments[name] = dept
            click.echo(f"  Created department: {name}")
        else:
            departments[name] = existing

    db.session.commit()
    click.echo(click.style(f"Departments: {Department.query.count()} total", fg="green"))

    
    skills_data = [
        ("Python", "technical"),
        ("JavaScript", "technical"),
        ("TypeScript", "technical"),
        ("SQL", "technical"),
        ("PostgreSQL", "technical"),
        ("Docker", "technical"),
        ("Kubernetes", "technical"),
        ("AWS", "technical"),
        ("Git", "technical"),
        ("Linux", "technical"),
        ("CI/CD", "technical"),
        ("Flask", "technical"),
        ("Django", "technical"),
        ("React", "technical"),
        ("Node.js", "technical"),
        ("Machine Learning", "technical"),
        ("Deep Learning", "technical"),
        ("NLP", "technical"),
        ("Statistics", "technical"),
        ("Data Visualization", "technical"),
        ("Testing", "technical"),
        ("Automation", "technical"),
        ("Selenium", "technical"),
        ("API Testing", "technical"),
        ("Performance Testing", "technical"),
        ("Cybersecurity", "technical"),
        ("Network Security", "technical"),
        ("Penetration Testing", "technical"),
        ("SIEM", "technical"),
        ("Compliance", "technical"),
        ("Terraform", "technical"),
        ("Ansible", "technical"),
        ("Monitoring", "technical"),
        ("System Design", "technical"),
        ("Communication", "soft"),
        ("Project Management", "soft"),
        ("Agile", "soft"),
        ("Mentoring", "soft"),
        ("Code Review", "soft"),
        ("Problem Solving", "soft"),
    ]

    skills = {}
    for name, category in skills_data:
        existing = Skill.query.filter_by(name=name).first()
        if not existing:
            skill = Skill(name=name, category=category)
            db.session.add(skill)
            skills[name] = skill
        else:
            skills[name] = existing

    db.session.commit()
    click.echo(click.style(f"Skills: {Skill.query.count()} total", fg="green"))

    
    employees_without_dept = User.query.filter(
        User.role.in_(["employee", "manager"]),
        User.department_id.is_(None)
    ).all()

    dept_list = list(departments.values())
    if dept_list and employees_without_dept:
        import random
        for user in employees_without_dept:
            user.department_id = random.choice(dept_list).id
        db.session.commit()
        click.echo(f"Assigned departments to {len(employees_without_dept)} users")

    
    managers = User.query.filter_by(role="manager", is_approved=True, is_active=True).all()
    if managers:
        projects_data = [
            ("API Platform Upgrade", "Modernize the API platform with new authentication", ["Python", "Flask", "Docker", "PostgreSQL"]),
            ("Mobile App Backend", "Backend services for mobile application", ["Python", "AWS", "PostgreSQL", "Git"]),
            ("Data Pipeline Project", "Build ETL pipelines for analytics", ["Python", "SQL", "AWS", "Docker"]),
            ("Security Audit System", "Automated security scanning and auditing", ["Python", "Cybersecurity", "Docker", "Linux"]),
            ("ML Model Deployment", "Deploy ML models to production", ["Python", "Machine Learning", "Docker", "AWS"]),
        ]

        import random
        for title, description, req_skills in projects_data:
            existing = Project.query.filter_by(title=title).first()
            if not existing:
                manager = random.choice(managers)
                project = Project(
                    title=title,
                    description=description,
                    status=random.choice(["planning", "active"]),
                    manager_id=manager.id,
                )
                db.session.add(project)
                db.session.flush()  

                
                for skill_name in req_skills:
                    if skill_name in skills:
                        ps = ProjectSkill(
                            project_id=project.id,
                            skill_id=skills[skill_name].id,
                            is_mandatory=random.choice([True, True, False]),
                            minimum_proficiency=random.randint(2, 4),
                        )
                        db.session.add(ps)
                click.echo(f"  Created project: {title} (Manager: {manager.username})")

        db.session.commit()
        click.echo(click.style(f"Projects: {Project.query.count()} total", fg="green"))

    if full:
        
        employees = User.query.filter_by(role="employee", is_approved=True, is_active=True).all()
        skill_list = list(skills.values())

        import random
        for employee in employees[:20]:  
            
            num_skills = random.randint(3, 7)
            chosen_skills = random.sample(skill_list, min(num_skills, len(skill_list)))

            for skill in chosen_skills:
                existing = UserSkill.query.filter_by(user_id=employee.id, skill_id=skill.id).first()
                if not existing:
                    us = UserSkill(
                        user_id=employee.id,
                        skill_id=skill.id,
                        proficiency_level=random.randint(1, 5),
                        is_verified=random.choice([True, False]),
                    )
                    db.session.add(us)

        db.session.commit()
        click.echo(click.style(f"User skills: {UserSkill.query.count()} total", fg="green"))

        
        projects = Project.query.filter_by(status="active").all()
        employees = User.query.filter_by(role="employee", is_approved=True, is_active=True).all()

        if projects and employees:
            for project in projects:
                
                num_assignments = min(random.randint(2, 4), len(employees))
                chosen_employees = random.sample(employees, num_assignments)

                for emp in chosen_employees:
                    existing = ProjectAssignment.query.filter_by(
                        project_id=project.id, user_id=emp.id
                    ).first()
                    if not existing:
                        pa = ProjectAssignment(
                            project_id=project.id,
                            user_id=emp.id,
                            role_in_project=random.choice(["Developer", "Lead", "Analyst", "Tester"]),
                            status="active",
                        )
                        db.session.add(pa)

            db.session.commit()
            click.echo(click.style(f"Project assignments: {ProjectAssignment.query.count()} total", fg="green"))

    click.echo(click.style("\nSeed data complete!", fg="green"))




@click.command("seed-manager-data")
@click.argument("manager_id", type=int)
@with_appcontext
def seed_manager_data(manager_id: int):
    """
    Seed specific projects, skills, and approved employees for a single manager.
    
    MANAGER_ID: The ID of the user (must have role='manager')
    """
    from faker import Faker
    from app import db
    from app.models import User, Project, Department, Skill, ProjectSkill, ProjectAssignment, UserSkill
    
    fake = Faker()
    
    
    manager = db.session.get(User, manager_id)
    if not manager or manager.role != "manager":
        click.echo(click.style(f"Error: User with ID {manager_id} not found or is not a manager.", fg="red"))
        return

    click.echo(f"Seeding data for Manager: {click.style(manager.username, bold=True)}")

    
    all_depts = Department.query.all()
    if not all_depts:
        click.echo("No departments found. Please run 'flask seed-data' first.")
        return
    
    all_skills = Skill.query.all()
    if not all_skills:
        click.echo("No skills found. Please run 'flask seed-data' first.")
        return

    
    manager.department_id = random.choice([d.id for d in all_depts])
    manager.job_title = "Senior Project Manager"
    manager.is_approved = True
    
    
    project_count = random.randint(2, 4)
    for _ in range(project_count):
        project = Project(
            title=fake.catch_phrase(),
            description=fake.paragraph(nb_sentences=3),
            status=random.choice(["planning", "active"]),
            manager_id=manager.id,
            start_date=fake.date_between(start_date="-1y", end_date="today"),
            end_date=fake.date_between(start_date="today", end_date="+1y")
        )
        db.session.add(project)
        db.session.flush() 

        
        sampled_skills = random.sample(all_skills, k=min(len(all_skills), random.randint(3, 5)))
        for s in sampled_skills:
            ps = ProjectSkill(
                project_id=project.id,
                skill_id=s.id,
                is_mandatory=random.choice([True, False]),
                minimum_proficiency=random.randint(2, 4)
            )
            db.session.add(ps)

        
        emp_count = random.randint(3, 5)
        for _ in range(emp_count):
            employee = User(
                username=fake.user_name(),
                email=fake.unique.email(),
                role="employee",
                is_active=True,
                is_approved=True, 
                department_id=manager.department_id,
                job_title=fake.job()
            )
            employee.set_password("password123")
            db.session.add(employee)
            db.session.flush()

            
            assignment = ProjectAssignment(
                project_id=project.id,
                user_id=employee.id,
                role_in_project=random.choice(["Developer", "Lead", "QA", "Analyst"]),
                status="active"
            )
            db.session.add(assignment)

            
            for s in random.sample(all_skills, k=random.randint(2, 4)):
                us = UserSkill(
                    user_id=employee.id,
                    skill_id=s.id,
                    proficiency_level=random.randint(1, 5),
                    is_verified=True
                )
                db.session.add(us)

    try:
        db.session.commit()
        click.echo(click.style(f"Successfully seeded {project_count} projects for {manager.username}.", fg="green"))
    except Exception as e:
        db.session.rollback()
        click.echo(click.style(f"Error committing data: {str(e)}", fg="red"))