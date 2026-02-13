"""
Tests for setup_jest() function in adw_config_test.py

Verifies interactive Jest configuration flow:
1. Jest has built-in JSON support (no plugin required)
2. Displays recommended JSON command with benefits
3. Handles user accept/edit/reject choices
4. Returns appropriate test config dict
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestSetupJest:
    """Test setup_jest() interactive flow."""

    def test_setup_jest_accept_recommended(self, monkeypatch, tmp_path):
        """Test setup_jest when user accepts recommended command."""
        monkeypatch.chdir(tmp_path)

        with patch("builtins.input", return_value="a"):  # User accepts
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            assert result == {
                "framework": "jest",
                "test_command": "npm test -- --json --outputFile=.adw/test-results.json",
                "output_format": "json",
                "json_output_file": ".adw/test-results.json",
                "parser": "jest",
            }

    def test_setup_jest_edit_command(self, monkeypatch, tmp_path):
        """Test setup_jest when user chooses to edit command."""
        monkeypatch.chdir(tmp_path)

        # User chooses edit, then enters custom command
        inputs = iter(["e", "npm test -- --json --outputFile=custom.json --coverage"])

        with patch("builtins.input", side_effect=inputs):
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            assert result["framework"] == "jest"
            assert (
                result["test_command"]
                == "npm test -- --json --outputFile=custom.json --coverage"
            )
            assert result["output_format"] == "json"
            assert result["parser"] == "jest"

    def test_setup_jest_edit_empty_command(self, monkeypatch, tmp_path):
        """Test setup_jest when user chooses edit but enters empty string."""
        monkeypatch.chdir(tmp_path)

        # User chooses edit, then enters nothing (fallback to recommended)
        inputs = iter(["e", ""])

        with patch("builtins.input", side_effect=inputs):
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            # Should fallback to recommended command
            assert (
                result["test_command"]
                == "npm test -- --json --outputFile=.adw/test-results.json"
            )
            assert result["output_format"] == "json"
            assert result["parser"] == "jest"

    def test_setup_jest_reject_json_mode(self, monkeypatch, tmp_path):
        """Test setup_jest when user rejects JSON mode."""
        monkeypatch.chdir(tmp_path)

        with patch("builtins.input", return_value="r"):  # User rejects
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            assert result == {
                "framework": "jest",
                "test_command": "npm test",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

    def test_setup_jest_invalid_choice(self, monkeypatch, tmp_path):
        """Test setup_jest when user enters invalid choice (defaults to reject)."""
        monkeypatch.chdir(tmp_path)

        with patch("builtins.input", return_value="xyz"):  # Invalid choice
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            # Should default to console fallback
            assert result["test_command"] == "npm test"
            assert result["output_format"] == "console"
            assert result["parser"] == "console"

    def test_setup_jest_return_dict_structure(self, monkeypatch, tmp_path):
        """Test setup_jest always returns dict with required keys."""
        monkeypatch.chdir(tmp_path)

        with patch("builtins.input", return_value="a"):
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

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

            # Verify framework is always jest
            assert result["framework"] == "jest"

    def test_setup_jest_json_mode_has_correct_parser(self, monkeypatch, tmp_path):
        """Test setup_jest returns 'jest' parser when JSON mode selected."""
        monkeypatch.chdir(tmp_path)

        with patch("builtins.input", return_value="a"):
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            assert result["parser"] == "jest"
            assert result["output_format"] == "json"

    def test_setup_jest_console_mode_has_correct_parser(self, monkeypatch, tmp_path):
        """Test setup_jest returns 'console' parser when console mode selected."""
        monkeypatch.chdir(tmp_path)

        with patch("builtins.input", return_value="r"):
            from scripts.adw_config_test import setup_jest

            result = setup_jest()

            assert result["parser"] == "console"
            assert result["output_format"] == "console"
            assert result["json_output_file"] is None


class TestDetectJestFramework:
    """Test detect_test_framework calls setup_jest for Jest projects."""

    def test_detect_calls_setup_jest_for_jest_dependency(self, monkeypatch, tmp_path):
        """Test detect_test_framework calls setup_jest when jest is in devDependencies."""
        monkeypatch.chdir(tmp_path)

        # Create package.json with jest in devDependencies
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"jest": "^29.0.0"}}')

        with patch("scripts.adw_config_test.setup_jest") as mock_setup_jest:
            mock_setup_jest.return_value = {
                "framework": "jest",
                "test_command": "npm test",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

            from scripts.adw_config_test import detect_test_framework

            result = detect_test_framework()

            # Verify setup_jest was called
            mock_setup_jest.assert_called_once()

            # Verify result is from setup_jest
            assert result["framework"] == "jest"

    def test_detect_calls_setup_jest_for_react_scripts(self, monkeypatch, tmp_path):
        """Test detect_test_framework calls setup_jest when react-scripts is detected."""
        monkeypatch.chdir(tmp_path)

        # Create package.json with react-scripts
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"react-scripts": "^5.0.0"}}')

        with patch("scripts.adw_config_test.setup_jest") as mock_setup_jest:
            mock_setup_jest.return_value = {
                "framework": "jest",
                "test_command": "npm test",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

            from scripts.adw_config_test import detect_test_framework

            result = detect_test_framework()

            # Verify setup_jest was called
            mock_setup_jest.assert_called_once()

            # Verify result is from setup_jest
            assert result["framework"] == "jest"

    def test_detect_calls_setup_jest_for_jest_in_dependencies(
        self, monkeypatch, tmp_path
    ):
        """Test detect_test_framework calls setup_jest when jest is in dependencies."""
        monkeypatch.chdir(tmp_path)

        # Create package.json with jest in dependencies (unusual but valid)
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"jest": "^29.0.0"}}')

        with patch("scripts.adw_config_test.setup_jest") as mock_setup_jest:
            mock_setup_jest.return_value = {
                "framework": "jest",
                "test_command": "npm test",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

            from scripts.adw_config_test import detect_test_framework

            result = detect_test_framework()

            # Verify setup_jest was called
            mock_setup_jest.assert_called_once()

            # Verify result is from setup_jest
            assert result["framework"] == "jest"
