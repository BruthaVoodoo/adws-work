"""
Integration tests for test configuration in adw_setup.py

Tests verify that adw setup integrates test framework detection:
1. Detects test framework configuration
2. Prompts user to apply configuration
3. Saves configuration to config.yaml
4. Skips if configuration already exists
5. Handles detection failures gracefully
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import yaml

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestSetupTestConfigIntegration:
    """Test test configuration integration in adw setup."""

    def test_setup_detects_and_applies_jest_config(self, tmp_path, monkeypatch):
        """Test setup detects Jest and applies configuration when user accepts."""
        # Create ADWS folder with valid config (no test_configuration)
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
language: javascript
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Create package.json with Jest
        package_json = {
            "name": "test-project",
            "devDependencies": {"jest": "^29.0.0"},
        }
        import json

        (tmp_path / "package.json").write_text(json.dumps(package_json))

        # Set required environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Mock health checks
        with (
            patch("scripts.adw_setup.check_env_vars") as mock_env,
            patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
            patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
            patch("scripts.adw_setup.check_github_cli") as mock_gh,
            patch("scripts.adw_setup.check_opencode_server_wrapper") as mock_opencode,
            patch("builtins.input", return_value="y"),  # User accepts config
        ):
            from scripts.adw_tests.health_check import CheckResult

            mock_env.return_value = CheckResult(success=True, details={})
            mock_issue.return_value = CheckResult(success=True, details={})
            mock_repo.return_value = CheckResult(success=True, details={})
            mock_gh.return_value = CheckResult(success=True, details={})
            mock_opencode.return_value = CheckResult(success=True, details={})

            # Run setup
            from scripts.adw_setup import run_setup

            exit_code = run_setup()

            # Verify success
            assert exit_code == 0

            # Verify test_configuration was saved
            with open(adws_dir / "config.yaml", "r") as f:
                saved_config = yaml.safe_load(f)

            assert "test_configuration" in saved_config
            test_config = saved_config["test_configuration"]
            assert test_config["framework"] == "jest"
            assert "npm test" in test_config["test_command"]
            assert test_config["output_format"] == "json"
            assert test_config["parser"] == "jest"

    def test_setup_detects_pytest_config(self, tmp_path, monkeypatch):
        """Test setup detects Pytest and applies configuration."""
        # Create ADWS folder
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

        # Create pytest.ini
        (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = tests\n")

        # Set environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        monkeypatch.chdir(tmp_path)

        # Mock health checks and subprocess (no pytest-json-report)
        with (
            patch("scripts.adw_setup.check_env_vars") as mock_env,
            patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
            patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
            patch("scripts.adw_setup.check_github_cli") as mock_gh,
            patch("scripts.adw_setup.check_opencode_server_wrapper") as mock_opencode,
            patch("builtins.input", return_value="y"),
            patch("subprocess.run") as mock_subprocess,
        ):
            from scripts.adw_tests.health_check import CheckResult

            mock_env.return_value = CheckResult(success=True, details={})
            mock_issue.return_value = CheckResult(success=True, details={})
            mock_repo.return_value = CheckResult(success=True, details={})
            mock_gh.return_value = CheckResult(success=True, details={})
            mock_opencode.return_value = CheckResult(success=True, details={})

            # Mock subprocess to indicate pytest-json-report not installed
            mock_subprocess.return_value = MagicMock(returncode=1)

            from scripts.adw_setup import run_setup

            exit_code = run_setup()
            assert exit_code == 0

            # Verify pytest console config was saved
            with open(adws_dir / "config.yaml", "r") as f:
                saved_config = yaml.safe_load(f)

            assert "test_configuration" in saved_config
            test_config = saved_config["test_configuration"]
            assert test_config["framework"] == "pytest"
            assert test_config["test_command"] == "pytest"
            assert test_config["output_format"] == "console"
            assert test_config["parser"] == "console"

    def test_setup_skips_if_test_config_exists(self, tmp_path, monkeypatch):
        """Test setup skips detection if test_configuration already exists."""
        # Create ADWS folder with existing test_configuration
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
language: python
test_configuration:
  framework: pytest
  test_command: pytest
  output_format: console
  parser: console
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Set environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        monkeypatch.chdir(tmp_path)

        # Mock health checks
        with (
            patch("scripts.adw_setup.check_env_vars") as mock_env,
            patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
            patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
            patch("scripts.adw_setup.check_github_cli") as mock_gh,
            patch("scripts.adw_setup.check_opencode_server_wrapper") as mock_opencode,
            patch("builtins.input") as mock_input,  # Should not be called
        ):
            from scripts.adw_tests.health_check import CheckResult

            mock_env.return_value = CheckResult(success=True, details={})
            mock_issue.return_value = CheckResult(success=True, details={})
            mock_repo.return_value = CheckResult(success=True, details={})
            mock_gh.return_value = CheckResult(success=True, details={})
            mock_opencode.return_value = CheckResult(success=True, details={})

            from scripts.adw_setup import run_setup

            exit_code = run_setup()
            assert exit_code == 0

            # Verify input was NOT called (no prompt for existing config)
            mock_input.assert_not_called()

            # Verify config unchanged
            with open(adws_dir / "config.yaml", "r") as f:
                saved_config = yaml.safe_load(f)

            assert saved_config["test_configuration"]["framework"] == "pytest"

    def test_setup_handles_user_skip(self, tmp_path, monkeypatch):
        """Test setup handles user choosing to skip test configuration."""
        # Create ADWS folder
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Create package.json with Jest
        package_json = {"devDependencies": {"jest": "^29.0.0"}}
        import json

        (tmp_path / "package.json").write_text(json.dumps(package_json))

        # Set environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        monkeypatch.chdir(tmp_path)

        # Mock health checks
        with (
            patch("scripts.adw_setup.check_env_vars") as mock_env,
            patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
            patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
            patch("scripts.adw_setup.check_github_cli") as mock_gh,
            patch("scripts.adw_setup.check_opencode_server_wrapper") as mock_opencode,
            patch("builtins.input", return_value="skip"),  # User skips
        ):
            from scripts.adw_tests.health_check import CheckResult

            mock_env.return_value = CheckResult(success=True, details={})
            mock_issue.return_value = CheckResult(success=True, details={})
            mock_repo.return_value = CheckResult(success=True, details={})
            mock_gh.return_value = CheckResult(success=True, details={})
            mock_opencode.return_value = CheckResult(success=True, details={})

            from scripts.adw_setup import run_setup

            exit_code = run_setup()
            assert exit_code == 0

            # Verify test_configuration was NOT saved
            with open(adws_dir / "config.yaml", "r") as f:
                saved_config = yaml.safe_load(f)

            assert "test_configuration" not in saved_config

    def test_setup_handles_detection_failure(self, tmp_path, monkeypatch):
        """Test setup handles gracefully when detection fails."""
        # Create ADWS folder (no project files for detection)
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Set environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        monkeypatch.chdir(tmp_path)

        # Mock health checks
        with (
            patch("scripts.adw_setup.check_env_vars") as mock_env,
            patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
            patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
            patch("scripts.adw_setup.check_github_cli") as mock_gh,
            patch("scripts.adw_setup.check_opencode_server_wrapper") as mock_opencode,
        ):
            from scripts.adw_tests.health_check import CheckResult

            mock_env.return_value = CheckResult(success=True, details={})
            mock_issue.return_value = CheckResult(success=True, details={})
            mock_repo.return_value = CheckResult(success=True, details={})
            mock_gh.return_value = CheckResult(success=True, details={})
            mock_opencode.return_value = CheckResult(success=True, details={})

            from scripts.adw_setup import run_setup

            exit_code = run_setup()

            # Setup should still succeed even if test detection fails
            assert exit_code == 0

            # Verify no test_configuration was added
            with open(adws_dir / "config.yaml", "r") as f:
                saved_config = yaml.safe_load(f)

            assert "test_configuration" not in saved_config

    def test_setup_handles_exception_in_detection(self, tmp_path, monkeypatch):
        """Test setup handles exceptions during test framework detection."""
        # Create ADWS folder
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        logs_dir = adws_dir / "logs"
        logs_dir.mkdir()

        config_content = """
source_dir: src
test_dir: tests
"""
        (adws_dir / "config.yaml").write_text(config_content)

        # Set environment variables
        monkeypatch.setenv("JIRA_SERVER", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_USERNAME", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("BITBUCKET_API_TOKEN", "test-bb-token")
        monkeypatch.setenv("BITBUCKET_WORKSPACE", "test-ws")
        monkeypatch.setenv("BITBUCKET_REPO_NAME", "test-repo")

        monkeypatch.chdir(tmp_path)

        # Mock health checks and force exception in detection
        with (
            patch("scripts.adw_setup.check_env_vars") as mock_env,
            patch("scripts.adw_setup.check_issue_connectivity") as mock_issue,
            patch("scripts.adw_setup.check_repo_connectivity") as mock_repo,
            patch("scripts.adw_setup.check_github_cli") as mock_gh,
            patch("scripts.adw_setup.check_opencode_server_wrapper") as mock_opencode,
            patch(
                "scripts.adw_config_test.detect_test_framework",
                side_effect=Exception("Detection error"),
            ),
        ):
            from scripts.adw_tests.health_check import CheckResult

            mock_env.return_value = CheckResult(success=True, details={})
            mock_issue.return_value = CheckResult(success=True, details={})
            mock_repo.return_value = CheckResult(success=True, details={})
            mock_gh.return_value = CheckResult(success=True, details={})
            mock_opencode.return_value = CheckResult(success=True, details={})

            from scripts.adw_setup import run_setup

            exit_code = run_setup()

            # Setup should still succeed even with exception
            assert exit_code == 0
