"""Helpers for performance benchmarks."""

import asyncio

from mailview.models import Attachment, Email


def make_email(i: int, with_attachment: bool = False) -> Email:
    """Create a realistic test email."""
    return Email(
        id=f"email-{i:05d}",
        sender=f"sender{i}@example.com",
        to=[f"to{i}@example.com"],
        subject=f"Test Email #{i}",
        html_body=f"<h1>Email {i}</h1><p>Content here.</p>",
        text_body=f"Email {i}\n\nContent here.",
        attachments=[
            Attachment(
                filename="doc.pdf",
                content_type="application/pdf",
                size=1024,
                content=b"x" * 1024,
            )
        ]
        if with_attachment
        else [],
    )


def run_async(coro):
    """Run async function synchronously (for benchmark compatibility).

    Uses asyncio.Runner on Python 3.11+ for reliable loop management.
    """
    with asyncio.Runner() as runner:
        return runner.run(coro)
