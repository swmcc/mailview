"""Tests for ASGI middleware."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mailview.middleware import MailviewMiddleware
from mailview.models import Email


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test.db")


def homepage(request):
    """Simple homepage handler."""
    return PlainTextResponse("Hello from app")


def create_app(middleware_kwargs=None):
    """Create a test Starlette app with middleware."""
    app = Starlette(routes=[Route("/", homepage)])
    kwargs = middleware_kwargs or {}
    return MailviewMiddleware(app, **kwargs)


class TestMiddlewareInit:
    """Tests for middleware initialization."""

    def test_default_mount_path(self, temp_db_path):
        """Test default mount path is /_mail."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        assert app.mount_path == "/_mail"

    def test_custom_mount_path(self, temp_db_path):
        """Test custom mount path."""
        app = create_app(
            {
                "enabled": True,
                "db_path": temp_db_path,
                "mount_path": "/_emails",
            }
        )
        assert app.mount_path == "/_emails"

    def test_mount_path_strips_trailing_slash(self, temp_db_path):
        """Test trailing slash is stripped from mount path."""
        app = create_app(
            {
                "enabled": True,
                "db_path": temp_db_path,
                "mount_path": "/_mail/",
            }
        )
        assert app.mount_path == "/_mail"

    def test_enabled_true(self, temp_db_path):
        """Test explicitly enabled."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        assert app.enabled is True
        assert app._mailview_app is not None

    def test_enabled_false(self, temp_db_path):
        """Test explicitly disabled."""
        app = create_app({"enabled": False})
        assert app.enabled is False
        assert app._mailview_app is None

    def test_auto_detect_dev(self, temp_db_path):
        """Test auto-detection when enabled=None."""
        with patch.dict(os.environ, {"DEBUG": "1"}, clear=True):
            app = create_app({"db_path": temp_db_path})
            assert app.enabled is True

    def test_auto_detect_prod(self):
        """Test auto-detection in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            app = create_app()
            assert app.enabled is False

    def test_custom_db_path(self, temp_db_path):
        """Test custom database path."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        assert app.store.db_path == temp_db_path

    def test_empty_mount_path_raises(self):
        """Test that empty mount_path raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            create_app({"enabled": True, "mount_path": ""})

    def test_root_mount_path_raises(self):
        """Test that root mount_path raises ValueError."""
        with pytest.raises(ValueError, match="non-root"):
            create_app({"enabled": True, "mount_path": "/"})


class TestMiddlewareRouting:
    """Tests for middleware request routing."""

    def test_passthrough_when_disabled(self):
        """Test requests pass through when disabled."""
        app = create_app({"enabled": False})
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello from app"

    def test_passthrough_non_mailview_paths(self, temp_db_path):
        """Test non-mailview paths pass through."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello from app"

    def test_routes_to_mailview_api(self, temp_db_path):
        """Test mailview API paths are routed correctly."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/_mail/api/emails")
        assert response.status_code == 200
        assert "emails" in response.json()

    def test_custom_mount_path_routing(self, temp_db_path):
        """Test routing with custom mount path."""
        app = create_app(
            {
                "enabled": True,
                "db_path": temp_db_path,
                "mount_path": "/_custom",
            }
        )
        client = TestClient(app, raise_server_exceptions=False)

        # Should not route old path
        response = client.get("/_mail/api/emails")
        assert response.status_code == 404

        # Should route new path
        response = client.get("/_custom/api/emails")
        assert response.status_code == 200

    def test_mount_path_boundary_does_not_match_prefix(self, temp_db_path):
        """Test default mount path does not capture similarly-prefixed routes."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        client = TestClient(app, raise_server_exceptions=False)

        # Requests to /_mailbox/... should not be handled by the /_mail mount
        response = client.get("/_mailbox/api/emails")
        assert response.status_code == 404


class TestMiddlewareIntegration:
    """Integration tests with FastAPI-style usage."""

    async def test_email_capture_integration(self, temp_db_path):
        """Test capturing and listing emails via middleware."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        store = app.mailview_store

        # Capture an email
        email = Email(
            id="integration-test",
            sender="test@example.com",
            to=["recipient@example.com"],
            subject="Integration Test",
            text_body="Test body",
        )
        await store.save(email)

        # List via API
        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/_mail/api/emails")
        assert response.status_code == 200
        data = response.json()
        assert len(data["emails"]) == 1
        assert data["emails"][0]["subject"] == "Integration Test"

    def test_mailview_store_property_when_enabled(self, temp_db_path):
        """Test mailview_store property returns store when enabled."""
        app = create_app({"enabled": True, "db_path": temp_db_path})
        assert app.mailview_store is not None

    def test_mailview_store_property_when_disabled(self):
        """Test mailview_store property returns None when disabled."""
        app = create_app({"enabled": False})
        assert app.mailview_store is None
