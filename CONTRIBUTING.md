# Contributing to F1 Lap Bot

Thank you for contributing! This project uses **automated semantic versioning** based on conventional commits.

## Commit Message Format

All commits **MUST** follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types and Version Bumps

| Type | Version Bump | Description | Example |
|------|--------------|-------------|---------|
| `feat` | **MINOR** (v2.1.0 → v2.2.0) | New feature | `feat: add /lap compare command` |
| `fix` | **PATCH** (v2.1.0 → v2.1.1) | Bug fix | `fix: resolve telemetry parsing error` |
| `perf` | **PATCH** (v2.1.0 → v2.1.1) | Performance improvement | `perf: optimize database queries` |
| `refactor` | **PATCH** (v2.1.0 → v2.1.1) | Code refactoring | `refactor: simplify lap validation logic` |
| `docs` | **No release** | Documentation only | `docs: update README` |
| `style` | **No release** | Code style changes | `style: format with black` |
| `test` | **No release** | Adding tests | `test: add unit tests for validation` |
| `chore` | **No release** | Maintenance | `chore: update dependencies` |
| `ci` | **No release** | CI/CD changes | `ci: add new workflow` |

### Breaking Changes (MAJOR)

For breaking changes that bump the MAJOR version (v2.1.0 → v3.0.0):

**Option 1: Add `!` after type**
```bash
git commit -m "feat!: redesign /lap command structure"
```

**Option 2: Add `BREAKING CHANGE:` in footer**
```bash
git commit -m "feat: redesign lap command structure

BREAKING CHANGE: /lap submit now requires track parameter first"
```

## Examples

### Feature (MINOR bump)
```bash
git commit -m "feat: add ELO rating system

Implements skill-based rating for drivers using ELO algorithm.
Closes #15"
```

### Bug Fix (PATCH bump)
```bash
git commit -m "fix: correct sector time calculation

Fixes issue where sector 3 times were incorrectly summed.
Closes #42"
```

### Breaking Change (MAJOR bump)
```bash
git commit -m "feat!: change API response format

BREAKING CHANGE: API now returns lap times in milliseconds instead of seconds.
Clients need to update their parsing logic.

Migration guide: multiply all time values by 1000"
```

### Documentation (No release)
```bash
git commit -m "docs: add deployment guide to README"
```

## Workflow

### 1. Create Feature Branch
```bash
git checkout -b feature/30-add-new-command
```

### 2. Make Changes
Write your code following the project structure and conventions.

### 3. Commit with Conventional Format
```bash
git commit -m "feat: add /lap compare command

Allows users to compare lap times between two drivers.
Includes head-to-head statistics and visual comparison.

Closes #30"
```

### 4. Push and Create PR
```bash
git push origin feature/30-add-new-command
gh pr create --fill
```

### 5. Merge to Main
When the PR is merged to `main`, **semantic-release automatically**:
- ✅ Analyzes all commits since last release
- ✅ Determines next version (MAJOR.MINOR.PATCH)
- ✅ Generates CHANGELOG.md
- ✅ Creates git tag
- ✅ Creates GitHub Release
- ✅ Updates VERSION file

## Version Bumping Rules

### Scenario 1: Single Feature
```
Commits: feat: add compare command
Result: v2.1.0 → v2.2.0 (MINOR)
```

### Scenario 2: Multiple Fixes
```
Commits:
  - fix: resolve parsing error
  - fix: correct time formatting
Result: v2.1.0 → v2.1.1 (PATCH)
```

### Scenario 3: Feature + Fixes
```
Commits:
  - feat: add new command
  - fix: resolve bug
  - fix: another bug
Result: v2.1.0 → v2.2.0 (MINOR - highest change wins)
```

### Scenario 4: Breaking Change
```
Commits:
  - feat!: redesign API
  - feat: add feature
  - fix: bug fix
Result: v2.1.0 → v3.0.0 (MAJOR - breaking change)
```

### Scenario 5: Only Docs/Chores
```
Commits:
  - docs: update README
  - chore: update dependencies
Result: No release created
```

## Release Process

### Automatic (Recommended)
1. Merge PR to main with conventional commits
2. Wait ~2 minutes for GitHub Actions
3. Release is automatically created

### Manual Tag (Deprecated)
The old manual tagging is still possible but **NOT recommended**:
```bash
git tag -a v2.2.0 -m "Release v2.2.0"
git push origin v2.2.0
```

## Commit Message Tips

### Good Examples ✅
```
feat: add driver comparison feature
fix: resolve telemetry connection timeout
perf: optimize database query for leaderboards
refactor: simplify validation logic
docs: add API documentation
```

### Bad Examples ❌
```
added new feature           # Missing type
Fix bug                     # Wrong capitalization
feat added compare          # Missing colon
update: change something    # Invalid type
```

## Scope (Optional)

You can add a scope to provide more context:

```
feat(commands): add /lap compare
fix(telemetry): resolve packet parsing
perf(database): optimize lap time queries
```

Common scopes:
- `commands` - Discord commands
- `telemetry` - UDP telemetry integration
- `database` - Database operations
- `api` - API endpoints
- `bot` - Bot core functionality

## Testing Your Changes

Before committing, ensure:
```bash
# Run tests (if available)
pytest tests/

# Format code
black src/ tests/

# Type checking
mypy src/
```

## Getting Help

- **Conventional Commits:** https://www.conventionalcommits.org/
- **Semantic Versioning:** https://semver.org/
- **Project Issues:** https://github.com/yannicktuerk/F1-Lap-Bot/issues

## Quick Reference Card

```
Type       │ Version  │ When to Use
───────────┼──────────┼─────────────────────────
feat       │ MINOR    │ New feature
fix        │ PATCH    │ Bug fix
perf       │ PATCH    │ Performance improvement
refactor   │ PATCH    │ Code refactoring
feat!      │ MAJOR    │ Breaking change
docs       │ -        │ Documentation only
chore      │ -        │ Maintenance
test       │ -        │ Tests only
```

---

**Remember:** Commit messages drive the release process. Write clear, descriptive commits!
