"""Mailview - Zero-config email interceptor for Python ASGI apps."""

from mailview.backend import MailviewBackend, capture_email
from mailview.env import (
    is_dev_environment,
    is_mailview_enabled,
    is_production_environment,
)
from mailview.middleware import MailviewMiddleware
from mailview.models import Attachment, Email
from mailview.paths import normalize_mount_path
from mailview.router import MailviewRouter, create_routes
from mailview.store import EmailStore

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Email",
    "Attachment",
    "EmailStore",
    "MailviewBackend",
    "MailviewMiddleware",
    "MailviewRouter",
    "capture_email",
    "create_routes",
    "is_dev_environment",
    "is_mailview_enabled",
    "is_production_environment",
    "normalize_mount_path",
]
