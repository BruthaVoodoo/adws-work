#!/usr/bin/env python3
"""
Unit tests for Pytest JSON parser.

Tests coverage:
- parse_pytest_json() with pytest-json-report formats
- Fixture errors
- Multiple test failures
- Edge cases and error handling
"""

import json
import pytest
import tempfile
import os

# Import functions under test
from scripts.adw_modules.test_parsers import (
    parse_pytest_json,
)


class TestPytestParser:
    """Test suite for parse_pytest_json() function."""

    def test_file_not_found_returns_error(self):
        """Test that missing file returns error structure."""
        result = parse_pytest_json("/nonexistent/path/report.json")

        assert result["test_framework"] == "pytest"
        assert "error" in result
        assert "File not found" in result["error"]

    def test_fixture_error(self):
        """Test parsing pytest fixture error."""
        pytest_output = {
            "summary": {"total": 1, "passed": 0, "failed": 0, "error": 1},
            "tests": [
                {
                    "nodeid": "tests/test_app.py::test_with_db",
                    "outcome": "failed",
                    "location": ["tests/test_app.py", 10, "test_with_db"],
                    "call": {
                        "longrepr": "ERROR at setup of test_with_db\n"
                        "fixture 'db_connection' not found\n"
                        "available fixtures: cache, capfd, capsys\n"
                        ">   fixture 'db_connection' not found"
                    },
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            assert len(result["failed_test_details"]) == 1
            failed = result["failed_test_details"][0]
            assert "fixture" in failed["error_message"].lower()
            assert "db_connection" in failed["error_message"]
        finally:
            os.unlink(temp_path)

    def test_multiple_failed_tests_different_files(self):
        """Test parsing multiple failures across different files."""
        pytest_output = {
            "summary": {"total": 5, "passed": 2, "failed": 3},
            "tests": [
                {
                    "nodeid": "tests/test_math.py::test_add",
                    "outcome": "passed",
                    "location": ["tests/test_math.py", 5, "test_add"],
                },
                {
                    "nodeid": "tests/test_math.py::test_subtract",
                    "outcome": "failed",
                    "location": ["tests/test_math.py", 10, "test_subtract"],
                    "call": {"longrepr": "AssertionError: assert 1 == 2"},
                },
                {
                    "nodeid": "tests/test_string.py::test_concat",
                    "outcome": "failed",
                    "location": ["tests/test_string.py", 8, "test_concat"],
                    "call": {"longrepr": "TypeError: can only concatenate str"},
                },
                {
                    "nodeid": "tests/test_string.py::test_split",
                    "outcome": "passed",
                    "location": ["tests/test_string.py", 15, "test_split"],
                },
                {
                    "nodeid": "tests/test_api.py::test_fetch",
                    "outcome": "failed",
                    "location": ["tests/test_api.py", 20, "test_fetch"],
                    "call": {"longrepr": "ConnectionError: Failed to fetch"},
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            assert result["failed_tests"] == 3
            assert len(result["failed_test_details"]) == 3

            # Verify different files
            files = [f["file_path"] for f in result["failed_test_details"]]
            assert "tests/test_math.py" in files
            assert "tests/test_string.py" in files
            assert "tests/test_api.py" in files
        finally:
            os.unlink(temp_path)

    def test_longrepr_dict_format(self):
        """Test handling of longrepr as dict (alternative pytest format)."""
        pytest_output = {
            "summary": {"total": 1, "passed": 0, "failed": 1},
            "tests": [
                {
                    "nodeid": "test.py::test_func",
                    "outcome": "failed",
                    "location": ["test.py", 1, "test_func"],
                    "call": {
                        "longrepr": {
                            "reprcrash": {
                                "path": "test.py",
                                "lineno": 5,
                                "message": "AssertionError: assert False",
                            },
                            "reprtraceback": {
                                "entries": [{"data": "test.py:5: AssertionError"}]
                            },
                        }
                    },
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            assert len(result["failed_test_details"]) == 1
            # Should convert dict to string
            assert isinstance(result["failed_test_details"][0]["error_message"], str)
        finally:
            os.unlink(temp_path)

    def test_all_tests_passed(self):
        """Test parsing pytest output with all tests passing."""
        pytest_output = {"summary": {"total": 5, "passed": 5, "failed": 0}, "tests": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            assert result["test_framework"] == "pytest"
            assert result["total_tests"] == 5
            assert result["passed_tests"] == 5
            assert result["failed_tests"] == 0
            assert len(result["failed_test_details"]) == 0
        finally:
            os.unlink(temp_path)

    def test_single_failed_test(self):
        """Test parsing pytest output with single failed test."""
        pytest_output = {
            "summary": {"total": 3, "passed": 2, "failed": 1},
            "tests": [
                {
                    "nodeid": "tests/test_math.py::test_addition",
                    "outcome": "passed",
                    "location": ["tests/test_math.py", 10, "test_addition"],
                },
                {
                    "nodeid": "tests/test_math.py::test_subtraction",
                    "outcome": "failed",
                    "location": ["tests/test_math.py", 15, "test_subtraction"],
                    "call": {
                        "longrepr": "AssertionError: assert 1 == 2\n  where 1 = subtract(5, 3)"
                    },
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            assert result["test_framework"] == "pytest"
            assert result["total_tests"] == 3
            assert result["passed_tests"] == 2
            assert result["failed_tests"] == 1
            assert len(result["failed_test_details"]) == 1

            failed_test = result["failed_test_details"][0]
            assert failed_test["test_name"] == "tests/test_math.py::test_subtraction"
            assert failed_test["file_path"] == "tests/test_math.py"
            assert "AssertionError" in failed_test["error_message"]
        finally:
            os.unlink(temp_path)

    def test_pytest_assert_introspection_cleaned(self):
        """Test that pytest assert introspection output is cleaned."""
        verbose_assert = """
AssertionError: assert 1 == 2
  where 1 = subtract(5, 3)
  and 2 = expected_value
Very long detailed comparison output that goes on for many lines and contains 
unnecessary verbose information about variable states and comparisons that are 
not helpful for the LLM to understand the core issue with the test failure here.
""" + ("x" * 300)  # Very long line

        pytest_output = {
            "summary": {"total": 1, "passed": 0, "failed": 1},
            "tests": [
                {
                    "nodeid": "test.py::test_func",
                    "outcome": "failed",
                    "location": ["test.py", 1, "test_func"],
                    "call": {"longrepr": verbose_assert},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            failed_test = result["failed_test_details"][0]
            stack_trace = failed_test["stack_trace"]

            # Should keep AssertionError
            assert "AssertionError" in stack_trace
            # Should remove very long lines
            for line in stack_trace.split("\n"):
                assert len(line) < 250  # Should be reasonable length
        finally:
            os.unlink(temp_path)


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
