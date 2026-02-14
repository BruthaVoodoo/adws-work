#!/usr/bin/env python3
"""
Unit tests for console output parser (fallback mode).

Tests coverage:
- parse_console_output() with various console outputs
- ANSI code removal
- Log deduplication
- Boilerplate filtering
- Test failure extraction (Jest, Pytest, Generic)
- Console output compression
- Token reduction metrics
"""

import pytest
from scripts.adw_modules.console_parser import (
    parse_console_output,
    _remove_ansi_codes,
    _deduplicate_logs,
    _filter_boilerplate,
    _extract_test_failures,
    _compress_console_output,
)


class TestConsoleParser:
    """Test suite for parse_console_output() function."""

    def test_empty_output_returns_error(self):
        """Test that empty output returns error structure."""
        result = parse_console_output("")

        assert result["test_framework"] == "console"
        assert result["parse_mode"] == "console"
        assert "error" in result
        assert "Empty console output" in result["error"]

    def test_basic_console_output_parsing(self):
        """Test basic parsing and compression."""
        console_output = """
Running tests...
Test suite started
FAIL src/app.test.js
  ● App renders correctly
    Expected: true
    Received: false
Test suite completed
"""

        result = parse_console_output(console_output)

        assert result["test_framework"] == "console"
        assert result["parse_mode"] == "console"
        assert result["original_size"] > 0
        assert result["compressed_size"] > 0
        assert result["reduction_percent"] >= 0

    def test_token_reduction_metrics(self):
        """Test that compression reduces token count."""
        # Create verbose output with repetition
        console_output = "\n".join(["Starting test..." for _ in range(100)])
        console_output += "\nFAILED test_math.py::test_add - AssertionError"

        result = parse_console_output(console_output)

        # Should achieve significant reduction
        assert result["compressed_size"] < result["original_size"]
        assert result["reduction_percent"] > 0


class TestAnsiRemoval:
    """Test suite for _remove_ansi_codes() function."""

    def test_removes_ansi_color_codes(self):
        """Test that ANSI color codes are removed."""
        text_with_ansi = "\x1b[31mERROR:\x1b[0m Test failed"
        cleaned = _remove_ansi_codes(text_with_ansi)

        assert "\x1b" not in cleaned
        assert "ERROR: Test failed" == cleaned

    def test_removes_ansi_formatting_codes(self):
        """Test that ANSI formatting codes are removed."""
        text = "\x1b[1m\x1b[4mBold Underline\x1b[0m"
        cleaned = _remove_ansi_codes(text)

        assert "\x1b" not in cleaned
        assert "Bold Underline" == cleaned

    def test_plain_text_unchanged(self):
        """Test that plain text without ANSI codes is unchanged."""
        plain = "No ANSI codes here"
        cleaned = _remove_ansi_codes(plain)

        assert plain == cleaned


class TestLogDeduplication:
    """Test suite for _deduplicate_logs() function."""

    def test_deduplicates_repeated_lines(self):
        """Test that repeated lines are deduplicated with count."""
        text = """
Line 1
Line 2
Line 2
Line 2
Line 3
"""
        result = _deduplicate_logs(text)

        # Should only have 3 unique lines
        lines = result.strip().split("\n")
        assert len(lines) == 3
        assert "Line 2 [repeated 3x]" in result

    def test_single_occurrence_no_count(self):
        """Test that single occurrences don't get count annotation."""
        text = "Line 1\nLine 2\nLine 3"
        result = _deduplicate_logs(text)

        assert "[repeated" not in result
        assert "Line 1" in result
        assert "Line 2" in result

    def test_normalizes_whitespace_for_comparison(self):
        """Test that whitespace differences are normalized."""
        text = "Line 1\n  Line 1  \nLine 1   "
        result = _deduplicate_logs(text)

        lines = result.strip().split("\n")
        assert len(lines) == 1
        assert "[repeated 3x]" in result

    def test_many_repeated_lines(self):
        """Test deduplication with many repetitions (realistic test output)."""
        # Simulate verbose test output with repeated warnings
        text = "\n".join(["Warning: Deprecated API" for _ in range(50)])
        text += "\nActual error occurred"

        result = _deduplicate_logs(text)

        # Should compress 50 warnings to 1 line with count
        assert "[repeated 50x]" in result
        assert "Actual error occurred" in result
        # Result should be much shorter
        assert len(result) < len(text) // 10

    def test_mixed_unique_and_repeated(self):
        """Test mix of unique and repeated lines."""
        text = """
Unique line 1
Repeated line
Unique line 2
Repeated line
Repeated line
Unique line 3
Another repeated
Another repeated
"""
        result = _deduplicate_logs(text)

        lines = [l for l in result.split("\n") if l.strip()]
        # Should have 5 unique lines
        assert len(lines) == 5
        assert "Repeated line [repeated 3x]" in result
        assert "Another repeated [repeated 2x]" in result

    def test_preserves_original_line_formatting(self):
        """Test that original line formatting is preserved."""
        text = "  Indented line\n  Indented line\n  Indented line"
        result = _deduplicate_logs(text)

        # First occurrence should preserve indentation
        assert "  Indented line [repeated 3x]" in result


class TestBoilerplateFiltering:
    """Test suite for _filter_boilerplate() function."""

    def test_filters_empty_lines(self):
        """Test that empty lines are filtered."""
        text = "Line 1\n\n\nLine 2\n\n"
        result = _filter_boilerplate(text)

        assert result == "Line 1\nLine 2"

    def test_filters_jest_summary_headers(self):
        """Test that Jest summary headers are filtered."""
        text = """
FAIL test.js
Test Suites: 1 failed, 1 total
Tests: 1 failed, 1 total
Snapshots: 0 total
Time: 1.5s
"""
        result = _filter_boilerplate(text)

        assert "Test Suites:" not in result
        assert "Tests:" not in result
        assert "Snapshots:" not in result
        assert "Time:" not in result
        assert "FAIL test.js" in result

    def test_filters_node_modules_stack_traces(self):
        """Test that node_modules stack traces are filtered."""
        text = """
Error at test.js:10
    at Module.load (node_modules/jest/runtime.js:100)
    at myFunction (src/app.js:20)
    at internal/process.js:50
"""
        result = _filter_boilerplate(text)

        assert "node_modules" not in result
        assert "internal" not in result
        assert "test.js" in result
        assert "app.js" in result

    def test_filters_separator_lines(self):
        """Test that separator lines are filtered."""
        text = "Line 1\n----\n====\nLine 2"
        result = _filter_boilerplate(text)

        assert "----" not in result
        assert "====" not in result


class TestFailureExtraction:
    """Test suite for _extract_test_failures() function."""

    def test_extracts_jest_failures(self):
        """Test extraction of Jest-style failures."""
        console = """
FAIL src/components/Button.test.js
  ● Button component › renders correctly

    Expected: "Submit"
    Received: "Click"

      10 |   expect(button).toHaveText("Submit")
      11 | })

FAIL src/app.test.js
  ● App › shows title

    Cannot find element
"""
        failures = _extract_test_failures(console)

        assert len(failures) == 2
        assert failures[0]["file_path"] == "src/components/Button.test.js"
        assert "Button component › renders correctly" in failures[0]["test_name"]
        assert "Expected:" in failures[0]["error_message"]

    def test_extracts_pytest_failures(self):
        """Test extraction of pytest-style failures."""
        console = """
FAILED tests/test_math.py::test_addition - AssertionError: assert 1 == 2
FAILED tests/test_string.py::test_concat - TypeError: unsupported operand
"""
        failures = _extract_test_failures(console)

        assert len(failures) == 2
        assert failures[0]["file_path"] == "tests/test_math.py"
        assert failures[0]["test_name"] == "test_addition"
        assert "AssertionError" in failures[0]["error_message"]

        assert failures[1]["file_path"] == "tests/test_string.py"
        assert failures[1]["test_name"] == "test_concat"

    def test_extracts_generic_errors(self):
        """Test extraction of generic error patterns."""
        console = """
Running tests...
Error: Connection timeout
Failed: Invalid configuration
"""
        failures = _extract_test_failures(console)

        assert len(failures) == 2
        assert "Connection timeout" in failures[0]["error_message"]
        assert "Invalid configuration" in failures[1]["error_message"]

    def test_no_failures_returns_empty_list(self):
        """Test that output with no failures returns empty list."""
        console = "All tests passed!\n✓ 10 tests completed"
        failures = _extract_test_failures(console)

        assert failures == []


class TestConsoleCompression:
    """Test suite for _compress_console_output() function."""

    def test_keeps_error_lines(self):
        """Test that lines with errors are kept."""
        text = """
Starting tests
Error: Test failed
Regular log line
Another error occurred
"""
        result = _compress_console_output(text)

        assert "Error: Test failed" in result
        assert "Another error occurred" in result

    def test_keeps_assertion_lines(self):
        """Test that assertion-related lines are kept."""
        text = """
Running test
Expected: 5
Received: 3
assert 5 == 3
Done
"""
        result = _compress_console_output(text)

        assert "Expected:" in result
        assert "Received:" in result
        assert "assert" in result

    def test_keeps_indented_context_lines(self):
        """Test that indented lines (error context) are kept."""
        text = """
Error occurred
  at function_name (file.js:10)
  at caller (file.js:20)
Other line
"""
        result = _compress_console_output(text)

        assert "at function_name" in result
        assert "at caller" in result

    def test_truncates_very_long_lines(self):
        """Test that very long lines are truncated."""
        long_line = "x" * 600
        text = f"Short line\n{long_line}\nAnother short line"

        result = _compress_console_output(text)

        assert "[truncated]" in result
        # Should truncate to 500 chars + marker
        assert len(result) < len(text)

    def test_falls_back_if_too_aggressive(self):
        """Test fallback to first 100 lines if compression too aggressive."""
        # Create output with very short lines that get filtered out
        text = "\n".join([f"x{i}" for i in range(150)])

        result = _compress_console_output(text)

        # Should keep first 100 lines when falling back
        lines = result.split("\n")
        assert len(lines) <= 100


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
