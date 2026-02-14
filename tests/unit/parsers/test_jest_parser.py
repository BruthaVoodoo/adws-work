#!/usr/bin/env python3
"""
Unit tests for Jest JSON parser.

Tests coverage:
- parse_jest_json() with various Jest output formats
- Stack trace compression
- Node_modules filtering
- Edge cases and error handling
"""

import json
import pytest
import tempfile
import os

# Import functions under test
from scripts.adw_modules.test_parsers import (
    parse_jest_json,
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


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
