# FastAPI + Mailview Example

A simple FastAPI app demonstrating mailview email capture.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Or install mailview from local source
pip install -e ../../
pip install fastapi uvicorn
```

## Run

```bash
uvicorn app:app --reload
```

## Usage

1. Open http://localhost:8000
2. Click "Send a test email" (or any send option)
3. Click "View captured emails" to open mailview at `/_mail`

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Home page with links |
| `/send` | Send a plaintext email |
| `/send-html` | Send an HTML email |
| `/send-multipart` | Send email with HTML + plaintext |
| `/_mail` | Mailview inbox UI |

## How it works

```python
from mailview import EmailStore, MailviewBackend, MailviewMiddleware

# Shared database path ensures middleware and backend use the same data
DB_PATH = "/tmp/mailview/example.db"

# Middleware serves the UI at /_mail
app.add_middleware(MailviewMiddleware, enabled=True, db_path=DB_PATH)

# Backend captures emails using the same db_path
store = EmailStore(db_path=DB_PATH)
backend = MailviewBackend(store=store)

# Capture an email
await backend.send(msg)
```
