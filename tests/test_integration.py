"""Integration tests for mailview with real ASGI apps.

Tests the full workflow: middleware → backend → store → API → UI
"""

import tempfile
from email.message import EmailMessage
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from mailview import MailviewBackend, MailviewMiddleware
from mailview.store import EmailStore


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


# -----------------------------------------------------------------------------
# FastAPI Integration Tests
# -----------------------------------------------------------------------------


class TestFastAPIIntegration:
    """Integration tests with FastAPI."""

    @pytest.fixture
    def fastapi_app(self, temp_db_path):
        """Create a FastAPI app with mailview middleware."""
        app = FastAPI()
        store = EmailStore(db_path=temp_db_path)
        backend = MailviewBackend(store=store)

        @app.get("/")
        async def home():
            return {"status": "ok"}

        @app.get("/send")
        async def send_email():
            msg = EmailMessage()
            msg["From"] = "sender@example.com"
            msg["To"] = "recipient@example.com"
            msg["Subject"] = "Integration Test Email"
            msg.set_content("Hello from integration test!")
            email = await backend.send(msg)
            return {"id": email.id, "subject": email.subject}

        @app.get("/send-html")
        async def send_html():
            msg = EmailMessage()
            msg["From"] = "sender@example.com"
            msg["To"] = "recipient@example.com"
            msg["Subject"] = "HTML Integration Test"
            msg.set_content("Plain text fallback")
            msg.add_alternative("<h1>Hello HTML!</h1>", subtype="html")
            email = await backend.send(msg)
            return {"id": email.id}

        @app.get("/send-with-attachment")
        async def send_with_attachment():
            msg = EmailMessage()
            msg["From"] = "sender@example.com"
            msg["To"] = "recipient@example.com"
            msg["Subject"] = "Email with Attachment"
            msg.set_content("See attached file")
            msg.add_attachment(
                b"test file content",
                maintype="application",
                subtype="octet-stream",
                filename="test.bin",
            )
            email = await backend.send(msg)
            return {"id": email.id}

        wrapped = MailviewMiddleware(app, enabled=True, db_path=temp_db_path)
        return wrapped

    @pytest.fixture
    async def client(self, fastapi_app):
        """Create async HTTP client for the app."""
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_full_workflow(self, client):
        """Test complete email capture and retrieval workflow."""
        # Given: App is running
        response = await client.get("/")
        assert response.status_code == 200

        # When: Send an email
        response = await client.get("/send")
        assert response.status_code == 200
        email_id = response.json()["id"]

        # Then: Email appears in API
        response = await client.get("/_mail/api/emails")
        assert response.status_code == 200
        emails = response.json()["emails"]
        assert len(emails) == 1
        assert emails[0]["id"] == email_id
        assert emails[0]["subject"] == "Integration Test Email"

        # And: Can retrieve single email
        response = await client.get(f"/_mail/api/emails/{email_id}")
        assert response.status_code == 200
        email = response.json()["email"]
        assert email["text_body"] == "Hello from integration test!\n"

        # And: UI is served
        response = await client.get("/_mail")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Mailview" in response.text

        # When: Delete the email
        response = await client.delete(f"/_mail/api/emails/{email_id}")
        assert response.status_code == 200

        # Then: Email is gone
        response = await client.get("/_mail/api/emails")
        assert response.json()["emails"] == []

    async def test_html_email(self, client):
        """Test HTML email with multipart alternative."""
        # Send HTML email
        response = await client.get("/send-html")
        email_id = response.json()["id"]

        # Verify both text and HTML bodies
        response = await client.get(f"/_mail/api/emails/{email_id}")
        email = response.json()["email"]
        assert email["text_body"] == "Plain text fallback\n"
        assert "<h1>Hello HTML!</h1>" in email["html_body"]

        # Verify HTML endpoint
        response = await client.get(f"/_mail/api/emails/{email_id}/html")
        assert response.status_code == 200
        assert "<h1>Hello HTML!</h1>" in response.text

    async def test_email_with_attachment(self, client):
        """Test email with attachment."""
        # Send email with attachment
        response = await client.get("/send-with-attachment")
        email_id = response.json()["id"]

        # Verify attachment in email details
        response = await client.get(f"/_mail/api/emails/{email_id}")
        email = response.json()["email"]
        assert len(email["attachments"]) == 1
        assert email["attachments"][0]["filename"] == "test.bin"

        # Download attachment
        response = await client.get(
            f"/_mail/api/emails/{email_id}/attachments/test.bin"
        )
        assert response.status_code == 200
        assert response.content == b"test file content"

    async def test_delete_all_emails(self, client):
        """Test bulk delete."""
        # Send multiple emails
        await client.get("/send")
        await client.get("/send")
        await client.get("/send")

        response = await client.get("/_mail/api/emails")
        assert len(response.json()["emails"]) == 3

        # Delete all
        response = await client.delete("/_mail/api/emails")
        assert response.status_code == 200
        assert response.json()["deleted"] == 3

        # Verify empty
        response = await client.get("/_mail/api/emails")
        assert response.json()["emails"] == []


# -----------------------------------------------------------------------------
# Starlette Integration Tests
# -----------------------------------------------------------------------------


class TestStarletteIntegration:
    """Integration tests with plain Starlette."""

    @pytest.fixture
    def starlette_app(self, temp_db_path):
        """Create a Starlette app with mailview middleware."""
        store = EmailStore(db_path=temp_db_path)
        backend = MailviewBackend(store=store)

        async def home(request):
            return JSONResponse({"status": "ok"})

        async def send_email(request):
            msg = EmailMessage()
            msg["From"] = "starlette@example.com"
            msg["To"] = "recipient@example.com"
            msg["Subject"] = "Starlette Test Email"
            msg.set_content("Hello from Starlette!")
            email = await backend.send(msg)
            return JSONResponse({"id": email.id})

        app = Starlette(
            routes=[
                Route("/", home),
                Route("/send", send_email),
            ]
        )

        return MailviewMiddleware(app, enabled=True, db_path=temp_db_path)

    @pytest.fixture
    async def client(self, starlette_app):
        """Create async HTTP client for the app."""
        transport = ASGITransport(app=starlette_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_full_workflow(self, client):
        """Test complete workflow with Starlette."""
        # Send email
        response = await client.get("/send")
        assert response.status_code == 200
        email_id = response.json()["id"]

        # Verify in API
        response = await client.get("/_mail/api/emails")
        emails = response.json()["emails"]
        assert len(emails) == 1
        assert emails[0]["subject"] == "Starlette Test Email"

        # Verify UI
        response = await client.get("/_mail")
        assert response.status_code == 200
        assert "Mailview" in response.text

        # Delete and verify
        response = await client.delete(f"/_mail/api/emails/{email_id}")
        assert response.status_code == 200

        response = await client.get("/_mail/api/emails")
        assert response.json()["emails"] == []


# -----------------------------------------------------------------------------
# Production Safety Tests
# -----------------------------------------------------------------------------


class TestProductionSafety:
    """Tests for production safety - middleware should not activate in prod."""

    @pytest.fixture
    def prod_app(self):
        """Create app with mailview explicitly disabled for safety tests."""
        app = FastAPI()

        @app.get("/")
        async def home():
            return {"status": "ok"}

        # Explicitly disable mailview (bypasses environment-based detection)
        return MailviewMiddleware(app, enabled=False)

    @pytest.fixture
    async def client(self, prod_app):
        """Create async HTTP client."""
        transport = ASGITransport(app=prod_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_middleware_disabled_passthrough(self, client):
        """Test that disabled middleware passes requests through."""
        # App routes work
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

        # Mailview routes are not mounted (404 from app, not mailview)
        response = await client.get("/_mail")
        assert response.status_code == 404

        response = await client.get("/_mail/api/emails")
        assert response.status_code == 404

    async def test_explicit_enable_overrides(self, temp_db_path):
        """Test that enabled=True overrides environment detection."""
        app = FastAPI()

        @app.get("/")
        async def home():
            return {"status": "ok"}

        # Explicitly enable
        wrapped = MailviewMiddleware(app, enabled=True, db_path=temp_db_path)

        transport = ASGITransport(app=wrapped)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/_mail/api/emails")
            assert response.status_code == 200


# -----------------------------------------------------------------------------
# Email Type Coverage Tests
# -----------------------------------------------------------------------------


class TestEmailTypes:
    """Test all email type variations."""

    @pytest.fixture
    def backend(self, temp_db_path):
        """Create a backend for sending test emails."""
        store = EmailStore(db_path=temp_db_path)
        return MailviewBackend(store=store)

    @pytest.fixture
    def app(self, temp_db_path):
        """Create app with mailview middleware."""
        app = FastAPI()
        return MailviewMiddleware(app, enabled=True, db_path=temp_db_path)

    @pytest.fixture
    async def client(self, app):
        """Create async HTTP client."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def test_plain_text_only(self, client, backend):
        """Test plain text email without HTML."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Plain Text Only"
        msg.set_content("Just plain text, no HTML.")

        email = await backend.send(msg)

        response = await client.get(f"/_mail/api/emails/{email.id}")
        data = response.json()["email"]
        assert data["text_body"] == "Just plain text, no HTML.\n"
        assert data["html_body"] is None
        assert data["has_text"] is True
        assert data["has_html"] is False

    async def test_html_only(self, client, backend):
        """Test HTML-only email without plain text fallback."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "HTML Only"
        msg.set_content("<p>HTML only, no plain text.</p>", subtype="html")

        email = await backend.send(msg)

        response = await client.get(f"/_mail/api/emails/{email.id}")
        data = response.json()["email"]
        assert data["html_body"] == "<p>HTML only, no plain text.</p>\n"
        assert data["text_body"] is None
        assert data["has_html"] is True
        assert data["has_text"] is False

    async def test_multipart_alternative(self, client, backend):
        """Test multipart/alternative with both text and HTML."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Multipart Alternative"
        msg.set_content("Plain text version")
        msg.add_alternative("<p>HTML version</p>", subtype="html")

        email = await backend.send(msg)

        response = await client.get(f"/_mail/api/emails/{email.id}")
        data = response.json()["email"]
        assert data["text_body"] == "Plain text version\n"
        assert "<p>HTML version</p>" in data["html_body"]
        assert data["has_text"] is True
        assert data["has_html"] is True

    async def test_multiple_recipients(self, client, backend):
        """Test email with multiple To, Cc, and Bcc recipients."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "to1@example.com, to2@example.com"
        msg["Cc"] = "cc@example.com"
        msg["Bcc"] = "bcc@example.com"
        msg["Subject"] = "Multiple Recipients"
        msg.set_content("Test")

        email = await backend.send(msg)

        response = await client.get(f"/_mail/api/emails/{email.id}")
        data = response.json()["email"]
        assert data["to"] == ["to1@example.com", "to2@example.com"]
        assert data["cc"] == ["cc@example.com"]
        assert data["bcc"] == ["bcc@example.com"]

    async def test_custom_headers(self, client, backend):
        """Test that custom headers are preserved."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Custom Headers"
        msg["X-Custom-Header"] = "custom-value"
        msg["X-Priority"] = "1"
        msg.set_content("Test")

        email = await backend.send(msg)

        response = await client.get(f"/_mail/api/emails/{email.id}")
        data = response.json()["email"]
        assert data["headers"]["X-Custom-Header"] == "custom-value"
        assert data["headers"]["X-Priority"] == "1"
