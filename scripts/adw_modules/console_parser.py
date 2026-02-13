"""
Console output parser for test frameworks (fallback mode).

This module provides intelligent parsing of console test output when
JSON output is unavailable or unparseable. Implements aggressive token
reduction while preserving failure information.
"""

import re
from typing import Dict, List, Any


def parse_console_output(console_output: str) -> Dict[str, Any]:
    """
    Fallback parser for console test output with intelligent truncation.

    Implements aggressive token reduction strategies:
    - Remove ANSI escape codes
    - Deduplicate repeated log messages
    - Compress stack traces
    - Filter test runner boilerplate
    - Extract test names and errors via regex

    Args:
        console_output: Raw console output string from test execution

    Returns:
        Dictionary containing:
        - test_framework: "console"
        - parse_mode: "console"
        - failed_test_details: List of extracted failures
        - original_size: Original character count
        - compressed_size: Compressed character count
        - reduction_percent: Percentage reduction
    """
    if not console_output:
        return {
            "test_framework": "console",
            "parse_mode": "console",
            "error": "Empty console output",
            "failed_test_details": [],
        }

    original_size = len(console_output)

    # Step 1: Remove ANSI escape codes
    cleaned = _remove_ansi_codes(console_output)

    # Step 2: Deduplicate repeated log messages
    cleaned = _deduplicate_logs(cleaned)

    # Step 3: Filter test runner boilerplate
    cleaned = _filter_boilerplate(cleaned)

    # Step 4: Extract test failures with regex
    failed_details = _extract_test_failures(cleaned)

    # Step 5: Compress remaining output
    compressed = _compress_console_output(cleaned)

    compressed_size = len(compressed)
    reduction_percent = round(
        ((original_size - compressed_size) / original_size * 100)
        if original_size > 0
        else 0,
        2,
    )

    return {
        "test_framework": "console",
        "parse_mode": "console",
        "failed_test_details": failed_details,
        "compressed_output": compressed,
        "original_size": original_size,
        "compressed_size": compressed_size,
        "reduction_percent": reduction_percent,
    }


def _remove_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    Args:
        text: Text containing ANSI codes

    Returns:
        Cleaned text without ANSI codes
    """
    # Pattern matches ANSI escape sequences
    ansi_pattern = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_pattern.sub("", text)


def _deduplicate_logs(text: str) -> str:
    """
    Deduplicate repeated log messages, showing once with count.

    Args:
        text: Text with potentially repeated lines

    Returns:
        Deduplicated text with counts
    """
    lines = text.split("\n")
    seen_lines = {}
    result = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Normalize whitespace for comparison
        normalized = " ".join(line.split())

        if normalized in seen_lines:
            seen_lines[normalized]["count"] += 1
        else:
            seen_lines[normalized] = {"original": line, "count": 1}
            result.append(line)

    # Add count annotations for duplicates
    final_result = []
    for line in result:
        normalized = " ".join(line.split())
        count = seen_lines[normalized]["count"]
        if count > 1:
            final_result.append(f"{line} [repeated {count}x]")
        else:
            final_result.append(line)

    return "\n".join(final_result)


def _filter_boilerplate(text: str) -> str:
    """
    Filter test runner boilerplate and noise.

    Args:
        text: Console output text

    Returns:
        Filtered text with boilerplate removed
    """
    lines = text.split("\n")
    filtered = []

    # Boilerplate patterns to skip
    skip_patterns = [
        r"^\s*$",  # Empty lines
        r"^-+$",  # Separator lines
        r"^=+$",  # Separator lines
        r"Test Suites:",  # Jest summary headers
        r"Tests:",  # Test summary headers
        r"Snapshots:",  # Snapshot headers
        r"Time:",  # Time headers
        r"Ran all test suites",  # Jest completion messages
        r"coverage",  # Coverage output (case insensitive)
        r"^\s*at\s+.*node_modules",  # Stack traces through node_modules
        r"^\s*at\s+.*internal",  # Internal stack frames
    ]

    for line in lines:
        # Check if line matches any skip pattern
        should_skip = any(
            re.search(pattern, line, re.IGNORECASE) for pattern in skip_patterns
        )

        if not should_skip:
            filtered.append(line)

    return "\n".join(filtered)


def _extract_test_failures(text: str) -> List[Dict[str, Any]]:
    """
    Extract test failures using regex patterns for common frameworks.

    Args:
        text: Console output text

    Returns:
        List of failure dictionaries
    """
    failures = []

    # Pattern 1: Jest-style failures
    # FAIL src/components/Button.test.js
    #   ● Button component › renders correctly
    jest_pattern = re.compile(
        r"FAIL\s+(.+?)\n\s*●\s+(.+?)\n\n([\s\S]*?)(?=\nFAIL\s|\n\nTest Suites:|\Z)",
        re.MULTILINE,
    )

    for match in jest_pattern.finditer(text):
        file_path = match.group(1).strip()
        test_name = match.group(2).strip()
        error_block = match.group(3).strip()

        # Compress error block using imported function
        from .test_parsers import _compress_stack_trace

        compressed_error = _compress_stack_trace(error_block, first_n=8, last_n=3)

        failures.append(
            {
                "test_name": test_name,
                "file_path": file_path,
                "error_message": error_block[:500],
                "stack_trace": compressed_error,
            }
        )

    # Pattern 2: Pytest-style failures
    # FAILED tests/test_math.py::test_addition - AssertionError: assert 1 == 2
    pytest_pattern = re.compile(r"FAILED\s+(.+?)\s+-\s+(.+?)(?:\n|$)", re.MULTILINE)

    for match in pytest_pattern.finditer(text):
        test_path = match.group(1).strip()
        error_msg = match.group(2).strip()

        # Split test path into file and test name
        if "::" in test_path:
            file_path, test_name = test_path.split("::", 1)
        else:
            file_path = test_path
            test_name = "Unknown Test"

        failures.append(
            {
                "test_name": test_name,
                "file_path": file_path,
                "error_message": error_msg[:500],
                "stack_trace": error_msg,
            }
        )

    # Pattern 3: Generic "Error:" or "Failed:" patterns
    generic_pattern = re.compile(
        r"(?:Error|Failed|FAILED):\s*(.+?)(?:\n|$)", re.MULTILINE | re.IGNORECASE
    )

    # Only use generic if no specific patterns matched
    if not failures:
        for match in generic_pattern.finditer(text):
            error_msg = match.group(1).strip()
            failures.append(
                {
                    "test_name": "Unknown Test",
                    "file_path": "unknown",
                    "error_message": error_msg[:500],
                    "stack_trace": error_msg,
                }
            )

    return failures


def _compress_console_output(text: str) -> str:
    """
    Apply aggressive compression to console output.

    Args:
        text: Console text to compress

    Returns:
        Compressed text
    """
    lines = text.split("\n")

    # Keep only meaningful lines
    compressed = []
    for line in lines:
        stripped = line.strip()

        # Truncate very long lines (likely verbose output)
        if len(line) > 500:
            compressed.append(line[:500] + "... [truncated]")
            continue

        # Keep lines with errors, failures, or important info
        if any(
            keyword in stripped.lower()
            for keyword in [
                "error",
                "fail",
                "assert",
                "expected",
                "received",
                "undefined",
                "null",
                "exception",
                "test",
            ]
        ):
            compressed.append(line)
        # Keep indented lines (likely part of error context)
        elif line.startswith("  ") or line.startswith("\t"):
            compressed.append(line)
        # Keep non-empty lines that aren't too generic
        elif stripped and len(stripped) > 5:
            compressed.append(line)

    # If compression too aggressive, keep first 100 lines but still truncate long ones
    if len(compressed) < 10:
        fallback = []
        for line in lines[:100]:
            if len(line) > 500:
                fallback.append(line[:500] + "... [truncated]")
            else:
                fallback.append(line)
        return "\n".join(fallback)

    return "\n".join(compressed)
