# HireSense GitHub Pages Setup Instructions

## Step-by-Step Setup

### Step 1: Enable GitHub Pages

1. Navigate to your GitHub repository
2. Go to **Settings** (gear icon)
3. In the left sidebar, click **Pages**
4. Under "Build and deployment":
   - **Source**: Select `GitHub Actions` from the dropdown
   - Leave other settings as default

**Expected Result:** You should see a message like:
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

The workflow will automatically trigger and build documentation.

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

**Example:**
```
https://tanya.github.io/HireSense/
```

## Verifying Deployment

### Check Pages Status
1. Go to **Settings** → **Pages**
2. Look for the deployment status
3. You should see recent deployment history

### Test Documentation Access
- Visit the GitHub Pages URL
- Verify all documentation pages load correctly
- Check that internal links work

## Troubleshooting Setup

### Issue: "Your site is ready to be published" but no site visible

**Solution:**
1. Wait 5-10 minutes for initial deployment
2. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Check Actions tab for build failures

### Issue: Repository is Private

**Solution:**
GitHub Pages requires public repositories for free tier:
1. Go to **Settings** → **General**
2. Scroll to "Danger Zone"
3. Click **Make this repository public**

### Issue: Workflow File Not Found

**Solution:**
1. Ensure `.github/workflows/docs.yml` exists in repository root
2. Commit and push the file:
   ```bash
   git add .github/workflows/docs.yml
   git commit -m "Add GitHub Pages deployment workflow"
   git push origin main
   ```

### Issue: Build Failures in Actions

**Check logs:**
1. Go to **Actions** tab
2. Click the failed run
3. Expand **Build** job
4. Review error messages
5. Common issues:
   - Missing `requirements.txt`
   - Python version incompatibility
   - Missing Sphinx dependencies

## Post-Setup Verification

### Verify Workflow Configuration

1. **Actions Tab:**
   - Verify "Build and Deploy Sphinx Documentation" appears
   - Check workflow run history

2. **Pages Status:**
   - Go to Settings → Pages
   - Confirm deployment source is "GitHub Actions"

3. **Documentation Access:**
   - Visit the Pages URL
   - Verify homepage loads
   - Test navigation to different sections

## Automated Future Deployments

### Trigger Points

The workflow automatically triggers on:

- **Push to main/master branches** (full deploy)
- **Changes to:**
  - `app/` directory (all Python files)
  - `docs/` directory (Sphinx files)
  - `requirements.txt`
  - `.github/workflows/docs.yml`
- **Manual trigger** via Actions tab

### No Action Required

Once set up, documentation is automatically:
- Built when code changes
- Deployed to GitHub Pages
- Publicly accessible

## Customizing Pages URL

### Custom Domain (Optional)

To use a custom domain:

1. Go to **Settings** → **Pages**
2. Under "Custom domain":
   - Enter your domain (e.g., `docs.example.com`)
   - Click "Save"
3. Update DNS records:
   - Add CNAME record pointing to `<username>.github.io`
   - Wait for DNS propagation (up to 48 hours)

**Note:** Requires domain ownership and CNAME record setup.

## Publishing Documentation Manually (Local)

If you need to build documentation locally:

```bash
# 1. Install dependencies
pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# 2. Navigate to docs directory
cd docs

# 3. Build HTML
sphinx-build -b html . _build/html

# 4. Serve locally (optional)
# Python 3.7+
python -m http.server 8000 -d _build/html

# 5. Visit http://localhost:8000
```

## Continuous Integration Checks

### Add Status Badge to README

Show workflow status in your README:

```markdown
## Documentation

[![Documentation Build](https://github.com/<username>/HireSense/actions/workflows/docs.yml/badge.svg?branch=main)](https://github.com/<username>/HireSense/actions/workflows/docs.yml)

[View Full Documentation](https://<username>.github.io/HireSense/)
```

Replace `<username>` with your GitHub username.

## Summary Checklist

- [ ] Repository set to Public
- [ ] GitHub Pages enabled with GitHub Actions source
- [ ] `.github/workflows/docs.yml` committed and pushed
- [ ] Initial workflow run triggered
- [ ] Build succeeded (green checkmark in Actions)
- [ ] Documentation accessible at GitHub Pages URL
- [ ] Pages settings show deployment history
- [ ] Documentation tested and verified

## Next Steps

1. **Create Documentation Updates:**
   ```bash
   # Make changes to app/ or docs/
   git add .
   git commit -m "Update documentation"
   git push origin main
   ```

2. **Monitor Deployments:**
   - Check Actions tab for build status
   - Review documentation at Pages URL

3. **Maintain Documentation:**
   - Update docstrings in Python files
   - Keep `docs/index.rst` and `docs/modules.rst` current
   - Test documentation builds locally before pushing

## Getting Help

- **Sphinx Issues:** [Sphinx Documentation](https://www.sphinx-doc.org/)
- **GitHub Pages:** [GitHub Pages Guide](https://docs.github.com/en/pages)
- **GitHub Actions:** [Actions Documentation](https://docs.github.com/en/actions)
- **Project Issues:** Check repository Issues tab

---

**Your HireSense documentation is now automatically deployed to GitHub Pages!** 🚀
