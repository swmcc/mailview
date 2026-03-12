"""Shared fixtures for performance benchmarks.

Run all: pytest tests/performance/ -v --benchmark-only
Run group: pytest tests/performance/test_store.py --benchmark-only
Compare: pytest tests/performance/ --benchmark-compare
"""

import tempfile
from pathlib import Path

import pytest

from mailview.store import EmailStore

from .helpers import make_email, run_async


@pytest.fixture
def temp_db():
    """Fresh temp database for each test."""
    with tempfile.TemporaryDirectory() as d:
        yield str(Path(d) / "test.db")


@pytest.fixture
def store(temp_db):
    """Fresh store instance."""
    return EmailStore(db_path=temp_db)


@pytest.fixture(scope="module")
def populated_db():
    """Module-scoped DB with 1000 emails (created once, reused for reads).

    Half the emails have attachments for representative benchmarks.
    """
    with tempfile.TemporaryDirectory() as d:
        db_path = str(Path(d) / "populated.db")
        store = EmailStore(db_path=db_path)

        async def populate():
            for i in range(1000):
                with_attachment = i % 2 == 0
                await store.save(make_email(i, with_attachment=with_attachment))

        run_async(populate())
        yield db_path
