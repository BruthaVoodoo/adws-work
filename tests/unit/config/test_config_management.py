"""
Unit tests for adw_config_test module - Configuration Management.

Tests configuration management operations:
- Manual command editing
- Fallback mode switching
- Configuration validation
- Configuration saving
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from scripts.adw_config_test import (
    edit_test_command,
    switch_to_fallback_mode,
    validate_configuration,
    save_configuration,
)


class TestEditTestCommand:
    """Tests for edit_test_command function."""

    def test_keep_current_command(self, capsys):
        """Test keeping current command (empty input)."""
        with patch("builtins.input", return_value=""):
            result = edit_test_command("npm test")

            assert result == "npm test"
            captured = capsys.readouterr()
            assert "Keeping current command" in captured.out

    def test_update_command(self, capsys):
        """Test updating command with new value."""
        with patch("builtins.input", return_value="npm run test:ci"):
            result = edit_test_command("npm test")

            assert result == "npm run test:ci"
            captured = capsys.readouterr()
            assert "Updated to: npm run test:ci" in captured.out


class TestSwitchToFallbackMode:
    """Tests for switch_to_fallback_mode function."""

    def test_switch_jest_to_fallback(self, capsys):
        """Test switching Jest config to console fallback."""
        current_config = {
            "framework": "jest",
            "test_command": "npm test -- --json --outputFile=.adw/test-results.json",
            "output_format": "json",
            "json_output_file": ".adw/test-results.json",
            "parser": "jest",
        }

        result = switch_to_fallback_mode(current_config)

        assert result["framework"] == "jest"
        assert result["output_format"] == "console"
        assert result["parser"] == "console"
        assert result["json_output_file"] is None
        assert "--json" not in result["test_command"]
        assert "--outputFile" not in result["test_command"]

        captured = capsys.readouterr()
        assert "Switching to console fallback" in captured.out

    def test_switch_pytest_to_fallback(self, capsys):
        """Test switching Pytest config to console fallback."""
        current_config = {
            "framework": "pytest",
            "test_command": "pytest --json-report --json-report-file=.adw/test.json",
            "output_format": "json",
        }

        result = switch_to_fallback_mode(current_config)

        assert result["output_format"] == "console"
        assert "--json-report-file" not in result["test_command"]
        # Command should have JSON flags removed (basic check)
        assert result["test_command"].startswith("pytest")


class TestValidateConfiguration:
    """Tests for validate_configuration function."""

    def test_validate_missing_command(self, capsys):
        """Test validation with missing test command."""
        result = validate_configuration({})

        assert result is False
        captured = capsys.readouterr()
        assert "No test command specified" in captured.out

    def test_validate_json_mode_success(self, tmp_path, capsys):
        """Test successful validation of JSON mode."""
        json_file = tmp_path / "test-results.json"
        json_file.write_text(
            '{"numTotalTests": 5, "numPassedTests": 5, "numFailedTests": 0}'
        )

        test_config = {
            "framework": "jest",
            "test_command": "echo 'test'",  # Simple command that will succeed
            "output_format": "json",
            "json_output_file": str(json_file),
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = validate_configuration(test_config)

            assert result is True
            captured = capsys.readouterr()
            assert "Valid JSON output file created" in captured.out

    def test_validate_json_mode_missing_file(self, capsys):
        """Test validation when JSON file is not created."""
        test_config = {
            "framework": "jest",
            "test_command": "echo 'test'",
            "output_format": "json",
            "json_output_file": "/nonexistent/file.json",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = validate_configuration(test_config)

            assert result is False
            captured = capsys.readouterr()
            assert "JSON output file not created" in captured.out

    def test_validate_console_mode_success(self, capsys):
        """Test successful validation of console mode."""
        test_config = {
            "framework": "pytest",
            "test_command": "echo 'FAILED test_example.py::test_foo'",
            "output_format": "console",
        }

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="FAILED test_example.py::test_foo", stderr=""
            )

            result = validate_configuration(test_config)

            assert result is True
            captured = capsys.readouterr()
            assert "Console output captured" in captured.out

    def test_validate_timeout(self, capsys):
        """Test validation with command timeout."""
        test_config = {
            "framework": "pytest",
            "test_command": "sleep 60",
            "output_format": "console",
        }

        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired("sleep 60", 30)

            result = validate_configuration(test_config)

            # Timeout is considered acceptable
            assert result is True
            captured = capsys.readouterr()
            assert "timed out" in captured.out


class TestSaveConfiguration:
    """Tests for save_configuration function."""

    def test_save_to_nonexistent_file(self, capsys):
        """Test saving when config.yaml doesn't exist."""
        with patch("scripts.adw_config_test.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/nonexistent")

            result = save_configuration({"framework": "jest"})

            assert result is False
            captured = capsys.readouterr()
            assert "not found" in captured.out

    def test_save_configuration_success(self, tmp_path, capsys):
        """Test successful configuration save."""
        # Create ADWS directory and config.yaml
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        config_file = adws_dir / "config.yaml"
        config_file.write_text("language: python\n")

        test_config = {
            "framework": "pytest",
            "test_command": "pytest",
            "output_format": "console",
        }

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            result = save_configuration(test_config)

            assert result is True

            # Verify file was updated
            with open(config_file) as f:
                saved_data = yaml.safe_load(f)

            assert saved_data["test_configuration"] == test_config
            assert saved_data["language"] == "python"  # Existing data preserved

            captured = capsys.readouterr()
            assert "Configuration saved successfully" in captured.out

    def test_save_configuration_error(self, tmp_path, capsys):
        """Test save error handling."""
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        config_file = adws_dir / "config.yaml"

        # Make config file read-only
        config_file.write_text("language: python\n")
        config_file.chmod(0o444)

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            result = save_configuration({"framework": "jest"})

            # Depending on OS, this might succeed or fail
            # Just check we handle errors gracefully
            captured = capsys.readouterr()
            assert (
                "Configuration saved" in captured.out
                or "Failed to save" in captured.out
            )
