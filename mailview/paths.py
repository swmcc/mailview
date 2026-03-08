"""URL path utilities for mailview."""

from __future__ import annotations


def normalize_mount_path(mount_path: str) -> str:
    """Normalize and validate a URL mount path.

    Args:
        mount_path: The path to normalize

    Returns:
        Normalized path (leading slash, no trailing slash)

    Raises:
        ValueError: If path is empty or root-only
    """
    path = mount_path.strip().rstrip("/")
    if not path or path == "/":
        raise ValueError("mount_path must be a non-empty, non-root path")
    if not path.startswith("/"):
        path = "/" + path
    return path
