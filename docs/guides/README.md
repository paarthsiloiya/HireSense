# HireSense Documentation Guides

Welcome to the HireSense documentation guides. This directory contains comprehensive guides for setting up, developing, deploying, and maintaining HireSense.

---

## Available Guides

### 🚀 Getting Started

#### [SETUP.md](SETUP.md)
Complete setup instructions for HireSense, covering:
- Docker setup (recommended)
- Docker development mode with live reload
- Local virtual environment setup
- Database configuration
- Environment variables
- First-time setup and verification

**Start here if:** You're setting up HireSense for the first time or need to configure a development environment.

---

### 🧪 Development & Testing

#### [TESTING.md](TESTING.md)
Comprehensive testing guide covering:
- Test suite architecture (unit, integration, system tests)
- Running tests and generating coverage reports
- Writing new tests and modifying existing ones
- CI/CD integration
- Best practices for test-driven development

**Start here if:** You need to run tests, write new tests, or understand the testing infrastructure.

#### [UTILITY_SCRIPTS.md](UTILITY_SCRIPTS.md)
Documentation for utility scripts and Flask CLI commands:
- `seed-users` - Generate test users
- `seed-data` - Seed departments, skills, and projects
- `seed-projects` - Create realistic project data
- `clear-db` - Safely clear database
- Creating custom utility commands

**Start here if:** You need to generate test data or create custom management commands.

---

### 🗄️ Database Management

#### [MIGRATIONS.md](MIGRATIONS.md)
Database migration workflow and best practices:
- Flask-Migrate (Alembic) usage
- Creating and applying migrations
- Handling non-nullable columns
- Migration safety and review process
- Troubleshooting migration issues

**Start here if:** You're making database schema changes or need to understand the migration workflow.

---

### 🎨 Theming & Design

#### [THEMING.md](THEMING.md)
Guidelines for the Tailwind CSS v4 theming system:
- Semantic token naming conventions
- Brand colors and structural colors
- Using the theme in new components
- Modifying the global theme
- Dark mode preparation

**Start here if:** You're working on UI components or need to understand the design system.

---

### 🚢 Deployment

#### [DEPLOYMENT.md](DEPLOYMENT.md)
Complete deployment guide for Sphinx documentation to GitHub Pages:
- GitHub Pages setup instructions
- CI/CD pipeline architecture and details
- Deployment workflow and automation
- Quick reference commands
- Troubleshooting common issues
- Performance metrics and best practices

**Start here if:** You need to set up documentation deployment, understand the CI/CD pipeline, or troubleshoot deployment issues.

---

## Quick Navigation

### By Task

| I want to... | Read this guide |
|-------------|-----------------|
| Set up HireSense for the first time | [SETUP.md](SETUP.md) |
| Run or write tests | [TESTING.md](TESTING.md) |
| Generate test data | [UTILITY_SCRIPTS.md](UTILITY_SCRIPTS.md) |
| Make database changes | [MIGRATIONS.md](MIGRATIONS.md) |
| Work on UI components | [THEMING.md](THEMING.md) |
| Deploy documentation | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Troubleshoot deployment | [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) |

### By Experience Level

#### Beginners
1. Start with [SETUP.md](SETUP.md) to get the application running
2. Read [UTILITY_SCRIPTS.md](UTILITY_SCRIPTS.md) to generate test data
3. Review [THEMING.md](THEMING.md) to understand the UI

#### Intermediate
1. Review [TESTING.md](TESTING.md) to understand the test suite
2. Study [MIGRATIONS.md](MIGRATIONS.md) for database changes
3. Check [DEPLOYMENT.md](DEPLOYMENT.md) for documentation workflow

#### Advanced
1. All guides above
2. Refer to guides as needed for specific tasks
3. Contribute to improving these guides

---

## Additional Resources

### Project Documentation
- [Main README](../../README.md) - Project overview
- [Contributing Guide](../../CONTRIBUTING.md) - Contribution guidelines
- [License](../../LICENSE) - Project license

### Sphinx Documentation
- [docs/README.md](../README.md) - Sphinx documentation overview
- [docs/index.rst](../index.rst) - Generated documentation index
- [docs/conf.py](../conf.py) - Sphinx configuration

### External Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Pytest Documentation](https://docs.pytest.org/)
- [Sphinx Documentation](https://www.sphinx-doc.org/)

---

## Contributing to Documentation

Found an issue or want to improve the documentation?

1. **Report issues** - Create an issue on GitHub
2. **Submit improvements** - Create a pull request
3. **Ask questions** - Use GitHub discussions

### Documentation Standards

When updating guides:
- Use clear, concise language
- Include code examples where appropriate
- Add troubleshooting sections for common issues
- Keep table of contents updated
- Test all commands and procedures

---

## Guide Metadata

| Guide | Last Updated | Status |
|-------|--------------|--------|
| SETUP.md | 2026-03-29 | ✅ Complete |
| TESTING.md | 2026-03-20 | ✅ Complete |
| UTILITY_SCRIPTS.md | 2026-03-29 | ✅ Complete |
| MIGRATIONS.md | 2024-12-20 | ✅ Complete |
| THEMING.md | 2024-12-20 | ✅ Complete |
| DEPLOYMENT.md | 2026-03-29 | ✅ Complete |

---

## Getting Help

If you need assistance:

1. **Check the relevant guide first** - Most questions are answered in the guides
2. **Search existing issues** - Your question may have been answered
3. **Review the main README** - Contains project overview and quick start
4. **Ask in discussions** - Community support available
5. **Create an issue** - For bugs or feature requests

---

## Feedback

We're constantly improving our documentation. If you have suggestions:
- What topics need more detail?
- What examples would be helpful?
- What's confusing or unclear?
- What's missing?

Please share your feedback through GitHub issues or discussions.

---

**Documentation Version:** 1.0  
**Last Updated:** March 29, 2026  
**Maintained by:** HireSense Development Team
