<p align="center">
  <img src="contributing.svg" alt="Contributing to Mailview" width="800">
</p>

This document outlines how to get started.

## Development Setup

Requires [uv](https://docs.astral.sh/uv/) (fast Python package manager).

```bash
git clone https://github.com/swmcc/mailview.git
cd mailview
make local.install
```

That's it. The venv is created and deps are installed automatically.

## Make Targets

All local development commands are prefixed with `local.`:

| Command | Description |
|---------|-------------|
| `make local.install` | Create venv and install dev dependencies |
| `make local.check` | Run all checks (lint + security + tests) |
| `make local.test` | Run tests only |
| `make local.test.cov` | Run tests with coverage report |
| `make local.lint` | Run ruff linter |
| `make local.security` | Run bandit security scan |
| `make help` | Show all available targets |

All targets auto-install dependencies if the venv doesn't exist.

## Workflow

```bash
# First time setup
make local.install

# Before committing
make local.check

# Quick test run
make local.test
```

## Code Style

We use:
- **Ruff** for linting and formatting
- **Type hints** throughout
- **Docstrings** for public APIs

The linter runs automatically with `make local.check`.

## Commit Messages

Use clear, descriptive commit messages with an emoji prefix:

- 🐛 Bug fixes
- ✨ New features
- 📚 Documentation
- 🔧 Chores/refactoring
- 🧪 Tests
- 🎨 UI changes

Example: `🐛 Fix email parsing for multipart messages`

## Pull Requests

1. Fork the repo and create your branch from `main`
2. Make your changes
3. Run `make local.check` and ensure it passes
4. Update documentation if needed
5. Submit a PR with a clear description

CI will run the same checks on Python 3.11, 3.12, and 3.13.

## Reporting Bugs

Use the bug report template and include:
- Steps to reproduce
- Expected vs actual behavior
- Version info (Python, mailview, framework)

## Feature Requests

We welcome ideas! Use the feature request template and explain:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

## Code of Conduct

Be kind. Be respectful. We're all here to build something useful.

## Questions?

Open a discussion or issue - we're happy to help!
