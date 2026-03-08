# Contributing to Mailview

Thanks for your interest in contributing! This document outlines how to get started.

## Development Setup

```bash
git clone https://github.com/swmcc/mailview.git
cd mailview
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## Code Style

We use:
- **Ruff** for linting and formatting
- **Type hints** throughout
- **Docstrings** for public APIs

Run before committing:
```bash
ruff check .
ruff format .
```

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
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a PR with a clear description

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
