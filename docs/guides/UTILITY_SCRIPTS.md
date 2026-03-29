# HireSense Utility Scripts

This comprehensive guide documents all utility scripts available for development, testing, and maintenance tasks in HireSense.

---

## Table of Contents

- [Overview](#overview)
- [Available Commands](#available-commands)
- [Usage](#usage)
- [Testing & Verification](#testing--verification)
- [Adding New Utilities](#adding-new-utilities)
- [Troubleshooting](#troubleshooting)

---

## Overview

The `utility/` folder contains Flask CLI commands and helper scripts that are registered with the application at startup. All commands are accessed through the `flask` CLI.

**Location:** `<project-root>/utility/`

**Requirements:**
- Activate your virtual environment
- Ensure Flask app is properly configured (`.env` file in place)

---

## Available Commands

### seed-users

Generate fake users for testing and development purposes.

**File:** `utility/seed_users.py`

**Usage:**

```bash
# Default: Seed 30 approved users with mixed roles
flask seed-users

# Seed a specific number of users
flask seed-users 50

# Seed pending (unapproved) users
flask seed-users 20 --pending

# Seed approved users (default)
flask seed-users 20 --approved

# Seed only managers
flask seed-users 25 --role=manager

# Seed only employees
flask seed-users 25 --role=employee

# Seed mixed roles (default)
flask seed-users 30 --role=mixed

# Combine options: 15 pending employees
flask seed-users 15 --pending --role=employee

# Show help
flask seed-users --help
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `NUMBER` | 30 | Number of users to create |
| `--approved` | Yes | Create approved users |
| `--pending` | No | Create pending (unapproved) users |
| `--role` | `mixed` | Role for seeded users: `manager`, `employee`, or `mixed` |

**Default Credentials:**

All seeded users have the password: `password123`

**Output Example:**

```
$ flask seed-users 10 --pending --role=manager
Seeding 10 users...
Successfully added 10 fake users.

User Summary:
  - Total users in DB: 43
  - Approved: 33
  - Pending: 10
  - Managers: 25
  - Employees: 18
```

**Notes:**

- Users are created with realistic names, emails, and secure password hashes (`password123` by default)
- Duplicate emails are automatically skipped and reported in the "Skipped" summary
- Employees receive 3–7 random skills each (when `--role` includes `employee`) using the existing skill catalog
- Skill seeding reports verified totals and average skills per employee in the summary
- The command uses your configured database from `.env` or environment variables

---

### seed-data

Seed the database with departments, skills, projects, and optionally user skills and assignments.

**File:** `utility/seed_users.py`

**Usage:**

```bash
# Basic seed (departments, skills, sample projects)
flask seed-data

# Full seed (includes user skills and project assignments)
flask seed-data --full

# Show help
flask seed-data --help
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--full` | No | Include user skills and project assignments |

**What Gets Seeded:**

**Basic mode (`flask seed-data`):**
- Departments: Engineering, QA, Security, Data Science, DevOps, Product Management
- Skills: 40+ technical and soft skills (Python, JavaScript, Docker, AWS, etc.)
- Sample projects: 5 projects with skill requirements and random manager assignments

**Full mode (`flask seed-data --full`):**
- All of the above
- User skills: Random skills assigned to up to 20 employees
- Project assignments: Random employees assigned to active projects

**Output Example:**

```
$ flask seed-data --full
Seeding departments, skills, and projects...
  Created department: Engineering
  Created department: Quality Assurance
  ...
Departments: 6 total
Skills: 40 total
  Created project: API Platform Upgrade (Manager: jsmith)
  ...
Projects: 5 total
User skills: 87 total
Project assignments: 15 total

Seed data complete!
```

**Notes:**

- Requires approved managers and skills to exist before running (seed users/skills first)
- Safe to rerun—existing departments, skills, and projects are re-used instead of duplicated
- Sample projects receive random approved managers and matching skill requirements
- `--full` adds additional user skill assignments (up to 20 employees) and project assignments for active projects

---

### seed-projects

Generate realistic projects with skill requirements and employee assignments.

**File:** `utility/seed_projects.py`

**Usage:**

```bash
# Default: Seed 20 projects
flask seed-projects

# Seed a specific number of projects
flask seed-projects --count 50

# Show help
flask seed-projects --help
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--count` | 20 | Number of projects to create |

**What Gets Seeded:**

- Projects with titles, descriptions, status, dates, and manager assignments
- 3–8 random skill requirements per project with weighted proficiencies
- 2–6 approved employees per project with contextual assignment statuses

**Notes:**

- Requires approved managers, employees, and skills (seed the users and data commands first)
- Skills are sampled from the existing catalog and assignments respect employee availability
- Command shows progress per project and concludes with counts by status, skills, and assignments

---

### clear-db

Safely clear all database tables while preserving the admin user.

**File:** `utility/clear_db.py`

**Usage:**

```bash
# Warning prompt; requires confirmation to proceed
flask clear-db

# Run with confirmation
flask clear-db --confirm

# Show help
flask clear-db --help
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--confirm` | No | Must be passed for deletion to run |

**What Happens:**

- Deletes notifications, project assignments/skills, user skills, learning paths, resumes, projects, users (excluding `admin@hiresense.local`), skills, and departments in that order
- Commits after each step and reports the preserved admin user plus current counts
- Rolls back on error to keep the database safe

**Notes:**

- Running without `--confirm` simply describes the warning and how to rerun with confirmation
- Intended for development/testing environments only—use with caution in shared databases

---

## Usage

### Docker Environment

If running with Docker, execute commands inside the container:

```bash
# Enter container
docker compose exec app_5010 bash

# Run command
flask seed-users
```

Or run directly:

```bash
docker compose exec app_5010 flask seed-users 50
```

### Local Virtual Environment

```bash
# Activate virtual environment
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Run command
flask seed-users
```

---

## Testing & Verification

### Quick Test

To verify the seed-users command is working:

```bash
# Test with 5 users
flask seed-users 5

# Check output for:
# - "Successfully added 5 fake users"
# - User summary showing counts
```

### Comprehensive Testing

#### 1. Test Default Behavior

```bash
flask seed-users
```

**Expected:**
- Creates 30 users
- All approved
- Mixed roles (managers and employees)

#### 2. Test Custom Quantity

```bash
flask seed-users 50
```

**Expected:**
- Creates exactly 50 users

#### 3. Test Pending Users

```bash
flask seed-users 20 --pending
```

**Expected:**
- Creates 20 users with `is_approved=False`

#### 4. Test Role Filters

```bash
# Managers only
flask seed-users 15 --role=manager

# Employees only
flask seed-users 15 --role=employee

# Mixed (default)
flask seed-users 15 --role=mixed
```

**Expected:**
- Creates users with specified roles

#### 5. Test Combined Options

```bash
flask seed-users 10 --pending --role=manager
```

**Expected:**
- Creates 10 pending manager accounts

### Verification Script

Run this Python script to verify users were added:

```python
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    total = User.query.count()
    approved = User.query.filter_by(is_approved=True).count()
    pending = User.query.filter_by(is_approved=False).count()

    print(f"Total users: {total}")
    print(f"Approved: {approved}")
    print(f"Pending: {pending}")

    # Test password
    user = User.query.filter(User.id > 5).first()
    if user:
        can_login = user.check_password("password123")
        print(f"Password test: {'PASS' if can_login else 'FAIL'}")
```

### Expected Behavior

#### Success Output

```
Seeding 30 users...
Successfully added 30 fake users.

User Summary:
  - Total users in DB: 31
  - Approved: 30
  - Pending: 1
  - Managers: 14
  - Employees: 17
```

#### Duplicate Email Skipping

```
Seeding 10 users...
Skipped 2 users (duplicate emails).
Successfully added 8 fake users.
```

### Common Use Cases

#### Development Setup
```bash
# Create diverse test data
flask seed-users 50 --role=employee
flask seed-users 20 --role=manager
flask seed-users 30 --pending
```

#### Testing Pagination
```bash
# Create 100+ users to test pagination
flask seed-users 100
```

#### Testing Approval Workflow
```bash
# Create pending users to test approval
flask seed-users 25 --pending
```

### Integration with Admin Panel

After seeding users, verify in admin panel:

1. Navigate to `http://localhost:5010/admin/users`
2. Check pagination works with many users
3. Test filtering by role
4. Verify search functionality
5. Test bulk actions on seeded users

---

## Adding New Utilities

To add a new CLI command:

### Step 1: Create a new file in `utility/`

```python
# utility/my_command.py
import click
from flask.cli import with_appcontext

@click.command("my-command")
@click.argument("arg", default="value")
@with_appcontext
def my_command(arg):
    """Description of what the command does."""
    click.echo(f"Running with: {arg}")
```

### Step 2: Export in `__init__.py`

```python
# utility/__init__.py
from .seed_users import seed_users
from .my_command import my_command

__all__ = ["seed_users", "my_command"]
```

### Step 3: Register in `app/__init__.py`

```python
from utility.my_command import my_command
app.cli.add_command(my_command)
```

### Step 4: Test the command

```bash
flask my-command --help
flask my-command
```

---

## Troubleshooting

### Command Not Found

Ensure you're in the project root and your virtual environment is activated:

```bash
cd /path/to/HireSense
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
flask seed-users
```

### Database Connection Error

Verify your `.env` file has the correct `DATABASE_URL`:

```bash
# Check current config
flask shell
>>> from app import db
>>> print(db.engine.url)
```

### Import Error

If you see "No module named utility", ensure the project root is in your Python path:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
flask seed-users
```

### Issue: "No module named 'faker'"

**Solution:**
```bash
pip install faker
```

### Issue: Users not appearing in database

**Solution:**
Check database connection in `.env`:
```bash
DATABASE_URL=postgresql://user:pass@host:port/database
```

Verify with:
```bash
python -c "from app import create_app, db; from app.models import User; app = create_app(); app.app_context().push(); print(User.query.count())"
```

### Issue: Import errors

**Solution:**
Ensure project root is in Python path:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

---

## Notes

- All seeded users have password: `password123`
- Usernames and emails are generated using Faker library
- Users are created as active (not blacklisted)
- Duplicate emails are automatically skipped
- Command respects `DATABASE_URL` from `.env` file

---

## Automated Testing

The seed-users command is tested in:
- Unit tests: `testing/unit/test_admin.py`
- Integration tests: `testing/integration/test_integration.py`

Run tests:
```bash
pytest testing/ -v
```

---

## See Also

- [README.md](../../README.md) - Project overview and setup
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines
- [TESTING.md](TESTING.md) - Testing documentation

---

**Last Updated:** March 29, 2026  
**Status:** ✅ Production Ready
