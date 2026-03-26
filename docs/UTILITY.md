# Utility Scripts

This document describes the utility scripts available in the `utility/` folder at the project root. These scripts help with development, testing, and maintenance tasks.

---

## Table of Contents

- [Utility Scripts](#utility-scripts)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Available Commands](#available-commands)
    - [seed-users](#seed-users)
    - [seed-data](#seed-data)
    - [seed-projects](#seed-projects)
    - [clear-db](#clear-db)
  - [Usage](#usage)
    - [Docker Environment](#docker-environment)
    - [Local Virtual Environment](#local-virtual-environment)
  - [Adding New Utilities](#adding-new-utilities)
  - [Troubleshooting](#troubleshooting)
    - [Command Not Found](#command-not-found)
    - [Database Connection Error](#database-connection-error)
    - [Import Error](#import-error)
  - [See Also](#see-also)

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

## Adding New Utilities

To add a new CLI command:

1. **Create a new file** in `utility/`:

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

2. **Export in `__init__.py`**:

   ```python
   # utility/__init__.py
   from .seed_users import seed_users
   from .my_command import my_command

   __all__ = ["seed_users", "my_command"]
   ```

3. **Register in `app/__init__.py`**:

   ```python
   from utility.my_command import my_command
   app.cli.add_command(my_command)
   ```

4. **Test the command**:

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

---

## See Also

- [README.md](../README.md) - Project overview and setup
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [TESTING.md](TESTING.md) - Testing documentation
