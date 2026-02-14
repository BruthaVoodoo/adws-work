"""
Tests for setup_pytest() function in adw_config_test.py

Verifies interactive pytest configuration flow:
1. Checks for pytest-json-report plugin
2. Offers to auto-install if missing
3. Displays recommended JSON command with benefits
4. Handles user accept/edit/reject choices
5. Returns appropriate test config dict
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestSetupPytest:
    """Test setup_pytest() interactive flow."""

    def test_setup_pytest_with_plugin_installed_accept(self, monkeypatch, tmp_path):
        """Test setup_pytest when plugin is installed and user accepts recommended command."""
        monkeypatch.chdir(tmp_path)

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=True,
            ),
            patch("builtins.input", return_value="a"),
        ):  # User accepts
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            assert result == {
                "framework": "pytest",
                "test_command": "pytest --json-report --json-report-file=.adw/test-results.json",
                "output_format": "json",
                "json_output_file": ".adw/test-results.json",
                "parser": "pytest",
            }

    def test_setup_pytest_with_plugin_installed_edit(self, monkeypatch, tmp_path):
        """Test setup_pytest when user chooses to edit command."""
        monkeypatch.chdir(tmp_path)

        # User chooses edit, then enters custom command
        inputs = iter(["e", "pytest --json-report --json-report-file=custom.json -v"])

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=True,
            ),
            patch("builtins.input", side_effect=inputs),
        ):
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            assert result["framework"] == "pytest"
            assert (
                result["test_command"]
                == "pytest --json-report --json-report-file=custom.json -v"
            )
            assert result["output_format"] == "json"
            assert result["parser"] == "pytest"

    def test_setup_pytest_with_plugin_installed_edit_empty(self, monkeypatch, tmp_path):
        """Test setup_pytest when user chooses edit but enters empty string."""
        monkeypatch.chdir(tmp_path)

        # User chooses edit, then enters nothing (fallback to recommended)
        inputs = iter(["e", ""])

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=True,
            ),
            patch("builtins.input", side_effect=inputs),
        ):
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            # Should fallback to recommended command
            assert (
                result["test_command"]
                == "pytest --json-report --json-report-file=.adw/test-results.json"
            )
            assert result["output_format"] == "json"

    def test_setup_pytest_with_plugin_installed_reject(self, monkeypatch, tmp_path):
        """Test setup_pytest when user rejects JSON mode."""
        monkeypatch.chdir(tmp_path)

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=True,
            ),
            patch("builtins.input", return_value="r"),
        ):  # User rejects
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            assert result == {
                "framework": "pytest",
                "test_command": "pytest",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

    def test_setup_pytest_with_plugin_installed_invalid_choice(
        self, monkeypatch, tmp_path
    ):
        """Test setup_pytest when user enters invalid choice (defaults to reject)."""
        monkeypatch.chdir(tmp_path)

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=True,
            ),
            patch("builtins.input", return_value="xyz"),
        ):  # Invalid choice
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            # Should default to console fallback
            assert result["test_command"] == "pytest"
            assert result["output_format"] == "console"
            assert result["parser"] == "console"

    def test_setup_pytest_without_plugin_user_installs(self, monkeypatch, tmp_path):
        """Test setup_pytest when plugin not installed and user chooses to install."""
        monkeypatch.chdir(tmp_path)

        # Mock: plugin not installed initially, then user installs, then user accepts config
        def mock_check_installed():
            # First call: not installed
            # Second call (after install): installed
            if not hasattr(mock_check_installed, "call_count"):
                mock_check_installed.call_count = 0
            mock_check_installed.call_count += 1
            return mock_check_installed.call_count > 1

        inputs = iter(["y", "a"])  # Install plugin, then accept config

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                side_effect=mock_check_installed,
            ),
            patch(
                "scripts.adw_config_test.install_pytest_json_report", return_value=True
            ),
            patch("builtins.input", side_effect=inputs),
        ):
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            # Should have JSON config since plugin was installed
            assert result["output_format"] == "json"
            assert (
                result["test_command"]
                == "pytest --json-report --json-report-file=.adw/test-results.json"
            )
            assert result["parser"] == "pytest"

    def test_setup_pytest_without_plugin_user_declines_install(
        self, monkeypatch, tmp_path
    ):
        """Test setup_pytest when plugin not installed and user declines installation."""
        monkeypatch.chdir(tmp_path)

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=False,
            ),
            patch("builtins.input", return_value="n"),
        ):  # User declines install
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            # Should use console fallback
            assert result == {
                "framework": "pytest",
                "test_command": "pytest",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

    def test_setup_pytest_without_plugin_install_fails(self, monkeypatch, tmp_path):
        """Test setup_pytest when plugin installation fails."""
        monkeypatch.chdir(tmp_path)

        inputs = iter(["y"])  # User tries to install

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=False,
            ),
            patch(
                "scripts.adw_config_test.install_pytest_json_report", return_value=False
            ),
            patch("builtins.input", side_effect=inputs),
        ):
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            # Should fallback to console mode
            assert result["output_format"] == "console"
            assert result["test_command"] == "pytest"
            assert result["parser"] == "console"

    def test_setup_pytest_return_dict_structure(self, monkeypatch, tmp_path):
        """Test setup_pytest always returns dict with required keys."""
        monkeypatch.chdir(tmp_path)

        with (
            patch(
                "scripts.adw_config_test.check_pytest_json_report_installed",
                return_value=True,
            ),
            patch("builtins.input", return_value="a"),
        ):
            from scripts.adw_config_test import setup_pytest

            result = setup_pytest()

            # Verify all required keys exist
            required_keys = [
                "framework",
                "test_command",
                "output_format",
                "json_output_file",
                "parser",
            ]
            for key in required_keys:
                assert key in result, f"Missing required key: {key}"

            # Verify framework is always pytest
            assert result["framework"] == "pytest"

    def test_detect_test_framework_calls_setup_pytest(self, monkeypatch, tmp_path):
        """Test detect_test_framework calls setup_pytest for pytest projects."""
        monkeypatch.chdir(tmp_path)

        # Create pytest.ini to trigger pytest detection
        (tmp_path / "pytest.ini").write_text("[pytest]\n")

        with patch("scripts.adw_config_test.setup_pytest") as mock_setup_pytest:
            mock_setup_pytest.return_value = {
                "framework": "pytest",
                "test_command": "pytest",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

            from scripts.adw_config_test import detect_test_framework

            result = detect_test_framework()

            # Verify setup_pytest was called
            mock_setup_pytest.assert_called_once()

            # Verify result is from setup_pytest
            assert result["framework"] == "pytest"
