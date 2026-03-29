# HireSense Setup Guide

This comprehensive guide covers all setup options for HireSense, including Docker, local development, and development mode with live reload.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Docker Development Mode](#docker-development-mode)
- [Local Virtual Environment Setup](#local-virtual-environment-setup)
- [Database Setup](#database-setup)
- [Environment Configuration](#environment-configuration)
- [First-Time Setup](#first-time-setup)
- [Verification](#verification)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Docker Desktop** with Compose v2 - [Download Docker](https://www.docker.com/products/docker-desktop)
- **Git** - [Download Git](https://git-scm.com/downloads)
- **PostgreSQL 15** (for local setup only) - [Download PostgreSQL](https://www.postgresql.org/download/)

### System Requirements

- **OS:** Windows 10/11, macOS 10.15+, or Linux
- **RAM:** 4GB minimum (8GB recommended)
- **Disk:** 2GB free space
- **Network:** Internet connection for package downloads

---

## Quick Start (Docker)

Docker is the **recommended** setup method as it provides a consistent environment and handles all dependencies automatically.

### Step 1: Clone the Repository

```bash
git clone https://github.com/paarthsiloiya/HireSense.git
cd HireSense
```

### Step 2: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env
```

**Important:** Set `SECRET_KEY` and `ADMIN_PASSWORD` in `.env` before any non-local deployment.

**Example `.env` content:**
```env
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=Admin@1234
DATABASE_URL=postgresql://hiresense:hiresense@db:5432/hiresense
PORT=5010
```

### Step 3: Build and Start Services

```bash
docker compose up --build
```

This command:
- Starts PostgreSQL 15 on host port `5434` (container port `5432`)
- Starts three Flask instances on ports `5010`, `5011`, `5012`
- Creates the admin user automatically on first boot
- Sets up the database schema

**Initial startup takes 2-3 minutes** while Docker downloads images and builds containers.

### Step 4: Access the Application

Once you see log messages indicating the servers are running, open your browser:

| Port | URL                   | Description |
|------|-----------------------|-------------|
| 5010 | http://localhost:5010 | Primary portal |
| 5011 | http://localhost:5011 | Secondary portal |
| 5012 | http://localhost:5012 | Tertiary portal |

**Default Admin Credentials:**
- Username: `admin`
- Password: value of `ADMIN_PASSWORD` (default: `Admin@1234`)

### Step 5: Common Docker Commands

```bash
# Stop services (data kept)
docker compose down

# Stop and delete all data (including database)
docker compose down -v

# Rebuild after code changes
docker compose up --build

# View logs for all services
docker compose logs -f

# View logs for one service
docker compose logs -f app_5010

# Access container shell
docker compose exec app_5010 bash

# Run Flask commands
docker compose exec app_5010 flask seed-users
```

---

## Docker Development Mode

Use this mode while actively developing. Your local source tree is mounted into the containers so template and Python changes are reflected immediately without rebuilding.

### Step 1: Start Dev Mode

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

For the first time, or after changing `requirements.txt`, add `--build`:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
```

### Step 2: Make Changes

| Change Type | What to Do |
|-------------|------------|
| HTML / Tailwind classes | Refresh the browser |
| Python (`.py`) files | Flask debug server auto-restarts — refresh after a moment |
| `requirements.txt` | Restart with `--build` |

**Development Features:**
- ✅ Hot reload for Python code
- ✅ Template changes reflected immediately
- ✅ Debug mode enabled
- ✅ Detailed error pages
- ✅ No rebuild needed for most changes

### Step 3: View Logs

```bash
# All services
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f app_5010
```

### Step 4: Stop Dev Mode

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

---

## Local Virtual Environment Setup

This option gives you more control but requires manual setup of PostgreSQL and dependencies.

### Step 1: Clone the Repository

```bash
git clone https://github.com/paarthsiloiya/HireSense.git
cd HireSense
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**This installs:**
- Flask and related packages
- SQLAlchemy and PostgreSQL drivers
- Authentication libraries
- Testing frameworks
- Documentation tools

### Step 4: Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` to configure your local PostgreSQL connection:

```env
SECRET_KEY=your-secret-key-here
ADMIN_PASSWORD=Admin@1234
DATABASE_URL=postgresql://username:password@localhost:5432/hiresense
PORT=5010
```

**Replace:**
- `username` - Your PostgreSQL username
- `password` - Your PostgreSQL password
- `hiresense` - Your database name

### Step 5: Set Up PostgreSQL Database

**Create Database:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE hiresense;
CREATE USER hiresense WITH PASSWORD 'hiresense';
GRANT ALL PRIVILEGES ON DATABASE hiresense TO hiresense;

# Exit PostgreSQL
\q
```

### Step 6: Start the Application

**macOS / Linux:**
```bash
PORT=5010 python run.py
```

**Windows (PowerShell):**
```powershell
$env:PORT=5010; python run.py
```

**Windows (Command Prompt):**
```cmd
set PORT=5010
python run.py
```

Tables are created and the admin user is seeded automatically on first run.

### Step 7: Access the Application

Open your browser and navigate to:
```
http://localhost:5010
```

---

## Database Setup

### Automatic Migration

HireSense uses Flask-Migrate (Alembic) for database migrations. On first run, the application automatically:
- Creates all database tables
- Sets up indexes and constraints
- Seeds the admin user

### Manual Migration

If you need to run migrations manually:

```bash
# Initialize migrations (first time only)
flask db init

# Generate migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Using the helper script
python scripts/migrate.py -m "Description of changes"
```

### Database Schema

The application creates the following tables:
- `users` - User accounts and authentication
- `departments` - Department definitions
- `skills` - Skill catalog
- `projects` - Project management
- `user_skills` - User skill associations
- `project_skills` - Project skill requirements
- `project_assignments` - Employee project assignments
- `resumes` - Resume storage
- `learning_paths` - Career development paths
- `notifications` - User notifications

---

## Environment Configuration

### Required Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key for sessions | (generated) |
| `ADMIN_PASSWORD` | Admin user password | `Admin@1234` |
| `DATABASE_URL` | PostgreSQL connection string | See below |
| `PORT` | Application port | `5010` |

### DATABASE_URL Format

**Docker:**
```
postgresql://hiresense:hiresense@db:5432/hiresense
```

**Local:**
```
postgresql://username:password@localhost:5432/database_name
```

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production) | `production` |
| `FLASK_DEBUG` | Enable debug mode | `False` |
| `SESSION_COOKIE_SECURE` | Require HTTPS for cookies | `False` |
| `SESSION_COOKIE_HTTPONLY` | HTTP-only session cookies | `True` |
| `PERMANENT_SESSION_LIFETIME` | Session timeout (seconds) | `3600` |

---

## First-Time Setup

### Create Admin User

The admin user is created automatically on first startup with:
- Username: `admin`
- Email: `admin@hiresense.local`
- Password: value from `ADMIN_PASSWORD` in `.env`
- Role: `admin`

**Cannot register via UI** - admin is system-created only.

### Create Test Users

Use utility scripts to create test data:

```bash
# Seed 50 employees
flask seed-users 50 --role=employee

# Seed 20 managers
flask seed-users 20 --role=manager

# Seed departments and skills
flask seed-data

# Seed projects
flask seed-projects --count 30
```

### Register Regular Users

Managers and employees can register via the UI:
1. Go to `http://localhost:5010/auth/register`
2. Fill in registration form
3. Choose role: Manager or Employee
4. Submit registration
5. Wait for admin approval (for managers)

---

## Verification

### Verify Docker Setup

```bash
# Check running containers
docker ps

# Should see:
# - hiresense-db-1
# - hiresense-app_5010-1
# - hiresense-app_5011-1
# - hiresense-app_5012-1

# Check database connection
docker compose exec app_5010 flask shell
>>> from app import db
>>> db.session.execute('SELECT 1').scalar()
1
```

### Verify Local Setup

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Check database connection
flask shell
>>> from app import db
>>> db.session.execute('SELECT 1').scalar()
1

# Check admin user exists
>>> from app.models import User
>>> User.query.filter_by(username='admin').first()
<User admin>
```

### Test Login

1. Open browser to `http://localhost:5010`
2. Enter admin credentials
3. Should redirect to admin dashboard
4. Verify navigation works

---

## Common Commands

### Docker Commands

```bash
# Start all services
docker compose up -d

# Stop all services
docker compose down

# Rebuild containers
docker compose up --build

# View logs
docker compose logs -f

# Execute command in container
docker compose exec app_5010 flask seed-users

# Access container shell
docker compose exec app_5010 bash

# Database backup
docker compose exec db pg_dump -U hiresense hiresense > backup.sql

# Database restore
docker compose exec -T db psql -U hiresense hiresense < backup.sql
```

### Flask Commands

```bash
# Run development server (local)
flask run --port 5010

# Run migrations
flask db upgrade

# Seed users
flask seed-users 30

# Seed data
flask seed-data --full

# Clear database
flask clear-db --confirm

# Open Flask shell
flask shell
```

### Development Commands

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run linter
flake8 app/

# Format code
black app/

# Build documentation
cd docs && sphinx-build -b html . _build/html
```

---

## Troubleshooting

### Docker Issues

#### Issue: Port already in use
**Solution:**
```bash
# Check what's using the port
# Windows
netstat -ano | findstr :5010

# macOS/Linux
lsof -i :5010

# Stop the process or change PORT in .env
```

#### Issue: Database connection failed
**Solution:**
```bash
# Check database container is running
docker compose ps

# Restart database
docker compose restart db

# Check logs
docker compose logs db
```

#### Issue: Permission denied
**Solution:**
```bash
# On Linux, try with sudo
sudo docker compose up

# Or add your user to docker group
sudo usermod -aG docker $USER
```

### Local Setup Issues

#### Issue: Module not found
**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # or .venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: PostgreSQL connection refused
**Solution:**
```bash
# Check PostgreSQL is running
# macOS
brew services list

# Linux
sudo systemctl status postgresql

# Windows - check Services app

# Verify connection string in .env
```

#### Issue: Admin user not created
**Solution:**
```bash
# Create admin manually
flask shell
>>> from app import db
>>> from app.models import User
>>> admin = User(username='admin', email='admin@hiresense.local', role='admin', is_approved=True)
>>> admin.set_password('Admin@1234')
>>> db.session.add(admin)
>>> db.session.commit()
```

### Common Errors

#### Error: "SECRET_KEY not set"
**Solution:** Ensure `.env` file exists and contains `SECRET_KEY`

#### Error: "Database does not exist"
**Solution:** Create database manually or run migrations

#### Error: "Port 5010 already in use"
**Solution:** Change `PORT` in `.env` or stop the conflicting service

---

## Next Steps

After successful setup:

1. **Explore the application**
   - Login as admin
   - Create test users
   - Upload sample resumes
   - Test features

2. **Read documentation**
   - [TESTING.md](TESTING.md) - Testing guide
   - [MIGRATIONS.md](MIGRATIONS.md) - Database migrations
   - [UTILITY_SCRIPTS.md](UTILITY_SCRIPTS.md) - Utility commands

3. **Start developing**
   - Review codebase structure
   - Check [CONTRIBUTING.md](../../CONTRIBUTING.md)
   - Set up your IDE

---

## Support

For issues or questions:
- Check this documentation
- Review [GitHub Issues](https://github.com/paarthsiloiya/HireSense/issues)
- Consult the project README

---

**Last Updated:** March 29, 2026  
**Status:** ✅ Production Ready
