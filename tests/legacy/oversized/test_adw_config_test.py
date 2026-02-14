"""
Unit tests for adw_config_test module.

Tests the test configuration reconfiguration command including:
- Display current configuration
- Test framework detection
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
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from scripts.adw_config_test import (
    display_current_config,
    detect_test_framework,
    edit_test_command,
    switch_to_fallback_mode,
    validate_configuration,
    save_configuration,
    setup_custom_framework,
    check_pytest_json_report_installed,
    install_pytest_json_report,
    offer_pytest_json_report_install,
)


class TestDisplayCurrentConfig:
    """Tests for display_current_config function."""

    def test_display_empty_config(self, capsys):
        """Test displaying when no test_configuration exists."""
        with patch("scripts.adw_config_test.config._data", {}):
            result = display_current_config()

            assert result == {}
            captured = capsys.readouterr()
            assert "No test_configuration found" in captured.out

    def test_display_existing_config(self, capsys):
        """Test displaying existing test configuration."""
        test_config = {
            "framework": "jest",
            "test_command": "npm test",
            "output_format": "json",
            "json_output_file": ".adw/test-results.json",
            "parser": "jest",
        }

        with patch(
            "scripts.adw_config_test.config._data", {"test_configuration": test_config}
        ):
            result = display_current_config()

            assert result == test_config
            captured = capsys.readouterr()
            assert "jest" in captured.out
            assert "npm test" in captured.out
            assert "json" in captured.out


class TestDetectTestFramework:
    """Tests for detect_test_framework function."""

    def test_detect_jest(self, tmp_path, capsys):
        """Test detecting Jest framework."""
        # Create package.json with Jest
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"jest": "^29.0.0"}}')

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch("builtins.input", return_value="a"):  # User accepts
                result = detect_test_framework()

                assert result["framework"] == "jest"
                assert "npm test" in result["test_command"]
                assert result["output_format"] == "json"
                assert result["parser"] == "jest"

                captured = capsys.readouterr()
                assert "Detected: Jest" in captured.out

    def test_detect_react_scripts(self, tmp_path, capsys):
        """Test detecting React (which includes Jest)."""
        package_json = tmp_path / "package.json"
        package_json.write_text('{"dependencies": {"react-scripts": "^5.0.0"}}')

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch("builtins.input", return_value="a"):  # User accepts
                result = detect_test_framework()

                assert result["framework"] == "jest"
                assert "npm test" in result["test_command"]

                captured = capsys.readouterr()
                assert "Detected: Jest" in captured.out

    def test_detect_pytest_with_plugin(self, tmp_path, capsys):
        """Test detecting Pytest with pytest-json-report plugin."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch(
                "scripts.adw_config_test.offer_pytest_json_report_install",
                return_value=True,
            ):
                with patch("builtins.input", return_value="a"):  # User accepts
                    result = detect_test_framework()

                    assert result["framework"] == "pytest"
                    assert "--json-report" in result["test_command"]
                    assert result["output_format"] == "json"

                    captured = capsys.readouterr()
                    assert "Detected: Pytest" in captured.out
                    assert "plugin available" in captured.out

    def test_detect_pytest_without_plugin(self, tmp_path, capsys):
        """Test detecting Pytest without JSON plugin."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch(
                "scripts.adw_config_test.offer_pytest_json_report_install",
                return_value=False,
            ):
                result = detect_test_framework()

                assert result["framework"] == "pytest"
                assert result["test_command"] == "pytest"
                assert result["output_format"] == "console"
                assert result["parser"] == "console"

                captured = capsys.readouterr()
                assert "console fallback mode" in captured.out

    def test_detect_go(self, tmp_path, capsys):
        """Test detecting Go test framework."""
        go_mod = tmp_path / "go.mod"
        go_mod.write_text("module example.com/myapp\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            result = detect_test_framework()

            assert result["framework"] == "go"
            assert result["test_command"] == "go test ./..."
            assert result["output_format"] == "console"

    def test_detect_rust(self, tmp_path, capsys):
        """Test detecting Rust test framework."""
        cargo_toml = tmp_path / "Cargo.toml"
        cargo_toml.write_text("[package]\nname = 'myapp'\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            result = detect_test_framework()

            assert result["framework"] == "rust"
            assert result["test_command"] == "cargo test"

    def test_detect_no_framework(self, tmp_path, capsys):
        """Test when no framework can be detected."""
        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            result = detect_test_framework()

            assert result == {}
            captured = capsys.readouterr()
            assert "Could not detect" in captured.out


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


class TestIntegration:
    """Integration tests for full workflow."""

    def test_detect_and_save_workflow(self, tmp_path):
        """Test complete workflow: detect -> validate -> save."""
        # Setup test project with Jest
        package_json = tmp_path / "package.json"
        package_json.write_text('{"devDependencies": {"jest": "^29.0.0"}}')

        # Create ADWS directory
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        config_file = adws_dir / "config.yaml"
        config_file.write_text("language: javascript\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch("builtins.input", return_value="a"):  # User accepts
                # Step 1: Detect
                detected = detect_test_framework()
                assert detected["framework"] == "jest"

                # Step 2: Save
                result = save_configuration(detected)
                assert result is True

                # Step 3: Verify
                with open(config_file) as f:
                    saved = yaml.safe_load(f)

                assert saved["test_configuration"]["framework"] == "jest"
                assert "npm test" in saved["test_configuration"]["test_command"]


class TestSetupCustomFramework:
    """Tests for setup_custom_framework function."""

    def test_setup_custom_console_mode(self, capsys):
        """Test setting up custom framework with console output."""
        inputs = ["go test ./...", "n"]  # command, no JSON support

        with patch("builtins.input", side_effect=inputs):
            result = setup_custom_framework()

            assert result["framework"] == "custom"
            assert result["test_command"] == "go test ./..."
            assert result["output_format"] == "console"
            assert result["parser"] == "console"
            assert result["json_output_file"] is None

            captured = capsys.readouterr()
            assert "Custom Framework Setup" in captured.out
            assert "Using console output mode" in captured.out

    def test_setup_custom_json_mode(self, capsys):
        """Test setting up custom framework with JSON output."""
        inputs = [
            "rspec --format json",  # command
            "y",  # has JSON support
            ".adw/rspec-results.json",  # JSON file path
            "n",  # don't update command
        ]

        with patch("builtins.input", side_effect=inputs):
            result = setup_custom_framework()

            assert result["framework"] == "custom"
            assert result["test_command"] == "rspec --format json"
            assert result["output_format"] == "json"
            assert result["parser"] == "generic"
            assert result["json_output_file"] == ".adw/rspec-results.json"

            captured = capsys.readouterr()
            assert "JSON output file: .adw/rspec-results.json" in captured.out

    def test_setup_custom_json_mode_with_command_update(self, capsys):
        """Test setting up custom framework and updating command for JSON flags."""
        inputs = [
            "mvn test",  # initial command
            "y",  # has JSON support
            "target/surefire-reports/TEST-results.json",  # JSON file
            "y",  # update command
            "mvn test -Dsurefire.reportFormat=json",  # updated command
        ]

        with patch("builtins.input", side_effect=inputs):
            result = setup_custom_framework()

            assert result["framework"] == "custom"
            assert result["test_command"] == "mvn test -Dsurefire.reportFormat=json"
            assert result["output_format"] == "json"
            assert result["parser"] == "generic"

    def test_setup_custom_json_without_file_path(self, capsys):
        """Test JSON mode selection but no file path provided (fallback to console)."""
        inputs = [
            "cargo test",  # command
            "y",  # has JSON support
            "",  # no file path
        ]

        with patch("builtins.input", side_effect=inputs):
            result = setup_custom_framework()

            assert result["framework"] == "custom"
            assert result["test_command"] == "cargo test"
            assert result["output_format"] == "console"
            assert result["parser"] == "console"
            assert result["json_output_file"] is None

            captured = capsys.readouterr()
            assert "falling back to console mode" in captured.out

    def test_setup_custom_empty_command(self, capsys):
        """Test setup with empty command returns empty dict."""
        inputs = [""]  # empty command

        with patch("builtins.input", side_effect=inputs):
            result = setup_custom_framework()

            assert result == {}

            captured = capsys.readouterr()
            assert "Test command is required" in captured.out

    def test_setup_custom_displays_examples(self, capsys):
        """Test that examples are displayed to user."""
        inputs = ["dotnet test", "n"]

        with patch("builtins.input", side_effect=inputs):
            setup_custom_framework()

            captured = capsys.readouterr()
            assert "Examples of test commands:" in captured.out
            assert "go test" in captured.out
            assert "rspec" in captured.out
            assert "mvn test" in captured.out
            assert "cargo test" in captured.out
            assert "dotnet test" in captured.out


class TestPytestJsonReportInstallation:
    """Tests for pytest-json-report installation functions."""

    def test_check_pytest_json_report_installed_true(self):
        """Test checking for installed pytest-json-report."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = check_pytest_json_report_installed()

            assert result is True
            mock_run.assert_called_once()
            assert "pip" in mock_run.call_args[0][0]
            assert "show" in mock_run.call_args[0][0]
            assert "pytest-json-report" in mock_run.call_args[0][0]

    def test_check_pytest_json_report_installed_false(self):
        """Test checking for missing pytest-json-report."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = check_pytest_json_report_installed()

            assert result is False

    def test_check_pytest_json_report_exception(self):
        """Test handling exception during check."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Command failed")

            result = check_pytest_json_report_installed()

            assert result is False

    def test_install_pytest_json_report_success(self, capsys):
        """Test successful installation of pytest-json-report."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")

            result = install_pytest_json_report()

            assert result is True
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "pip" in call_args
            assert "install" in call_args
            assert "pytest-json-report" in call_args

            captured = capsys.readouterr()
            assert "Installing pytest-json-report" in captured.out
            assert "installed successfully" in captured.out

    def test_install_pytest_json_report_failure(self, capsys):
        """Test failed installation of pytest-json-report."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Installation error"
            )

            result = install_pytest_json_report()

            assert result is False

            captured = capsys.readouterr()
            assert "Installation failed" in captured.out

    def test_install_pytest_json_report_timeout(self, capsys):
        """Test installation timeout."""
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired("pip install", 120)

            result = install_pytest_json_report()

            assert result is False

            captured = capsys.readouterr()
            assert "timed out" in captured.out

    def test_install_pytest_json_report_exception(self, capsys):
        """Test installation exception handling."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = install_pytest_json_report()

            assert result is False

            captured = capsys.readouterr()
            assert "Installation error" in captured.out

    def test_offer_pytest_json_report_already_installed(self):
        """Test offer when package is already installed."""
        with patch(
            "scripts.adw_config_test.check_pytest_json_report_installed",
            return_value=True,
        ):
            result = offer_pytest_json_report_install()

            assert result is True

    def test_offer_pytest_json_report_user_accepts(self, capsys):
        """Test offer when user accepts installation."""
        with patch(
            "scripts.adw_config_test.check_pytest_json_report_installed"
        ) as mock_check:
            # First call: not installed, second call after install: installed
            mock_check.side_effect = [False, True]

            with patch(
                "scripts.adw_config_test.install_pytest_json_report", return_value=True
            ):
                with patch("builtins.input", return_value="y"):
                    result = offer_pytest_json_report_install()

                    assert result is True

                    captured = capsys.readouterr()
                    assert (
                        "pytest-json-report plugin enables JSON output" in captured.out
                    )
                    assert "Benefits:" in captured.out

    def test_offer_pytest_json_report_user_declines(self, capsys):
        """Test offer when user declines installation."""
        with patch(
            "scripts.adw_config_test.check_pytest_json_report_installed",
            return_value=False,
        ):
            with patch("builtins.input", return_value="n"):
                result = offer_pytest_json_report_install()

                assert result is False

                captured = capsys.readouterr()
                assert "Skipping installation" in captured.out
                assert "console fallback mode" in captured.out

    def test_offer_pytest_json_report_install_fails(self, capsys):
        """Test offer when installation fails."""
        with patch(
            "scripts.adw_config_test.check_pytest_json_report_installed",
            return_value=False,
        ):
            with patch(
                "scripts.adw_config_test.install_pytest_json_report", return_value=False
            ):
                with patch("builtins.input", return_value="y"):
                    result = offer_pytest_json_report_install()

                    assert result is False

                    captured = capsys.readouterr()
                    assert "Installation failed" in captured.out

    def test_offer_pytest_json_report_install_verification_fails(self, capsys):
        """Test offer when install succeeds but verification fails."""
        with patch(
            "scripts.adw_config_test.check_pytest_json_report_installed"
        ) as mock_check:
            # First: not installed, after install: still not installed (verification fails)
            mock_check.side_effect = [False, False]

            with patch(
                "scripts.adw_config_test.install_pytest_json_report", return_value=True
            ):
                with patch("builtins.input", return_value="y"):
                    result = offer_pytest_json_report_install()

                    assert result is False

                    captured = capsys.readouterr()
                    assert "verification failed" in captured.out


class TestDetectTestFrameworkWithAutoInstall:
    """Tests for framework detection with auto-install integration."""

    def test_detect_pytest_offers_install_when_missing(self, tmp_path, capsys):
        """Test that pytest detection offers to install plugin when missing."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch(
                "scripts.adw_config_test.offer_pytest_json_report_install",
                return_value=False,
            ):
                result = detect_test_framework()

                assert result["framework"] == "pytest"
                assert result["output_format"] == "console"
                assert result["parser"] == "console"

    def test_detect_pytest_uses_json_when_installed(self, tmp_path, capsys):
        """Test that pytest detection uses JSON mode when plugin is available."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        with patch("scripts.adw_config_test.Path.cwd", return_value=tmp_path):
            with patch(
                "scripts.adw_config_test.offer_pytest_json_report_install",
                return_value=True,
            ):
                with patch("builtins.input", return_value="a"):  # User accepts
                    result = detect_test_framework()

                    assert result["framework"] == "pytest"
                    assert result["output_format"] == "json"
                    assert result["parser"] == "pytest"
                    assert "--json-report" in result["test_command"]
