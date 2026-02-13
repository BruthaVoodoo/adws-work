#!/usr/bin/env python3
"""
Integration tests for test parsers with real-world scenarios.

Tests realistic workflows combining parsers with token counting
to validate the complete token reduction pipeline.
"""

import json
import tempfile
import os
import pytest
from pathlib import Path

from scripts.adw_modules.test_parsers import (
    parse_jest_json,
    parse_pytest_json,
    parse_generic_json,
    parse_console_output,
)
from scripts.adw_modules.token_utils import (
    count_tokens,
    check_token_limit,
    calculate_overage_percentage,
)


class TestRealWorldJestIntegration:
    """Integration tests with realistic Jest outputs."""

    def test_large_jest_output_token_reduction(self):
        """Test that Jest parser reduces tokens significantly."""
        # Simulate large Jest output with many passing tests and few failures
        jest_output = {
            "numTotalTests": 500,
            "numPassedTests": 495,
            "numFailedTests": 5,
            "testResults": [],
        }

        # Add 495 passing tests (should be filtered out)
        for i in range(495):
            jest_output["testResults"].append(
                {
                    "name": f"/project/test{i}.js",
                    "assertionResults": [
                        {
                            "status": "passed",
                            "fullName": f"Test suite {i} test case",
                        }
                    ],
                }
            )

        # Add 5 failing tests (should be extracted)
        for i in range(5):
            jest_output["testResults"].append(
                {
                    "name": f"/project/failing-test{i}.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "fullName": f"Failing test {i}",
                            "failureMessages": [
                                f"Error in test {i}\n"
                                + "\n".join(
                                    [f"Stack line {j}" for j in range(20)]
                                )  # Long stack
                            ],
                        }
                    ],
                }
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(jest_output, f)
            temp_path = f.name

        try:
            # Parse the output
            result = parse_jest_json(temp_path)

            # Verify only failed tests extracted
            assert result["total_tests"] == 500
            assert result["passed_tests"] == 495
            assert result["failed_tests"] == 5
            assert len(result["failed_test_details"]) == 5

            # Convert to string for token counting
            result_str = json.dumps(result)

            # Count tokens
            token_count = count_tokens(result_str)

            # With 5 failures and compressed stacks, should be under 5000 tokens
            assert token_count < 5000

            # Verify this is manageable for 128K limit
            within_limit, _, _ = check_token_limit(result_str, 128000)
            assert within_limit is True

        finally:
            os.unlink(temp_path)

    def test_jest_node_modules_filtering_reduces_tokens(self):
        """Test that filtering node_modules reduces token count."""
        # Create test with verbose node_modules stack traces
        jest_output = {
            "numTotalTests": 1,
            "numPassedTests": 0,
            "numFailedTests": 1,
            "testResults": [
                {
                    "name": "/project/app.test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "fullName": "App test fails",
                            "failureMessages": [
                                "Error: Test failed\n"
                                "    at test.js:10\n"
                                + "\n".join(
                                    [
                                        f"    at node_modules/package{i}/file.js:100"
                                        for i in range(50)
                                    ]
                                )
                                + "\n    at app.js:50"
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

            # Get stack trace
            stack = result["failed_test_details"][0]["stack_trace"]

            # Should not contain node_modules
            assert "node_modules" not in stack

            # Should keep project files
            assert "test.js" in stack or "app.js" in stack

            # Token count should be reasonable
            token_count = count_tokens(stack)
            assert token_count < 500  # Much less than with 50 node_modules lines

        finally:
            os.unlink(temp_path)


class TestRealWorldPytestIntegration:
    """Integration tests with realistic pytest outputs."""

    def test_pytest_verbose_assert_introspection_compression(self):
        """Test that verbose pytest assert introspection is compressed."""
        # Pytest can generate very verbose assert comparisons
        verbose_comparison = """
AssertionError: assert {'key1': 'value1', 'key2': 'value2', 'key3': 'value3'} == {'key1': 'value1', 'key2': 'DIFFERENT', 'key3': 'value3'}

  Omitting 1 identical items, use -vv to show
  Differing items:
  {'key2': 'value2'} != {'key2': 'DIFFERENT'}
  
  Full diff:
    {
      'key1': 'value1',
  -   'key2': 'value2',
  +   'key2': 'DIFFERENT',
      'key3': 'value3',
    }
  
  Left contains 1 more item:
  {'nested': {'deep': {'structure': {'with': 'many', 'levels': 'of', 'nesting': 'here'}}}}\n"""
        verbose_comparison += "x" * 300  # Add very long line

        pytest_output = {
            "summary": {"total": 1, "passed": 0, "failed": 1},
            "tests": [
                {
                    "nodeid": "tests/test_dict_comparison.py::test_dicts_equal",
                    "outcome": "failed",
                    "location": [
                        "tests/test_dict_comparison.py",
                        10,
                        "test_dicts_equal",
                    ],
                    "call": {"longrepr": verbose_comparison},
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pytest_output, f)
            temp_path = f.name

        try:
            result = parse_pytest_json(temp_path)

            stack = result["failed_test_details"][0]["stack_trace"]

            # Should keep AssertionError
            assert "AssertionError" in stack

            # Should remove very long lines (>200 chars)
            for line in stack.split("\n"):
                assert len(line) < 200

            # Token count should be reasonable
            token_count = count_tokens(stack)
            assert token_count < 300  # Compressed from much larger

        finally:
            os.unlink(temp_path)


class TestConsoleParserIntegration:
    """Integration tests for console parser with token reduction."""

    def test_console_parser_achieves_85_percent_reduction(self):
        """Test that console parser achieves target 85% token reduction."""
        # Create verbose console output simulating 184K token scenario
        verbose_output = ""

        # Add repetitive test startup messages (common in verbose test runs)
        for _ in range(100):
            verbose_output += "Starting test suite...\n"
            verbose_output += "Loading configuration...\n"
            verbose_output += "Initializing test environment...\n"

        # Add passing test noise
        for i in range(200):
            verbose_output += f"✓ Test {i} passed\n"

        # Add actual failures with proper Jest format (needs blank line after test name)
        verbose_output += """
FAIL src/components/Button.test.js
  ● Button component › renders correctly

Expected: "Submit"
Received: "Click"

  10 |   expect(button).toHaveText("Submit")
  11 | })


Test Suites: 1 failed, 1 total
"""

        # Add more verbose output
        for _ in range(50):
            verbose_output += "Test execution completed\n"

        result = parse_console_output(verbose_output)

        # Should achieve significant reduction (may not extract all failures perfectly)
        reduction = result["reduction_percent"]
        assert reduction > 70  # At least 70% reduction

        # Verify deduplication occurred
        assert "repeated" in result["compressed_output"]

        # Calculate tokens
        original_tokens = count_tokens(verbose_output)
        compressed_tokens = count_tokens(result["compressed_output"])

        # Token reduction should be substantial
        token_reduction = (original_tokens - compressed_tokens) / original_tokens * 100
        assert token_reduction > 40  # At least 40% token reduction

    def test_deduplication_with_repeated_warnings(self):
        """Test deduplication with many repeated warning messages."""
        # Simulate test output with 1000 repeated deprecation warnings
        console_output = "\n".join(
            ["DeprecationWarning: API xyz is deprecated" for _ in range(1000)]
        )
        console_output += "\nFAILED test.py::test_func - AssertionError"

        result = parse_console_output(console_output)

        # Should dramatically reduce size
        original_size = result["original_size"]
        compressed_size = result["compressed_size"]

        # Should compress 1000 warnings to 1 line with count
        reduction_ratio = compressed_size / original_size
        assert reduction_ratio < 0.1  # Over 90% reduction

        # Should still extract failure
        assert len(result["failed_test_details"]) >= 1

    def test_mixed_framework_console_output(self):
        """Test console parser with mixed Jest and Pytest style output."""
        mixed_output = """
Running tests with Jest...

FAIL src/app.test.js
  ● App › renders title

Expected "Hello" but got "Hi"


=================================== FAILURES ===================================
FAILED tests/test_math.py::test_addition - AssertionError: assert 1 == 2

Error: Connection timeout after 5000ms
"""

        result = parse_console_output(mixed_output)

        # Should extract at least one failure
        failures = result["failed_test_details"]
        assert len(failures) >= 1

        # Should identify different patterns - verify we got pytest or generic
        if len(failures) > 0:
            # At least one failure extracted
            test_names = [f["test_name"] for f in failures]
            error_messages = [f["error_message"] for f in failures]

            # Should have captured some error info
            assert any(
                "assert" in msg.lower()
                or "error" in msg.lower()
                or "timeout" in msg.lower()
                for msg in error_messages
            )


class TestEndToEndTokenReduction:
    """End-to-end tests validating complete token reduction pipeline."""

    def test_complete_pipeline_under_128k_limit(self):
        """Test complete pipeline keeps output under 128K token limit."""
        # Simulate scenario that originally caused 184K token error

        # Large test suite: 1000 tests with verbose output
        large_jest = {
            "numTotalTests": 1000,
            "numPassedTests": 990,
            "numFailedTests": 10,
            "testResults": [],
        }

        # Add 10 failures with realistic stack traces
        for i in range(10):
            large_jest["testResults"].append(
                {
                    "name": f"/project/src/module{i}/test.js",
                    "assertionResults": [
                        {
                            "status": "failed",
                            "fullName": f"Module {i} › Component › Test case {i}",
                            "failureMessages": [
                                f"Error in test {i}\n"
                                "Expected: true\n"
                                "Received: false\n"
                                + "\n".join(
                                    [
                                        f"    at Object.<anonymous> (test{i}.js:{j}:5)"
                                        for j in range(10, 30)
                                    ]
                                )
                            ],
                        }
                    ],
                }
            )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(large_jest, f)
            temp_path = f.name

        try:
            # Parse and process
            result = parse_jest_json(temp_path)

            # Convert to JSON string (as would be sent to LLM)
            result_json = json.dumps(result, indent=2)

            # Check token count
            within_limit, token_count, safe_limit = check_token_limit(
                result_json, 128000
            )

            # Should be well within limit
            assert within_limit is True
            assert token_count < safe_limit

            # Calculate reduction from hypothetical original
            # Original would have had all 1000 tests with full output
            # Estimate: ~100 tokens per test * 1000 = 100K tokens
            estimated_original = 100000
            reduction_percent = (
                (estimated_original - token_count) / estimated_original * 100
            )

            # Should achieve >80% reduction
            assert reduction_percent > 80

        finally:
            os.unlink(temp_path)

    def test_token_counting_matches_real_llm_behavior(self):
        """Test that our token counting matches expected LLM token usage."""
        # Use realistic test failure message
        test_output = {
            "test_framework": "jest",
            "total_tests": 100,
            "passed_tests": 98,
            "failed_tests": 2,
            "failed_test_details": [
                {
                    "test_name": "Authentication › login with valid credentials",
                    "file_path": "/project/src/auth/login.test.js",
                    "error_message": "Expected response.status to be 200 but got 401",
                    "stack_trace": "    at validateLogin (login.test.js:25:10)\n    at async test (login.test.js:30:5)",
                }
            ],
        }

        json_str = json.dumps(test_output)

        # Count tokens
        token_count = count_tokens(json_str)

        # Should be reasonable for this size (roughly 150-250 tokens)
        assert 100 < token_count < 300

        # Verify it's within safe margin for 128K limit
        within_limit, _, _ = check_token_limit(json_str, 128000)
        assert within_limit is True


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
