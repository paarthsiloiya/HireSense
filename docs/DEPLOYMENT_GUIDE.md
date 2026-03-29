# HireSense Sphinx Documentation Deployment Guide

## Overview

This guide explains how the HireSense project's Sphinx documentation is automatically built and deployed to GitHub Pages using GitHub Actions.

## Workflow Structure

### GitHub Actions Workflow File
**Location:** `.github/workflows/docs.yml`

The workflow performs two main jobs:

#### 1. **Build Job**
- Runs on: `ubuntu-latest`
- Triggers on:
  - Push to `main`, `master`, or `develop` branches
  - Changes to `app/`, `docs/`, `requirements.txt`, or the workflow file itself
  - Manual workflow dispatch (GitHub UI)
  
**Build Steps:**
1. Checkout repository
2. Set up Python 3.10
3. Install system dependencies (build-essential)
4. Install Python dependencies:
   - Sphinx and plugins
   - Flask and related packages
   - spaCy language model
5. Build Sphinx documentation
6. Verify build succeeded

#### 2. **Deploy Job**
- Runs after successful build
- Only triggers on pushes to `main` or `master` branches
- Uses GitHub Pages deployment environment

**Deploy Steps:**
1. Build documentation
2. Upload artifacts to GitHub Pages
3. Deploy using GitHub's native Pages action

## Setup Requirements

### 1. GitHub Repository Configuration

Enable GitHub Pages in your repository:

```
1. Go to Settings → Pages
2. Under "Build and deployment":
   - Source: GitHub Actions
   - (The workflow will handle deployment automatically)
```

### 2. Repository Secrets (Optional)

The workflow does not require secrets for GitHub Pages deployment (native GitHub Actions integration is used).

### 3. Branch Protection Rules (Recommended)

```
1. Go to Settings → Branches
2. Add rule for main/master branch:
   - Require status checks to pass before merging
   - Select "Build and Deploy Sphinx Documentation" job
```

## Local Development

### Build Documentation Locally

```bash
# Navigate to project root
cd /path/to/HireSense

# Install dependencies
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Build documentation
sphinx-build -b html docs docs/_build/html

# Open in browser
# On Windows: start docs/_build/html/index.html
# On macOS: open docs/_build/html/index.html
# On Linux: firefox docs/_build/html/index.html
```

### Build with Warnings as Errors (CI-mode)

```bash
sphinx-build -b html -W --keep-going docs docs/_build/html
```

### Clean and Rebuild

```bash
# Remove old build
rm -rf docs/_build/

# Rebuild
sphinx-build -b html docs docs/_build/html
```

## Documentation Structure

```
docs/
├── conf.py                 # Sphinx configuration
├── index.rst              # Main documentation index
├── modules.rst            # Auto-generated module documentation
├── _build/                # Build output (generated)
│   └── html/              # Deployed to GitHub Pages
└── _static/               # Static files
```

## Accessing Deployed Documentation

Once deployed, the documentation is available at:

```
https://<github-username>.github.io/HireSense/
```

**Example:**
```
https://tanya.github.io/HireSense/
```

## Troubleshooting

### Workflow Failed

Check the GitHub Actions logs:
1. Go to repository → Actions tab
2. Click the failed workflow run
3. View detailed logs for each step

### Common Issues

#### Issue: "spaCy model download failed"
**Solution:** The workflow continues even if spaCy model fails (marked with `|| true`). Documentation will build but NLP features may show reduced functionality.

```bash
# To fix locally:
python -m spacy download en_core_web_lg
```

#### Issue: "Module import errors during Sphinx build"
**Solution:** The workflow uses a degraded import approach. If specific modules fail:

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

## Workflow Customization

### Modify Trigger Events

Edit `.github/workflows/docs.yml`:

```yaml
on:
  push:
    branches:
      - main
      - master
      - develop  # Add/remove branches as needed
    paths:
      - 'app/**'
      - 'docs/**'
```

### Change Python Version

```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.11'  # Update version
```

### Add Custom Build Steps

```yaml
- name: Custom step
  run: |
    # Your custom commands here
    echo "Building documentation..."
```

## Best Practices

### 1. **Keep Documentation Updated**
- Update docstrings whenever code changes
- Follow Sphinx/reStructuredText format
- Use consistent formatting

### 2. **Test Locally Before Pushing**
```bash
sphinx-build -b html -W docs docs/_build/html
```

### 3. **Review Pull Requests**
- GitHub Actions will build documentation for PRs
- Review build logs before merging
- Ensure no warnings/errors introduced

### 4. **Maintain Sphinx Configuration**
- Keep `docs/conf.py` updated
- Add new modules to `docs/modules.rst`
- Update theme and extensions as needed

### 5. **Use Meaningful Docstrings**
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

## Monitoring and Maintenance

### Check Workflow Status
1. Go to Actions tab in GitHub
2. View latest "Build and Deploy Sphinx Documentation" run
3. Check build logs for warnings

### Update Dependencies
```bash
# Install latest Sphinx and plugins
pip install --upgrade sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Update docs/conf.py if needed
```

### Archive Old Documentation

GitHub Pages serves the latest build. Previous versions are not archived by this workflow. To maintain version history:

1. Use explicit versioning in `docs/conf.py`
2. Create branches for release documentation
3. Configure separate Pages branches for versions (advanced)

## CI/CD Integration

### Status Badge

Add to README.md:

```markdown
[![Documentation](https://github.com/<owner>/HireSense/actions/workflows/docs.yml/badge.svg)](https://github.com/<owner>/HireSense/actions/workflows/docs.yml)
```

Replace `<owner>` with your GitHub username.

## Support and Issues

For issues with:

- **Sphinx:** Visit [Sphinx Documentation](https://www.sphinx-doc.org/)
- **GitHub Pages:** See [GitHub Pages Docs](https://docs.github.com/en/pages)
- **GitHub Actions:** Check [Actions Documentation](https://docs.github.com/en/actions)

## Summary

The HireSense documentation is now:

✅ **Automatically built** on every push to main/master  
✅ **Deployed** to GitHub Pages  
✅ **Publicly accessible** via GitHub Pages URL  
✅ **Version controlled** with source code  
✅ **Professionally formatted** with Sphinx  

All documentation changes are tracked in Git and automatically published!
