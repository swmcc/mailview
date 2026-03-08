"""Basic tests for mailview."""

import mailview


def test_version():
    """Check version is set."""
    assert mailview.__version__ == "0.1.0"
