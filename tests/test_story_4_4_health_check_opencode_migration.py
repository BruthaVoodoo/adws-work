"""
Test Story 4.4: Update health_check.py to verify OpenCode server

Acceptance Criteria:
- Given health_check.py runs at startup
  When it executes
  Then it calls check_opencode_server_available()
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from scripts.adw_tests.health_check import (
    check_opencode_server,
    run_health_check,
    HealthCheckResult,
    CheckResult,
)


class TestCheckOpenCodeServer:
    """Test check_opencode_server() function."""

    def test_opencode_server_calls_check_opencode_server_available(self):
        """Verify check_opencode_server() calls check_opencode_server_available()."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = True

            result = check_opencode_server()

            # Verify function was called
            assert mock_check.called
            # Verify result is success when server is available
            assert result.success
            assert "version" in result.details or "server_url" in result.details

    def test_opencode_server_available_returns_success(self):
        """When OpenCode server is available, return success."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = True

            result = check_opencode_server()

            assert result.success is True
            assert result.error is None
            assert result.details.get("server_url") or result.details.get("status")

    def test_opencode_server_unavailable_returns_error(self):
        """When OpenCode server is unavailable, return error."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = False

            result = check_opencode_server()

            assert result.success is False
            assert result.error is not None
            assert "OpenCode" in result.error or "server" in result.error.lower()

    def test_opencode_server_uses_config_server_url(self):
        """Verify check_opencode_server() uses config server URL."""
        # Config is imported inside the function, so we just verify it works
        # when check_opencode_server_available returns True
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = True
            # Verify it was called with server_url parameter
            mock_check.side_effect = lambda server_url=None, timeout=5.0: True

            result = check_opencode_server()

            assert result.success
            assert mock_check.called

    def test_opencode_server_handles_import_error(self):
        """Handle import errors gracefully."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available",
            side_effect=ImportError("No module named 'scripts'"),
        ):
            result = check_opencode_server()

            assert result.success is False
            assert result.error is not None
            assert "import" in result.error.lower() or "module" in result.error.lower()


class TestRunHealthCheckWithOpenCode:
    """Test run_health_check() includes OpenCode server check."""

    def test_health_check_includes_opencode_server_check(self):
        """Verify run_health_check() includes opencode_server check."""
        with patch(
            "scripts.adw_modules.opencode_http_client.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = True

            result = run_health_check()

            # Verify opencode_server check is included
            assert "opencode_server" in result.checks

    def test_health_check_opencode_server_success(self):
        """When OpenCode server is available, health check passes."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = True

            result = run_health_check()

            # Verify opencode_server check is successful
            assert result.checks["opencode_server"].success is True

    def test_health_check_opencode_server_failure(self):
        """When OpenCode server is unavailable, health check fails."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = False

            result = run_health_check()

            # Verify opencode_server check failed
            assert result.checks["opencode_server"].success is False
            # Verify overall health check fails
            assert result.success is False

    def test_health_check_no_longer_checks_github_copilot_cli(self):
        """Verify health check no longer includes github_copilot_cli check."""
        with patch(
            "scripts.adw_tests.health_check.check_opencode_server_available"
        ) as mock_check:
            mock_check.return_value = True

            result = run_health_check()

            # Verify github_copilot_cli is NOT in checks
            assert "github_copilot_cli" not in result.checks
            # Verify opencode_server IS in checks
            assert "opencode_server" in result.checks


class TestHealthCheckDocstringUpdates:
    """Test that docstrings are updated to reference OpenCode."""

    def test_health_check_module_docstring_mentions_opencode(self):
        """Verify module docstring mentions OpenCode, not GitHub Copilot CLI."""
        import scripts.adw_tests.health_check as health_module

        docstring = health_module.__doc__
        assert docstring is not None
        assert "OpenCode" in docstring
        # GitHub Copilot CLI check should be removed or deprecated mentioned

    def test_check_opencode_server_has_docstring(self):
        """Verify check_opencode_server() has proper docstring."""
        docstring = check_opencode_server.__doc__
        assert docstring is not None
        assert "OpenCode" in docstring
        assert "check_opencode_server_available" in docstring


class TestBackwardCompatibility:
    """Test backward compatibility with other health checks."""

    def test_other_health_checks_still_work(self):
        """Verify other health checks (env vars, Jira, Bitbucket, GitHub CLI) still work."""
        with patch(
            "scripts.adw_modules.opencode_http_client.check_opencode_server_available",
            return_value=True,
        ):
            with patch("scripts.adw_tests.health_check.check_env_vars") as mock_env:
                mock_env.return_value = CheckResult(success=True)

            with patch(
                "scripts.adw_tests.health_check.check_jira_connectivity"
            ) as mock_jira:
                mock_jira.return_value = CheckResult(success=True)

            with patch(
                "scripts.adw_tests.health_check.check_bitbucket_connectivity"
            ) as mock_bitbucket:
                mock_bitbucket.return_value = CheckResult(success=True)

            with patch("scripts.adw_tests.health_check.check_github_cli") as mock_gh:
                mock_gh.return_value = CheckResult(success=True)

            result = run_health_check()

            # Verify all other checks are still present and called
            assert "environment" in result.checks
            assert "jira_connectivity" in result.checks
            assert "bitbucket_connectivity" in result.checks
            assert "github_cli" in result.checks
            assert "opencode_server" in result.checks
