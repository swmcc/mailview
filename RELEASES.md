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

- [ ] Create and push tag:
  ```bash
  git tag vX.Y.Z
  git push origin main --tags
  ```
- [ ] Build and validate package:
  ```bash
  make release.check
  ```
- [ ] (Optional) Test on TestPyPI first:
  ```bash
  make release.test
  pip install --index-url https://test.pypi.org/simple/ mailview
  ```
- [ ] Upload to PyPI:
  ```bash
  make release.publish
  ```
- [ ] Create GitHub release from tag (copy changelog section as notes)

## After Release

- [ ] Verify package on PyPI: https://pypi.org/project/mailview/
- [ ] Test install: `pip install mailview==X.Y.Z`
- [ ] Bump version in `pyproject.toml` to next dev version (e.g., `0.2.0`)
- [ ] Add new `[Unreleased]` section to CHANGELOG.md

## Version Numbering (SemVer)

While in `0.x.x` (pre-1.0):
- **Patch** (0.1.0 → 0.1.1): Bug fixes
- **Minor** (0.1.0 → 0.2.0): New features, may include breaking changes

After `1.0.0`:
- **Patch**: Bug fixes (backwards compatible)
- **Minor**: New features (backwards compatible)
- **Major**: Breaking changes
