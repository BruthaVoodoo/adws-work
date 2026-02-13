"""
Test output parsers for Jest and Pytest JSON formats.

This module provides parsers to extract failed test information from
test framework JSON outputs, optimized for LLM consumption.
Also includes test framework detection functionality.
"""

import json
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
import os


def parse_jest_json(json_file_path: str) -> Dict[str, Any]:
    """
    Parse Jest JSON output file and extract only failed tests.

    Args:
        json_file_path: Path to Jest JSON output file

    Returns:
        Dictionary containing:
        - test_framework: "jest"
        - total_tests: int
        - passed_tests: int
        - failed_tests: int
        - failed_test_details: List of failed test objects with:
            - test_name: str
            - file_path: str
            - error_message: str
            - stack_trace: str (compressed: first 10 + last 5 lines)
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            jest_data = json.load(f)
    except FileNotFoundError:
        return {
            "test_framework": "jest",
            "error": f"File not found: {json_file_path}",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_test_details": [],
        }
    except json.JSONDecodeError as e:
        return {
            "test_framework": "jest",
            "error": f"Invalid JSON: {str(e)}",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_test_details": [],
        }

    # Extract summary statistics
    num_total_tests = jest_data.get("numTotalTests", 0)
    num_passed_tests = jest_data.get("numPassedTests", 0)
    num_failed_tests = jest_data.get("numFailedTests", 0)

    failed_details = []

    # Parse test results from test suites
    test_results = jest_data.get("testResults", [])

    for test_suite in test_results:
        file_path = test_suite.get("name", "unknown")

        # Filter out node_modules from file paths
        if "node_modules" in file_path:
            continue

        assertion_results = test_suite.get("assertionResults", [])

        for assertion in assertion_results:
            status = assertion.get("status", "")

            # Only process failed tests
            if status == "failed":
                test_name = assertion.get(
                    "fullName", assertion.get("title", "Unknown Test")
                )

                # Extract error message
                failure_messages = assertion.get("failureMessages", [])
                error_message = (
                    "\n".join(failure_messages)
                    if failure_messages
                    else "No error message"
                )

                # Compress stack trace
                stack_trace = _compress_stack_trace(error_message)

                # Filter node_modules from stack trace
                stack_trace = _filter_node_modules_from_stack(stack_trace)

                failed_details.append(
                    {
                        "test_name": test_name,
                        "file_path": file_path,
                        "error_message": error_message[
                            :500
                        ],  # Limit error message length
                        "stack_trace": stack_trace,
                    }
                )

    return {
        "test_framework": "jest",
        "total_tests": num_total_tests,
        "passed_tests": num_passed_tests,
        "failed_tests": num_failed_tests,
        "failed_test_details": failed_details,
    }


def _compress_stack_trace(stack_trace: str, first_n: int = 10, last_n: int = 5) -> str:
    """
    Compress stack trace by keeping first N and last N lines.

    Args:
        stack_trace: Full stack trace string
        first_n: Number of lines to keep from the beginning
        last_n: Number of lines to keep from the end

    Returns:
        Compressed stack trace string
    """
    if not stack_trace:
        return ""

    lines = stack_trace.split("\n")

    # If stack trace is short enough, return as-is
    if len(lines) <= (first_n + last_n):
        return stack_trace

    # Keep first N and last N lines
    first_lines = lines[:first_n]
    last_lines = lines[-last_n:]

    omitted_count = len(lines) - (first_n + last_n)
    separator = [f"\n... ({omitted_count} lines omitted) ...\n"]

    compressed = first_lines + separator + last_lines
    return "\n".join(compressed)


def _filter_node_modules_from_stack(stack_trace: str) -> str:
    """
    Filter out node_modules references from stack trace.

    Args:
        stack_trace: Stack trace string

    Returns:
        Filtered stack trace with node_modules lines removed
    """
    if not stack_trace:
        return ""

    lines = stack_trace.split("\n")
    filtered_lines = [line for line in lines if "node_modules" not in line]

    return "\n".join(filtered_lines)


def parse_pytest_json(json_file_path: str) -> Dict[str, Any]:
    """
    Parse pytest-json-report output and extract only failed tests.

    Expects pytest-json-report plugin format.
    Install with: pip install pytest-json-report
    Run with: pytest --json-report --json-report-file=report.json

    Args:
        json_file_path: Path to pytest JSON report file

    Returns:
        Dictionary containing:
        - test_framework: "pytest"
        - total_tests: int
        - passed_tests: int
        - failed_tests: int
        - failed_test_details: List of failed test objects with:
            - test_name: str
            - file_path: str
            - error_message: str
            - stack_trace: str (compressed)
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            pytest_data = json.load(f)
    except FileNotFoundError:
        return {
            "test_framework": "pytest",
            "error": f"File not found: {json_file_path}",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_test_details": [],
        }
    except json.JSONDecodeError as e:
        return {
            "test_framework": "pytest",
            "error": f"Invalid JSON: {str(e)}",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_test_details": [],
        }

    # Extract summary from report
    summary = pytest_data.get("summary", {})
    total_tests = summary.get("total", 0)
    passed_tests = summary.get("passed", 0)
    failed_tests = summary.get("failed", 0)

    failed_details = []

    # Parse test results
    tests = pytest_data.get("tests", [])

    for test in tests:
        outcome = test.get("outcome", "")

        # Only process failed tests
        if outcome == "failed":
            test_name = test.get("nodeid", "Unknown Test")
            file_path = test.get("location", ["unknown"])[0]

            # Extract call information for error details
            call_info = test.get("call", {})

            # Get longrepr for error message (pytest-specific)
            longrepr = call_info.get("longrepr", "")

            # Handle different longrepr formats
            if isinstance(longrepr, str):
                error_message = longrepr
            elif isinstance(longrepr, dict):
                # pytest-json-report sometimes formats longrepr as dict
                error_message = str(longrepr)
            else:
                error_message = "No error message available"

            # Compress stack trace
            stack_trace = _compress_stack_trace(error_message)

            # Handle pytest assert introspection output
            stack_trace = _clean_pytest_assert_output(stack_trace)

            failed_details.append(
                {
                    "test_name": test_name,
                    "file_path": file_path,
                    "error_message": error_message[:500],  # Limit error message length
                    "stack_trace": stack_trace,
                }
            )

    return {
        "test_framework": "pytest",
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "failed_test_details": failed_details,
    }


def _clean_pytest_assert_output(stack_trace: str) -> str:
    """
    Clean pytest assert introspection output to reduce noise.

    Pytest includes detailed variable comparisons in assert failures.
    This function keeps the important parts while reducing verbosity.

    Args:
        stack_trace: Raw pytest stack trace

    Returns:
        Cleaned stack trace
    """
    if not stack_trace:
        return ""

    # Remove excessive whitespace while preserving structure
    lines = stack_trace.split("\n")
    cleaned_lines = []

    for line in lines:
        # Keep assertion error lines
        if "AssertionError" in line or "assert" in line.lower():
            cleaned_lines.append(line)
        # Keep file references
        elif ".py" in line and ":" in line:
            cleaned_lines.append(line)
        # Keep error type lines
        elif any(err in line for err in ["Error", "Exception", "Failed"]):
            cleaned_lines.append(line)
        # Skip very long lines (likely verbose comparisons)
        elif len(line) < 200:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def parse_generic_json(json_file_path: str) -> Dict[str, Any]:
    """
    Generic JSON parser for unknown test frameworks.

    Attempts best-effort parsing by looking for common patterns:
    - tests/results arrays
    - status/passed/failed fields
    - error/message fields

    Args:
        json_file_path: Path to JSON output file

    Returns:
        Dictionary with extracted information or error details
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {
            "test_framework": "unknown",
            "error": f"File not found: {json_file_path}",
            "parse_mode": "generic",
            "failed_test_details": [],
        }
    except json.JSONDecodeError as e:
        return {
            "test_framework": "unknown",
            "error": f"Invalid JSON: {str(e)}",
            "parse_mode": "generic",
            "failed_test_details": [],
        }

    # Attempt to identify test framework
    framework = _identify_framework(data)

    # Try common patterns for test results
    failed_details = []
    total_tests = 0
    failed_tests = 0
    passed_tests = 0

    # Pattern 1: Look for 'tests' or 'results' array
    test_array = data.get("tests") or data.get("results") or data.get("testResults")

    if test_array and isinstance(test_array, list):
        for test in test_array:
            if not isinstance(test, dict):
                continue

            total_tests += 1

            # Check for failure indicators
            status = test.get("status") or test.get("outcome") or test.get("result")
            passed = test.get("passed", True)

            is_failed = (
                status and status.lower() in ["failed", "failure", "error"]
            ) or (passed is False)

            if is_failed:
                failed_tests += 1

                # Extract test details
                test_name = (
                    test.get("name")
                    or test.get("title")
                    or test.get("nodeid")
                    or test.get("fullName")
                    or "Unknown Test"
                )

                file_path = (
                    test.get("file")
                    or test.get("location")
                    or test.get("filePath")
                    or "unknown"
                )

                error_message = (
                    test.get("error")
                    or test.get("message")
                    or test.get("failureMessage")
                    or "No error message"
                )

                if isinstance(error_message, list):
                    error_message = "\n".join(str(e) for e in error_message)

                failed_details.append(
                    {
                        "test_name": test_name,
                        "file_path": str(file_path),
                        "error_message": str(error_message)[:500],
                        "stack_trace": _compress_stack_trace(str(error_message)),
                    }
                )
            else:
                passed_tests += 1

    # Pattern 2: Look for summary statistics
    summary = data.get("summary") or {}
    if summary:
        total_tests = total_tests or summary.get("total", 0)
        passed_tests = passed_tests or summary.get("passed", 0)
        failed_tests = failed_tests or summary.get("failed", 0)

    # If no tests found, indicate that console fallback may be needed
    if total_tests == 0 and not failed_details:
        return {
            "test_framework": framework,
            "parse_mode": "generic",
            "warning": "No test results found in JSON. Consider using console output parser.",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "failed_test_details": [],
        }

    return {
        "test_framework": framework,
        "parse_mode": "generic",
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "failed_test_details": failed_details,
    }


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
        r"FAIL\s+(.+?)\n\s*●\s+(.+?)\n\n([\s\S]*?)(?=\n\s*●|\n\nTest Suites:|\Z)",
        re.MULTILINE,
    )

    for match in jest_pattern.finditer(text):
        file_path = match.group(1).strip()
        test_name = match.group(2).strip()
        error_block = match.group(3).strip()

        # Compress error block
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

        # Skip very long lines (likely verbose output)
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

    # If compression too aggressive, return more
    if len(compressed) < 10:
        return "\n".join(lines[:100])  # Keep first 100 lines

    return "\n".join(compressed)


def _identify_framework(data: Dict[str, Any]) -> str:
    """
    Attempt to identify test framework from JSON structure.

    Args:
        data: Parsed JSON data

    Returns:
        Framework name or "unknown"
    """
    # Check for Jest-specific fields
    if "numTotalTests" in data or "testResults" in data:
        return "jest"

    # Check for pytest-specific fields
    if "pytest_version" in data or ("summary" in data and "duration" in data):
        return "pytest"

    # Check for other frameworks
    if "mocha" in str(data).lower():
        return "mocha"

    if "jasmine" in str(data).lower():
        return "jasmine"

    return "unknown"


def detect_test_framework(project_path: str) -> Dict[str, Any]:
    """
    Detect test framework by scanning project for configuration files.

    Scans for:
    - Jest: package.json (with jest field or test script), jest.config.js/ts
    - Pytest: pytest.ini, pyproject.toml, setup.cfg, conftest.py

    Args:
        project_path: Root directory of project to scan

    Returns:
        Dictionary containing:
        - framework: "jest" | "pytest" | "mocha" | "unknown" | "multiple"
        - confidence: "high" | "medium" | "low" | "none"
        - detected_from: List of files that indicated framework
        - recommended_command: Shell command with JSON output configured
        - frameworks_detected: List of all detected frameworks (if multiple)
        - warning: Warning message if multiple frameworks detected
        - notes: Additional detection notes

    Examples:
        >>> detect_test_framework("/path/to/project")
        {
            "framework": "jest",
            "confidence": "high",
            "detected_from": ["package.json"],
            "recommended_command": "npm test -- --json --outputFile=.adw/test-results.json"
        }
    """
    project_dir = Path(project_path)

    # Check if directory exists
    if not project_dir.exists() or not project_dir.is_dir():
        return {
            "framework": "unknown",
            "confidence": "none",
            "detected_from": [],
            "recommended_command": "Please specify test command manually - project directory not found",
            "notes": f"Directory does not exist: {project_path}",
        }

    detected_frameworks = []
    detection_sources = {}  # framework -> list of source files

    # Detect Jest
    jest_detected, jest_sources = _detect_jest(project_dir)
    if jest_detected:
        detected_frameworks.append("jest")
        detection_sources["jest"] = jest_sources

    # Detect Pytest
    pytest_detected, pytest_sources, pytest_confidence = _detect_pytest(project_dir)
    if pytest_detected:
        detected_frameworks.append("pytest")
        detection_sources["pytest"] = pytest_sources

    # Detect Mocha (basic detection)
    mocha_detected, mocha_sources = _detect_mocha(project_dir)
    if mocha_detected:
        detected_frameworks.append("mocha")
        detection_sources["mocha"] = mocha_sources

    # Handle detection results
    if len(detected_frameworks) == 0:
        return {
            "framework": "unknown",
            "confidence": "none",
            "detected_from": [],
            "recommended_command": "Please specify test command manually - no test framework detected",
            "notes": "No recognized test framework configuration found. Checked for Jest, Pytest, Mocha.",
        }

    if len(detected_frameworks) > 1:
        # Multiple frameworks detected
        return {
            "framework": "multiple",
            "confidence": "high",
            "frameworks_detected": detected_frameworks,
            "detected_from": sum(detection_sources.values(), []),  # Flatten all sources
            "recommended_command": f"Multiple frameworks detected ({', '.join(detected_frameworks)}). Please specify which to use.",
            "warning": f"Multiple test frameworks detected: {', '.join(detected_frameworks)}. Consider using separate test commands or clarifying which framework to use.",
            "notes": "Multiple frameworks found. Configure test command based on your primary framework.",
        }

    # Single framework detected
    framework = detected_frameworks[0]
    sources = detection_sources[framework]

    if framework == "jest":
        confidence = "high"
        recommended_cmd = _generate_jest_command(project_dir)
    elif framework == "pytest":
        confidence = pytest_confidence
        recommended_cmd = _generate_pytest_command()
    elif framework == "mocha":
        confidence = "medium"
        recommended_cmd = _generate_mocha_command()
    else:
        confidence = "low"
        recommended_cmd = "Please specify test command manually"

    return {
        "framework": framework,
        "confidence": confidence,
        "detected_from": sources,
        "recommended_command": recommended_cmd,
        "notes": f"Detected {framework} from {', '.join(sources)}",
    }


def _detect_jest(project_dir: Path) -> tuple[bool, List[str]]:
    """
    Detect Jest test framework.

    Returns:
        (detected: bool, sources: List[str])
    """
    sources = []

    # Check for jest.config.js/ts
    for config_file in ["jest.config.js", "jest.config.ts", "jest.config.json"]:
        if (project_dir / config_file).exists():
            sources.append(config_file)

    # Check package.json
    package_json_path = project_dir / "package.json"
    if package_json_path.exists():
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)

            # Check for jest configuration field
            if "jest" in package_data:
                sources.append("package.json (jest config)")

            # Check for jest in test script
            scripts = package_data.get("scripts", {})
            test_script = scripts.get("test", "")
            if "jest" in test_script.lower():
                sources.append("package.json (test script)")

            # Check for jest in devDependencies
            dev_deps = package_data.get("devDependencies", {})
            if "jest" in dev_deps:
                sources.append("package.json (dependencies)")

        except (json.JSONDecodeError, IOError):
            # Malformed package.json - ignore
            pass

    return len(sources) > 0, sources


def _detect_pytest(project_dir: Path) -> tuple[bool, List[str], str]:
    """
    Detect Pytest test framework.

    Returns:
        (detected: bool, sources: List[str], confidence: str)
    """
    sources = []
    confidence = "high"

    # Check for pytest.ini
    if (project_dir / "pytest.ini").exists():
        sources.append("pytest.ini")

    # Check for pyproject.toml with [tool.pytest.ini_options]
    pyproject_path = project_dir / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "[tool.pytest" in content:
                    sources.append("pyproject.toml")
        except IOError:
            pass

    # Check for setup.cfg with [tool:pytest]
    setup_cfg_path = project_dir / "setup.cfg"
    if setup_cfg_path.exists():
        try:
            with open(setup_cfg_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "[tool:pytest]" in content or "[pytest]" in content:
                    sources.append("setup.cfg")
        except IOError:
            pass

    # Check for conftest.py (lower confidence)
    if (project_dir / "conftest.py").exists():
        sources.append("conftest.py")
        if len(sources) == 1:  # Only conftest, no explicit config
            confidence = "medium"

    # Check for tox.ini with pytest
    tox_ini_path = project_dir / "tox.ini"
    if tox_ini_path.exists():
        try:
            with open(tox_ini_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "pytest" in content:
                    sources.append("tox.ini")
        except IOError:
            pass

    return len(sources) > 0, sources, confidence


def _detect_mocha(project_dir: Path) -> tuple[bool, List[str]]:
    """
    Detect Mocha test framework.

    Returns:
        (detected: bool, sources: List[str])
    """
    sources = []

    # Check for .mocharc.json/js
    for config_file in [".mocharc.json", ".mocharc.js", ".mocharc.yaml", "mocha.opts"]:
        if (project_dir / config_file).exists():
            sources.append(config_file)

    # Check package.json for mocha
    package_json_path = project_dir / "package.json"
    if package_json_path.exists():
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)

            # Check test script
            scripts = package_data.get("scripts", {})
            test_script = scripts.get("test", "")
            if "mocha" in test_script.lower():
                sources.append("package.json (test script)")

            # Check devDependencies
            dev_deps = package_data.get("devDependencies", {})
            if "mocha" in dev_deps:
                sources.append("package.json (dependencies)")

        except (json.JSONDecodeError, IOError):
            pass

    return len(sources) > 0, sources


def _generate_jest_command(project_dir: Path) -> str:
    """
    Generate recommended Jest command with JSON output.

    Args:
        project_dir: Project root directory

    Returns:
        Recommended command string
    """
    # Check if using npm or yarn
    has_package_lock = (project_dir / "package-lock.json").exists()
    has_yarn_lock = (project_dir / "yarn.lock").exists()

    if has_yarn_lock:
        runner = "yarn test"
    elif has_package_lock:
        runner = "npm test --"
    else:
        runner = "npx jest"

    # JSON output command
    output_path = ".adw/test-results.json"
    return f"{runner} --json --outputFile={output_path}"


def _generate_pytest_command() -> str:
    """
    Generate recommended Pytest command with JSON output.

    Returns:
        Recommended command string
    """
    output_path = ".adw/test-results.json"
    return f"pytest --json-report --json-report-file={output_path}"


def _generate_mocha_command() -> str:
    """
    Generate recommended Mocha command with JSON output.

    Returns:
        Recommended command string
    """
    output_path = ".adw/test-results.json"
    return f"mocha --reporter json > {output_path}"
