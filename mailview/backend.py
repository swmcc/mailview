"""Email capture backend for mailview.

Intercepts outgoing emails and stores them instead of sending.
"""

from __future__ import annotations

from email.message import EmailMessage, Message
from email.utils import getaddresses
from typing import TYPE_CHECKING

from mailview.models import Attachment, Email
from mailview.store import EmailStore

if TYPE_CHECKING:
    from collections.abc import Sequence


class MailviewBackend:
    """Email backend that captures emails instead of sending.

    Compatible with standard Python email patterns and async frameworks.
    """

    def __init__(self, store: EmailStore | None = None) -> None:
        """Initialize backend with optional store.

        Args:
            store: EmailStore instance. Creates default if not provided.
        """
        self.store = store or EmailStore()

    async def send(
        self,
        message: Message | EmailMessage,
        *,
        sender: str | None = None,
        recipients: Sequence[str] | None = None,
    ) -> Email:
        """Capture an email message instead of sending.

        Args:
            message: Email message to capture
            sender: Override sender (uses From header if not provided)
            recipients: Override recipients (uses To/Cc/Bcc if not provided)

        Returns:
            Captured Email object
        """
        email = self.parse_message(message, sender=sender, recipients=recipients)
        await self.store.save(email)
        return email

    def parse_message(
        self,
        message: Message | EmailMessage,
        *,
        sender: str | None = None,
        recipients: Sequence[str] | None = None,
    ) -> Email:
        """Parse email.message.Message into Email model.

        Args:
            message: Email message to parse
            sender: Override sender address
            recipients: Override recipient list

        Returns:
            Parsed Email object
        """
        # Extract sender
        from_addr = sender or message.get("From", "")

        # Extract recipients
        if recipients is not None:
            # Normalize string to list (avoid splitting chars)
            to_list = [recipients] if isinstance(recipients, str) else list(recipients)
            cc_list: list[str] = []
            bcc_list: list[str] = []
        else:
            to_list = self._parse_address_list(message.get("To", ""))
            cc_list = self._parse_address_list(message.get("Cc", ""))
            bcc_list = self._parse_address_list(message.get("Bcc", ""))

        # Extract subject
        subject = message.get("Subject", "")

        # Extract bodies and attachments
        html_body: str | None = None
        text_body: str | None = None
        attachments: list[Attachment] = []

        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                # Use get_content_disposition() for case-insensitive matching
                content_disposition = part.get_content_disposition()

                # Skip multipart containers
                if part.is_multipart():
                    continue

                # Handle attachments (both "attachment" and "inline")
                is_attachment = content_disposition == "attachment"
                is_inline = content_disposition == "inline"
                if is_attachment or is_inline:
                    attachments.append(self._parse_attachment(part))
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = part.get_content_charset() or "utf-8"
                        html_body = payload.decode(charset, errors="replace")
                elif content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        charset = part.get_content_charset() or "utf-8"
                        text_body = payload.decode(charset, errors="replace")
        else:
            # Single part message
            content_type = message.get_content_type()
            payload = message.get_payload(decode=True)
            if payload:
                charset = message.get_content_charset() or "utf-8"
                if isinstance(payload, bytes):
                    decoded = payload.decode(charset, errors="replace")
                else:
                    decoded = str(payload)

                if content_type == "text/html":
                    html_body = decoded
                else:
                    text_body = decoded

        # Extract headers (exclude standard ones we handle separately)
        excluded_headers = {"from", "to", "cc", "bcc", "subject", "content-type"}
        headers = {
            key: value
            for key, value in message.items()
            if key.lower() not in excluded_headers
        }

        return Email(
            sender=from_addr,
            to=to_list,
            cc=cc_list,
            bcc=bcc_list,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            headers=headers,
            attachments=attachments,
        )

    def _parse_address_list(self, header_value: str) -> list[str]:
        """Parse address list from header using RFC 5322 parsing.

        Args:
            header_value: Raw header value

        Returns:
            List of email addresses (with display names if present)
        """
        if not header_value:
            return []
        # Use stdlib parser to handle quoted names with commas
        # e.g., "Doe, John" <john@example.com>
        parsed = getaddresses([header_value])
        # Return formatted addresses: "Name <email>" or just "email"
        return [f"{name} <{addr}>" if name else addr for name, addr in parsed if addr]

    def _parse_attachment(self, part: Message) -> Attachment:
        """Parse attachment from message part.

        Args:
            part: Message part containing attachment

        Returns:
            Attachment object
        """
        filename = part.get_filename() or "unnamed"
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True)
        content = payload if isinstance(payload, bytes) else b""

        return Attachment(
            filename=filename,
            content_type=content_type,
            size=len(content),
            content=content,
        )


# Convenience function for simple usage
async def capture_email(
    message: Message | EmailMessage,
    *,
    store: EmailStore | None = None,
    sender: str | None = None,
    recipients: Sequence[str] | None = None,
) -> Email:
    """Capture an email message.

    Convenience function for one-off captures without creating a backend.

    Args:
        message: Email message to capture
        store: Optional EmailStore instance
        sender: Override sender address
        recipients: Override recipient list

    Returns:
        Captured Email object
    """
    backend = MailviewBackend(store=store)
    return await backend.send(message, sender=sender, recipients=recipients)
