"""Tests for environment detection."""

import logging
import os
from unittest.mock import patch

from mailview.env import (
    is_dev_environment,
    is_mailview_enabled,
    is_production_environment,
)


class TestIsDevEnvironment:
    """Tests for dev environment detection."""

    def test_debug_true(self):
        """Test DEBUG=1 is detected."""
        with patch.dict(os.environ, {"DEBUG": "1"}, clear=True):
            assert is_dev_environment() is True

    def test_debug_true_string(self):
        """Test DEBUG=true is detected."""
        with patch.dict(os.environ, {"DEBUG": "true"}, clear=True):
            assert is_dev_environment() is True

    def test_debug_yes(self):
        """Test DEBUG=yes is detected."""
        with patch.dict(os.environ, {"DEBUG": "yes"}, clear=True):
            assert is_dev_environment() is True

    def test_environment_development(self):
        """Test ENVIRONMENT=development is detected."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            assert is_dev_environment() is True

    def test_env_dev(self):
        """Test ENV=dev is detected."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=True):
            assert is_dev_environment() is True

    def test_fastapi_env(self):
        """Test FASTAPI_ENV=development is detected."""
        with patch.dict(os.environ, {"FASTAPI_ENV": "development"}, clear=True):
            assert is_dev_environment() is True

    def test_flask_env(self):
        """Test FLASK_ENV=development is detected."""
        with patch.dict(os.environ, {"FLASK_ENV": "development"}, clear=True):
            assert is_dev_environment() is True

    def test_production_not_detected(self):
        """Test production environment is not detected as dev."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            assert is_dev_environment() is False

    def test_no_env_vars(self):
        """Test no env vars returns False."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_dev_environment() is False

    def test_case_insensitive(self):
        """Test env var values are case-insensitive."""
        with patch.dict(os.environ, {"DEBUG": "TRUE"}, clear=True):
            assert is_dev_environment() is True

        with patch.dict(os.environ, {"ENVIRONMENT": "DEVELOPMENT"}, clear=True):
            assert is_dev_environment() is True


class TestIsMailviewEnabled:
    """Tests for mailview enabled detection."""

    def test_mailview_enabled_true(self):
        """Test MAILVIEW_ENABLED=true forces enable."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "true"}, clear=True):
            assert is_mailview_enabled() is True

    def test_mailview_enabled_1(self):
        """Test MAILVIEW_ENABLED=1 forces enable."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "1"}, clear=True):
            assert is_mailview_enabled() is True

    def test_mailview_enabled_yes(self):
        """Test MAILVIEW_ENABLED=yes forces enable."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "yes"}, clear=True):
            assert is_mailview_enabled() is True

    def test_mailview_enabled_false(self):
        """Test MAILVIEW_ENABLED=false forces disable."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "false"}, clear=True):
            assert is_mailview_enabled() is False

    def test_mailview_enabled_0(self):
        """Test MAILVIEW_ENABLED=0 forces disable."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "0"}, clear=True):
            assert is_mailview_enabled() is False

    def test_mailview_enabled_no(self):
        """Test MAILVIEW_ENABLED=no forces disable."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "no"}, clear=True):
            assert is_mailview_enabled() is False

    def test_mailview_enabled_overrides_debug(self):
        """Test MAILVIEW_ENABLED=false overrides DEBUG=true."""
        env = {"MAILVIEW_ENABLED": "false", "DEBUG": "true"}
        with patch.dict(os.environ, env, clear=True):
            assert is_mailview_enabled() is False

    def test_falls_back_to_dev_detection(self):
        """Test falls back to is_dev_environment when not set."""
        with patch.dict(os.environ, {"DEBUG": "1"}, clear=True):
            assert is_mailview_enabled() is True

        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            assert is_mailview_enabled() is False

    def test_logs_warning_when_force_enabled(self, caplog):
        """Test warning is logged when force-enabled."""
        env = {"MAILVIEW_ENABLED": "true"}
        with (
            patch.dict(os.environ, env, clear=True),
            caplog.at_level(logging.WARNING, logger="mailview"),
        ):
            is_mailview_enabled()
            assert "force-enabled" in caplog.text
            assert "MAILVIEW_ENABLED" in caplog.text

    def test_no_warning_when_auto_detected(self, caplog):
        """Test no warning when auto-detected as dev."""
        with (
            patch.dict(os.environ, {"DEBUG": "1"}, clear=True),
            caplog.at_level(logging.WARNING, logger="mailview"),
        ):
            is_mailview_enabled()
            assert "force-enabled" not in caplog.text

    def test_case_insensitive(self):
        """Test MAILVIEW_ENABLED values are case-insensitive."""
        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "TRUE"}, clear=True):
            assert is_mailview_enabled() is True

        with patch.dict(os.environ, {"MAILVIEW_ENABLED": "FALSE"}, clear=True):
            assert is_mailview_enabled() is False

    def test_logs_production_warning_when_force_enabled_in_prod(self, caplog):
        """Test stronger warning is logged when force-enabled in production."""
        env = {"MAILVIEW_ENABLED": "true", "ENVIRONMENT": "production"}
        with (
            patch.dict(os.environ, env, clear=True),
            caplog.at_level(logging.WARNING, logger="mailview"),
        ):
            is_mailview_enabled()
            assert "PRODUCTION" in caplog.text
            assert "exposes captured emails" in caplog.text

    def test_warns_on_unrecognized_value(self, caplog):
        """Test warning is logged for unrecognized MAILVIEW_ENABLED values."""
        env = {"MAILVIEW_ENABLED": "enabled", "DEBUG": "1"}
        with (
            patch.dict(os.environ, env, clear=True),
            caplog.at_level(logging.WARNING, logger="mailview"),
        ):
            result = is_mailview_enabled()
            assert "not recognized" in caplog.text
            assert "enabled" in caplog.text
            # Should fall back to auto-detection (DEBUG=1 -> True)
            assert result is True


class TestIsProductionEnvironment:
    """Tests for production environment detection."""

    def test_environment_production(self):
        """Test ENVIRONMENT=production is detected."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=True):
            assert is_production_environment() is True

    def test_environment_prod(self):
        """Test ENVIRONMENT=prod is detected."""
        with patch.dict(os.environ, {"ENVIRONMENT": "prod"}, clear=True):
            assert is_production_environment() is True

    def test_environment_staging(self):
        """Test ENVIRONMENT=staging is detected as production-like."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=True):
            assert is_production_environment() is True

    def test_env_production(self):
        """Test ENV=production is detected."""
        with patch.dict(os.environ, {"ENV": "production"}, clear=True):
            assert is_production_environment() is True

    def test_development_not_detected(self):
        """Test development environment is not detected as production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            assert is_production_environment() is False

    def test_no_env_vars(self):
        """Test no env vars returns False."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_production_environment() is False

    def test_case_insensitive(self):
        """Test production detection is case-insensitive."""
        with patch.dict(os.environ, {"ENVIRONMENT": "PRODUCTION"}, clear=True):
            assert is_production_environment() is True
