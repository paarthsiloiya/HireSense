# HireSense Documentation - Quick Reference Card

## 🚀 Quick Links

| Resource | Link |
|----------|------|
| Documentation | `https://<username>.github.io/HireSense/` |
| API Reference | Documentation URL + `/modules.html` |
| GitHub Repo | Repository main branch |
| Actions Workflow | Repository → Actions tab |
| Pages Settings | Repository → Settings → Pages |

## 📝 Common Tasks

### I Want to Update Documentation

```bash
# 1. Edit Python docstrings
vim app/models.py  # or your file

# 2. Test locally
cd docs
sphinx-build -b html . _build/html

# 3. Commit and push
git add .
git commit -m "Update documentation"
git push origin main
```

**Result:** Documentation auto-updates in ~1 minute

### I Want to Build Documentation Locally

```bash
# Install dependencies
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Build
cd docs
sphinx-build -b html . _build/html

# View
# Windows: start _build/html/index.html
# Mac: open _build/html/index.html
# Linux: firefox _build/html/index.html
```

### I Want to Clean Old Build

```bash
cd docs
rm -rf _build/
sphinx-build -b html . _build/html
```

### I Want to Trigger Workflow Manually

**Option 1: Via GitHub UI**
1. Go to Actions tab
2. Click "Build and Deploy Sphinx Documentation"
3. Click "Run workflow"

**Option 2: Push to main**
```bash
git push origin main
```

### I Want to Check Build Status

1. Go to repository → Actions tab
2. Look for "Build and Deploy Sphinx Documentation"
3. Most recent run shows status
4. Green checkmark = Success, Red X = Failed

### I Found an Error in Documentation

```bash
# 1. Find the docstring in Python code
grep -r "your error text" app/

# 2. Edit the docstring
vim app/your_file.py

# 3. Push changes
git commit -am "Fix documentation error"
git push origin main
```

## 📋 Docstring Template

Use this template for all Python docstrings:

```python
def function_name(param1: str, param2: int) -> Dict:
    """
    Brief description of what function does.
    
    Longer description if needed.
    
    :param param1: Description of param1.
    :type param1: str
    :param param2: Description of param2.
    :type param2: int
    :returns: Description of return value.
    :rtype: Dict
    :raises ValueError: When something goes wrong.
    """
    pass
```

## 🔍 Documentation Structure

```
docs/
├── index.rst              ← Main page
├── modules.rst            ← API reference (auto-updated)
├── conf.py                ← Sphinx settings
├── README.md              ← This folder overview
├── GITHUB_PAGES_SETUP.md  ← Setup instructions
├── DEPLOYMENT_GUIDE.md    ← Deployment details
├── CI_CD_PIPELINE.md      ← Pipeline documentation
└── _build/html/           ← Generated HTML (don't commit)
```

## ⚙️ Before You Deploy

**Checklist:**

- [ ] Docstrings added to all new functions
- [ ] Docstrings follow Sphinx format (`:param:`, `:returns:`, etc.)
- [ ] Build tests locally: `sphinx-build -b html docs docs/_build/html`
- [ ] No warnings/errors in build output
- [ ] Ready to push to main branch

## 🛑 Troubleshooting

### "Build Failed" on GitHub Actions

1. Click the failed workflow in Actions tab
2. Expand "Build" job
3. Read the error message carefully
4. Common issues:
   - Missing import in docstring
   - Invalid Sphinx syntax
   - Python syntax error
5. Fix locally and test before pushing

### "Documentation Not Updating"

1. Verify you pushed to `main` or `master` branch
2. Check Actions tab for successful build
3. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
4. Clear browser cache if needed
5. Wait 5-10 minutes for first deployment

### "Can't Access Documentation"

1. Verify GitHub Pages is enabled:
   - Settings → Pages
   - Source should be "GitHub Actions"
2. Repository must be public
3. Wait 5-10 minutes for first deployment
4. Check correct URL: `https://<username>.github.io/HireSense/`

### "spaCy Download Failed"

This is non-critical. Documentation still builds.

To fix locally:
```bash
python -m spacy download en_core_web_lg
```

## 📊 Workflow Status

### Check Current Status

1. GitHub repo → Actions tab
2. Look for "Build and Deploy Sphinx Documentation"
3. Latest run shows status

### What Each Status Means

| Status | Meaning | Action |
|--------|---------|--------|
| 🟢 Green | Success | Documentation live |
| 🔴 Red | Failed | Fix error, check logs |
| 🟡 Yellow | In Progress | Wait 30-50 seconds |
| ⚪ Queued | Waiting | Will start soon |

## 🎓 Learn More

For detailed information:
- [Setup Instructions](GITHUB_PAGES_SETUP.md) - Initial configuration
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - How to deploy
- [CI/CD Pipeline](CI_CD_PIPELINE.md) - Technical details
- [Sphinx Docs](https://www.sphinx-doc.org/) - Official Sphinx documentation

## 💡 Best Practices

### ✅ Do This

```python
def get_user_by_id(user_id: int) -> Optional[User]:
    """
    Retrieve user by ID.
    
    :param user_id: The user's ID.
    :type user_id: int
    :returns: User object or None if not found.
    :rtype: Optional[User]
    :raises ValueError: If user_id is negative.
    """
    pass
```

### ❌ Don't Do This

```python
def get_user_by_id(user_id):
    # Get user by id
    pass

def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user"""
    pass
```

## 🔄 Workflow Rules

| Event | Builds? | Deploys? |
|-------|---------|----------|
| Push to main | ✅ Yes | ✅ Yes |
| Push to master | ✅ Yes | ✅ Yes |
| Push to develop | ✅ Yes | ❌ No |
| Pull request | ✅ Yes | ❌ No |
| Push other branch | ❌ No | ❌ No |
| Manual trigger | ✅ Yes | ✅ Yes |

## 🎯 Quick Actions

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

## 📞 Getting Help

**Can't figure something out?**

1. Check this card again
2. Read detailed guides (links above)
3. Check GitHub Actions logs
4. Review similar docstrings in code
5. Check Sphinx documentation

**For workflow issues:**
- Go to Actions tab
- Click the failing run
- Expand relevant job step
- Read error message carefully

---

## Setup Status

- [x] Sphinx documentation configured
- [x] GitHub Actions workflow created
- [x] GitHub Pages enabled
- [x] All modules documented
- [x] Workflow tested and working
- [x] Documentation deployed
- [x] Team documentation prepared

**You're all set!** Push to main and watch your documentation deploy! 🚀

---

**Last Updated:** March 29, 2026  
**Workflow:** Production Ready ✅
