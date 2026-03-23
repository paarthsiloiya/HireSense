# Utility Scripts

This document describes the utility scripts available in the `utility/` folder at the project root. These scripts help with development, testing, and maintenance tasks.

---

## Table of Contents

- [Overview](#overview)
- [Available Commands](#available-commands)
  - [seed-users](#seed-users)
- [Usage](#usage)
- [Adding New Utilities](#adding-new-utilities)

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

- Users are created with realistic names and email addresses using the Faker library
- Duplicate emails are automatically skipped
- All users are created as active (not blacklisted)
- The command uses your configured database from `.env` or environment variables

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
