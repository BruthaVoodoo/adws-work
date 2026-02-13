#!/usr/bin/env python3
"""
Unit tests for test output parsers (Jest, Pytest, Generic).

Tests coverage:
- parse_jest_json() with various Jest output formats
- parse_pytest_json() with pytest-json-report formats
- parse_generic_json() with unknown test frameworks
- Stack trace compression
- Node_modules filtering
- Edge cases and error handling
"""

import json
import pytest
import tempfile
import os
from pathlib import Path

# Import functions under test
from scripts.adw_modules.test_parsers import (
    parse_jest_json,
    parse_pytest_json,
    parse_generic_json,
    _compress_stack_trace,
    _filter_node_modules_from_stack,
    _clean_pytest_assert_output,
    _identify_framework,
)


class TestJestParser:
    """Test suite for parse_jest_json() function."""

    def test_file_not_found_returns_error(self):
        """Test that missing file returns error structure."""
        result = parse_jest_json("/nonexistent/path/file.json")

        assert result["test_framework"] == "jest"
        assert "error" in result
        assert "File not found" in result["error"]
        assert result["total_tests"] == 0
        assert result["failed_tests"] == 0

    def test_multiple_failed_tests_same_file(self):
        """Test parsing multiple failures in same test file."""
        jest_output = {
            "numTotalTests": 5,
            "numPassedTests": 2,
            "numFailedTests": 3,
            "testResults": [
                {
                    "name": "/project/src/app.test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "fullName": "App renders title",
                            "failureMessages": ["Expected 'Hello' but got 'Hi'"],
                        },
                        {
                            "status": "passed",
                            "fullName": "App has logo",
                        },
                        {
                            "status": "failed",
                            "fullName": "App shows menu",
                            "failureMessages": ["Menu not found"],
                        },
                        {
                            "status": "failed",
                            "fullName": "App handles click",
                            "failureMessages": ["onClick not called"],
                        },
                    ],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            assert result["failed_tests"] == 3
            assert len(result["failed_test_details"]) == 3
            assert all(
                fail["file_path"] == "/project/src/app.test.js"
                for fail in result["failed_test_details"]
            )
        finally:
            os.unlink(temp_path)

    def test_async_test_failure(self):
        """Test parsing async test failure with promise rejection."""
        jest_output = {
            "numTotalTests": 1,
            "numPassedTests": 0,
            "numFailedTests": 1,
            "testResults": [
                {
                    "name": "/project/async.test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "fullName": "async operation fetches data",
                            "failureMessages": [
                                "Error: Unhandled promise rejection\n"
                                "    at async getData (src/api.js:10:5)\n"
                                "    at async test (async.test.js:15:3)\n"
                                "Expected: {data: 'value'}\n"
                                "Received: undefined"
                            ],
                        }
                    ],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            assert len(result["failed_test_details"]) == 1
            failed = result["failed_test_details"][0]
            assert "async operation fetches data" in failed["test_name"]
            assert "promise rejection" in failed["error_message"].lower()
        finally:
            os.unlink(temp_path)

    def test_invalid_json_returns_error(self):
        """Test that invalid JSON returns error structure."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json")
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            assert result["test_framework"] == "jest"
            assert "error" in result
            assert "Invalid JSON" in result["error"]
        finally:
            os.unlink(temp_path)

    def test_all_tests_passed(self):
        """Test parsing Jest output with all tests passing."""
        jest_output = {
            "numTotalTests": 5,
            "numPassedTests": 5,
            "numFailedTests": 0,
            "testResults": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            assert result["test_framework"] == "jest"
            assert result["total_tests"] == 5
            assert result["passed_tests"] == 5
            assert result["failed_tests"] == 0
            assert len(result["failed_test_details"]) == 0
        finally:
            os.unlink(temp_path)

    def test_single_failed_test(self):
        """Test parsing Jest output with single failed test."""
        jest_output = {
            "numTotalTests": 3,
            "numPassedTests": 2,
            "numFailedTests": 1,
            "testResults": [
                {
                    "name": "/project/src/math.test.js",
                    "assertionResults": [
                        {
                            "status": "passed",
                            "title": "adds 1 + 2 to equal 3",
                            "fullName": "Math operations adds 1 + 2 to equal 3",
                        },
                        {
                            "status": "failed",
                            "title": "subtracts 5 - 3 to equal 2",
                            "fullName": "Math operations subtracts 5 - 3 to equal 2",
                            "failureMessages": ["Expected: 2\nReceived: 1"],
                        },
                    ],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            assert result["test_framework"] == "jest"
            assert result["total_tests"] == 3
            assert result["passed_tests"] == 2
            assert result["failed_tests"] == 1
            assert len(result["failed_test_details"]) == 1

            failed_test = result["failed_test_details"][0]
            assert (
                failed_test["test_name"] == "Math operations subtracts 5 - 3 to equal 2"
            )
            assert failed_test["file_path"] == "/project/src/math.test.js"
            assert "Expected: 2" in failed_test["error_message"]
        finally:
            os.unlink(temp_path)

    def test_node_modules_filtered_from_file_paths(self):
        """Test that tests in node_modules are filtered out."""
        jest_output = {
            "numTotalTests": 2,
            "numPassedTests": 1,
            "numFailedTests": 1,
            "testResults": [
                {
                    "name": "/project/node_modules/some-lib/test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "title": "should fail",
                            "fullName": "Node modules test should fail",
                            "failureMessages": ["Error from node_modules"],
                        }
                    ],
                },
                {
                    "name": "/project/src/app.test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "title": "should fail",
                            "fullName": "App test should fail",
                            "failureMessages": ["Real error"],
                        }
                    ],
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            # Should only have 1 failed test (node_modules filtered out)
            assert len(result["failed_test_details"]) == 1
            assert "app.test.js" in result["failed_test_details"][0]["file_path"]
            assert "node_modules" not in result["failed_test_details"][0]["file_path"]
        finally:
            os.unlink(temp_path)

    def test_stack_trace_compression(self):
        """Test that long stack traces are compressed."""
        long_stack = "\n".join([f"Line {i}" for i in range(30)])

        jest_output = {
            "numTotalTests": 1,
            "numPassedTests": 0,
            "numFailedTests": 1,
            "testResults": [
                {
                    "name": "/project/test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "fullName": "Test with long stack",
                            "failureMessages": [long_stack],
                        }
                    ],
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            result = parse_jest_json(temp_path)

            failed_test = result["failed_test_details"][0]
            stack_trace = failed_test["stack_trace"]

            # Should contain compression indicator
            assert "lines omitted" in stack_trace
            # Should be shorter than original
            assert len(stack_trace) < len(long_stack)
        finally:
            os.unlink(temp_path)


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


class TestGenericParser:
    """Test suite for parse_generic_json() function."""

    def test_file_not_found_returns_error(self):
        """Test that missing file returns error structure."""
        result = parse_generic_json("/nonexistent/path/output.json")

        assert result["test_framework"] == "unknown"
        assert "error" in result
        assert result["parse_mode"] == "generic"

    def test_mocha_style_output(self):
        """Test parsing mocha-style JSON output."""
        mocha_output = {
            "stats": {"tests": 10, "passes": 8, "failures": 2},
            "tests": [
                {
                    "title": "should validate input",
                    "fullTitle": "Validator should validate input",
                    "state": "failed",
                    "err": {
                        "message": "Expected true to be false",
                        "stack": "Error: Expected true\n    at validate.js:10",
                    },
                },
                {
                    "title": "should handle errors",
                    "fullTitle": "ErrorHandler should handle errors",
                    "state": "failed",
                    "err": {"message": "Timeout of 2000ms exceeded"},
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mocha_output, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)

            # Should detect failures even if format is different
            assert result["parse_mode"] == "generic"
            # May or may not parse all details correctly, but should not error
            assert "error" not in result or "failed_test_details" in result
        finally:
            os.unlink(temp_path)

    def test_nested_test_results(self):
        """Test parsing deeply nested test results structure."""
        nested_output = {
            "testResults": [
                {
                    "tests": [
                        {
                            "name": "nested test 1",
                            "status": "passed",
                            "file": "test1.js",
                        },
                        {
                            "name": "nested test 2",
                            "status": "failed",
                            "file": "test2.js",
                            "error": "Assertion failed",
                        },
                    ]
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(nested_output, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)

            # Should handle nested structure
            assert result["parse_mode"] == "generic"
            assert "failed_test_details" in result
        finally:
            os.unlink(temp_path)

    def test_error_message_as_list(self):
        """Test handling error messages provided as array."""
        output_with_array = {
            "tests": [
                {
                    "name": "test with array errors",
                    "status": "failed",
                    "file": "test.js",
                    "error": [
                        "Error 1: First problem",
                        "Error 2: Second problem",
                        "Error 3: Third problem",
                    ],
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(output_with_array, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)

            assert len(result["failed_test_details"]) == 1
            error_msg = result["failed_test_details"][0]["error_message"]
            # Should join array into string
            assert "Error 1" in error_msg
            assert "Error 2" in error_msg
            assert "Error 3" in error_msg
        finally:
            os.unlink(temp_path)

    def test_empty_json_returns_warning(self):
        """Test that empty JSON returns warning about console fallback."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)

            assert result["parse_mode"] == "generic"
            assert "warning" in result
            assert "console output parser" in result["warning"]
        finally:
            os.unlink(temp_path)

    def test_generic_tests_array_with_status_field(self):
        """Test parsing generic format with tests array and status field."""
        generic_output = {
            "tests": [
                {"name": "test1", "status": "passed", "file": "test1.js"},
                {
                    "name": "test2",
                    "status": "failed",
                    "file": "test2.js",
                    "error": "Test failed",
                },
                {"name": "test3", "status": "passed", "file": "test3.js"},
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(generic_output, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)

            assert result["parse_mode"] == "generic"
            assert result["total_tests"] == 3
            assert result["passed_tests"] == 2
            assert result["failed_tests"] == 1
            assert len(result["failed_test_details"]) == 1
            assert result["failed_test_details"][0]["test_name"] == "test2"
        finally:
            os.unlink(temp_path)

    def test_generic_results_array_with_passed_field(self):
        """Test parsing generic format with results array and passed field."""
        generic_output = {
            "results": [
                {"title": "test1", "passed": True, "filePath": "test1.js"},
                {
                    "title": "test2",
                    "passed": False,
                    "filePath": "test2.js",
                    "message": "Failed",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(generic_output, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)

            assert result["total_tests"] == 2
            assert result["failed_tests"] == 1
            assert result["failed_test_details"][0]["test_name"] == "test2"
        finally:
            os.unlink(temp_path)

    def test_framework_identification_jest(self):
        """Test that Jest format is identified correctly."""
        jest_like = {"numTotalTests": 5, "testResults": []}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_like, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)
            assert result["test_framework"] == "jest"
        finally:
            os.unlink(temp_path)

    def test_framework_identification_pytest(self):
        """Test that pytest format is identified correctly."""
        pytest_like = {"pytest_version": "7.0.0", "summary": {}, "duration": 1.5}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_like, f)
            temp_path = f.name

        try:
            result = parse_generic_json(temp_path)
            assert result["test_framework"] == "pytest"
        finally:
            os.unlink(temp_path)


class TestHelperFunctions:
    """Test suite for helper functions."""

    def test_compress_stack_trace_short_unchanged(self):
        """Test that short stack traces are not compressed."""
        short_stack = "Line 1\nLine 2\nLine 3"
        result = _compress_stack_trace(short_stack, first_n=10, last_n=5)
        assert result == short_stack

    def test_compress_stack_trace_long_compressed(self):
        """Test that long stack traces are compressed."""
        lines = [f"Line {i}" for i in range(30)]
        long_stack = "\n".join(lines)

        result = _compress_stack_trace(long_stack, first_n=5, last_n=3)

        # Should contain first and last lines
        assert "Line 0" in result
        assert "Line 29" in result
        # Should contain omission indicator
        assert "lines omitted" in result

    def test_compress_stack_trace_custom_params(self):
        """Test compression with different first_n and last_n values."""
        lines = [f"Line {i}" for i in range(50)]
        long_stack = "\n".join(lines)

        # Test with first_n=15, last_n=10
        result = _compress_stack_trace(long_stack, first_n=15, last_n=10)

        # Should keep first 15
        assert "Line 0" in result
        assert "Line 14" in result
        # Should keep last 10
        assert "Line 49" in result
        assert "Line 40" in result
        # Middle should be omitted (25 lines)
        assert "25 lines omitted" in result

    def test_compress_stack_trace_exact_boundary(self):
        """Test compression at exact first_n + last_n boundary."""
        # If stack has exactly first_n + last_n lines, should not compress
        lines = [f"Line {i}" for i in range(15)]  # 15 lines
        stack = "\n".join(lines)

        result = _compress_stack_trace(stack, first_n=10, last_n=5)

        # Should return unchanged since 15 <= 10 + 5
        assert result == stack
        assert "omitted" not in result

    def test_compress_stack_trace_empty(self):
        """Test compression with empty stack trace."""
        result = _compress_stack_trace("", first_n=10, last_n=5)
        assert result == ""

    def test_compress_stack_trace_realistic_jest(self):
        """Test compression with realistic Jest stack trace."""
        jest_stack = """Error: expect(received).toBe(expected)

Expected: "Hello World"
Received: "Hello"

    at Object.<anonymous> (test.js:10:21)
    at Promise.then.completed (node_modules/jest-circus/build/utils.js:333:28)
    at new Promise (<anonymous>)
    at callAsyncCircusFn (node_modules/jest-circus/build/utils.js:259:10)
    at _callCircusTest (node_modules/jest-circus/build/run.js:276:40)
    at processTicksAndRejections (node:internal/process/task_queues:95:5)
    at async _runTest (node_modules/jest-circus/build/run.js:208:3)
    at async _runTestsForDescribeBlock (node_modules/jest-circus/build/run.js:96:9)
    at async _runTestsForDescribeBlock (node_modules/jest-circus/build/run.js:90:9)
    at async run (node_modules/jest-circus/build/run.js:31:3)
    at async runAndTransformResultsToJestFormat (node_modules/jest-circus/build/legacy-code-todo-rewrite/jestAdapterInit.js:135:21)
    at async jestAdapter (node_modules/jest-circus/build/legacy-code-todo-rewrite/jestAdapter.js:79:19)
    at async runTestInternal (node_modules/jest-runner/build/runTest.js:367:16)
    at async runTest (node_modules/jest-runner/build/runTest.js:444:34)"""

        result = _compress_stack_trace(jest_stack, first_n=8, last_n=3)

        # Should keep error message
        assert "expect(received).toBe(expected)" in result
        # Should keep test file reference
        assert "test.js:10:21" in result
        # Should compress middle
        assert "omitted" in result

    def test_filter_node_modules_from_stack(self):
        """Test that node_modules lines are filtered from stack."""
        stack = """Error: Test failed
    at Object.<anonymous> (/project/test.js:10:5)
    at Module._compile (/project/node_modules/jest/runtime.js:100:5)
    at Object.Module._extensions..js (node:internal/modules/cjs/loader.js:1159:10)
    at Module.load (/project/src/app.js:50:10)
    at Function.Module._load (/project/node_modules/core-js/library/module.js:500:3)
    at runTest (/project/test.js:20:5)"""

        result = _filter_node_modules_from_stack(stack)

        # Should keep project lines
        assert "/project/test.js" in result
        assert "/project/src/app.js" in result
        # Should remove node_modules lines
        assert "node_modules" not in result

    def test_filter_node_modules_preserves_structure(self):
        """Test that filtering preserves overall stack structure."""
        stack = """Error at test.js:5
    at projectFunc (src/app.js:10)
    at npmPackage (node_modules/package/index.js:50)
    at projectFunc2 (src/utils.js:20)
    at internal (node_modules/internal.js:100)
    at finalFunc (test.js:30)"""

        result = _filter_node_modules_from_stack(stack)

        lines = [l for l in result.split("\n") if l.strip()]
        # Should keep 4 non-node_modules lines
        assert len(lines) == 4
        assert "test.js" in result
        assert "src/app.js" in result
        assert "src/utils.js" in result

    def test_clean_pytest_assert_output(self):
        """Test that pytest assert output is cleaned."""
        verbose = (
            """AssertionError: assert 1 == 2
    at test_func (/project/test.py:15)
    Very long comparison line with many details: """
            + ("x" * 250)
            + """
    Another line with error details
    Error details continue"""
        )

        result = _clean_pytest_assert_output(verbose)

        # Should keep assertion and file references
        assert "AssertionError" in result
        assert "test.py" in result
        # Should remove very long lines
        for line in result.split("\n"):
            assert len(line) < 200

    def test_identify_framework_jest(self):
        """Test Jest framework identification."""
        jest_data = {"numTotalTests": 5, "testResults": []}
        assert _identify_framework(jest_data) == "jest"

    def test_identify_framework_pytest(self):
        """Test pytest framework identification."""
        pytest_data = {"pytest_version": "7.0", "summary": {}}
        assert _identify_framework(pytest_data) == "pytest"

    def test_identify_framework_mocha(self):
        """Test mocha framework identification."""
        mocha_data = {"stats": {"tests": 5}, "mocha": True}
        assert _identify_framework(mocha_data) == "mocha"

    def test_identify_framework_unknown(self):
        """Test unknown framework identification."""
        unknown_data = {"some_field": "value"}
        assert _identify_framework(unknown_data) == "unknown"


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
