# Contributing to HireSense

Thank you for your interest in contributing to HireSense! This document explains the preferred contribution workflow (fork → branch → pull request), branch naming conventions, how to keep your branch up to date with upstream, and gives a concrete, step-by-step example showing how to contribute two features (feature1 and feature2). The instructions aim to be friendly to beginners and include exact git commands you can copy & paste.

---

## Table of contents

- Purpose
- Before you start (prerequisites)
- Branching & naming conventions
- Step-by-step workflow (create fork, branch, change, push, open PR)
- How to make PRs for multiple features (recommended and alternate approaches)
- Keeping your branch up to date with upstream
- Working with PR feedback & updating your branch
- Git commands quick reference
- PR checklist & best practices
- Troubleshooting & help

---

## Purpose

We want contributions to be easy to review, safe to merge, and simple for contributors to manage. To achieve that, please:

- Fork the repository to your GitHub account.
- Create a descriptive branch for each feature or fix.
- Make focused, well-documented commits.
- Open a pull request from your fork/branch to the main repository.
- Keep your branch up to date with the upstream `main` (or `main` branch name used by this repo).

---

## Before you start (prerequisites)

- A GitHub account.
- Git installed locally (git >= 2.20 recommended).
- Basic familiarity with the command line (we include commands below).
- Optional but recommended: an editor you like (VS Code, etc.) and any repo-specific linters/tests configured locally.

---

## Branch naming conventions

Use clear, consistent branch names. Examples:

- feature/<short-description> — new features
  - e.g. `feature/resume-parsing-skills-extraction`
- fix/<short-description> — bug fixes
  - e.g. `fix/typo-in-parser`
- chore/<short-description> — maintenance tasks
  - e.g. `chore/update-deps`
- docs/<short-description> — documentation changes
  - e.g. `docs/add-contributing-guidelines`

Keep branch names lower-case and hyphen-separated. Include a JIRA/issue number if your project tracks issues: `feature/123-add-something`.

---

## Step-by-step: Fork → branch → PR (the recommended workflow)

1. Fork the repo on GitHub
   - Click "Fork" in the top-right of the repository page to create a copy under your account.

2. Clone your fork locally
   - Replace `<your-username>` with your GitHub username:
     ```
     git clone https://github.com/<your-username>/HireSense.git
     cd HireSense
     ```

3. Add the upstream remote (the original repo)
   ```
   git remote add upstream https://github.com/paarthsiloiya/HireSense.git
   git fetch upstream
   ```

4. Create a new branch from upstream/main
   - Always start from the latest upstream `main`.
   ```
   git checkout -b feature/short-description upstream/main
   ```

5. Work on your changes
   - Make changes, run tests, run linters.
   - Stage and commit logically grouped changes with clear commit messages:
     ```
     git add .
     git commit -m "feat(parser): add skill entity extraction"
     ```

6. Push your branch to your fork
   ```
   git push origin feature/short-description
   ```

7. Open a Pull Request (PR)
   - On GitHub, open a PR from `your-username/HireSense:feature/short-description` into `paarthsiloiya/HireSense:main`.
   - Fill in the PR title and description (see PR template section below).
   - Link the PR to issue(s) if relevant.

8. Respond to review feedback
   - Make requested changes on the same branch, commit, push — the PR will update automatically.

9. After merge
   - Delete your branch locally and on your fork if you like:
     ```
     git push origin --delete feature/short-description
     git branch -D feature/short-description
     ```

---

## Creating PRs for multiple features — recommended approach (one feature per branch/PR)

Why: Smaller, focused PRs are easier to review and land independently. If you are implementing multiple features, create separate branches and separate PRs.

Example: You want to add two features: `feature1` and `feature2`.

1. Ensure local `main` is up to date:
   ```
   git checkout main
   git fetch upstream
   git reset --hard upstream/main
   ```

2. Create branches for each feature:
   ```
   git checkout -b feature/feature1 upstream/main
   # Implement feature1
   git add .
   git commit -m "feat(feature1): implement initial version of feature1"
   git push origin feature/feature1

   # Back to main
   git checkout main
   git fetch upstream
   git reset --hard upstream/main

   # Create branch for feature2
   git checkout -b feature/feature2 upstream/main
   # Implement feature2
   git add .
   git commit -m "feat(feature2): implement initial version of feature2"
   git push origin feature/feature2
   ```

3. Open one PR per branch on GitHub:
   - PR A: `feature/feature1` → upstream `main`
   - PR B: `feature/feature2` → upstream `main`

4. Keep each branch up to date individually (see "Keeping your branch up to date" below).

Notes:
- If feature2 depends on feature1, you can either:
  - Implement feature1 first, get it merged, then branch feature2 off updated `main`; or
  - Create feature2 branch from feature1 for development, but keep feature2 branch rebased onto `main` before final PR so that PRs are easy to review and land.

---

## Alternate approach: Multiple features in a single PR (only when they are tightly related)

If two small features are tightly related and must be reviewed together, you can:

1. Create a branch named `feature/feature1-and-feature2` (or `feature/combined/<description>`).
   ```
   git checkout -b feature/feature1-and-feature2 upstream/main
   ```
2. Implement both features on that branch, commit logically grouped changes.
3. Push and open a single PR.

Caveats:
- Larger PRs are harder to review.
- If maintainers request splitting, be prepared to create separate branches/PRs.

---

## Example scenario: Contribute feature1 and feature2 with commands and keeping branches up to date

This example follows the recommended approach (two branches, two PRs). We'll also show how to keep branches up to date if upstream `main` changes while you work.

1. Setup once (fork, clone, and add upstream):
   ```
   git clone https://github.com/<your-username>/HireSense.git
   cd HireSense
   git remote add upstream https://github.com/paarthsiloiya/HireSense.git
   git fetch upstream
   ```

2. Create branch for feature1 and push:
   ```
   git checkout -b feature/feature1 upstream/main
   # Work: edit files, test locally
   git add .
   git commit -m "feat(feature1): add feature1 implementation"
   git push origin feature/feature1
   # Open PR from GitHub UI: your fork's feature/feature1 -> upstream main
   ```

3. Create branch for feature2 and push:
   ```
   git checkout main
   git fetch upstream
   git reset --hard upstream/main
   git checkout -b feature/feature2 upstream/main
   # Work: implement feature2
   git add .
   git commit -m "feat(feature2): add feature2 implementation"
   git push origin feature/feature2
   # Open PR for feature2 as well
   ```

4. If upstream `main` has changed and you need to update your branch (recommended: rebase approach below), see next section.

---

## Keeping your branch up to date with upstream/main

Two common strategies: rebase (clean history) or merge (preserve merge commits). We recommend rebase for feature branches to keep history linear.

Important: Only rebase local branches that you control and have pushed to your fork. If your branch is shared with others, coordinate before force-pushing.

Preferred (rebase):

1. Fetch upstream changes:
   ```
   git fetch upstream
   ```

2. Checkout your feature branch and rebase onto upstream/main:
   ```
   git checkout feature/feature1
   git rebase upstream/main
   ```

3. Resolve conflicts if any:
   - Edit conflicting files.
   - git add <file>
   - git rebase --continue

4. Push changes to your fork (force push required after rebase):
   ```
   git push --force-with-lease origin feature/feature1
   ```

Notes:
- Use `--force-with-lease` (safer than `--force`) to avoid overwriting others' work.
- The PR will automatically update with your pushed changes.

Alternative (merge):

1. Fetch upstream and merge:
   ```
   git fetch upstream
   git checkout feature/feature1
   git merge upstream/main
   # Resolve conflicts if any, commit
   git push origin feature/feature1
   ```

Merge keeps a merge commit in history.

---

## Updating an open PR after requested changes

1. Make changes on the same branch:
   ```
   # you are on feature/feature1
   git add .
   git commit -m "fix(feature1): address review comment about X"
   git push origin feature/feature1
   ```
2. The PR will automatically update. Add a comment describing what changed for reviewers.

---

## Resolving merge conflicts (common workflow)

If a conflict occurs during rebase or merge:

1. Git will pause and show conflicting files. Example commands:
   ```
   # after `git rebase upstream/main` or `git merge upstream/main`
   git status
   # Edit files to resolve conflicts
   git add path/to/conflicted-file
   # if rebasing:
   git rebase --continue
   # if merging:
   git commit   # if needed
   git push origin feature/...
   ```

If you want to abort the rebase/merge:
- Abort rebase:
  ```
  git rebase --abort
  ```
- Abort merge:
  ```
  git merge --abort
  ```

---

## PR title & description template (suggested)

Title:
```
feat(parser): add skill extraction from resume text
```

Description:
```
## Summary
Brief one-paragraph summary of what changes and why.

## Changes
- Added X
- Modified Y
- Removed Z

## How to test
1. Steps to reproduce before changes.
2. Steps to test this change locally.

## Related issues
- Fixes: #123
- Depends on: #122 (if applicable)

## Checklist
- [ ] I have run tests locally
- [ ] I added/updated unit tests
- [ ] I followed code style
- [ ] I updated relevant documentation
```

---

## Commit message guidelines

Use clear, concise commit messages. Optionally follow Conventional Commits:

- feat(scope): short summary
- fix(scope): short summary
- docs(scope): short summary
- chore: short summary

Add a longer description in the commit body if necessary. If the project uses a DCO (Developer Certificate of Origin), add a `Signed-off-by: Your Name <you@example.com>` line when required.

---

## PR checklist (what maintainers will look for)

- Does the change do one thing and do it well? (Prefer small, focused PRs.)
- Tests: new tests or updated tests included.
- Lint: code passes linters.
- CI: PR passes CI checks.
- Documentation: relevant docs/README updated.
- Commit messages and branch name follow guidelines.
- No sensitive data or secrets included.

---

## Git commands quick reference (most common)

- Clone your fork:
  ```
  git clone https://github.com/<your-username>/HireSense.git
  ```
- Add upstream:
  ```
  git remote add upstream https://github.com/paarthsiloiya/HireSense.git
  git fetch upstream
  ```
- Create a new branch from upstream/main:
  ```
  git checkout -b feature/desc upstream/main
  ```
- Stage & commit:
  ```
  git add .
  git commit -m "feat(scope): message"
  ```
- Push branch:
  ```
  git push origin feature/desc
  ```
- Rebase branch onto upstream/main:
  ```
  git fetch upstream
  git checkout feature/desc
  git rebase upstream/main
  git push --force-with-lease origin feature/desc
  ```
- Merge upstream into branch:
  ```
  git fetch upstream
  git checkout feature/desc
  git merge upstream/main
  git push origin feature/desc
  ```

---

## Troubleshooting & common questions

- "My push was rejected" → You probably need to pull or rebase. Use `git fetch upstream` then rebase or merge as shown above.
- "I accidentally committed to main" → Create a branch from that commit, reset main to upstream/main, and push. Ask maintainers if you need help.
- "How do I split a big change into smaller PRs?" → Create feature branches for each logical piece. Use `git cherry-pick` or `git rebase -i` to split commits.

---

## Licensing and Contributor Agreement

By contributing, you agree that your contributions will be licensed under the same license as this repository. If this repository requires a Contributor License Agreement (CLA) or sign-off, follow the instructions provided in PR checks. If `Signed-off-by` is required, sign commits like:
```
git commit -s -m "feat: example commit"
```

---

## Getting help

If you get stuck:
- Open an issue describing the problem and what you tried.
- Or join the project's communication channels (if any are listed in the README).
- Provide steps to reproduce and any error messages.

---

Thank you for helping improve HireSense. We appreciate thoughtful contributions and will work with you through reviews to get your changes merged. If anything in this guide is unclear, please open an issue titled "Contributing guide: clarification needed" and we'll update the document.