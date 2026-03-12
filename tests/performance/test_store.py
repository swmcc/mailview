"""Store read/write benchmarks."""

import pytest

from mailview.store import EmailStore

from .helpers import make_email, run_async


class TestWrite:
    """Write operation benchmarks."""

    def test_single_email(self, benchmark, store):
        """Write a single email."""
        i = [0]

        def write():
            run_async(store.save(make_email(i[0])))
            i[0] += 1

        benchmark.pedantic(write, rounds=100)

    def test_email_with_attachment(self, benchmark, store):
        """Write email with 1KB attachment."""
        i = [0]

        def write():
            run_async(store.save(make_email(i[0], with_attachment=True)))
            i[0] += 1

        benchmark.pedantic(write, rounds=100)

    @pytest.mark.parametrize("count", [100, 500, 1000])
    def test_batch(self, benchmark, temp_db, count):
        """Batch write throughput."""
        emails = [make_email(i) for i in range(count)]

        def write_batch():
            async def _write():
                s = EmailStore(db_path=temp_db)
                await s.delete_all()  # Clear DB for consistent state each round
                for e in emails:
                    await s.save(e)

            run_async(_write())

        benchmark.pedantic(write_batch, rounds=3)


class TestRead:
    """Read operation benchmarks (uses pre-populated 1000-email DB)."""

    def test_get_all(self, benchmark, populated_db):
        """Fetch all 1000 emails."""
        store = EmailStore(db_path=populated_db)
        # Warm up to exclude initialization from benchmark
        run_async(store.get_all())
        result = benchmark(lambda: run_async(store.get_all()))
        assert len(result) == 1000

    def test_get_by_id(self, benchmark, populated_db):
        """Fetch single email by ID."""
        store = EmailStore(db_path=populated_db)
        # Warm up to exclude initialization from benchmark
        run_async(store.get_by_id("email-00500"))
        result = benchmark(lambda: run_async(store.get_by_id("email-00500")))
        assert result is not None

    def test_count(self, benchmark, populated_db):
        """Count emails."""
        store = EmailStore(db_path=populated_db)
        # Warm up to exclude initialization from benchmark
        run_async(store.count())
        result = benchmark(lambda: run_async(store.count()))
        assert result == 1000

    def test_get_attachment_counts(self, benchmark, populated_db):
        """Fetch attachment counts for all emails."""
        store = EmailStore(db_path=populated_db)
        # Warm up to exclude initialization from benchmark
        run_async(store.get_attachment_counts())
        result = benchmark(lambda: run_async(store.get_attachment_counts()))
        assert isinstance(result, dict)
        assert result  # Should not be empty (half of emails have attachments)
        assert any(count > 0 for count in result.values())
