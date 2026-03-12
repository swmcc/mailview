"""API endpoint benchmarks."""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mailview.middleware import MailviewMiddleware


@pytest.fixture
def client(populated_db):
    """Test client with 1000 pre-populated emails."""
    app = Starlette(routes=[Route("/", lambda r: PlainTextResponse("OK"))])
    wrapped = MailviewMiddleware(app, db_path=populated_db, enabled=True)
    client = TestClient(wrapped)
    try:
        yield client
    finally:
        client.close()


class TestListEndpoint:
    """GET /_mail/api/emails benchmarks."""

    def test_list_1000_emails(self, benchmark, client):
        """List all emails (1000 in DB)."""
        response = benchmark(lambda: client.get("/_mail/api/emails"))
        assert response.status_code == 200
        assert len(response.json()["emails"]) == 1000


class TestDetailEndpoint:
    """GET /_mail/api/emails/{id} benchmarks."""

    def test_get_email(self, benchmark, client):
        """Fetch single email detail."""
        response = benchmark(lambda: client.get("/_mail/api/emails/email-00500"))
        assert response.status_code == 200

    def test_get_email_html(self, benchmark, client):
        """Fetch email HTML body."""
        response = benchmark(lambda: client.get("/_mail/api/emails/email-00500/html"))
        assert response.status_code == 200
