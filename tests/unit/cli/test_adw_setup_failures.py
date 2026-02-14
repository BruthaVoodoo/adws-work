"""
Integration tests for adw_setup.py - Failure modes and error handling

Tests verify that adw setup command:
1. Returns non-zero exit code on failure with actionable messages
2. Handles missing ADWS folder, config, and environment variables
3. Handles connectivity failures for Jira, Bitbucket, and OpenCode
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


class TestAdwSetupFailureModes:
    """Test adw setup in various failure modes."""

    def test_setup_fails_when_adws_folder_missing(self, tmp_path, monkeypatch, capsys):
        """Test setup fails when ADWS folder doesn't exist."""
        # Set environment variables but don't create ADWS folder
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            from scripts.adw_setup import main as setup_main

            with pytest.raises(SystemExit) as exc_info:
                setup_main()

            # Should exit with non-zero code
            assert exc_info.value.code != 0

            captured = capsys.readouterr()
            # Should have actionable error message
            assert "ADWS" in captured.out or "ADWS" in captured.err
            assert (
                "folder" in captured.out.lower() or "directory" in captured.out.lower()
            )

        finally:
            os.chdir(original_cwd)

    def test_setup_fails_when_config_missing(self, tmp_path, monkeypatch, capsys):
        """Test setup fails when config.yaml doesn't exist in ADWS folder."""
        # Create ADWS folder but no config.yaml
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()

        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            from scripts.adw_setup import main as setup_main

            with pytest.raises(SystemExit) as exc_info:
                setup_main()

            assert exc_info.value.code != 0

            captured = capsys.readouterr()
            assert "config" in captured.out.lower() or "config" in captured.err.lower()

        finally:
            os.chdir(original_cwd)

    def test_setup_fails_on_missing_env_vars(self, tmp_path, monkeypatch, capsys):
        """Test setup fails when required environment variables are missing."""
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

        # Mock os.getenv to simulate missing env vars
        def mock_getenv(key, default=None):
            # Only return value for the one env var we set
            if key == "JIRA_SERVER":
                return "https://test.atlassian.net"
            return default

        monkeypatch.setattr(os, "getenv", mock_getenv)

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            from scripts.adw_setup import main as setup_main

            with pytest.raises(SystemExit) as exc_info:
                setup_main()

            assert exc_info.value.code != 0

            captured = capsys.readouterr()
            # Should have actionable error about missing env vars
            assert (
                "environment" in captured.out.lower() or "env" in captured.out.lower()
            )
            assert "variable" in captured.out.lower()

        finally:
            os.chdir(original_cwd)

    def test_setup_fails_on_opencode_unavailable(self, tmp_path, monkeypatch, capsys):
        """Test setup fails when OpenCode server is not available."""
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

        # Set all env vars
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            # Mock health checks but make OpenCode fail
            with (
                patch("scripts.adw_setup.check_env_vars") as mock_env,
                patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
                patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
                patch("scripts.adw_setup.check_github_cli") as mock_gh,
                patch(
                    "scripts.adw_setup.check_opencode_server_wrapper"
                ) as mock_opencode,
            ):
                from scripts.adw_tests.health_check import CheckResult

                mock_env.return_value = CheckResult(success=True, details={})
                mock_issue.return_value = CheckResult(success=True, details={})
                mock_repo.return_value = CheckResult(success=True, details={})
                mock_gh.return_value = CheckResult(success=True, details={})
                mock_opencode.return_value = CheckResult(
                    success=False, error="OpenCode server not available"
                )

                from scripts.adw_setup import main as setup_main

                with pytest.raises(SystemExit) as exc_info:
                    setup_main()

                assert exc_info.value.code != 0

                captured = capsys.readouterr()
                # Should have actionable error about OpenCode
                assert (
                    "opencode" in captured.out.lower()
                    or "opencode" in captured.err.lower()
                )

        finally:
            os.chdir(original_cwd)

    def test_setup_fails_on_jira_connectivity_issue(
        self, tmp_path, monkeypatch, capsys
    ):
        """Test setup fails when Jira connectivity check fails."""
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

        # Set all env vars
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            # Mock health checks but make Jira fail
            with (
                patch("scripts.adw_setup.check_env_vars") as mock_env,
                patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
                patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
                patch("scripts.adw_setup.check_github_cli") as mock_gh,
                patch(
                    "scripts.adw_setup.check_opencode_server_wrapper"
                ) as mock_opencode,
            ):
                from scripts.adw_tests.health_check import CheckResult

                mock_env.return_value = CheckResult(success=True, details={})
                mock_issue.return_value = CheckResult(
                    success=False, error="Jira authentication failed"
                )
                mock_repo.return_value = CheckResult(success=True, details={})
                mock_gh.return_value = CheckResult(success=True, details={})
                mock_opencode.return_value = CheckResult(success=True, details={})

                from scripts.adw_setup import main as setup_main

                with pytest.raises(SystemExit) as exc_info:
                    setup_main()

                assert exc_info.value.code != 0

                captured = capsys.readouterr()
                # Should have actionable error about Jira
                assert "jira" in captured.out.lower() or "jira" in captured.err.lower()

        finally:
            os.chdir(original_cwd)

    def test_setup_fails_on_bitbucket_connectivity_issue(
        self, tmp_path, monkeypatch, capsys
    ):
        """Test setup fails when Bitbucket connectivity check fails."""
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

        # Set all env vars
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        original_cwd = os.getcwd()
        monkeypatch.chdir(tmp_path)

        try:
            # Mock health checks but make Bitbucket fail
            with (
                patch("scripts.adw_setup.check_env_vars") as mock_env,
                patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
                patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
                patch("scripts.adw_setup.check_github_cli") as mock_gh,
                patch(
                    "scripts.adw_setup.check_opencode_server_wrapper"
                ) as mock_opencode,
            ):
                from scripts.adw_tests.health_check import CheckResult

                mock_env.return_value = CheckResult(success=True, details={})
                mock_issue.return_value = CheckResult(success=True, details={})
                mock_repo.return_value = CheckResult(
                    success=False, error="Bitbucket API returned 401 Unauthorized"
                )
                mock_gh.return_value = CheckResult(success=True, details={})
                mock_opencode.return_value = CheckResult(success=True, details={})

                from scripts.adw_setup import main as setup_main

                with pytest.raises(SystemExit) as exc_info:
                    setup_main()

                assert exc_info.value.code != 0

                captured = capsys.readouterr()
                # Should have actionable error about Bitbucket
                assert (
                    "bitbucket" in captured.out.lower()
                    or "bitbucket" in captured.err.lower()
                )

        finally:
            os.chdir(original_cwd)
