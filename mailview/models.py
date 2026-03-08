"""Email data models for mailview."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class Attachment:
    """Email attachment metadata and content."""

    filename: str
    content_type: str
    size: int
    content: bytes = field(repr=False)

    def to_dict(self) -> dict[str, Any]:
        """Serialize attachment to dict (without content for listings)."""
        return {
            "filename": self.filename,
            "content_type": self.content_type,
            "size": self.size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Attachment:
        """Create Attachment from dict (metadata only; content defaults to empty bytes)."""
        return cls(
            filename=data.get("filename", ""),
            content_type=data.get("content_type", ""),
            size=data.get("size", 0),
            content=b"",
        )


@dataclass
class Email:
    """Captured email message."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    subject: str = ""
    html_body: str | None = None
    text_body: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    attachments: list[Attachment] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def recipients(self) -> list[str]:
        """All recipients (to + cc + bcc)."""
        return self.to + self.cc + self.bcc

    @property
    def has_html(self) -> bool:
        """Check if email has HTML body."""
        return self.html_body is not None and len(self.html_body) > 0

    @property
    def has_text(self) -> bool:
        """Check if email has plaintext body."""
        return self.text_body is not None and len(self.text_body) > 0

    @property
    def is_multipart(self) -> bool:
        """Check if email has both HTML and plaintext."""
        return self.has_html and self.has_text

    def to_dict(self, include_bodies: bool = True) -> dict[str, Any]:
        """Serialize email to dict for JSON/storage.

        Args:
            include_bodies: Include HTML and text bodies (False for listings)
        """
        data: dict[str, Any] = {
            "id": self.id,
            "sender": self.sender,
            "to": self.to,
            "cc": self.cc,
            "bcc": self.bcc,
            "subject": self.subject,
            "headers": self.headers,
            "attachments": [a.to_dict() for a in self.attachments],
            "created_at": self.created_at.isoformat(),
            "has_html": self.has_html,
            "has_text": self.has_text,
        }
        if include_bodies:
            data["html_body"] = self.html_body
            data["text_body"] = self.text_body
        return data

    def to_json(self, include_bodies: bool = True) -> str:
        """Serialize email to JSON string."""
        return json.dumps(self.to_dict(include_bodies))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Email:
        """Create Email from dict."""
        # Parse created_at if string
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now(UTC)

        # Normalize recipient fields: always lists; accept a single string.
        def _normalize_recipients(value: Any) -> list[str]:
            if value is None:
                return []
            if isinstance(value, str):
                return [value]
            if isinstance(value, list):
                return value
            try:
                return list(value)
            except TypeError:
                return []

        to = _normalize_recipients(data.get("to"))
        cc = _normalize_recipients(data.get("cc"))
        bcc = _normalize_recipients(data.get("bcc"))

        # Normalize headers: always a dict.
        raw_headers = data.get("headers")
        if raw_headers is None:
            headers: dict[str, str] = {}
        elif isinstance(raw_headers, dict):
            headers = raw_headers
        else:
            try:
                headers = dict(raw_headers)
            except (TypeError, ValueError):
                headers = {}

        return cls(
            id=data.get("id", str(uuid.uuid4())),
            sender=data.get("sender", ""),
            to=to,
            cc=cc,
            bcc=bcc,
            subject=data.get("subject", ""),
            html_body=data.get("html_body"),
            text_body=data.get("text_body"),
            headers=headers,
            attachments=[
                Attachment.from_dict(a) for a in data.get("attachments", [])
            ],
            created_at=created_at,
        )

    @classmethod
    def from_json(cls, json_str: str) -> Email:
        """Create Email from JSON string."""
        return cls.from_dict(json.loads(json_str))
