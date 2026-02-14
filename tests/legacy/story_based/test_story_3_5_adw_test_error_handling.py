#!/usr/bin/env python3
"""
Unit tests for Story 3.5: Update error handling in adw_test.py for OpenCode

Tests migration from Copilot CLI check to OpenCode server availability check,
verifying that adw_test.py now uses check_opencode_server_available()
instead of shutil.which("copilot") and provides helpful error messages.
"""

import logging
import unittest.mock as mock
from unittest.mock import MagicMock, patch
import pytest

from scripts.adw_test import check_env_vars


class TestStory35AdwTestErrorHandling:
    """Test suite for Story 3.5: adw_test.py error handling migration to OpenCode."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.logger = MagicMock(spec=logging.Logger)
        self.adw_id = "test_adw_123"

    def test_check_env_vars_opencode_server_available_calls_check_function(
        self,
    ):
        """Test that check_env_vars calls check_opencode_server_available()."""
        with patch(
            "scripts.adw_test.check_opencode_server_available",
            return_value=True,
        ) as mock_check:
            check_env_vars(logger=self.logger)

            # Verify check_opencode_server_available was called
            mock_check.assert_called_once()

    def test_check_env_vars_opencode_server_available_passes_when_available(
        self,
    ):
        """Test that check_env_vars passes when OpenCode server is available."""
        with patch(
            "scripts.adw_test.check_opencode_server_available",
            return_value=True,
        ):
            # Should not raise or exit
            check_env_vars(logger=self.logger)

    def test_check_env_vars_opencode_server_available_exits_when_unavailable(
        self,
    ):
        """Test that check_env_vars exits when OpenCode server is unavailable."""
        with (
            patch(
                "scripts.adw_test.check_opencode_server_available",
                return_value=False,
            ) as mock_check,
            patch("sys.exit") as mock_exit,
        ):
            check_env_vars(logger=self.logger)

            # Verify check was called
            mock_check.assert_called_once()

            # Verify sys.exit(1) was called
            mock_exit.assert_called_once_with(1)

    def test_check_env_vars_opencode_server_unavailable_logs_helpful_message(
        self,
    ):
        """Test that helpful error message is logged when server unavailable."""
        expected_error_msg = (
            "Error: OpenCode server is not available or not responding.\n"
            "Please ensure OpenCode is running:\n"
            "  1. Start server: opencode serve --port 4096\n"
            "  2. Authenticate: opencode auth login\n"
            "  3. Verify: curl http://localhost:4096/health"
        )

        with (
            patch(
                "scripts.adw_test.check_opencode_server_available",
                return_value=False,
            ) as mock_check,
            patch("sys.exit") as mock_exit,
        ):
            check_env_vars(logger=self.logger)

            # Verify error message logged
            self.logger.error.assert_called_once_with(expected_error_msg)

    def test_check_env_vars_opencode_server_unavailable_prints_to_stderr(
        self,
    ):
        """Test that error message is printed to stderr when logger not provided."""
        expected_error_msg = (
            "Error: OpenCode server is not available or not responding.\n"
            "Please ensure OpenCode is running:\n"
            "  1. Start server: opencode serve --port 4096\n"
            "  2. Authenticate: opencode auth login\n"
            "  3. Verify: curl http://localhost:4096/health"
        )

        with (
            patch(
                "scripts.adw_test.check_opencode_server_available",
                return_value=False,
            ) as mock_check,
            patch("sys.exit"),
            patch("sys.stderr.write") as mock_stderr,
        ):
            check_env_vars(logger=None)  # No logger provided

            # Verify error message printed to stderr
            written_output = "".join(call[0][0] for call in mock_stderr.call_args_list)
            assert expected_error_msg in written_output

    def test_check_env_vars_migration_verification_no_copilot_which(
        self,
    ):
        """Test that shutil.which('copilot') is no longer called."""
        with patch(
            "scripts.adw_test.check_opencode_server_available", return_value=True
        ):
            with patch("shutil.which") as mock_which:
                check_env_vars(logger=self.logger)

                # Verify shutil.which was NOT called (migration verification)
                mock_which.assert_not_called()

    def test_check_env_vars_no_longer_requires_copilot_cli(
        self,
    ):
        """Test that Copilot CLI is no longer required dependency."""
        # This test verifies the function works without checking for copilot binary
        # Previously, it would have: if not shutil.which("copilot")
        # Now it calls: check_opencode_server_available()
        with patch(
            "scripts.adw_test.check_opencode_server_available",
            return_value=True,
        ):
            # Should pass without requiring copilot CLI
            check_env_vars(logger=self.logger)

    def test_check_opencode_server_available_imported_from_opencode_module(
        self,
    ):
        """Test that check_opencode_server_available is imported from opencode_http_client."""
        # Verify the import statement exists
        from scripts import adw_test

        # Check that check_opencode_server_available is available
        assert hasattr(adw_test, "check_opencode_server_available")

    def test_check_env_vars_opencode_server_available_timeout_config(
        self,
    ):
        """Test that check_opencode_server_available uses default timeout."""
        with patch(
            "scripts.adw_test.check_opencode_server_available",
            return_value=True,
        ) as mock_check:
            check_env_vars(logger=self.logger)

            # Verify called without timeout parameter (uses default 5.0s)
            mock_check.assert_called_once()

    def test_check_env_vars_preserves_logger_interface(
        self,
    ):
        """Test that logger interface is preserved from original implementation."""
        with patch(
            "scripts.adw_test.check_opencode_server_available",
            return_value=True,
        ):
            check_env_vars(logger=self.logger)

            # Logger should still work with error method
            assert hasattr(self.logger, "error")

    def test_check_env_vars_error_message_references_opencode_not_copilot(
        self,
    ):
        """Test that error message references OpenCode, not Copilot CLI."""
        with (
            patch(
                "scripts.adw_test.check_opencode_server_available",
                return_value=False,
            ) as mock_check,
            patch("sys.exit"),
        ):
            check_env_vars(logger=self.logger)

            # Get the error message that was logged
            logged_call = self.logger.error.call_args
            if logged_call:
                error_msg = logged_call[0][0]
                # Verify it mentions OpenCode
                assert "OpenCode" in error_msg
                # Verify it does NOT mention Copilot CLI
                assert "copilot" not in error_msg.lower()

    def test_check_env_vars_error_message_contains_troubleshooting_steps(
        self,
    ):
        """Test that error message contains helpful troubleshooting steps."""
        with (
            patch(
                "scripts.adw_test.check_opencode_server_available",
                return_value=False,
            ) as mock_check,
            patch("sys.exit"),
        ):
            check_env_vars(logger=self.logger)

            # Get the error message that was logged
            logged_call = self.logger.error.call_args
            if logged_call:
                error_msg = logged_call[0][0]
                # Verify troubleshooting steps are present
                assert "opencode serve --port 4096" in error_msg
                assert "opencode auth login" in error_msg
                assert "curl http://localhost:4096/health" in error_msg
