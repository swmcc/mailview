"""Tests for email capture backend."""

import tempfile
from email.message import EmailMessage
from pathlib import Path

import pytest

from mailview.backend import MailviewBackend, capture_email
from mailview.models import Email
from mailview.store import EmailStore


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


@pytest.fixture
def store(temp_db_path):
    """Create a store with temporary database."""
    return EmailStore(db_path=temp_db_path)


@pytest.fixture
def backend(store):
    """Create a backend with test store."""
    return MailviewBackend(store=store)


class TestMailviewBackendInit:
    """Tests for backend initialization."""

    def test_creates_default_store(self):
        """Test that backend creates default store if none provided."""
        backend = MailviewBackend()
        assert backend.store is not None

    def test_uses_provided_store(self, store):
        """Test that backend uses provided store."""
        backend = MailviewBackend(store=store)
        assert backend.store is store


class TestParseMessage:
    """Tests for parsing email messages."""

    def test_parse_simple_text_email(self, backend):
        """Test parsing a simple plaintext email."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Test Subject"
        msg.set_content("Hello, World!")

        email = backend.parse_message(msg)

        assert email.sender == "sender@example.com"
        assert email.to == ["recipient@example.com"]
        assert email.subject == "Test Subject"
        assert email.text_body == "Hello, World!\n"
        assert email.html_body is None

    def test_parse_html_email(self, backend):
        """Test parsing HTML-only email."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "HTML Email"
        msg.set_content("<p>Hello, World!</p>", subtype="html")

        email = backend.parse_message(msg)

        assert email.html_body == "<p>Hello, World!</p>\n"
        assert email.text_body is None

    def test_parse_multipart_email(self, backend):
        """Test parsing multipart email with both HTML and text."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Multipart Email"
        msg.set_content("Plain text version")
        msg.add_alternative("<p>HTML version</p>", subtype="html")

        email = backend.parse_message(msg)

        assert email.text_body == "Plain text version\n"
        assert email.html_body == "<p>HTML version</p>\n"

    def test_parse_multiple_recipients(self, backend):
        """Test parsing email with multiple recipients."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "one@example.com, two@example.com"
        msg["Cc"] = "cc@example.com"
        msg["Bcc"] = "bcc1@example.com, bcc2@example.com"
        msg["Subject"] = "Multi-recipient"
        msg.set_content("Hello")

        email = backend.parse_message(msg)

        assert email.to == ["one@example.com", "two@example.com"]
        assert email.cc == ["cc@example.com"]
        assert email.bcc == ["bcc1@example.com", "bcc2@example.com"]

    def test_parse_with_attachment(self, backend):
        """Test parsing email with attachment."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "With Attachment"
        msg.set_content("See attached file")
        msg.add_attachment(
            b"file content here",
            maintype="application",
            subtype="octet-stream",
            filename="test.bin",
        )

        email = backend.parse_message(msg)

        assert email.text_body == "See attached file\n"
        assert len(email.attachments) == 1
        assert email.attachments[0].filename == "test.bin"
        assert email.attachments[0].content == b"file content here"
        assert email.attachments[0].size == 17

    def test_parse_with_multiple_attachments(self, backend):
        """Test parsing email with multiple attachments."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Multiple Attachments"
        msg.set_content("Files attached")
        msg.add_attachment(
            b"text content", maintype="text", subtype="plain", filename="doc.txt"
        )
        msg.add_attachment(
            b"image data", maintype="image", subtype="png", filename="image.png"
        )

        email = backend.parse_message(msg)

        assert len(email.attachments) == 2
        assert email.attachments[0].filename == "doc.txt"
        assert email.attachments[1].filename == "image.png"

    def test_parse_extracts_headers(self, backend):
        """Test that custom headers are extracted."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Headers Test"
        msg["X-Custom-Header"] = "custom value"
        msg["X-Priority"] = "1"
        msg.set_content("Body")

        email = backend.parse_message(msg)

        assert "X-Custom-Header" in email.headers
        assert email.headers["X-Custom-Header"] == "custom value"
        assert email.headers["X-Priority"] == "1"
        # Standard headers should be excluded
        assert "From" not in email.headers
        assert "To" not in email.headers
        assert "Subject" not in email.headers

    def test_parse_with_sender_override(self, backend):
        """Test that sender can be overridden."""
        msg = EmailMessage()
        msg["From"] = "original@example.com"
        msg["To"] = "recipient@example.com"
        msg.set_content("Body")

        email = backend.parse_message(msg, sender="override@example.com")

        assert email.sender == "override@example.com"

    def test_parse_with_recipients_override(self, backend):
        """Test that recipients can be overridden."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "original@example.com"
        msg["Cc"] = "cc@example.com"
        msg.set_content("Body")

        email = backend.parse_message(msg, recipients=["override@example.com"])

        assert email.to == ["override@example.com"]
        assert email.cc == []  # Cleared when recipients overridden
        assert email.bcc == []


class TestSend:
    """Tests for sending (capturing) emails."""

    async def test_send_stores_email(self, backend, store):
        """Test that send stores the email."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Stored Email"
        msg.set_content("This should be stored")

        email = await backend.send(msg)

        assert email.id is not None
        stored = await store.get_by_id(email.id)
        assert stored is not None
        assert stored.subject == "Stored Email"

    async def test_send_returns_email(self, backend):
        """Test that send returns the captured email."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg.set_content("Body")

        email = await backend.send(msg)

        assert isinstance(email, Email)
        assert email.sender == "sender@example.com"

    async def test_send_with_overrides(self, backend, store):
        """Test send with sender and recipient overrides."""
        msg = EmailMessage()
        msg["From"] = "original@example.com"
        msg["To"] = "original-to@example.com"
        msg.set_content("Body")

        email = await backend.send(
            msg,
            sender="override-sender@example.com",
            recipients=["override-to@example.com"],
        )

        assert email.sender == "override-sender@example.com"
        assert email.to == ["override-to@example.com"]


class TestCaptureEmailFunction:
    """Tests for the convenience capture_email function."""

    async def test_capture_email_basic(self, store):
        """Test basic email capture."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Convenience Function"
        msg.set_content("Test body")

        email = await capture_email(msg, store=store)

        assert email.subject == "Convenience Function"
        stored = await store.get_by_id(email.id)
        assert stored is not None

    async def test_capture_email_with_overrides(self, store):
        """Test capture with overrides."""
        msg = EmailMessage()
        msg["From"] = "original@example.com"
        msg["To"] = "original@example.com"
        msg.set_content("Body")

        email = await capture_email(
            msg,
            store=store,
            sender="new-sender@example.com",
            recipients=["new-recipient@example.com"],
        )

        assert email.sender == "new-sender@example.com"
        assert email.to == ["new-recipient@example.com"]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_parse_empty_recipients(self, backend):
        """Test parsing with no recipients."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg.set_content("No recipients")

        email = backend.parse_message(msg)

        assert email.to == []
        assert email.cc == []
        assert email.bcc == []

    def test_parse_no_subject(self, backend):
        """Test parsing with no subject."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg.set_content("No subject")

        email = backend.parse_message(msg)

        assert email.subject == ""

    def test_parse_no_body(self, backend):
        """Test parsing message with no body."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Empty"

        email = backend.parse_message(msg)

        assert email.text_body is None
        assert email.html_body is None

    def test_parse_attachment_no_filename(self, backend):
        """Test parsing attachment without filename."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg.set_content("Body")
        msg.add_attachment(b"data", maintype="application", subtype="octet-stream")

        email = backend.parse_message(msg)

        assert len(email.attachments) == 1
        assert email.attachments[0].filename == "unnamed"

    def test_parse_recipients_override_empty_list(self, backend):
        """Test that empty list override clears recipients."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "original@example.com"
        msg.set_content("Body")

        email = backend.parse_message(msg, recipients=[])

        assert email.to == []

    def test_parse_recipients_override_string(self, backend):
        """Test that string recipient is normalized to list."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "original@example.com"
        msg.set_content("Body")

        email = backend.parse_message(msg, recipients="single@example.com")

        assert email.to == ["single@example.com"]


class TestPayloadEdgeCases:
    """Tests for edge cases with email payloads."""

    def test_parse_multipart_with_none_payload(self, backend):
        """Test parsing multipart where a part has None payload."""
        from email import message_from_string

        # Create a malformed multipart message with an empty part
        raw = """\
From: sender@example.com
To: recipient@example.com
Subject: Empty Part
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain

Text body
--boundary123
Content-Type: text/html

--boundary123--"""

        msg = message_from_string(raw)
        email = backend.parse_message(msg)

        # Should handle gracefully - text body should be extracted
        assert "Text body" in (email.text_body or "")
        # HTML part has empty payload, should not crash
        assert email.html_body is None or email.html_body == ""

    def test_parse_single_part_with_str_payload(self, backend):
        """Test single-part message where payload is already a string."""
        from email.message import Message

        # Create a Message (not EmailMessage) with a string payload
        msg = Message()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "String Payload"
        msg["Content-Type"] = "text/plain; charset=utf-8"
        # Set payload as string without encoding
        msg.set_payload("This is already a string")

        email = backend.parse_message(msg)

        # Should handle string payload gracefully
        assert email.text_body == "This is already a string"

    def test_parse_single_part_html_with_str_payload(self, backend):
        """Test single-part HTML message where payload is already a string."""
        from email.message import Message

        msg = Message()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "HTML String Payload"
        msg["Content-Type"] = "text/html; charset=utf-8"
        msg.set_payload("<p>HTML as string</p>")

        email = backend.parse_message(msg)

        assert email.html_body == "<p>HTML as string</p>"
        assert email.text_body is None

    def test_parse_single_part_non_bytes_payload(self, backend):
        """Test single-part message with non-bytes payload via mocking."""
        from unittest.mock import MagicMock

        # Create a mock message that returns a string from get_payload(decode=True)
        mock_msg = MagicMock()
        mock_msg.get.side_effect = lambda key, default="": {
            "From": "sender@example.com",
            "To": "recipient@example.com",
            "Subject": "Mock Message",
        }.get(key, default)
        mock_msg.is_multipart.return_value = False
        mock_msg.get_content_type.return_value = "text/plain"
        mock_msg.get_payload.return_value = "String payload directly"  # Not bytes
        mock_msg.get_content_charset.return_value = "utf-8"
        mock_msg.items.return_value = []

        email = backend.parse_message(mock_msg)

        # Should convert string payload using str()
        assert email.text_body == "String payload directly"

    def test_parse_multipart_non_bytes_html_payload(self, backend):
        """Test multipart message where HTML part has non-bytes payload."""
        from unittest.mock import MagicMock

        # Create mock parts
        text_part = MagicMock()
        text_part.is_multipart.return_value = False
        text_part.get_content_type.return_value = "text/plain"
        text_part.get_content_disposition.return_value = None
        text_part.get_payload.return_value = b"Plain text"
        text_part.get_content_charset.return_value = "utf-8"

        html_part = MagicMock()
        html_part.is_multipart.return_value = False
        html_part.get_content_type.return_value = "text/html"
        html_part.get_content_disposition.return_value = None
        html_part.get_payload.return_value = "HTML as string"  # Not bytes!
        html_part.get_content_charset.return_value = "utf-8"

        # Create mock message
        mock_msg = MagicMock()
        mock_msg.get.side_effect = lambda key, default="": {
            "From": "sender@example.com",
            "To": "recipient@example.com",
            "Subject": "Mock Multipart",
        }.get(key, default)
        mock_msg.is_multipart.return_value = True
        mock_msg.walk.return_value = [mock_msg, text_part, html_part]
        mock_msg.items.return_value = []

        email = backend.parse_message(mock_msg)

        # Text part should be decoded from bytes
        assert email.text_body == "Plain text"
        # HTML part with string payload should be skipped (isinstance check fails)
        assert email.html_body is None

    def test_parse_multipart_non_bytes_text_payload(self, backend):
        """Test multipart message where text part has non-bytes payload."""
        from unittest.mock import MagicMock

        # Create mock text part with non-bytes payload
        text_part = MagicMock()
        text_part.is_multipart.return_value = False
        text_part.get_content_type.return_value = "text/plain"
        text_part.get_content_disposition.return_value = None
        text_part.get_payload.return_value = "String not bytes"  # Not bytes!
        text_part.get_content_charset.return_value = "utf-8"

        # Create mock message
        mock_msg = MagicMock()
        mock_msg.get.side_effect = lambda key, default="": {
            "From": "sender@example.com",
            "To": "recipient@example.com",
            "Subject": "Mock Multipart Text",
        }.get(key, default)
        mock_msg.is_multipart.return_value = True
        mock_msg.walk.return_value = [mock_msg, text_part]
        mock_msg.items.return_value = []

        email = backend.parse_message(mock_msg)

        # Text part with string payload should be skipped
        assert email.text_body is None


class TestLegacyMessage:
    """Tests for legacy email.message.Message support."""

    def test_parse_legacy_message(self, backend):
        """Test parsing a legacy Message built from string."""
        from email import message_from_string

        raw = """\
From: sender@example.com
To: recipient@example.com
Subject: Legacy Message
Content-Type: text/plain; charset="utf-8"

This is the body."""

        msg = message_from_string(raw)
        email = backend.parse_message(msg)

        assert email.sender == "sender@example.com"
        assert email.to == ["recipient@example.com"]
        assert email.subject == "Legacy Message"
        assert "This is the body." in email.text_body

    def test_parse_legacy_multipart(self, backend):
        """Test parsing a legacy multipart Message."""
        from email import message_from_string

        raw = """\
From: sender@example.com
To: recipient@example.com
Subject: Multipart Legacy
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

Plain text body
--boundary123
Content-Type: text/html; charset="utf-8"

<p>HTML body</p>
--boundary123--"""

        msg = message_from_string(raw)
        email = backend.parse_message(msg)

        assert email.sender == "sender@example.com"
        assert "Plain text body" in email.text_body
        assert "<p>HTML body</p>" in email.html_body
