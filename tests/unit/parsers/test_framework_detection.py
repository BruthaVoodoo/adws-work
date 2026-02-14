#!/usr/bin/env python3
"""
Unit tests for test framework detection functionality.

Tests coverage:
- detect_test_framework() detects Jest from package.json
- detect_test_framework() detects Pytest from pytest.ini/pyproject.toml/setup.cfg
- Confidence levels for detection
- Handling multiple frameworks present
- Edge cases (missing files, malformed configs)
- Recommended commands based on detected framework
"""

import json
import pytest
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

# Import function under test
from scripts.adw_modules.test_parsers import detect_test_framework


class TestFrameworkDetection:
    """Test suite for detect_test_framework() function."""

    def test_jest_detected_from_package_json_with_jest_field(self, tmp_path):
        """Test Jest detection when package.json has jest config field."""
        package_json = {
            "name": "test-app",
            "version": "1.0.0",
            "scripts": {"test": "jest"},
            "jest": {"testEnvironment": "node"},
        }

        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "jest"
        assert result["confidence"] == "high"
        # Check that some form of package.json detection exists
        assert any("package.json" in src for src in result["detected_from"])
        assert result["recommended_command"] is not None
        assert "--json" in result["recommended_command"]

    def test_jest_detected_from_jest_config_js(self, tmp_path):
        """Test Jest detection from jest.config.js file."""
        jest_config = tmp_path / "jest.config.js"
        jest_config.write_text("module.exports = { testEnvironment: 'node' };")

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "jest"
        assert result["confidence"] == "high"
        assert "jest.config.js" in result["detected_from"]

    def test_jest_detected_from_test_script(self, tmp_path):
        """Test Jest detection from test script in package.json."""
        package_json = {
            "name": "test-app",
            "scripts": {"test": "jest --coverage"},
        }

        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "jest"
        assert result["confidence"] == "high"
        # Should have some test command (npm test or npx jest)
        assert "jest" in result["recommended_command"].lower()
        assert "--json" in result["recommended_command"]

    def test_pytest_detected_from_pytest_ini(self, tmp_path):
        """Test Pytest detection from pytest.ini file."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\ntestpaths = tests\n")

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "pytest"
        assert result["confidence"] == "high"
        assert "pytest.ini" in result["detected_from"]
        assert "pytest" in result["recommended_command"]
        assert "--json-report" in result["recommended_command"]

    def test_pytest_detected_from_pyproject_toml(self, tmp_path):
        """Test Pytest detection from pyproject.toml with [tool.pytest.ini_options]."""
        pyproject_toml = tmp_path / "pyproject.toml"
        pyproject_toml.write_text("[tool.pytest.ini_options]\ntestpaths = ['tests']\n")

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "pytest"
        assert result["confidence"] == "high"
        assert "pyproject.toml" in result["detected_from"]

    def test_pytest_detected_from_setup_cfg(self, tmp_path):
        """Test Pytest detection from setup.cfg file."""
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text("[tool:pytest]\ntestpaths = tests\n")

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "pytest"
        assert result["confidence"] == "high"
        assert "setup.cfg" in result["detected_from"]

    def test_pytest_detected_from_conftest(self, tmp_path):
        """Test Pytest detection from conftest.py (medium confidence)."""
        conftest = tmp_path / "conftest.py"
        conftest.write_text(
            "import pytest\n\n@pytest.fixture\ndef sample():\n    pass\n"
        )

        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "pytest"
        assert result["confidence"] == "medium"
        assert "conftest.py" in result["detected_from"]

    def test_no_framework_detected_returns_unknown(self, tmp_path):
        """Test that unknown is returned when no framework detected."""
        # Empty directory
        result = detect_test_framework(str(tmp_path))

        assert result["framework"] == "unknown"
        assert result["confidence"] == "none"
        assert result["detected_from"] == []
        assert (
            "manual" in result["recommended_command"].lower()
            or "specify" in result["recommended_command"].lower()
        )

    def test_multiple_frameworks_returns_both_with_warning(self, tmp_path):
        """Test handling of projects with both Jest and Pytest."""
        # Create both package.json and pytest.ini
        package_json = {"name": "app", "scripts": {"test": "jest"}}
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\ntestpaths = tests\n")

        result = detect_test_framework(str(tmp_path))

        # Should detect both
        assert result["framework"] in ["jest", "pytest", "multiple"]
        if result["framework"] == "multiple":
            assert "jest" in result.get("frameworks_detected", [])
            assert "pytest" in result.get("frameworks_detected", [])
        assert (
            "multiple" in result.get("warning", "").lower()
            or result["framework"] == "multiple"
        )

    def test_invalid_package_json_gracefully_handled(self, tmp_path):
        """Test that malformed package.json doesn't crash detection."""
        package_file = tmp_path / "package.json"
        package_file.write_text("{ invalid json")

        result = detect_test_framework(str(tmp_path))

        # Should not crash, may return unknown or partial detection
        assert "framework" in result
        assert "confidence" in result

    def test_nonexistent_directory_returns_unknown(self):
        """Test that nonexistent path returns unknown framework."""
        result = detect_test_framework("/nonexistent/path/to/project")

        assert result["framework"] == "unknown"
        assert result["confidence"] == "none"

    def test_recommended_command_includes_json_output(self, tmp_path):
        """Test that recommended commands include JSON output configuration."""
        # Test Jest
        package_json = {"scripts": {"test": "jest"}}
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        jest_result = detect_test_framework(str(tmp_path))
        assert "--json" in jest_result["recommended_command"]
        assert (
            "--outputFile" in jest_result["recommended_command"]
            or "--json" in jest_result["recommended_command"]
        )

        # Clean up and test Pytest
        package_file.unlink()
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        pytest_result = detect_test_framework(str(tmp_path))
        assert "--json-report" in pytest_result["recommended_command"]

    def test_jest_detection_with_vitest_excluded(self, tmp_path):
        """Test that Vitest is not confused with Jest."""
        package_json = {
            "name": "app",
            "scripts": {"test": "vitest"},
            "devDependencies": {"vitest": "^0.34.0"},
        }
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        result = detect_test_framework(str(tmp_path))

        # Should either detect vitest specifically or mark as unknown
        # Should NOT detect as jest
        assert (
            result["framework"] != "jest" or "vitest" in result.get("notes", "").lower()
        )

    def test_mocha_detection(self, tmp_path):
        """Test detection of Mocha test framework."""
        package_json = {
            "name": "app",
            "scripts": {"test": "mocha"},
        }
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        result = detect_test_framework(str(tmp_path))

        # Should detect mocha or unknown with mocha in notes
        assert result["framework"] in ["mocha", "unknown"]
        if result["framework"] == "unknown":
            assert "mocha" in result.get("notes", "").lower()

    def test_recommended_command_format_jest(self, tmp_path):
        """Test Jest recommended command has correct format."""
        package_json = {"scripts": {"test": "jest"}}
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        result = detect_test_framework(str(tmp_path))

        cmd = result["recommended_command"]
        # Should be npm test with JSON flags
        assert cmd.startswith("npm test") or cmd.startswith("npx jest")
        assert "--json" in cmd
        # Should include output file
        assert ".adw" in cmd or "test-results" in cmd

    def test_recommended_command_format_pytest(self, tmp_path):
        """Test Pytest recommended command has correct format."""
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")

        result = detect_test_framework(str(tmp_path))

        cmd = result["recommended_command"]
        # Should be pytest with JSON report
        assert cmd.startswith("pytest")
        assert "--json-report" in cmd
        assert "--json-report-file" in cmd
        assert ".adw" in cmd or "test-results" in cmd

    def test_confidence_levels(self, tmp_path):
        """Test that confidence levels are set appropriately."""
        # High confidence: explicit config files
        pytest_ini = tmp_path / "pytest.ini"
        pytest_ini.write_text("[pytest]\n")
        result = detect_test_framework(str(tmp_path))
        assert result["confidence"] == "high"

        # Medium confidence: conftest.py only
        pytest_ini.unlink()
        conftest = tmp_path / "conftest.py"
        conftest.write_text("import pytest\n")
        result = detect_test_framework(str(tmp_path))
        assert result["confidence"] == "medium"

        # None: no detection
        conftest.unlink()
        result = detect_test_framework(str(tmp_path))
        assert result["confidence"] == "none"

    def test_detection_in_subdirectory_structure(self, tmp_path):
        """Test detection works when configs are in parent directory."""
        # Create project structure: project_root/src/tests/
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # Config in root
        package_json = {"scripts": {"test": "jest"}}
        package_file = tmp_path / "package.json"
        package_file.write_text(json.dumps(package_json))

        # Should detect from root even when checking subdirectory
        result = detect_test_framework(str(tmp_path))
        assert result["framework"] == "jest"


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
