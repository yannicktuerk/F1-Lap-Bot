# Telemetry System Development Branch Guide

## Branch: `develop/telemetry-system`

This branch is dedicated to the complete implementation of the F1 Lap Bot telemetry system expansion.

## Overview

This branch serves as the **main integration branch** for all telemetry-related features (Issues #32-63). All feature branches should be created from and merged back into this branch.

## Branch Strategy

### Main Branch: `develop/telemetry-system`
- Base branch for all telemetry features
- Contains completed and tested features
- Regularly synced with `main` to avoid conflicts
- Will be merged to `main` when telemetry system is complete and tested

### Feature Branches

Create feature branches from `develop/telemetry-system` following this pattern:

```bash
# Phase 1 - Foundation
git checkout develop/telemetry-system
git checkout -b feature/32-telemetry-sample-vo
git checkout -b feature/33-car-setup-snapshot
git checkout -b feature/34-lap-trace-entity
git checkout -b feature/35-telemetry-repository-interface
git checkout -b feature/36-sqlite-schema
git checkout -b feature/37-sqlite-telemetry-repository

# Phase 2 - Track Reconstruction
git checkout -b feature/38-centerline-computation
git checkout -b feature/39-curvature-calculation
git checkout -b feature/40-elevation-extraction
git checkout -b feature/41-track-profile-vo
git checkout -b feature/42-reconstruct-track-usecase

# Phase 3 - Mathe-Coach
git checkout -b feature/43-ideal-lap-constructor
git checkout -b feature/44-ideal-lap-vo
git checkout -b feature/45-lap-comparator
git checkout -b feature/46-mathe-coach-feedback
git checkout -b feature/47-mathe-coach-usecase
git checkout -b feature/48-lap-coach-command

# Phase 4 - KI-Coach
git checkout -b feature/49-world-model-state
git checkout -b feature/50-world-model-action
git checkout -b feature/51-world-model-interface
git checkout -b feature/52-dp-planner
git checkout -b feature/53-optimal-lap-vo
git checkout -b feature/54-ki-coach-feedback
git checkout -b feature/55-ki-coach-usecase
git checkout -b feature/56-lap-kicoach-command

# Phase 5 - Integration
git checkout -b feature/57-session-management
git checkout -b feature/58-http-api-telemetry
git checkout -b feature/59-telemetry-ingestion

# Phase 6 - Quality
git checkout -b feature/60-domain-unit-tests
git checkout -b feature/61-integration-tests
git checkout -b feature/62-documentation
git checkout -b feature/63-db-migrations
```

## Workflow

### 1. Start New Feature

```bash
# Update develop branch
git checkout develop/telemetry-system
git pull origin develop/telemetry-system

# Create feature branch
git checkout -b feature/<issue-number>-<short-description>

# Work on feature...
```

### 2. Commit Changes

Follow conventional commit format:

```bash
git add .
git commit -m "feat(telemetry): implement TelemetrySample VO (#32)

- Add TelemetrySample dataclass with F1 25 UDP field mappings
- Implement validation for speed, gear, throttle ranges
- Add unit tests with 100% coverage

Closes #32"
```

### 3. Push Feature Branch

```bash
git push -u origin feature/<issue-number>-<short-description>
```

### 4. Create Pull Request

- **Base branch:** `develop/telemetry-system`
- **Compare branch:** `feature/<issue-number>-<short-description>`
- **Title:** Follow conventional commit format
- **Description:** 
  - Link to issue: `Closes #XX`
  - Brief description of changes
  - Testing done
  - Screenshots (if UI changes)

### 5. Review & Merge

- Get approval from reviewer
- Ensure all checks pass (tests, lint)
- Merge to `develop/telemetry-system`
- Delete feature branch

## Phase Completion

After completing each phase:

1. **Tag the phase completion:**
   ```bash
   git tag -a telemetry-phase-1-complete -m "Phase 1: Foundation complete"
   git push origin telemetry-phase-1-complete
   ```

2. **Verify phase success metrics** (see `TELEMETRY_IMPLEMENTATION_ROADMAP.md`)

3. **Update progress** in GitHub project board

## Final Merge to Main

When telemetry system is complete:

1. **Create PR to main:**
   ```bash
   # From GitHub UI:
   # Base: main
   # Compare: develop/telemetry-system
   ```

2. **PR Requirements:**
   - All 32 issues closed
   - All tests passing (≥90% domain, ≥80% application coverage)
   - Documentation complete
   - Reviewed and approved

3. **Merge strategy:** Squash merge or merge commit (decided by team)

## Sync with Main

Regularly sync `develop/telemetry-system` with `main` to avoid conflicts:

```bash
git checkout develop/telemetry-system
git fetch origin
git merge origin/main
# Resolve conflicts if any
git push origin develop/telemetry-system
```

## Continuous Integration

All feature branches must pass CI checks:
- ✅ Unit tests
- ✅ Integration tests
- ✅ Linting (eslint, flake8, etc.)
- ✅ Type checking
- ✅ Build succeeds

## Communication

- **Issue discussions:** Use GitHub issue comments
- **PR reviews:** Use GitHub PR review system
- **Blocker/questions:** Tag team members in issue comments

## Links

- **Issues:** [#32-#63](https://github.com/yannicktuerk/F1-Lap-Bot/issues?q=is%3Aissue+label%3Atelemetry)
- **Roadmap:** [TELEMETRY_IMPLEMENTATION_ROADMAP.md](../TELEMETRY_IMPLEMENTATION_ROADMAP.md)
- **Specification:** [warp_prompt_f1_lap_bot.md](../warp_prompt_f1_lap_bot.md)
- **Project Board:** [GitHub Projects](https://github.com/yannicktuerk/F1-Lap-Bot/projects)

---

**Happy coding! 🏎️💨**
