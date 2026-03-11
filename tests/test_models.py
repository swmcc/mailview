"""Tests for email data models."""

import json

from mailview.models import Attachment, Email


class TestAttachment:
    """Tests for Attachment model."""

    def test_create_attachment(self):
        """Test basic attachment creation."""
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
            size=1024,
            content=b"test content",
        )
        assert attachment.filename == "test.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size == 1024
        assert attachment.content == b"test content"

    def test_attachment_to_dict(self):
        """Test attachment serialization (without content)."""
        attachment = Attachment(
            filename="image.png",
            content_type="image/png",
            size=2048,
            content=b"binary data",
        )
        data = attachment.to_dict()
        assert data == {
            "filename": "image.png",
            "content_type": "image/png",
            "size": 2048,
        }
        # Content should not be in dict
        assert "content" not in data

    def test_attachment_from_dict(self):
        """Test attachment deserialization from dict."""
        data = {
            "filename": "doc.pdf",
            "content_type": "application/pdf",
            "size": 512,
        }
        attachment = Attachment.from_dict(data)
        assert attachment.filename == "doc.pdf"
        assert attachment.content_type == "application/pdf"
        assert attachment.size == 512
        assert attachment.content == b""

    def test_attachment_from_dict_minimal(self):
        """Test attachment deserialization with minimal data."""
        attachment = Attachment.from_dict({})
        assert attachment.filename == ""
        assert attachment.content_type == ""
        assert attachment.size == 0
        assert attachment.content == b""


class TestEmail:
    """Tests for Email model."""

    def test_create_email_defaults(self):
        """Test email creation with defaults."""
        email = Email()
        assert email.id is not None
        assert len(email.id) == 36  # UUID format
        assert email.sender == ""
        assert email.to == []
        assert email.cc == []
        assert email.bcc == []
        assert email.subject == ""
        assert email.html_body is None
        assert email.text_body is None
        assert email.headers == {}
        assert email.attachments == []
        assert email.created_at is not None

    def test_create_email_with_values(self):
        """Test email creation with provided values."""
        email = Email(
            id="test-123",
            sender="from@example.com",
            to=["to@example.com"],
            cc=["cc@example.com"],
            bcc=["bcc@example.com"],
            subject="Test Subject",
            html_body="<p>Hello</p>",
            text_body="Hello",
            headers={"X-Custom": "value"},
        )
        assert email.id == "test-123"
        assert email.sender == "from@example.com"
        assert email.to == ["to@example.com"]
        assert email.cc == ["cc@example.com"]
        assert email.bcc == ["bcc@example.com"]
        assert email.subject == "Test Subject"
        assert email.html_body == "<p>Hello</p>"
        assert email.text_body == "Hello"
        assert email.headers == {"X-Custom": "value"}

    def test_recipients_property(self):
        """Test recipients combines to, cc, bcc."""
        email = Email(
            to=["a@test.com", "b@test.com"],
            cc=["c@test.com"],
            bcc=["d@test.com"],
        )
        assert email.recipients == [
            "a@test.com",
            "b@test.com",
            "c@test.com",
            "d@test.com",
        ]

    def test_has_html_true(self):
        """Test has_html with HTML body."""
        email = Email(html_body="<p>Content</p>")
        assert email.has_html is True

    def test_has_html_false_none(self):
        """Test has_html with None."""
        email = Email(html_body=None)
        assert email.has_html is False

    def test_has_html_false_empty(self):
        """Test has_html with empty string."""
        email = Email(html_body="")
        assert email.has_html is False

    def test_has_text_true(self):
        """Test has_text with text body."""
        email = Email(text_body="Plain text")
        assert email.has_text is True

    def test_has_text_false_none(self):
        """Test has_text with None."""
        email = Email(text_body=None)
        assert email.has_text is False

    def test_has_text_false_empty(self):
        """Test has_text with empty string."""
        email = Email(text_body="")
        assert email.has_text is False

    def test_is_multipart_true(self):
        """Test is_multipart with both bodies."""
        email = Email(html_body="<p>HTML</p>", text_body="Text")
        assert email.is_multipart is True

    def test_is_multipart_false_html_only(self):
        """Test is_multipart with HTML only."""
        email = Email(html_body="<p>HTML</p>")
        assert email.is_multipart is False

    def test_is_multipart_false_text_only(self):
        """Test is_multipart with text only."""
        email = Email(text_body="Text")
        assert email.is_multipart is False


class TestEmailSerialization:
    """Tests for Email serialization."""

    def test_to_dict_full(self):
        """Test full serialization."""
        email = Email(
            id="test-id",
            sender="from@test.com",
            to=["to@test.com"],
            subject="Subject",
            html_body="<p>HTML</p>",
            text_body="Text",
        )
        data = email.to_dict()
        assert data["id"] == "test-id"
        assert data["sender"] == "from@test.com"
        assert data["to"] == ["to@test.com"]
        assert data["subject"] == "Subject"
        assert data["html_body"] == "<p>HTML</p>"
        assert data["text_body"] == "Text"
        assert data["has_html"] is True
        assert data["has_text"] is True
        assert "created_at" in data

    def test_to_dict_without_bodies(self):
        """Test serialization without bodies (for listings)."""
        email = Email(
            id="test-id",
            html_body="<p>HTML</p>",
            text_body="Text",
        )
        data = email.to_dict(include_bodies=False)
        assert "html_body" not in data
        assert "text_body" not in data
        assert data["has_html"] is True
        assert data["has_text"] is True

    def test_to_dict_with_attachments(self):
        """Test serialization with attachments."""
        email = Email(
            attachments=[
                Attachment(
                    filename="test.txt",
                    content_type="text/plain",
                    size=100,
                    content=b"test",
                )
            ]
        )
        data = email.to_dict()
        assert len(data["attachments"]) == 1
        assert data["attachments"][0]["filename"] == "test.txt"

    def test_to_json(self):
        """Test JSON serialization."""
        email = Email(id="json-test", subject="JSON Test")
        json_str = email.to_json()
        parsed = json.loads(json_str)
        assert parsed["id"] == "json-test"
        assert parsed["subject"] == "JSON Test"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "from-dict",
            "sender": "test@example.com",
            "to": ["recipient@example.com"],
            "subject": "From Dict",
            "html_body": "<p>Body</p>",
            "created_at": "2026-01-15T10:30:00+00:00",
        }
        email = Email.from_dict(data)
        assert email.id == "from-dict"
        assert email.sender == "test@example.com"
        assert email.to == ["recipient@example.com"]
        assert email.subject == "From Dict"
        assert email.html_body == "<p>Body</p>"
        assert email.created_at.year == 2026

    def test_from_dict_minimal(self):
        """Test deserialization with minimal data."""
        email = Email.from_dict({})
        assert email.id is not None
        assert email.sender == ""
        assert email.to == []

    def test_from_json(self):
        """Test deserialization from JSON."""
        json_str = '{"id": "json-id", "subject": "From JSON"}'
        email = Email.from_json(json_str)
        assert email.id == "json-id"
        assert email.subject == "From JSON"

    def test_roundtrip_serialization(self):
        """Test serialize then deserialize preserves data."""
        original = Email(
            id="roundtrip",
            sender="sender@test.com",
            to=["to@test.com"],
            cc=["cc@test.com"],
            subject="Roundtrip Test",
            html_body="<p>HTML</p>",
            text_body="Text",
            headers={"X-Test": "value"},
        )
        json_str = original.to_json()
        restored = Email.from_json(json_str)

        assert restored.id == original.id
        assert restored.sender == original.sender
        assert restored.to == original.to
        assert restored.cc == original.cc
        assert restored.subject == original.subject
        assert restored.html_body == original.html_body
        assert restored.text_body == original.text_body
        assert restored.headers == original.headers

    def test_roundtrip_serialization_with_attachments(self):
        """Test serialize then deserialize preserves attachment metadata."""
        original = Email(
            id="roundtrip-attachments",
            subject="Attachment Roundtrip",
            attachments=[
                Attachment(
                    filename="report.pdf",
                    content_type="application/pdf",
                    size=4096,
                    content=b"binary content",
                )
            ],
        )
        json_str = original.to_json()
        restored = Email.from_json(json_str)

        assert len(restored.attachments) == 1
        assert restored.attachments[0].filename == "report.pdf"
        assert restored.attachments[0].content_type == "application/pdf"
        assert restored.attachments[0].size == 4096
        # Content is not serialized; restored attachment has empty content
        assert restored.attachments[0].content == b""

    def test_from_dict_with_attachments(self):
        """Test deserialization from dict containing attachment metadata."""
        data = {
            "id": "with-attachments",
            "subject": "Has Attachments",
            "attachments": [
                {"filename": "a.txt", "content_type": "text/plain", "size": 10},
                {"filename": "b.png", "content_type": "image/png", "size": 200},
            ],
        }
        email = Email.from_dict(data)
        assert len(email.attachments) == 2
        assert email.attachments[0].filename == "a.txt"
        assert email.attachments[1].filename == "b.png"
        assert email.attachments[1].size == 200


class TestEdgeCases:
    """Tests for edge cases and robustness."""

    def test_from_dict_created_at_none(self):
        """Test from_dict with explicitly None created_at."""
        data = {"id": "test", "created_at": None}
        email = Email.from_dict(data)
        assert email.created_at is not None  # Should default to now

    def test_from_dict_recipients_as_string(self):
        """Test from_dict normalizes single string recipient to list."""
        data = {"to": "single@example.com", "cc": "cc@example.com"}
        email = Email.from_dict(data)
        assert email.to == ["single@example.com"]
        assert email.cc == ["cc@example.com"]

    def test_from_dict_recipients_invalid_type(self):
        """Test from_dict handles non-iterable recipient gracefully."""
        data = {"to": 12345, "cc": object()}  # Invalid types
        email = Email.from_dict(data)
        # Should return empty list for non-iterable types
        assert email.to == []
        assert email.cc == []

    def test_from_dict_recipients_as_tuple(self):
        """Test from_dict handles tuple recipients."""
        data = {"to": ("a@test.com", "b@test.com")}
        email = Email.from_dict(data)
        assert email.to == ["a@test.com", "b@test.com"]

    def test_from_dict_headers_invalid_type(self):
        """Test from_dict handles invalid headers gracefully."""
        data = {"headers": "not a dict"}
        email = Email.from_dict(data)
        assert email.headers == {}

    def test_from_dict_headers_as_list_of_tuples(self):
        """Test from_dict converts list of tuples to dict."""
        data = {"headers": [("X-Key", "value"), ("X-Other", "other")]}
        email = Email.from_dict(data)
        assert email.headers == {"X-Key": "value", "X-Other": "other"}

    def test_from_dict_headers_unconvertible(self):
        """Test from_dict handles unconvertible headers."""
        data = {"headers": 12345}  # Can't convert int to dict
        email = Email.from_dict(data)
        assert email.headers == {}

    def test_from_dict_datetime_with_z_suffix(self):
        """Test parsing ISO datetime with Z suffix (common in JavaScript)."""
        data = {"created_at": "2026-01-15T10:30:00Z"}
        email = Email.from_dict(data)
        assert email.created_at.year == 2026
        assert email.created_at.month == 1
        assert email.created_at.day == 15
        assert email.created_at.tzinfo is not None

    def test_from_dict_datetime_naive_gets_utc(self):
        """Test that naive datetime strings get UTC timezone."""
        data = {"created_at": "2026-01-15T10:30:00"}
        email = Email.from_dict(data)
        assert email.created_at.tzinfo is not None

    def test_attachment_default_content(self):
        """Test Attachment can be created without explicit content."""
        attachment = Attachment(
            filename="metadata-only.pdf",
            content_type="application/pdf",
            size=1024,
        )
        assert attachment.content == b""
        assert attachment.filename == "metadata-only.pdf"
