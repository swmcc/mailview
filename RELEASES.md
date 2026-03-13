# Release Checklist

Personal checklist for releasing new versions of mailview.

## Before Release

- [ ] All PRs for this release are merged to `main`
- [ ] `git checkout main && git pull`
- [ ] All tests pass: `make local.check`
- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`:
  - [ ] Move items from `[Unreleased]` to new version section
  - [ ] Add release date
  - [ ] Add comparison link at bottom of file
- [ ] Commit: `git commit -am "Release vX.Y.Z"`

## Release

Push the tag - GitHub Actions handles the rest:

```bash
git tag vX.Y.Z
git push origin main --tags
```

This triggers `.github/workflows/release.yml` which:
1. Runs tests
2. Builds the package
3. Publishes to PyPI (via Trusted Publishers)
4. Creates a GitHub Release with release notes

## After Release

- [ ] Check GitHub Actions: https://github.com/swmcc/mailview/actions
- [ ] Verify package on PyPI: https://pypi.org/project/mailview/
- [ ] Test install: `pip install mailview==X.Y.Z`
- [ ] Bump version in `pyproject.toml` to next dev version (e.g., `0.2.0`)
- [ ] Add new `[Unreleased]` section to CHANGELOG.md

## Manual Release (fallback)

If GitHub Actions fails, use the Makefile targets:

```bash
make release.check    # Build and validate
make release.publish  # Upload to PyPI (requires ~/.pypirc)
```

## Version Numbering (SemVer)

While in `0.x.x` (pre-1.0):
- **Patch** (0.1.0 → 0.1.1): Bug fixes
- **Minor** (0.1.0 → 0.2.0): New features, may include breaking changes

After `1.0.0`:
- **Patch**: Bug fixes (backwards compatible)
- **Minor**: New features (backwards compatible)
- **Major**: Breaking changes

## First-Time Setup (PyPI Trusted Publishers)

1. Go to https://pypi.org/manage/account/publishing/
2. Add pending publisher:
   - Owner: `swmcc`
   - Repository: `mailview`
   - Workflow: `release.yml`
   - Environment: `pypi`
3. Create GitHub environment:
   - Go to repo Settings → Environments
   - Create environment named `pypi`
