"""Mailview - Zero-config email interceptor for Python ASGI apps."""

from mailview.backend import MailviewBackend, capture_email
from mailview.models import Attachment, Email
from mailview.store import EmailStore

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Email",
    "Attachment",
    "EmailStore",
    "MailviewBackend",
    "capture_email",
]
