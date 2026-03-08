"""Mailview - Zero-config email interceptor for Python ASGI apps."""

__version__ = "0.1.0"

from mailview.models import Attachment, Email

__all__ = ["__version__", "Email", "Attachment"]
