"""Tests for SQLite storage layer."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from mailview.models import Attachment, Email
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
def sample_email():
    """Create a sample email for testing."""
    return Email(
        id="test-email-123",
        sender="sender@example.com",
        to=["to@example.com"],
        cc=["cc@example.com"],
        subject="Test Subject",
        html_body="<p>Hello World</p>",
        text_body="Hello World",
        headers={"X-Custom": "value"},
    )


@pytest.fixture
def email_with_attachment():
    """Create an email with attachment."""
    return Email(
        id="email-with-attach",
        sender="sender@example.com",
        to=["to@example.com"],
        subject="With Attachment",
        html_body="<p>See attached</p>",
        attachments=[
            Attachment(
                filename="test.txt",
                content_type="text/plain",
                size=13,
                content=b"Hello, World!",
            ),
            Attachment(
                filename="image.png",
                content_type="image/png",
                size=100,
                content=b"fake png data",
            ),
        ],
    )


class TestEmailStoreInit:
    """Tests for store initialization."""

    async def test_creates_directory(self, temp_db_path):
        """Test that store creates directory if needed."""
        nested_path = str(Path(temp_db_path).parent / "nested" / "dir" / "test.db")
        store = EmailStore(db_path=nested_path)
        await store._ensure_initialized()
        assert Path(nested_path).parent.exists()

    async def test_creates_tables(self, store, temp_db_path):
        """Test that tables are created on init."""
        await store._ensure_initialized()
        assert Path(temp_db_path).exists()


class TestEmailStoreSave:
    """Tests for saving emails."""

    async def test_save_email(self, store, sample_email):
        """Test saving a basic email."""
        await store.save(sample_email)
        count = await store.count()
        assert count == 1

    async def test_save_multiple_emails(self, store):
        """Test saving multiple emails."""
        for i in range(5):
            email = Email(id=f"email-{i}", subject=f"Email {i}")
            await store.save(email)
        count = await store.count()
        assert count == 5

    async def test_save_email_with_attachments(self, store, email_with_attachment):
        """Test saving email with attachments."""
        await store.save(email_with_attachment)
        retrieved = await store.get_by_id(email_with_attachment.id)
        assert len(retrieved.attachments) == 2

    async def test_save_replaces_existing(self, store, sample_email):
        """Test that saving with same ID replaces."""
        await store.save(sample_email)
        sample_email.subject = "Updated Subject"
        await store.save(sample_email)

        count = await store.count()
        assert count == 1

        retrieved = await store.get_by_id(sample_email.id)
        assert retrieved.subject == "Updated Subject"


class TestEmailStoreGetAll:
    """Tests for getting all emails."""

    async def test_get_all_empty(self, store):
        """Test get_all on empty store."""
        emails = await store.get_all()
        assert emails == []

    async def test_get_all_returns_emails(self, store, sample_email):
        """Test get_all returns saved emails."""
        await store.save(sample_email)
        emails = await store.get_all()
        assert len(emails) == 1
        assert emails[0].id == sample_email.id

    async def test_get_all_ordered_by_created_at(self, store):
        """Test emails are ordered newest first."""
        from datetime import UTC, datetime

        old_email = Email(
            id="old",
            subject="Old",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        new_email = Email(
            id="new",
            subject="New",
            created_at=datetime(2026, 6, 1, tzinfo=UTC),
        )
        await store.save(old_email)
        await store.save(new_email)

        emails = await store.get_all()
        assert emails[0].id == "new"
        assert emails[1].id == "old"


class TestEmailStoreGetById:
    """Tests for getting single email."""

    async def test_get_by_id_found(self, store, sample_email):
        """Test getting existing email."""
        await store.save(sample_email)
        retrieved = await store.get_by_id(sample_email.id)

        assert retrieved is not None
        assert retrieved.id == sample_email.id
        assert retrieved.sender == sample_email.sender
        assert retrieved.to == sample_email.to
        assert retrieved.subject == sample_email.subject
        assert retrieved.html_body == sample_email.html_body
        assert retrieved.text_body == sample_email.text_body
        # Verify created_at round-trips as datetime, not string
        assert isinstance(retrieved.created_at, datetime)
        assert retrieved.created_at.tzinfo is not None

    async def test_get_by_id_not_found(self, store):
        """Test getting non-existent email."""
        retrieved = await store.get_by_id("does-not-exist")
        assert retrieved is None

    async def test_get_by_id_includes_attachments(self, store, email_with_attachment):
        """Test that get_by_id includes attachment content."""
        await store.save(email_with_attachment)
        retrieved = await store.get_by_id(email_with_attachment.id)

        assert len(retrieved.attachments) == 2
        assert retrieved.attachments[0].filename == "test.txt"
        assert retrieved.attachments[0].content == b"Hello, World!"


class TestEmailStoreGetAttachment:
    """Tests for getting attachments."""

    async def test_get_attachment_found(self, store, email_with_attachment):
        """Test getting existing attachment."""
        await store.save(email_with_attachment)
        attachment = await store.get_attachment(email_with_attachment.id, "test.txt")

        assert attachment is not None
        assert attachment.filename == "test.txt"
        assert attachment.content_type == "text/plain"
        assert attachment.content == b"Hello, World!"

    async def test_get_attachment_not_found(self, store, email_with_attachment):
        """Test getting non-existent attachment."""
        await store.save(email_with_attachment)
        attachment = await store.get_attachment(
            email_with_attachment.id, "nonexistent.txt"
        )
        assert attachment is None

    async def test_get_attachment_wrong_email(self, store, email_with_attachment):
        """Test getting attachment with wrong email ID."""
        await store.save(email_with_attachment)
        attachment = await store.get_attachment("wrong-id", "test.txt")
        assert attachment is None


class TestEmailStoreDelete:
    """Tests for deleting emails."""

    async def test_delete_existing(self, store, sample_email):
        """Test deleting existing email."""
        await store.save(sample_email)
        result = await store.delete(sample_email.id)

        assert result is True
        count = await store.count()
        assert count == 0

    async def test_delete_non_existing(self, store):
        """Test deleting non-existent email."""
        result = await store.delete("does-not-exist")
        assert result is False

    async def test_delete_removes_attachments(self, store, email_with_attachment):
        """Test that deleting email removes attachments."""
        await store.save(email_with_attachment)
        await store.delete(email_with_attachment.id)

        attachment = await store.get_attachment(email_with_attachment.id, "test.txt")
        assert attachment is None


class TestEmailStoreDeleteAll:
    """Tests for clearing all emails."""

    async def test_delete_all_empty(self, store):
        """Test delete_all on empty store."""
        count = await store.delete_all()
        assert count == 0

    async def test_delete_all_with_emails(self, store):
        """Test delete_all removes all emails."""
        for i in range(3):
            await store.save(Email(id=f"email-{i}"))

        count = await store.delete_all()
        assert count == 3

        remaining = await store.count()
        assert remaining == 0


class TestEmailStoreCount:
    """Tests for counting emails."""

    async def test_count_empty(self, store):
        """Test count on empty store."""
        count = await store.count()
        assert count == 0

    async def test_count_with_emails(self, store):
        """Test count with emails."""
        for i in range(7):
            await store.save(Email(id=f"email-{i}"))
        count = await store.count()
        assert count == 7
