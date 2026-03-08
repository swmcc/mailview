# Mailview

<p align="center">
  <img src="assets/logo.svg" alt="Mailview" width="800">
</p>

<p align="center">
  <strong>Capture outgoing emails during development and view them in a browser UI mounted inside your app.</strong>
</p>

<p align="center">
  No Docker. No SMTP server. No external services. Just one line of middleware.<br>
  Inspired by Ruby's <a href="https://github.com/ryanb/letter_opener">letter_opener</a>.
</p>

<p align="center">
  <a href="https://github.com/swmcc/mailview/actions/workflows/ci.yml"><img src="https://github.com/swmcc/mailview/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/swmcc/mailview/actions/workflows/codeql.yml"><img src="https://github.com/swmcc/mailview/actions/workflows/codeql.yml/badge.svg" alt="CodeQL"></a>
  <a href="https://pypi.org/project/mailview/"><img src="https://img.shields.io/pypi/v/mailview" alt="PyPI"></a>
  <a href="https://pypi.org/project/mailview/"><img src="https://img.shields.io/pypi/pyversions/mailview" alt="Python"></a>
  <a href="https://codecov.io/gh/swmcc/mailview"><img src="https://codecov.io/gh/swmcc/mailview/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://github.com/swmcc/mailview/blob/main/LICENSE"><img src="https://img.shields.io/github/license/swmcc/mailview" alt="License"></a>
</p>

## Installation

```bash
pip install mailview
```

## Quick Start

```python
from fastapi import FastAPI
from mailview import MailviewMiddleware

app = FastAPI()
app.add_middleware(MailviewMiddleware)
```

That's it. Visit `/_mail` in your browser to see captured emails.

## Features

- **Zero config** - add middleware, visit `/_mail`, done
- **Persistent storage** - emails survive dev server restarts (SQLite in temp dir)
- **Full email support** - HTML, plaintext, multipart, attachments
- **Sandboxed preview** - HTML emails render in an iframe without CSS bleed
- **Dev-only by default** - refuses to activate in production environments
- **Self-contained** - no external assets, works fully offline

## How It Works

Mailview provides drop-in email backends that intercept outgoing emails instead of sending them:

```python
# FastAPI-Mail
from mailview.backends import MailviewBackend
from fastapi_mail import FastMail, ConnectionConfig

config = ConnectionConfig(
    MAIL_BACKEND=MailviewBackend,
    # ... other config
)

# Or with any SMTP-based library, point it at Mailview's capture backend
```

Captured emails are stored in SQLite at `/tmp/mailview/mailview.db` and served through the `/_mail` UI.

## Browser UI

Navigate to `/_mail` to see:

- **Inbox** - list of captured emails with sender, recipients, subject, timestamp
- **HTML preview** - rendered email in a sandboxed iframe
- **Plaintext** - raw text version
- **Source** - raw email headers and body
- **Attachments** - download any attached files

Clear all emails with the delete button or `DELETE /_mail/api/emails`.

## Configuration

Mailview works with zero configuration, but you can customise if needed:

```python
app.add_middleware(
    MailviewMiddleware,
    mount_path="/_mail",        # Change the UI path (default: /_mail)
    db_path="/custom/path.db",  # Custom SQLite location (default: /tmp/mailview/mailview.db)
    enabled=True,               # Force enable/disable (default: auto-detect dev environment)
)
```

## Production Safety

Mailview **will not activate** unless it detects a development environment. It checks for:

- `DEBUG=true` or `DEBUG=1` environment variable
- `MAILVIEW_ENABLED=true` to explicitly enable
- Framework-specific debug flags (FastAPI's `debug=True`, etc.)

To be extra safe, don't include `mailview` in your production dependencies.

## Framework Support

| Framework | Status |
|-----------|--------|
| FastAPI | ✅ Supported |
| Starlette | ✅ Supported |
| Django | 🔜 Planned |
| Flask | 🔜 Planned |

## API Endpoints

The UI is powered by a simple JSON API:

| Method | Path | Description |
|--------|------|-------------|
| GET | `/_mail/api/emails` | List all captured emails |
| GET | `/_mail/api/emails/{id}` | Get a single email |
| GET | `/_mail/api/emails/{id}/html` | Get HTML body |
| GET | `/_mail/api/emails/{id}/attachments/{filename}` | Download attachment |
| DELETE | `/_mail/api/emails` | Clear all emails |
| DELETE | `/_mail/api/emails/{id}` | Delete a single email |

## Development

```bash
git clone https://github.com/swmcc/mailview.git
cd mailview
make local.install
make local.check
```

See [CONTRIBUTING.md](.github/CONTRIBUTING.md) for full development workflow.

## License

MIT
