# Contributing to HireSense

Thank you for your interest in contributing to HireSense. This document covers the contribution workflow, branch naming, keeping branches up to date, and a step-by-step example for contributing multiple features.

---

## Table of Contents

- Before You Start
- Local Development Setup
- Branching & Naming Conventions
- Step-by-Step Workflow
- Multiple Features
- Keeping Your Branch Up to Date
- PR Feedback & Updates
- Commit Message Guidelines
- PR Checklist
- Troubleshooting

---

## Before You Start

- A GitHub account
- Git 2.20+
- Python 3.11+
- Docker Desktop with Compose v2 (for containerised dev)
- A local PostgreSQL instance (for non-Docker dev)

---

## Local Development Setup

1. **Fork and clone the repository**

   ```bash
   git clone https://github.com/<your-username>/HireSense.git
   cd HireSense
   git remote add upstream https://github.com/paarthsiloiya/HireSense.git
   ```

2. **Set environment variables**

   ```bash
   cp .env.example .env
   # Edit .env — set DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD
   ```

3. **Start with live reload (recommended)**

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
   ```

   This mounts your local source into the containers and enables Flask's debug server. After the first build you can drop `--build` for subsequent starts:

   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

   | Change type | What to do |
   |-------------|------------|
   | HTML / Tailwind classes | Refresh the browser |
   | Python (`.py`) files | Flask auto-restarts — refresh after a moment |
   | `requirements.txt` | Restart with `--build` |

4. **Register test users**

   Visit `http://localhost:5010/auth/register` to create `manager` or `employee` accounts. The `admin` account is pre-seeded only — it cannot be registered.

   **Alternatively, seed test users via CLI:**

   ```bash
   # In Docker
   docker compose exec app_5010 flask seed-users

   # Local
   flask seed-users
   ```

   This creates 30 test users with password `password123`. See [docs/UTILITY.md](docs/UTILITY.md) for more options.

### Alternative: Local Virtual Environment (no Docker)

1. Create and activate a virtual environment

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run a portal

   ```bash
   # macOS / Linux
   PORT=5010 python run.py

   # Windows (PowerShell)
   $env:PORT=5010; python run.py
   ```

   On first run, all database tables are created and the `admin` user is seeded automatically.

### Frontend Styling

All templates extend `app/templates/base.html`. Tailwind CSS v4 is loaded via the `@tailwindcss/browser` CDN — there is no Node.js toolchain, no compilation step, and no CSS files to maintain. To style a page:

- Add Tailwind utility classes directly in any template HTML.
- For project-wide theme changes (custom fonts, colours), edit the `<style type="text/tailwindcss">` block inside `base.html`.
- Refresh the browser — changes are visible immediately (no rebuild required when using `docker-compose.dev.yml`).

---

## Branching & Naming Conventions

Use lowercase, hyphen-separated branch names:

- `feature/<description>` — new features
- `fix/<description>` — bug fixes
- `chore/<description>` — maintenance
- `docs/<description>` — documentation only

Include an issue number when one exists: `feature/42-resume-parser`.

---

## Step-by-Step Workflow

1. Ensure local `main` is up to date

   ```bash
   git checkout main
   git fetch upstream
   git reset --hard upstream/main
   ```

2. Create a branch from upstream/main

   ```bash
   git checkout -b feature/short-description upstream/main
   ```

3. Make changes, run and test locally

4. Commit with a clear message

   ```bash
   git add .
   git commit -m "feat(parser): add skill entity extraction"
   ```

5. Push to your fork

   ```bash
   git push origin feature/short-description
   ```

6. Open a Pull Request on GitHub from your fork's branch into `paarthsiloiya/HireSense:main`.

7. Respond to review feedback by committing additional changes to the same branch.

8. After merge, clean up

   ```bash
   git push origin --delete feature/short-description
   git branch -D feature/short-description
   ```

---

## Multiple Features

Create a separate branch and PR for each feature. This keeps reviews focused and allows independent merging.

```bash
# Feature 1
git checkout -b feature/feature1 upstream/main
# ... implement, commit, push, open PR

# Feature 2 — start fresh from upstream/main
git checkout main
git fetch upstream
git reset --hard upstream/main
git checkout -b feature/feature2 upstream/main
# ... implement, commit, push, open PR
```

If feature2 depends on feature1, wait for feature1 to merge before branching feature2 off the updated `main`.

---

## Keeping Your Branch Up to Date

Prefer rebase to keep a linear history:

```bash
git fetch upstream
git checkout feature/short-description
git rebase upstream/main
# Resolve any conflicts, then:
git push --force-with-lease origin feature/short-description
```

Use `--force-with-lease` instead of `--force` to avoid overwriting collaborators' work.

---

## PR Feedback & Updates

Make changes on the same branch, commit, and push — the PR updates automatically:

```bash
git add .
git commit -m "fix: address review comment about X"
git push origin feature/short-description
```

---

## Commit Message Guidelines

Follow Conventional Commits where possible:

```
feat(scope): short summary
fix(scope): short summary
docs(scope): short summary
chore: short summary
```

Add a body paragraph for non-trivial changes.

---

## Testing

**All contributions must include appropriate tests and maintain 85%+ code coverage.**

### Running Tests Locally

Before submitting a PR, run the test suite locally:

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=app --cov-report=term-missing

# Run specific test categories
pytest testing/unit/          # Unit tests only
pytest testing/integration/   # Integration tests only
pytest testing/system/        # System/E2E tests only
```

### Writing Tests

When adding new features or fixing bugs:

1. **Write tests first** (TDD approach recommended)
2. Place tests in the appropriate directory:
   - `testing/unit/` - Unit tests for isolated components
   - `testing/integration/` - Integration tests for module interactions
   - `testing/system/` - End-to-end workflow tests

3. **Ensure tests are**:
   - Independent and isolated
   - Repeatable and deterministic
   - Well-documented with clear docstrings
   - Following the Arrange-Act-Assert pattern

4. **Use existing fixtures** from `testing/conftest.py`:
   ```python
   def test_example(client, db_session, admin_user):
       # Your test code here
   ```

### Coverage Requirements

- **Minimum coverage**: 85%
- **CI/CD enforcement**: PRs with <85% coverage will be blocked
- **Check coverage locally**:
  ```bash
  pytest --cov=app --cov-report=html
  open testing/coverage_html/index.html
  ```

### Test Documentation

For comprehensive testing information, refer to **[TESTING.md](TESTING.md)**, which covers:

- Complete test suite architecture
- How to run, add, modify, and delete tests
- Coverage report interpretation
- Troubleshooting common issues
- Testing best practices

**Any questions about testing?** See [TESTING.md](TESTING.md) as the source of truth for all QA procedures.

---

## PR Checklist

- Change is focused and does one thing
- Tested locally (all three ports if relevant)
- **Tests written and passing (coverage ≥85%)**
- No secrets or credentials included
- Relevant documentation updated
- Commit messages follow guidelines
- Branch is rebased onto the latest upstream/main

---

## Troubleshooting

- **Push rejected** — fetch upstream and rebase, then push again.
- **Accidentally committed to main** — branch off that commit, reset main to upstream/main.
- **Merge conflict during rebase** — edit the conflicting files, `git add`, `git rebase --continue`. To abort: `git rebase --abort`.

---

## Licensing

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

---

Thank you for contributing to HireSense.

