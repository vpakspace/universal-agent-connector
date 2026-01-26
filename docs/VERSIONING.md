# Git Tags and Versioning Strategy

## Overview

Universal Agent Connector follows [Semantic Versioning 2.0.0](https://semver.org/) for all releases.

**Format:** `vMAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

## Version Format

### Release Types

**Major Version (v1.0.0, v2.0.0)**
- Breaking changes to API or behavior
- Major architectural changes
- Significant feature additions that change core functionality

**Minor Version (v1.1.0, v1.2.0)**
- New features (backward compatible)
- New database support
- New deployment options
- Significant improvements

**Patch Version (v1.0.1, v1.0.2)**
- Bug fixes
- Security patches
- Documentation updates
- Performance improvements (non-breaking)

**Pre-release (v1.1.0-alpha.1, v1.1.0-beta.1, v1.1.0-rc.1)**
- Alpha: Early testing, unstable
- Beta: Feature complete, testing
- RC (Release Candidate): Final testing before release

## Current Tags

### v1.0.0 (Latest Stable)
**Release Date:** 2026-01-26
**Type:** Major Release - Initial Public Release

Initial public release of Universal Agent Connector with full MCP and ontology support.

[See Release Notes](../RELEASE_NOTES_v1.0.0.md)

### Pre-Release Tags (if applicable)
List any alpha, beta, or RC tags used before v1.0.0

## Creating Tags

### Annotated Tags (Recommended)
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Universal Agent Connector v1.0.0 - Initial Public Release"

# Push tag to remote
git push origin v1.0.0

# Push all tags
git push origin --tags
```

### Lightweight Tags
```bash
# Create lightweight tag (not recommended for releases)
git tag v1.0.0

# Push tag
git push origin v1.0.0
```

## Tag Naming Conventions

### Release Tags
- `v1.0.0` - Stable release
- `v1.1.0-alpha.1` - Alpha pre-release
- `v1.1.0-beta.1` - Beta pre-release
- `v1.1.0-rc.1` - Release candidate

### Special Tags
- `latest` - Points to latest stable release (moved with each release)
- `stable` - Always points to most recent stable version

## Viewing Tags
```bash
# List all tags
git tag

# List tags matching pattern
git tag -l "v1.*"

# Show tag information
git show v1.0.0

# List tags with messages
git tag -n
```

## Checking Out Tags
```bash
# Checkout specific tag (detached HEAD)
git checkout v1.0.0

# Create branch from tag
git checkout -b hotfix-1.0.1 v1.0.0
```

## Deleting Tags
```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0
```

## Tag Verification (Signed Tags)

For security-critical releases, we use GPG-signed tags:
```bash
# Create signed tag
git tag -s v1.0.0 -m "Universal Agent Connector v1.0.0"

# Verify signed tag
git tag -v v1.0.0

# Push signed tag
git push origin v1.0.0
```

## Release Process

### 1. Prepare Release
- Update CHANGELOG.md
- Update version in code
- Run full test suite
- Update documentation

### 2. Create Release Branch
```bash
git checkout -b release/v1.0.0 develop
```

### 3. Finalize Release
```bash
# Make final adjustments
git add .
git commit -m "chore: prepare v1.0.0 release"

# Merge to main
git checkout main
git merge --no-ff release/v1.0.0
```

### 4. Create Tag
```bash
# Create annotated tag
git tag -a v1.0.0 -m "Universal Agent Connector v1.0.0 - Initial Public Release

Major features:
- MCP semantic routing with ontology
- Multi-database support
- Enterprise governance
- Universal Ontology Adapter
- Production deployment templates

See RELEASE_NOTES_v1.0.0.md for details."

# Push tag
git push origin v1.0.0
```

### 5. Create GitHub Release
- Go to GitHub Releases
- Click "Draft a new release"
- Select tag v1.0.0
- Copy content from RELEASE_NOTES_v1.0.0.md
- Attach any binaries/assets
- Publish release

### 6. Merge Back to Develop
```bash
git checkout develop
git merge --no-ff main
git push origin develop
```

## Version History

| Version | Date | Type | Highlights |
|---------|------|------|------------|
| v1.0.0 | 2026-01-26 | Major | Initial public release |
| (future versions will be listed here) |

## Hotfix Process

For critical bug fixes:
```bash
# Create hotfix branch from tag
git checkout -b hotfix/v1.0.1 v1.0.0

# Make fixes
git add .
git commit -m "fix: critical security issue"

# Merge to main
git checkout main
git merge --no-ff hotfix/v1.0.1

# Tag patch version
git tag -a v1.0.1 -m "Hotfix v1.0.1 - Security patch"

# Push
git push origin main v1.0.1

# Merge back to develop
git checkout develop
git merge --no-ff hotfix/v1.0.1
git push origin develop

# Delete hotfix branch
git branch -d hotfix/v1.0.1
```

## Best Practices

1. **Always use annotated tags** for releases (include `-a` flag)
2. **Use semantic versioning** consistently
3. **Write descriptive tag messages** with key changes
4. **Sign important releases** with GPG
5. **Never delete or move published tags** (creates confusion)
6. **Tag after merge to main**, not on feature branches
7. **Update CHANGELOG.md** before tagging
8. **Push tags separately** for visibility: `git push origin v1.0.0`

## Tag Automation

We use GitHub Actions to automate parts of the release process:
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          body_path: RELEASE_NOTES.md
          draft: false
          prerelease: false
```

## Questions?

For questions about versioning or releases:
- Open a [GitHub Discussion](https://github.com/cloudbadal007/universal-agent-connector/discussions)
- Contact maintainers
- See [CONTRIBUTING.md](../CONTRIBUTING.md)
