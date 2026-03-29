# HireSense Documentation Deployment Guide

This comprehensive guide covers all aspects of deploying HireSense Sphinx documentation to GitHub Pages, including setup, CI/CD pipeline details, and troubleshooting.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [GitHub Pages Setup](#github-pages-setup)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment Workflow](#deployment-workflow)
- [Quick Reference Commands](#quick-reference-commands)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

HireSense documentation is automatically built and deployed to GitHub Pages using GitHub Actions. The system uses Sphinx to generate professional HTML documentation from Python docstrings and deploys it to a publicly accessible URL.

**Key Benefits:**
- ✅ Automatic builds on every push
- ✅ Professional ReadTheDocs theme
- ✅ Free hosting on GitHub Pages
- ✅ HTTPS secured
- ✅ Auto-generated API documentation
- ✅ Version controlled with source code

---

## Quick Start

### Access Documentation

Once deployed, documentation is available at:

```
https://<username>.github.io/HireSense/
```

### Build Locally

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Build documentation
cd docs
sphinx-build -b html . _build/html

# Open in browser
# Windows: start _build/html/index.html
# macOS: open _build/html/index.html
# Linux: firefox _build/html/index.html
```

---

## GitHub Pages Setup

### Step 1: Enable GitHub Pages

1. Navigate to your GitHub repository
2. Go to **Settings** (gear icon)
3. In the left sidebar, click **Pages**
4. Under "Build and deployment":
   - **Source**: Select `GitHub Actions` from the dropdown
   - Leave other settings as default

**Expected Result:**
```
Your site is ready to be published at https://<username>.github.io/HireSense/
```

### Step 2: Verify Repository Settings

1. Go to **Settings** → **General**
2. Ensure visibility is set to **Public** (required for free GitHub Pages)
3. Note the repository URL

### Step 3: Trigger Documentation Build

You can trigger the workflow in three ways:

#### Option A: Push to Main Branch
```bash
git push origin main
```

#### Option B: Manual Trigger (GitHub UI)
1. Go to **Actions** tab
2. Click **Build and Deploy Sphinx Documentation** workflow
3. Click **Run workflow** → **Run workflow**

#### Option C: Push Changes
Push any changes to `app/`, `docs/`, or `requirements.txt`:
```bash
git add .
git commit -m "Update documentation"
git push origin main
```

### Step 4: Monitor Build Progress

1. Go to **Actions** tab
2. Click the workflow run (should be at the top)
3. Watch the build progress:
   - **Build** job runs first
   - **Deploy** job runs after successful build
   - Green checkmarks indicate success

### Step 5: Access Your Documentation

After successful deployment (2-3 minutes):

```
https://<username>.github.io/HireSense/
```

---

## CI/CD Pipeline

### Pipeline Architecture

```
┌─────────────────┐
│  Git Push to    │
│  main/master    │
├─────────────────┤
│ Triggers Workflow│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│   GitHub Actions Workflow Start     │
│   .github/workflows/docs.yml        │
└─────────────┬───────────────────────┘
              │
              ▼
      ┌──────────────────┐
      │   Build Job      │
      │ ubuntu-latest    │
      └────────┬─────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌──────────┐
│Python │ │Install│ │Download  │
│Setup  │ │Deps   │ │spaCy     │
└───┬───┘ └───┬───┘ └─────┬────┘
    │         │           │
    └─────────┴───────────┘
              │
              ▼
    ┌──────────────────┐
    │ Build Sphinx     │
    │ Documentation    │
    └────────┬─────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌──────────┐  ┌──────────────┐
│Success   │  │Failure       │
│          │  │(Logs saved)  │
└────┬─────┘  └──────────────┘
     │
     ▼
┌──────────────────────┐
│  Deploy Job          │
│  (if main/master)    │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
┌────────┐  ┌──────────────┐
│Upload  │  │Deploy to     │
│Artifacts│ │GitHub Pages  │
└────────┘  └──────────────┘
    │             │
    └──────┬──────┘
           ▼
┌──────────────────────────┐
│ Documentation Live at:   │
│ https://<user>.io/       │
│ HireSense/               │
└──────────────────────────┘
```

### Workflow Details

**File:** `.github/workflows/docs.yml`

**Automatic Triggers:**
- ✅ Push to `main`, `master`, or `develop` branches
- ✅ Changes to `app/`, `docs/`, or `requirements.txt`
- ✅ Changes to workflow file itself
- ✅ Manual trigger via GitHub UI

**Workflow Steps:**

#### Build Job
1. **Checkout Repository** - Clones the repository with full history
2. **Python Setup** - Installs Python 3.10 with pip caching
3. **System Dependencies** - Installs build-essential for psycopg2
4. **Python Dependencies** - Installs Sphinx and project requirements
5. **Download spaCy Model** - Gets English language model (continues on error)
6. **Build Documentation** - Runs `sphinx-build -b html -W --keep-going`
7. **Verify Build** - Confirms HTML output exists

#### Deploy Job (main/master only)
1. **Setup** - Checkout repository and setup Python
2. **Build** - Rebuild documentation
3. **Upload** - Upload HTML artifacts to GitHub Pages
4. **Deploy** - Publish to GitHub Pages URL

**Typical Duration:** 30-50 seconds

### Supported Branches

- `main` - Production documentation (full deploy)
- `master` - Alternative production branch (full deploy)
- `develop` - Development documentation (build only)

### Trigger Points

✅ **Rebuilds on changes to:**
- `app/` - Python source code
- `docs/` - Documentation files
- `requirements.txt` - Dependencies
- `.github/workflows/docs.yml` - Workflow file

❌ **No rebuild for:**
- README.md updates
- Test file changes
- Non-documentation files

---

## Deployment Workflow

### How It Works

```
Developer Push Code
    ↓
GitHub Detects Change
    ↓
Workflow Triggered
    ↓
Build Documentation
    ↓
Generate HTML
    ↓
Upload Artifacts
    ↓
GitHub Pages Deployment
    ↓
Live Documentation
```

### Update Documentation

1. **Update Docstrings**
   ```bash
   # Edit Python files and update docstrings
   git add .
   git commit -m "Update documentation"
   git push origin main
   ```

2. **Automatic Rebuild**
   - Workflow automatically triggers
   - Documentation rebuilds
   - Changes live in minutes

3. **Verify Changes**
   - Visit GitHub Pages URL
   - Check updated documentation
   - Verify all links work

### Rebuild Manually

**From Command Line:**
```bash
cd docs
sphinx-build -b html . _build/html
```

**From GitHub UI:**
1. Go to Actions tab
2. Select "Build and Deploy Sphinx Documentation"
3. Click "Run workflow"

---

## Quick Reference Commands

### Local Development

```bash
# View documentation locally
cd docs && sphinx-build -b html . _build/html && open _build/html/index.html

# Check for warnings
cd docs && sphinx-build -b html -W . _build/html

# Clean rebuild
cd docs && rm -rf _build && sphinx-build -b html . _build/html

# Verify docstring format
grep -r "def " app/ | head -20

# Test Python syntax
python -m py_compile app/**/*.py
```

### Workflow Commands

```bash
# Push to trigger build
git push origin main

# Check workflow status
# Go to: Repository → Actions tab

# View build logs
# Actions → Click workflow run → Expand job steps
```

### Docker Commands

```bash
# Build docs in Docker
docker compose exec app_5010 flask shell
>>> from app import create_app
>>> app = create_app()

# Install Sphinx in container
docker compose exec app_5010 pip install sphinx sphinx-rtd-theme
```

---

## Troubleshooting

### Build Fails

**Check Logs:**
1. Go to Actions tab
2. Click failing workflow
3. Expand "Build" job
4. Review error messages

**Common Issues:**

#### Issue: "spaCy model download failed"
**Solution:** The workflow continues even if spaCy model fails (marked with `|| true`). Documentation will build but NLP features may show reduced functionality.

```bash
# To fix locally:
python -m spacy download en_core_web_lg
```

#### Issue: "Module import errors during Sphinx build"
**Solution:**
1. Update `requirements.txt` with all dependencies
2. Verify Python version compatibility
3. Test locally before pushing:
   ```bash
   pip install -r requirements.txt
   sphinx-build -b html docs docs/_build/html
   ```

#### Issue: "Pages site not available"
**Solution:**
1. Ensure GitHub Pages is enabled in repository settings
2. Wait 5-10 minutes after first deployment
3. Check repository visibility (public repos required for free tier)

### Documentation Not Updating

**Verify:**
1. Push to correct branch (main/master)
2. Check Actions tab for successful build
3. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
4. Check GitHub Pages URL is correct

### Pages Not Available

**Check:**
1. Settings → Pages enabled
2. Source set to GitHub Actions
3. Repository is public
4. Wait 5-10 minutes after first deployment

### Workflow Not Triggering

**Cause:** Workflow file not in `.github/workflows/`

**Solution:**
```bash
git add .github/workflows/docs.yml
git commit -m "Add workflow"
git push
```

### Build Fails with Import Errors

**Cause:** Missing dependencies in `requirements.txt`

**Solution:**
```bash
# Update requirements.txt
pip freeze > requirements.txt
git push
```

### Pages URL Shows "404 Not Found"

**Cause:** Pages not enabled or first deployment

**Solution:**
1. Wait 5-10 minutes
2. Check Settings → Pages
3. Verify GitHub Actions source
4. Hard refresh browser

---

## Best Practices

### 1. Keep Documentation Updated

- Update docstrings whenever code changes
- Follow Sphinx/reStructuredText format
- Use consistent formatting

### 2. Test Locally Before Pushing

```bash
sphinx-build -b html -W docs docs/_build/html
```

### 3. Review Pull Requests

- GitHub Actions will build documentation for PRs
- Review build logs before merging
- Ensure no warnings/errors introduced

### 4. Maintain Sphinx Configuration

- Keep `docs/conf.py` updated
- Add new modules to `docs/modules.rst`
- Update theme and extensions as needed

### 5. Use Meaningful Docstrings

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.
    
    Longer description here if needed.
    
    :param param1: Description of param1.
    :type param1: str
    :param param2: Description of param2.
    :type param2: int
    :returns: Description of return value.
    :rtype: bool
    :raises ValueError: When invalid input provided.
    """
```

### 6. Docstring Standards

All docstrings follow Sphinx/reStructuredText format:

```python
def function(param1: str, param2: int) -> bool:
    """
    Brief one-line description.
    
    Longer description with more details
    can span multiple lines.
    
    :param param1: Description of first parameter.
    :type param1: str
    :param param2: Description of second parameter.
    :type param2: int
    :returns: Description of return value.
    :rtype: bool
    :raises ValueError: When parameter is invalid.
    """
    pass
```

### 7. Monitor Builds

**Check Workflow Status:**
1. Go to Actions tab in GitHub
2. View latest "Build and Deploy Sphinx Documentation" run
3. Check build logs for warnings

**Update Dependencies:**
```bash
# Install latest Sphinx and plugins
pip install --upgrade sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Update docs/conf.py if needed
```

---

## Performance Metrics

### Typical Workflow Times

| Step | Duration | Notes |
|------|----------|-------|
| Checkout | 2-3s | Clones repo |
| Python Setup | 3-5s | Install + cache |
| Install Deps | 10-20s | First run slower |
| Build Docs | 5-15s | Depends on size |
| Deploy | 1-3s | Upload artifacts |
| **Total** | **25-50s** | Typically ~30s |

### Optimization Tips

1. **Use Caching:**
   - Pip cache enabled by default
   - Reduces subsequent runs

2. **Minimal Triggers:**
   - Only build on relevant changes
   - Avoid unnecessary builds

3. **Parallel Jobs:**
   - Currently sequential
   - Can be parallelized if needed

---

## Status Badge

Add to README.md:

```markdown
[![Documentation](https://github.com/<owner>/HireSense/actions/workflows/docs.yml/badge.svg)](https://github.com/<owner>/HireSense/actions/workflows/docs.yml)
```

Replace `<owner>` with your GitHub username.

---

## Support Resources

### Documentation
- Sphinx: [https://www.sphinx-doc.org/](https://www.sphinx-doc.org/)
- GitHub Pages: [https://docs.github.com/en/pages](https://docs.github.com/en/pages)
- GitHub Actions: [https://docs.github.com/en/actions](https://docs.github.com/en/actions)
- ReadTheDocs Theme: [https://sphinx-rtd-theme.readthedocs.io/](https://sphinx-rtd-theme.readthedocs.io/)

---

## Summary

The HireSense documentation deployment system provides:

✅ **Automated Builds** - Every push triggers build  
✅ **Professional Deployment** - GitHub Actions → Pages  
✅ **Public Access** - Free hosting at GitHub Pages  
✅ **Version Control** - Docs tracked with code  
✅ **Zero Configuration** - Works out of the box  
✅ **Professional Theme** - ReadTheDocs styling  
✅ **API Documentation** - Auto-generated from docstrings  

**The complete deployment pipeline is production-ready!** 🚀

---

**Last Updated:** March 29, 2026  
**Status:** ✅ Production Ready
