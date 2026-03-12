"""Middleware overhead benchmarks.

Measures the cost of mailview middleware on passthrough requests
(requests that don't hit /_mail endpoints).
"""

import pytest
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from mailview.middleware import MailviewMiddleware


def make_app():
    """Create a minimal test app."""
    return Starlette(routes=[Route("/", lambda r: PlainTextResponse("OK"))])


@pytest.fixture
def base_client():
    """Client without any middleware."""
    client = TestClient(make_app())
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def enabled_client(temp_db):
    """Client with mailview middleware enabled."""
    wrapped = MailviewMiddleware(make_app(), db_path=temp_db, enabled=True)
    client = TestClient(wrapped)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def disabled_client(temp_db):
    """Client with mailview middleware disabled."""
    wrapped = MailviewMiddleware(make_app(), db_path=temp_db, enabled=False)
    client = TestClient(wrapped)
    try:
        yield client
    finally:
        client.close()


class TestPassthroughOverhead:
    """Measure overhead on non-mailview requests."""

    def test_baseline(self, benchmark, base_client):
        """Baseline: no middleware."""
        response = benchmark(lambda: base_client.get("/"))
        assert response.status_code == 200

    def test_enabled(self, benchmark, enabled_client):
        """Passthrough with middleware enabled."""
        response = benchmark(lambda: enabled_client.get("/"))
        assert response.status_code == 200

    def test_disabled(self, benchmark, disabled_client):
        """Passthrough with middleware disabled."""
        response = benchmark(lambda: disabled_client.get("/"))
        assert response.status_code == 200
