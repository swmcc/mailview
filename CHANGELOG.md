# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-03-13

### Fixed

- README images now display on PyPI (use absolute URLs)

## [0.1.0] - 2026-03-13

### Added

- Initial release
- ASGI middleware for FastAPI and Starlette
- Email capture backend replacing real email sending
- SQLite storage (persists across dev server restarts)
- Browser UI mounted at `/_mail`
- HTML preview in sandboxed iframe
- Plaintext and source views
- Headers table display
- Attachment download and inline preview
- Delete individual or all emails
- Production safety checks (only activates in dev environments)
- Configurable mount path and database location

[Unreleased]: https://github.com/swmcc/mailview/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/swmcc/mailview/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/swmcc/mailview/releases/tag/v0.1.0
