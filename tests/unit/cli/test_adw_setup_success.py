"""
Integration tests for adw_setup.py - Success flows and logging

Tests verify that adw setup command:
1. Runs configuration steps and validations
2. Prints single success message on completion
3. Writes setup log to ADWS/logs/
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))


class TestAdwSetupSuccess:
    """Test adw setup in success mode."""

    def test_setup_success_with_valid_config(self, tmp_path, monkeypatch):
        """Test setup succeeds when all configuration and health checks pass."""
        # Create ADWS folder with valid config
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
docs_dir: docs
language: python
test_command: uv run pytest
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Set required environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        # Change to temp directory
        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            # Mock health check functions to return success
            with (
                patch("scripts.adw_setup.check_env_vars") as mock_env,
                patch("scripts.adw_setup.check_jira_connectivity") as mock_jira,
                patch("scripts.adw_setup.check_bitbucket_connectivity") as mock_bb,
                patch("scripts.adw_setup.check_github_cli") as mock_gh,
                patch("scripts.adw_setup.check_opencode_server") as mock_opencode,
            ):
                from scripts.adw_tests.health_check import CheckResult

                mock_env.return_value = CheckResult(success=True, details={})
                mock_jira.return_value = CheckResult(
                    success=True, details={"version": "9.0"}
                )
                mock_bb.return_value = CheckResult(
                    success=True, details={"authenticated_user": "test-user"}
                )
                mock_gh.return_value = CheckResult(
                    success=True, details={"version": "gh version 2.0"}
                )
                mock_opencode.return_value = CheckResult(
                    success=True, details={"server_url": "http://localhost:4096"}
                )

                # Import and run setup
                from scripts.adw_setup import main as setup_main

                # Should complete without error
                try:
                    setup_main()
                except SystemExit as e:
                    # Exit code should be 0 for success
                    assert e.code == 0, f"Expected exit code 0, got {e.code}"

                # Verify setup log was created
                log_files = list(logs_dir.glob("setup_*.txt"))
                assert len(log_files) > 0, "Setup log file should be created"

        finally:
            os.chdir(original_cwd)

    def test_setup_prints_single_success_message(self, tmp_path, monkeypatch, capsys):
        """Test setup prints single success message on completion."""
        # Create ADWS folder with valid config
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
language: python
test_command: uv run pytest
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Set required environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            # Mock health check functions
            with (
                patch("scripts.adw_setup.check_env_vars") as mock_env,
                patch("scripts.adw_setup.check_jira_connectivity") as mock_jira,
                patch("scripts.adw_setup.check_bitbucket_connectivity") as mock_bb,
                patch("scripts.adw_setup.check_github_cli") as mock_gh,
                patch("scripts.adw_setup.check_opencode_server") as mock_opencode,
            ):
                from scripts.adw_tests.health_check import CheckResult

                mock_env.return_value = CheckResult(success=True, details={})
                mock_jira.return_value = CheckResult(success=True, details={})
                mock_bb.return_value = CheckResult(success=True, details={})
                mock_gh.return_value = CheckResult(success=True, details={})
                mock_opencode.return_value = CheckResult(success=True, details={})

                from scripts.adw_setup import main as setup_main

                try:
                    setup_main()
                except SystemExit:
                    pass

                captured = capsys.readouterr()

                # Should contain success message
                assert "✅" in captured.out or "SUCCESS" in captured.out.upper()
                assert (
                    "Setup completed successfully" in captured.out
                    or "setup" in captured.out.lower()
                )

        finally:
            os.chdir(original_cwd)


class TestAdwSetupLogging:
    """Test setup log file creation."""

    def test_setup_writes_log_file(self, tmp_path, monkeypatch):
        """Test setup writes log file to ADWS/logs/."""
        # Create ADWS folder with config
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
language: python
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Set env vars
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            # Mock all health checks to succeed
            with (
                patch("scripts.adw_setup.check_env_vars") as mock_env,
                patch("scripts.adw_setup.check_jira_connectivity") as mock_jira,
                patch("scripts.adw_setup.check_bitbucket_connectivity") as mock_bb,
                patch("scripts.adw_setup.check_github_cli") as mock_gh,
                patch("scripts.adw_setup.check_opencode_server") as mock_opencode,
            ):
                from scripts.adw_tests.health_check import CheckResult

                mock_env.return_value = CheckResult(success=True, details={})
                mock_jira.return_value = CheckResult(success=True, details={})
                mock_bb.return_value = CheckResult(success=True, details={})
                mock_gh.return_value = CheckResult(success=True, details={})
                mock_opencode.return_value = CheckResult(success=True, details={})

                from scripts.adw_setup import main as setup_main

                try:
                    setup_main()
                except SystemExit as e:
                    assert e.code == 0

                # Verify log file was created
                log_files = list(logs_dir.glob("setup_*.txt"))
                assert len(log_files) > 0, (
                    f"Expected setup log file, found {len(log_files)}"
                )

                # Verify log file has content
                log_content = log_files[0].read_text()
                assert len(log_content) > 0, "Log file should have content"
                # Should contain setup details
                assert "ADWS Setup" in log_content or "setup" in log_content.lower()

        finally:
            os.chdir(original_cwd)
