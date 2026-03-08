"""Tests for URL path utilities."""

import pytest

from mailview.paths import normalize_mount_path


class TestNormalizeMountPath:
    """Tests for mount path normalization."""

    def test_valid_path(self):
        """Test valid path is returned unchanged."""
        assert normalize_mount_path("/_mail") == "/_mail"

    def test_strips_trailing_slash(self):
        """Test trailing slash is stripped."""
        assert normalize_mount_path("/_mail/") == "/_mail"

    def test_adds_leading_slash(self):
        """Test leading slash is added if missing."""
        assert normalize_mount_path("_mail") == "/_mail"

    def test_strips_whitespace(self):
        """Test whitespace is stripped."""
        assert normalize_mount_path("  /_mail  ") == "/_mail"

    def test_empty_raises(self):
        """Test empty path raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            normalize_mount_path("")

    def test_whitespace_only_raises(self):
        """Test whitespace-only path raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            normalize_mount_path("   ")

    def test_root_raises(self):
        """Test root path raises ValueError."""
        with pytest.raises(ValueError, match="non-root"):
            normalize_mount_path("/")

    def test_root_with_trailing_slash_raises(self):
        """Test root with trailing slash raises ValueError."""
        with pytest.raises(ValueError, match="non-root"):
            normalize_mount_path("//")

    def test_nested_path(self):
        """Test nested paths work."""
        assert normalize_mount_path("/api/mail") == "/api/mail"
