"""Tests for API router."""

import tempfile
from pathlib import Path

import pytest
from starlette.routing import Router
from starlette.testclient import TestClient

from mailview.models import Attachment, Email
from mailview.router import MailviewRouter, create_routes
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
def router(store):
    """Create a router with test store."""
    return MailviewRouter(store=store)


@pytest.fixture
def client(router):
    """Create a test client for the router."""
    app = Router(routes=router.routes)
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def sample_email():
    """Create a sample email for testing."""
    return Email(
        id="test-email-123",
        sender="sender@example.com",
        to=["recipient@example.com"],
        subject="Test Subject",
        html_body="<p>Hello World</p>",
        text_body="Hello World",
    )


@pytest.fixture
def email_with_attachment():
    """Create an email with attachment."""
    return Email(
        id="email-with-attach",
        sender="sender@example.com",
        to=["recipient@example.com"],
        subject="With Attachment",
        html_body="<p>See attached</p>",
        attachments=[
            Attachment(
                filename="document.pdf",
                content_type="application/pdf",
                size=13,
                content=b"PDF content here",
            ),
        ],
    )


class TestListEmails:
    """Tests for GET /emails endpoint."""

    async def test_list_empty(self, client):
        """Test listing with no emails."""
        response = client.get("/_mail/api/emails")
        assert response.status_code == 200
        data = response.json()
        assert data["emails"] == []

    async def test_list_with_emails(self, client, store, sample_email):
        """Test listing with emails."""
        await store.save(sample_email)

        response = client.get("/_mail/api/emails")
        assert response.status_code == 200
        data = response.json()
        assert len(data["emails"]) == 1
        assert data["emails"][0]["id"] == "test-email-123"
        assert data["emails"][0]["subject"] == "Test Subject"

    async def test_list_excludes_bodies(self, client, store, sample_email):
        """Test that listing excludes email bodies and attachments."""
        await store.save(sample_email)

        response = client.get("/_mail/api/emails")
        data = response.json()
        assert "html_body" not in data["emails"][0]
        assert "text_body" not in data["emails"][0]
        assert "attachments" not in data["emails"][0]
        # But includes has_html/has_text flags
        assert data["emails"][0]["has_html"] is True
        assert data["emails"][0]["has_text"] is True

    async def test_list_includes_attachment_count(
        self, client, store, email_with_attachment
    ):
        """Test that listing includes attachment count."""
        await store.save(email_with_attachment)

        response = client.get("/_mail/api/emails")
        data = response.json()
        assert data["emails"][0]["attachment_count"] == 1


class TestGetEmail:
    """Tests for GET /emails/{id} endpoint."""

    async def test_get_existing(self, client, store, sample_email):
        """Test getting existing email."""
        await store.save(sample_email)

        response = client.get("/_mail/api/emails/test-email-123")
        assert response.status_code == 200
        data = response.json()
        assert data["email"]["id"] == "test-email-123"
        assert data["email"]["html_body"] == "<p>Hello World</p>"
        assert data["email"]["text_body"] == "Hello World"

    async def test_get_not_found(self, client):
        """Test getting non-existent email."""
        response = client.get("/_mail/api/emails/does-not-exist")
        assert response.status_code == 404
        assert response.json()["error"] == "Email not found"


class TestGetEmailHtml:
    """Tests for GET /emails/{id}/html endpoint."""

    async def test_get_html_body(self, client, store, sample_email):
        """Test getting HTML body."""
        await store.save(sample_email)

        response = client.get("/_mail/api/emails/test-email-123/html")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert response.text == "<p>Hello World</p>"

    async def test_get_html_no_body(self, client, store):
        """Test getting HTML when email has no HTML body."""
        email = Email(id="text-only", text_body="Plain text only")
        await store.save(email)

        response = client.get("/_mail/api/emails/text-only/html")
        assert response.status_code == 200
        assert "<p>No HTML content</p>" in response.text

    async def test_get_html_not_found(self, client):
        """Test getting HTML for non-existent email."""
        response = client.get("/_mail/api/emails/does-not-exist/html")
        assert response.status_code == 404


class TestGetAttachment:
    """Tests for GET /emails/{id}/attachments/{filename} endpoint."""

    async def test_get_attachment(self, client, store, email_with_attachment):
        """Test downloading attachment."""
        await store.save(email_with_attachment)

        url = "/_mail/api/emails/email-with-attach/attachments/document.pdf"
        response = client.get(url)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert "document.pdf" in response.headers["content-disposition"]
        assert response.content == b"PDF content here"

    async def test_get_attachment_inline(self, client, store, email_with_attachment):
        """Test inline attachment for previews."""
        await store.save(email_with_attachment)

        url = "/_mail/api/emails/email-with-attach/attachments/document.pdf?inline=1"
        response = client.get(url)
        assert response.status_code == 200
        assert "inline" in response.headers["content-disposition"]
        assert "document.pdf" in response.headers["content-disposition"]

    async def test_get_attachment_not_found(self, client, store, sample_email):
        """Test downloading non-existent attachment."""
        await store.save(sample_email)

        url = "/_mail/api/emails/test-email-123/attachments/missing.pdf"
        response = client.get(url)
        assert response.status_code == 404
        assert response.json()["error"] == "Attachment not found"

    async def test_get_attachment_email_not_found(self, client):
        """Test downloading attachment from non-existent email."""
        response = client.get("/_mail/api/emails/no-email/attachments/file.pdf")
        assert response.status_code == 404
        assert response.json()["error"] == "Email not found"


class TestDeleteEmail:
    """Tests for DELETE /emails/{id} endpoint."""

    async def test_delete_existing(self, client, store, sample_email):
        """Test deleting existing email."""
        await store.save(sample_email)

        response = client.delete("/_mail/api/emails/test-email-123")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        assert await store.get_by_id("test-email-123") is None

    async def test_delete_not_found(self, client):
        """Test deleting non-existent email."""
        response = client.delete("/_mail/api/emails/does-not-exist")
        assert response.status_code == 404
        assert response.json()["error"] == "Email not found"


class TestDeleteAllEmails:
    """Tests for DELETE /emails endpoint."""

    async def test_delete_all(self, client, store):
        """Test deleting all emails."""
        for i in range(3):
            await store.save(Email(id=f"email-{i}", subject=f"Email {i}"))

        response = client.delete("/_mail/api/emails")
        assert response.status_code == 200
        assert response.json()["deleted"] == 3

        # Verify all deleted
        assert await store.count() == 0

    async def test_delete_all_empty(self, client):
        """Test deleting all when already empty."""
        response = client.delete("/_mail/api/emails")
        assert response.status_code == 200
        assert response.json()["deleted"] == 0


class TestCreateRoutes:
    """Tests for create_routes convenience function."""

    def test_creates_routes(self):
        """Test that create_routes returns route list."""
        routes = create_routes()
        assert len(routes) == 8

    def test_creates_routes_with_store(self, store):
        """Test that create_routes accepts store."""
        routes = create_routes(store=store)
        assert len(routes) == 8


class TestMailviewRouterInit:
    """Tests for router initialization."""

    def test_creates_default_store(self):
        """Test that router creates default store if none provided."""
        router = MailviewRouter()
        assert router.store is not None

    def test_uses_provided_store(self, store):
        """Test that router uses provided store."""
        router = MailviewRouter(store=store)
        assert router.store is store


class TestIndexUI:
    """Tests for UI index endpoint."""

    def test_index_returns_html(self, client):
        """Test that index route returns HTML."""
        response = client.get("/_mail")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Mailview" in response.text

    def test_index_with_trailing_slash(self, client):
        """Test that index with trailing slash works."""
        response = client.get("/_mail/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_index_contains_required_elements(self, client):
        """Test that index contains required UI elements."""
        response = client.get("/_mail")
        html = response.text
        # Check for key UI elements
        assert "email-list" in html
        assert "refreshEmails" in html
        assert "deleteEmail" in html
        assert "/api/emails" in html

    def test_index_contains_detail_view_elements(self, client):
        """Test that index contains detail view with tabs and copy buttons."""
        response = client.get("/_mail")
        html = response.text
        # Check for detail view tabs (use visible labels, not JS tokens)
        assert "switchTab" in html
        assert "Source" in html
        assert "Headers" in html
        # Check for copy functionality
        assert "copyToClipboard" in html
        assert "copy-btn" in html
        # Check for headers table
        assert "headers-table" in html
        # Check for attachment functionality
        assert "attachments-list" in html
        assert "attachment-preview" in html
        assert "with-preview" in html
