"""
Tests for adw_test.py configuration integration with test_parsers.

Verifies that run_tests() correctly:
1. Loads test configuration from config.yaml
2. Routes to JSON parser when output_format="json"
3. Routes to console parser when output_format="console"
4. Handles missing/invalid configuration gracefully
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path


class TestAdwTestConfigIntegration:
    """Test adw_test.py integration with test configuration."""

    @patch("scripts.adw_test.subprocess.run")
    @patch("scripts.adw_test.config")
    def test_run_tests_uses_json_parser_when_configured(
        self, mock_config, mock_subprocess
    ):
        """Test that run_tests routes to JSON parser when output_format is json."""
        from scripts.adw_test import run_tests
        from scripts.adw_modules.data_types import TestResult
        import logging

        # Setup mock config with JSON output
        mock_config._data = {
            "test_configuration": {
                "framework": "jest",
                "test_command": "npm test -- --json --outputFile=test-results.json",
                "output_format": "json",
                "json_output_file": "test-results.json",
            }
        }
        mock_config.unit_test_timeout = 300

        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Tests passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Mock JSON parser response
        with patch("scripts.adw_test.run_and_parse_json") as mock_run_and_parse_json:
            mock_run_and_parse_json.return_value = (
                [
                    TestResult(
                        test_name="Test Suite",
                        passed=True,
                        execution_command="npm test",
                        test_purpose="Full test suite",
                        error=None,
                    )
                ],
                1,
                0,
            )

            # Execute
            logger = logging.getLogger("test")
            success, output, results, passed, failed = run_tests("test_adw_id", logger)

            # Verify JSON parser was called
            mock_run_and_parse_json.assert_called_once()
            assert success is True
            assert passed == 1
            assert failed == 0

    @patch("scripts.adw_test.subprocess.run")
    @patch("scripts.adw_test.config")
    def test_run_tests_uses_console_parser_when_configured(
        self, mock_config, mock_subprocess
    ):
        """Test that run_tests routes to console parser when output_format is console."""
        from scripts.adw_test import run_tests
        from scripts.adw_modules.data_types import TestResult
        import logging

        # Setup mock config with console output
        mock_config._data = {
            "test_configuration": {
                "framework": "pytest",
                "test_command": "pytest",
                "output_format": "console",
            }
        }
        mock_config.unit_test_timeout = 300

        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "All tests passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Mock console parser response
        with patch(
            "scripts.adw_test.run_and_parse_console"
        ) as mock_run_and_parse_console:
            mock_run_and_parse_console.return_value = (
                [
                    TestResult(
                        test_name="Test Suite",
                        passed=True,
                        execution_command="pytest",
                        test_purpose="Full test suite",
                        error=None,
                    )
                ],
                1,
                0,
            )

            # Execute
            logger = logging.getLogger("test")
            success, output, results, passed, failed = run_tests("test_adw_id", logger)

            # Verify console parser was called
            mock_run_and_parse_console.assert_called_once()
            assert success is True
            assert passed == 1
            assert failed == 0

    @patch("scripts.adw_test.subprocess.run")
    @patch("scripts.adw_test.config")
    def test_run_tests_handles_missing_config_gracefully(
        self, mock_config, mock_subprocess
    ):
        """Test that run_tests falls back to console parser when config is missing."""
        from scripts.adw_test import run_tests
        from scripts.adw_modules.data_types import TestResult
        import logging

        # Setup mock config with no test_configuration
        mock_config._data = {}
        mock_config.test_command = "pytest"
        mock_config.unit_test_timeout = 300

        # Mock subprocess result
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "All tests passed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Mock console parser response
        with patch(
            "scripts.adw_test.run_and_parse_console"
        ) as mock_run_and_parse_console:
            mock_run_and_parse_console.return_value = (
                [
                    TestResult(
                        test_name="Test Suite",
                        passed=True,
                        execution_command="pytest",
                        test_purpose="Full test suite",
                        error=None,
                    )
                ],
                1,
                0,
            )

            # Execute
            logger = logging.getLogger("test")
            success, output, results, passed, failed = run_tests("test_adw_id", logger)

            # Verify console parser was used as fallback
            mock_run_and_parse_console.assert_called_once()
            assert success is True

    @patch("scripts.adw_test.subprocess.run")
    @patch("scripts.adw_test.config")
    @patch("builtins.open", new_callable=mock_open, read_data='{"passed": true}')
    def test_run_and_parse_json_handles_jest_format(
        self, mock_file, mock_config, mock_subprocess
    ):
        """Test that run_and_parse_json correctly handles Jest JSON format."""
        from scripts.adw_test import run_and_parse_json
        import logging

        logger = logging.getLogger("test")

        with patch(
            "scripts.adw_modules.test_parsers.parse_jest_json"
        ) as mock_parse_jest:
            mock_parse_jest.return_value = {
                "test_framework": "jest",
                "total_tests": 10,
                "passed_tests": 10,
                "failed_tests": 0,
                "failed_test_details": [],
            }

            results, passed, failed = run_and_parse_json(
                "test-results.json", "jest", "npm test", logger
            )

            mock_parse_jest.assert_called_once_with("test-results.json")
            assert passed == 10
            assert failed == 0
            assert len(results) == 1
            assert results[0].passed is True

    @patch("scripts.adw_test.subprocess.run")
    @patch("scripts.adw_test.config")
    def test_run_and_parse_console_handles_failure_output(
        self, mock_config, mock_subprocess
    ):
        """Test that run_and_parse_console correctly handles test failures."""
        from scripts.adw_test import run_and_parse_console
        import logging

        logger = logging.getLogger("test")

        console_output = """
        FAIL src/test.js
        ● Test failed
        Expected true but got false
        """

        with patch(
            "scripts.adw_modules.test_parsers.parse_console_output"
        ) as mock_parse_console:
            mock_parse_console.return_value = {
                "test_framework": "console",
                "parse_mode": "console",
                "failed_test_details": [
                    {
                        "test_name": "Test failed",
                        "file_path": "src/test.js",
                        "error_message": "Expected true but got false",
                        "stack_trace": "Expected true but got false",
                    }
                ],
                "original_size": 100,
                "compressed_size": 80,
                "reduction_percent": 20.0,
            }

            results, passed, failed = run_and_parse_console(
                console_output, 1, "npm test", logger
            )

            mock_parse_console.assert_called_once_with(console_output)
            assert failed == 1
            assert passed == 0
            assert len(results) == 1
            assert results[0].passed is False
            assert (
                results[0].error and "Expected true but got false" in results[0].error
            )

    @patch("scripts.adw_test.subprocess.run")
    @patch("scripts.adw_test.config")
    def test_run_and_parse_json_handles_parsing_errors(
        self, mock_config, mock_subprocess
    ):
        """Test that run_and_parse_json handles JSON parsing errors gracefully."""
        from scripts.adw_test import run_and_parse_json
        import logging

        logger = logging.getLogger("test")

        with patch(
            "scripts.adw_modules.test_parsers.parse_jest_json"
        ) as mock_parse_jest:
            mock_parse_jest.return_value = {
                "test_framework": "jest",
                "error": "File not found: test-results.json",
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "failed_test_details": [],
            }

            results, passed, failed = run_and_parse_json(
                "test-results.json", "jest", "npm test", logger
            )

            assert failed == 1
            assert passed == 0
            assert len(results) == 1
            assert results[0].passed is False
            assert results[0].error and "JSON parsing failed" in results[0].error
