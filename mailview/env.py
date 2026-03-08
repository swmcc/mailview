"""Environment detection for mailview.

Provides functions to detect development environments and control
mailview activation safely.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("mailview")

# Canonical truthy/falsy values for env var parsing
_TRUTHY = frozenset(("1", "true", "yes"))
_FALSY = frozenset(("0", "false", "no"))
_DEV_VALUES = frozenset(("development", "dev"))
_PROD_VALUES = frozenset(("production", "prod", "staging"))


def _env_is_truthy(var_name: str) -> bool:
    """Check if an environment variable has a truthy value."""
    return os.environ.get(var_name, "").lower() in _TRUTHY


def _env_is_falsy(var_name: str) -> bool:
    """Check if an environment variable has a falsy value."""
    return os.environ.get(var_name, "").lower() in _FALSY


def is_production_environment() -> bool:
    """Check if running in a production-like environment.

    Returns True if any common production indicators are detected.
    """
    for var in ("ENVIRONMENT", "ENV", "FASTAPI_ENV", "FLASK_ENV"):
        if os.environ.get(var, "").lower() in _PROD_VALUES:
            return True
    return False


def is_dev_environment() -> bool:
    """Check if running in a development environment.

    Checks common environment indicators:
    - DEBUG env var is set and truthy (1, true, yes)
    - ENVIRONMENT/ENV is "development" or "dev"
    - FASTAPI_ENV is "development"
    - FLASK_ENV is "development"

    Returns:
        True if development environment detected
    """
    if _env_is_truthy("DEBUG"):
        return True

    for var in ("ENVIRONMENT", "ENV", "FASTAPI_ENV", "FLASK_ENV"):
        if os.environ.get(var, "").lower() in _DEV_VALUES:
            return True

    return False


def is_mailview_enabled() -> bool:
    """Check if mailview should be enabled.

    Activation rules (in order):
    1. MAILVIEW_ENABLED=true -> force enable (with warning)
    2. MAILVIEW_ENABLED=false -> force disable
    3. Otherwise, auto-detect via is_dev_environment()

    Returns:
        True if mailview should be enabled
    """
    if _env_is_truthy("MAILVIEW_ENABLED"):
        if is_production_environment():
            logger.warning(
                "Mailview force-enabled in PRODUCTION environment via "
                "MAILVIEW_ENABLED. This exposes captured emails - ensure "
                "this is intentional!"
            )
        else:
            logger.warning(
                "Mailview force-enabled via MAILVIEW_ENABLED. "
                "Ensure this is intentional and not running in production."
            )
        return True

    if _env_is_falsy("MAILVIEW_ENABLED"):
        return False

    # Warn if set to unrecognized value
    mailview_enabled = os.environ.get("MAILVIEW_ENABLED", "")
    if mailview_enabled:
        logger.warning(
            "MAILVIEW_ENABLED='%s' is not recognized (use true/false/1/0). "
            "Falling back to auto-detection.",
            mailview_enabled,
        )

    return is_dev_environment()
