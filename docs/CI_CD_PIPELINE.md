# HireSense Documentation CI/CD Pipeline

## Pipeline Overview

This document describes the complete CI/CD pipeline for building and deploying HireSense Sphinx documentation to GitHub Pages.

## Architecture

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

## Workflow Details

### 1. Trigger Events

The workflow is triggered on:

**Push Events:**
```yaml
on:
  push:
    branches:
      - main
      - master
      - develop
    paths:
      - 'app/**'
      - 'docs/**'
      - 'requirements.txt'
      - '.github/workflows/docs.yml'
```

**Pull Request Events:**
```yaml
on:
  pull_request:
    branches:
      - main
      - master
      - develop
    paths:
      - 'app/**'
      - 'docs/**'
      - 'requirements.txt'
```

**Manual Trigger:**
```yaml
workflow_dispatch:
```

### 2. Build Job

**Configuration:**
- **Runner:** `ubuntu-latest` (Ubuntu 22.04)
- **Runs On:** Every trigger event

**Steps in Order:**

#### Step 1: Checkout Repository
```bash
actions/checkout@v3
```
- Clones the repository
- Fetches all history (`fetch-depth: 0`)
- Prepares workspace

#### Step 2: Python Setup
```bash
python-version: '3.10'
cache: 'pip'
```
- Installs Python 3.10
- Enables pip caching for faster builds
- Reduces dependency download time

#### Step 3: System Dependencies
```bash
sudo apt-get install -y build-essential
```
- Installs C compiler and headers
- Required for psycopg2 (PostgreSQL driver)
- Enables native package compilation

#### Step 4: Python Dependencies
```bash
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
pip install -r requirements.txt
```
- Sphinx 9.1.0+ (latest)
- ReadTheDocs theme (professional styling)
- AutodocTypehints (improved type hints)
- All project requirements

#### Step 5: Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```
- Downloads English language model
- Continues on error (documentation still works)
- Required for NLP documentation

#### Step 6: Build Documentation
```bash
cd docs
sphinx-build -b html -W --keep-going . _build/html
```
- `-b html`: Build HTML output
- `-W`: Treat warnings as errors
- `--keep-going`: Continue on errors (logs all issues)
- Output: `docs/_build/html/`

#### Step 7: Verify Build
```bash
ls -la docs/_build/html/
```
- Confirms HTML output exists
- Lists generated files
- Validates build success

### 3. Deploy Job

**Configuration:**
- **Runs After:** Successful build
- **Only On:** Pushes to main/master
- **Environment:** `github-pages`

**Grant Permissions:**
```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

**Steps:**

#### Step 1: Checkout & Setup
- Checkout repository
- Setup Python environment
- Install dependencies (same as build)

#### Step 2: Build Documentation
```bash
sphinx-build -b html . _build/html
```

#### Step 3: Upload to Pages
```bash
actions/upload-pages-artifact@v2
with:
  path: docs/_build/html
```
- Uploads HTML artifacts
- Prepares for deployment

#### Step 4: Deploy
```bash
actions/deploy-pages@v2
```
- Publishes to GitHub Pages
- Updates live website
- Sets deployment URL

## File Structure Generated

```
docs/
├── _build/
│   └── html/
│       ├── index.html          (Main page)
│       ├── modules.html        (API reference)
│       ├── app/
│       │   ├── __init__.html
│       │   ├── admin.html
│       │   ├── auth.html
│       │   ├── employee.html
│       │   ├── manager.html
│       │   ├── models.html
│       │   ├── views.html
│       │   └── services/
│       │       ├── document_parser.html
│       │       ├── learning_path_service.html
│       │       ├── nlp_manager.html
│       │       ├── project_service.html
│       │       ├── resume_service.html
│       │       └── skill_service.html
│       ├── _static/            (CSS, JavaScript)
│       ├── _sources/           (Source files)
│       ├── objects.inv         (Inventory)
│       └── ...
└── (other source files)
```

## Environment Variables

The workflow uses these environment variables implicitly:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PYTHONUNBUFFERED` | `1` | Unbuffered Python output |
| `PIP_CACHE_DIR` | `/root/.cache/pip` | Pip cache location |
| `SPHINX_VERSION` | Latest | Sphinx version |

Custom environment variables can be added in workflow:

```yaml
env:
  PYTHON_VERSION: '3.10'
  SPHINX_BUILD_OPTS: '-W --keep-going'
```

## Caching Strategy

### Pip Cache
```yaml
cache: 'pip'
```

**Benefits:**
- Speeds up dependency installation
- Reduces GitHub bandwidth usage
- Caches across workflow runs

**Cache Key:** `pip-${{ hashFiles('**/requirements.txt') }}`

**Restore Key:** `pip-`

### Build Artifacts

Built documentation is temporarily stored in GitHub Actions artifacts:

```yaml
uses: actions/upload-pages-artifact@v2
with:
  path: docs/_build/html
  retention-days: 1
```

**Note:** Artifacts are automatically cleaned up after deployment.

## Error Handling

### Build Failures

The workflow includes error handling:

```yaml
continue-on-error: true  # For spaCy model download
```

**Behavior:**
- Build continues even if spaCy fails
- Documentation generated with reduced NLP features
- Warnings logged for review

### Deployment Failures

If deployment fails:

1. Check GitHub Actions logs
2. Verify Pages is enabled
3. Check permissions
4. Retry the workflow

**Manual retry:**
- Go to Actions tab
- Click failed workflow
- Click "Re-run failed jobs"

## Security Considerations

### Permissions Scope

The workflow uses minimal required permissions:

```yaml
permissions:
  contents: read          # Read repository
  pages: write            # Write to Pages
  id-token: write         # OIDC token (trusted publish)
```

### Public Repository Requirement

GitHub Pages free tier requires public repositories.

**For private repositories:**
- Upgrade to GitHub Pro/Enterprise
- Use alternative hosting (ReadTheDocs, etc.)

### No Secrets Required

This workflow doesn't require authentication secrets:
- GitHub Actions → GitHub Pages uses trusted authentication
- No deploy keys or tokens needed
- No credentials stored

## Monitoring and Logging

### View Workflow Logs

1. **GitHub Actions Tab:**
   - Repo → Actions → Select workflow
   - Click specific run
   - Expand job steps
   - View detailed logs

2. **Log Examples:**
   ```
   ✓ Checkout repository (3s)
   ✓ Set up Python (5s)
   ✓ Install dependencies (15s)
   ✓ Build documentation (8s)
   ✓ Deploy to Pages (2s)
   ```

### Check Build Status

**Status Badge:**
```markdown
[![Doc Status](https://github.com/<owner>/HireSense/actions/workflows/docs.yml/badge.svg)](https://github.com/<owner>/HireSense/actions/workflows/docs.yml)
```

**Alternatives:**
- Check Actions tab
- Configure branch protection status

### Email Notifications

GitHub automatically sends email on:
- Workflow success
- Workflow failure (configurable in settings)

**Configure in Settings:**
- Go to Settings → Notifications
- Enable/disable workflow notifications

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

## Troubleshooting Guide

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

### Documentation Not Updating

**Cause:** Deploy job skipped (not main branch)

**Solution:**
- Push to main/master branch
- Or manually trigger workflow

**Check:**
- Verify branch name in workflow
- Confirm push target

### Pages URL Shows "404 Not Found"

**Cause:** Pages not enabled or first deployment

**Solution:**
1. Wait 5-10 minutes
2. Check Settings → Pages
3. Verify GitHub Actions source
4. Hard refresh browser

## Advanced Configuration

### Custom Sphinx Options

Edit `.github/workflows/docs.yml`:

```yaml
- name: Build documentation
  run: |
    cd docs
    sphinx-build -b html \
      -W --keep-going \
      -D language=en \
      . _build/html
```

### Multiple Branches

Deploy different docs for different branches:

```yaml
on:
  push:
    branches:
      - main      # Production docs
      - develop   # Beta docs
      - 'v*'      # Version docs
```

### Custom Domain Setup

In Pages settings:
```
Custom domain: docs.yoursite.com
```

Then add DNS CNAME:
```
docs CNAME <username>.github.io
```

### Send to Slack

Add notification:

```yaml
- name: Notify Slack
  if: failure()
  run: |
    curl -X POST ${{ secrets.SLACK_WEBHOOK }} \
      -d '{"text":"Docs build failed"}'
```

## Best Practices

### 1. Docstring Standards
```python
def function(param: type) -> return_type:
    """
    Brief description.
    
    :param param: Description.
    :type param: type
    :returns: Description.
    :rtype: return_type
    """
```

### 2. Test Locally Before Push
```bash
sphinx-build -b html -W docs docs/_build/html
```

### 3. Review Build Logs
- Check Actions tab after push
- Fix warnings immediately
- Keep build clean

### 4. Keep Dependencies Updated
```bash
pip install --upgrade sphinx sphinx-rtd-theme
```

### 5. Document All Changes
- Update docstrings
- Add to API docs
- Run local build

## Maintenance Schedule

### Weekly
- Check Actions tab
- Verify documentation updates
- Monitor build times

### Monthly
- Update dependencies
- Review Sphinx configuration
- Audit documentation coverage

### Quarterly
- Upgrade Python version
- Update GitHub Actions versions
- Review security settings

## Production Checklist

- [x] Workflow file created (`.github/workflows/docs.yml`)
- [x] GitHub Pages enabled with Actions source
- [x] Sphinx configured (`docs/conf.py`)
- [x] Documentation structure created
- [x] Docstrings added to all modules
- [x] Local build tested
- [x] First workflow run successful
- [x] Documentation live and accessible
- [x] Status badge added to README
- [x] Team notified of docs URL

## Summary

The HireSense documentation pipeline provides:

✅ **Automated Builds** - Every push triggers build  
✅ **Professional Deployment** - GitHub Actions → Pages  
✅ **Public Access** - Free hosting at GitHub Pages  
✅ **Version Control** - Docs tracked with code  
✅ **Zero Configuration** - Works out of the box  
✅ **Professional Theme** - ReadTheDocs styling  
✅ **API Documentation** - Auto-generated from docstrings  

**The complete CI/CD pipeline is now production-ready!** 🚀
