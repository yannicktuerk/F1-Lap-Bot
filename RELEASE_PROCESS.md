# Release Process

This document describes how to create a new release for F1 Lap Bot using semantic versioning and automated GitHub Actions.

## Overview

The F1 Lap Bot uses **semantic versioning** (MAJOR.MINOR.PATCH) and automated release workflows triggered by git tags.

## Release Workflow

### 1. Version Number Strategy

Follow [semantic versioning](https://semver.org/):
- **MAJOR** (v3.0.0): Breaking changes, incompatible API changes
- **MINOR** (v2.1.0): New features, backward-compatible
- **PATCH** (v2.0.1): Bug fixes, backward-compatible

### 2. Creating a Release

#### Step 1: Ensure Code is Ready
```bash
# Make sure you're on main branch
git checkout main
git pull origin main

# Verify tests pass (if configured)
pytest tests/

# Ensure clean working directory
git status
```

#### Step 2: Create and Push Tag
```bash
# Create a signed tag with semantic version
git tag -a v2.1.0 -m "Release v2.1.0: Semantic versioning implementation"

# Push the tag to trigger the release workflow
git push origin v2.1.0
```

#### Step 3: GitHub Actions Workflow
The workflow (`.github/workflows/release.yml`) automatically:
1. ✅ Checks out the code
2. ✅ Sets up Python environment
3. ✅ Extracts version from tag
4. ✅ Creates VERSION file
5. ✅ Installs dependencies
6. ✅ Runs tests (if available)
7. ✅ Generates changelog from commits
8. ✅ Creates GitHub Release
9. ✅ Triggers deployment (optional)

#### Step 4: Verify Release
1. Go to GitHub repository → Releases
2. Verify the new release appears
3. Check release notes are generated
4. Verify VERSION file is attached

### 3. Version Display

The bot displays version in two places:

#### On Startup (Console)
```
🏎️  F1 Lap Time Bot v2.1.0

🚀 Starting F1 Lap Time Bot with Telemetry API...
```

#### Via Discord Command
```
/lap version
```
Shows:
- Current version
- Semantic version breakdown (MAJOR.MINOR.PATCH)
- Links to GitHub repository and issues
- Development mode indicator (if applicable)

### 4. Version Source Priority

The bot determines version from (in order):
1. **BOT_VERSION** environment variable (deployment)
2. **VERSION** file in project root (CI/CD generated)
3. **"development"** fallback (local development)

### 5. Deployment Integration

#### Setting Version in Environment
```bash
# For production deployment
export BOT_VERSION=v2.1.0

# Or in .env file (not committed)
BOT_VERSION=v2.1.0
```

#### Docker Deployment
```dockerfile
# In Dockerfile, pass version as build arg
ARG BOT_VERSION
ENV BOT_VERSION=${BOT_VERSION}

# Build with version
docker build --build-arg BOT_VERSION=v2.1.0 -t f1-lap-bot:v2.1.0 .
```

### 6. Changelog Management

#### Option A: Automated from Commits
The workflow automatically generates changelog from git commits between tags.

**Best Practice:** Write clear commit messages:
```bash
git commit -m "feat: Add semantic versioning system"
git commit -m "fix: Resolve telemetry parsing issue"
git commit -m "docs: Update README with version info"
```

#### Option B: Manual Changelog in README
Add version section to README.md:
```markdown
### Version 2.1.0 - 2025-11-13
#### ✨ New Features
- Semantic versioning with git tags
- Automated GitHub releases
- `/lap version` command

#### 🐛 Bug Fixes
- Fixed version display on startup
```

The workflow will extract this section if present.

### 7. Hotfix Releases

For urgent bug fixes:
```bash
# Create hotfix branch from main
git checkout -b hotfix/critical-bug main

# Fix the bug
git commit -m "fix: Critical bug in lap submission"

# Merge back to main
git checkout main
git merge hotfix/critical-bug

# Create patch release
git tag -a v2.0.2 -m "Hotfix: Critical bug in lap submission"
git push origin v2.0.2
```

### 8. Pre-release Versions

For testing before official release:
```bash
# Create pre-release tag
git tag -a v2.1.0-rc1 -m "Release candidate 1 for v2.1.0"
git push origin v2.1.0-rc1
```

Mark as pre-release in GitHub:
- Workflow creates release as draft
- Manually mark as "pre-release" on GitHub

### 9. Rollback Process

If a release has issues:
```bash
# Delete local tag
git tag -d v2.1.0

# Delete remote tag
git push origin :refs/tags/v2.1.0

# Delete release on GitHub (manual)
# Go to Releases → Edit → Delete Release

# Fix issues and create new tag
git tag -a v2.1.1 -m "Fix issues from v2.1.0"
git push origin v2.1.1
```

## Quick Reference

### Create Release
```bash
git tag -a v2.1.0 -m "Release v2.1.0: <description>"
git push origin v2.1.0
```

### List All Tags
```bash
git tag -l
```

### View Tag Details
```bash
git show v2.1.0
```

### Delete Tag
```bash
git tag -d v2.1.0
git push origin :refs/tags/v2.1.0
```

## Troubleshooting

### Workflow Doesn't Trigger
- Verify tag matches pattern `v*.*.*`
- Check GitHub Actions permissions (Settings → Actions → General)
- Ensure workflow file is on main branch

### Version Not Updating
- Check VERSION file is generated
- Verify BOT_VERSION environment variable
- Restart bot after deployment

### Release Creation Fails
- Check GitHub token permissions
- Verify GITHUB_TOKEN secret exists
- Review workflow logs in Actions tab

## Best Practices

1. ✅ Always test before tagging
2. ✅ Write descriptive release notes
3. ✅ Follow semantic versioning strictly
4. ✅ Keep changelog up to date
5. ✅ Tag from main branch only
6. ✅ Use signed tags for security
7. ✅ Never force-push tags
8. ✅ Document breaking changes clearly

## Resources

- [Semantic Versioning](https://semver.org/)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
