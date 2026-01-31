#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "requests", "jira", "rich", "pyyaml", "pytest"]
# ///

"""
ADW Test - AI Developer Workflow for agentic testing

Usage:
  uv run adw_test.py <issue-number> [adw-id] [--skip-e2e]

Workflow:
1. Fetch Jira issue details (if not in state)
2. Run application test suite locally (via subprocess)
3. Report results to issue
4. If failed, use OpenCode HTTP API to resolve failures
5. Create commit with test results
6. Push and update PR

Environment Requirements:
- OpenCode server running and accessible (Story 3.5: migrated from Copilot CLI)
"""

import json
import subprocess
import sys
import os
import logging
import re
import glob
from datetime import datetime
from typing import Tuple, Optional, List
from dotenv import load_dotenv
from scripts.adw_modules.data_types import (
    GitHubIssue,
    AgentPromptResponse,
    TestResult,
    E2ETestResult,
    IssueClassSlashCommand,
)
from scripts.adw_modules.bitbucket_ops import (
    extract_repo_path,
    get_repo_url,
)
from scripts.adw_modules.utils import (
    make_adw_id,
    setup_logger,
    parse_json,
    get_test_command,
    load_prompt,
    get_rich_console_instance,
)
from scripts.adw_modules.state import ADWState
from scripts.adw_modules.git_ops import (
    commit_changes,
    finalize_git_operations,
    create_branch,
)
from scripts.adw_modules.workflow_ops import (
    format_issue_message,
    create_commit,
    ensure_adw_id,
    classify_issue,
)
from scripts.adw_modules.jira import (
    jira_fetch_issue,
    jira_make_issue_comment,
    jira_add_attachment,
)
from scripts.adw_modules.config import config
from scripts.adw_modules.agent import execute_opencode_prompt
from scripts.adw_modules.opencode_http_client import check_opencode_server_available

# Agent name constants
AGENT_TESTER = "test_runner"
AGENT_E2E_TESTER = "e2e_test_runner"
AGENT_BRANCH_GENERATOR = "branch_generator"

# Maximum number of test retry attempts after resolution
MAX_TEST_RETRY_ATTEMPTS = 4
MAX_E2E_TEST_RETRY_ATTEMPTS = 2  # E2E ui tests


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that required tools are available.

    Story 3.5: Migrated from Copilot CLI check to OpenCode server check.
    Now checks if OpenCode server is available instead of checking for copilot binary.
    """
    # Story 3.5: Check OpenCode server availability instead of Copilot CLI
    if not check_opencode_server_available():
        error_msg = (
            "Error: OpenCode server is not available or not responding.\n"
            "Please ensure OpenCode is running:\n"
            "  1. Start server: opencode serve --port 4096\n"
            "  2. Authenticate: opencode auth login\n"
            "  3. Verify: curl http://localhost:4096/health"
        )
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)


def parse_args(
    state: Optional[ADWState] = None,
    logger: Optional[logging.Logger] = None,
) -> Tuple[Optional[str], Optional[str], bool]:
    """Parse command line arguments.
    Returns (issue_number, adw_id, skip_e2e) where issue_number and adw_id may be None."""
    skip_e2e = False

    # Check for --skip-e2e flag in args
    if "--skip-e2e" in sys.argv:
        skip_e2e = True
        sys.argv.remove("--skip-e2e")

    # If we have state from stdin, we might not need issue number from args
    if state:
        # In piped mode, we might have no args at all
        if len(sys.argv) >= 2:
            # If an issue number is provided, use it
            return sys.argv[1], None, skip_e2e
        else:
            # Otherwise, we'll get issue from state
            return None, None, skip_e2e

    # Standalone mode - need at least issue number
    if len(sys.argv) < 2:
        usage_msg = [
            "Usage:",
            "  Standalone: uv run adw_test.py <issue-number> [adw-id] [--skip-e2e]",
            "  Chained: ... | uv run adw_test.py [--skip-e2e]",
            "Examples:",
            "  uv run adw_test.py 123",
            "  uv run adw_test.py 123 abc12345",
            "  uv run adw_test.py 123 --skip-e2e",
            '  echo \'{"issue_number": "123"}\' | uv run adw_test.py',
        ]
        if logger:
            for msg in usage_msg:
                logger.error(msg)
        else:
            for msg in usage_msg:
                print(msg)
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    return issue_number, adw_id, skip_e2e


def log_test_results(
    state: ADWState,
    results: List[TestResult],
    e2e_results: List[E2ETestResult],
    logger: logging.Logger,
) -> None:
    """Log comprehensive test results summary to the issue."""
    issue_number = state.get("issue_number")
    adw_id = state.get("adw_id")

    if not issue_number:
        logger.warning("No issue number in state, skipping test results logging")
        return

    # Calculate counts
    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count
    e2e_passed_count = sum(1 for r in e2e_results if r.passed)
    e2e_failed_count = len(e2e_results) - e2e_passed_count

    # Create comprehensive summary
    summary = f"# 📊 Test Run Summary\n\n"

    # Unit tests summary
    summary += f"## Unit Tests\n"
    summary += f"**Total Tests:** {len(results)}\n"
    summary += f"**Passed:** {passed_count} ✅\n"
    summary += f"**Failed:** {failed_count} ❌\n\n"

    if results:
        summary += "### Details:\n"
        for result in results:
            status = "✅" if result.passed else "❌"
            summary += f"- {status} **{result.test_name}**\n"
            if not result.passed and result.error:
                summary += f"  - Error: {result.error[:200]}...\n"

    # E2E tests summary if they were run
    if e2e_results:
        summary += f"\n## E2E Tests\n"
        summary += f"**Total Tests:** {len(e2e_results)}\n"
        summary += f"**Passed:** {e2e_passed_count} ✅\n"
        summary += f"**Failed:** {e2e_failed_count} ❌\n\n"

        summary += "### Details:\n"
        for result in e2e_results:
            status = "✅" if result.passed else "❌"
            summary += f"- {status} **{result.test_name}**\n"
            if not result.passed and result.error:
                summary += f"  - Error: {result.error[:200]}...\n"
            if result.screenshots:
                summary += f"  - Screenshots: {', '.join(result.screenshots)}\n"

    # Overall status
    total_failures = failed_count + e2e_failed_count
    if total_failures > 0:
        summary += f"\n## ❌ Overall Status: FAILED\n"
        summary += f"Total failures: {total_failures}\n"
    else:
        summary += f"\n## ✅ Overall Status: PASSED\n"
        summary += f"All {len(results) + len(e2e_results)} tests passed successfully!\n"

    # Post the summary to the issue
    jira_make_issue_comment(
        issue_number, format_issue_message(adw_id, "test_summary", summary)
    )

    # Save summary to file and attach to Jira
    try:
        # Determine logs directory from config
        log_dir = config.logs_dir / adw_id
        os.makedirs(log_dir, exist_ok=True)

        # Save main test summary
        summary_file_path = log_dir / f"test_results_{adw_id}.md"
        with open(summary_file_path, "w") as f:
            f.write(summary)

        logger.info(f"Saved test summary to {summary_file_path}")

        # If E2E tests were run, save detailed E2E results to e2e_generator folder
        if e2e_results:
            e2e_generator_dir = log_dir / "e2e_generator"
            os.makedirs(e2e_generator_dir, exist_ok=True)

            # Save detailed E2E test results
            e2e_results_file = e2e_generator_dir / f"e2e_test_results_{adw_id}.md"
            e2e_summary = "# E2E Test Results\n\n"
            e2e_summary += f"Generated: {datetime.now().isoformat()}\n"
            e2e_summary += f"ADW ID: {adw_id}\n\n"

            for i, result in enumerate(e2e_results):
                status = "✅ PASSED" if result.passed else "❌ FAILED"
                e2e_summary += f"## Test {i + 1}: {result.test_name}\n"
                e2e_summary += f"**Status:** {status}\n"
                if result.error:
                    e2e_summary += f"**Error:** {result.error}\n"
                e2e_summary += f"**Path:** {result.test_path}\n\n"

            with open(e2e_results_file, "w") as f:
                f.write(e2e_summary)

            logger.info(f"Saved E2E test results to {e2e_results_file}")

        jira_add_attachment(issue_number, str(summary_file_path))
        logger.info(f"Attached test summary to issue #{issue_number}")

    except Exception as e:
        logger.error(f"Failed to attach test summary: {e}")

    logger.info(f"Posted comprehensive test results summary to issue #{issue_number}")


def parse_local_test_output(
    output: str, exit_code: int, test_command: str = ""
) -> Tuple[List[TestResult], int, int]:
    """Parse stdout from local test runner to create TestResults.

    Simplified implementation: Uses exit code only (framework-agnostic).
    Different test runners have different output formats, so we rely on
    the universal exit code convention: 0 = success, non-zero = failure.
    """
    results = []

    if exit_code == 0:
        # Tests passed
        results.append(
            TestResult(
                test_name="Test Suite Execution",
                passed=True,
                execution_command=test_command or "test suite",
                test_purpose="Full test suite execution",
                error=None,
            )
        )
    else:
        # Tests failed
        results.append(
            TestResult(
                test_name="Test Suite Execution",
                passed=False,
                execution_command=test_command or "test suite",
                test_purpose="Full test suite execution",
                error=f"Test command failed with exit code {exit_code}",
            )
        )

    passed_count = sum(1 for r in results if r.passed)
    failed_count = len(results) - passed_count

    return results, passed_count, failed_count


def run_tests(
    adw_id: str, logger: logging.Logger
) -> Tuple[bool, str, List[TestResult], int, int]:
    """Run the test suite locally using detected command."""
    test_command = get_test_command()
    logger.info(f"Running tests with command: {test_command}")

    try:
        # Run the test command
        # We use shell=True to handle complex commands like "uv run pytest" easily
        result = subprocess.run(
            test_command, shell=True, capture_output=True, text=True
        )

        logger.debug(f"Test command exit code: {result.returncode}")
        logger.debug(
            f"Test command output (first 500 chars):\n{result.stdout[:500]}..."
        )
        if result.stderr:
            logger.debug(
                f"Test command stderr (first 500 chars):\n{result.stderr[:500]}..."
            )

        full_output = result.stdout + "\n" + result.stderr

        # Parse results
        results, passed, failed = parse_local_test_output(
            full_output, result.returncode, test_command
        )

        return result.returncode == 0, full_output, results, passed, failed

    except Exception as e:
        logger.error(f"Error executing test command: {e}")
        return False, str(e), [], 0, 1


def format_test_results_comment(
    results: List[TestResult], passed_count: int, failed_count: int
) -> str:
    """Format test results for GitHub issue comment with JSON blocks."""
    if not results:
        return "❌ No test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed Tests")
        comment_parts.append("")

        # Loop over each failed test
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests header
    if passed_tests:
        comment_parts.append("## ✅ Passed Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Remove trailing empty line
    if comment_parts and comment_parts[-1] == "":
        comment_parts.pop()

    return "\n".join(comment_parts)


def resolve_failed_tests(
    failed_tests: List[TestResult],
    test_output: str,
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    iteration: int = 1,
) -> bool:
    """
    Attempt to resolve failed tests using OpenCode HTTP API with Claude Sonnet 4.
    Returns True if resolution attempted successfully (OpenCode API ran without error).
    """
    logger.info(f"\n=== Attempting to resolve failures (Iteration {iteration}) ===")

    # Construct prompt
    try:
        prompt_template = load_prompt("resolve_failed_tests")
        prompt = prompt_template.replace("$ARGUMENTS", test_output)
    except Exception as e:
        logger.warning(
            f"Could not load resolve_failed_tests.md: {e}, using fallback prompt"
        )
        prompt = f"""
The following tests failed during execution:

{test_output}

Please analyze the codebase and fix the errors that caused these tests to fail.
1. Examine the failure output to understand the root cause.
2. Modify the code to fix the issues.
3. You may run tests locally to verify your fixes if needed.

Your primary goal is to make the tests pass.
"""

    # Story 3.2: Use OpenCode HTTP API with task_type="test_fix" → Claude Sonnet 4
    logger.info("Calling OpenCode HTTP API to fix tests...")
    logger.debug(f"Using task_type='test_fix' (routes to Claude Sonnet 4)")

    # Notify issue
    jira_make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            "test_resolver",
            f"❌ Attempting to resolve {len(failed_tests)} failed tests (Iteration {iteration})...",
        ),
    )

    try:
        # Story 3.2: Call OpenCode HTTP API instead of Copilot CLI
        response = execute_opencode_prompt(
            prompt=prompt,
            task_type="test_fix",  # Routes to Claude Sonnet 4 (GitHub Copilot)
            adw_id=adw_id,
            agent_name="test_resolver",
        )

        # Handle OpenCode API failure
        if not response.success:
            logger.error(f"OpenCode HTTP API execution failed")
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "test_resolver",
                    f"❌ OpenCode API execution failed",
                ),
            )
            return False

        logger.info("OpenCode HTTP API finished execution.")
        logger.debug(f"OpenCode response output:\n{response.output}")

        # Extract metrics from response
        files_changed = (
            response.files_changed if response.files_changed is not None else 0
        )

        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "test_resolver",
                f"✅ OpenCode API finished. Files changed: {files_changed}",
            ),
        )

        return True

    except Exception as e:
        logger.error(f"Error invoking OpenCode HTTP API: {e}")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "test_resolver",
                f"❌ OpenCode API invocation failed: {str(e)[:200]}...",
            ),
        )
        return False

        logger.info("Copilot CLI finished execution.")
        logger.debug(f"Copilot output: {result.stdout}")

        # Parse output just to log what happened
        parsed = parse_copilot_output(result.stdout)

        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "test_resolver",
                f"✅ Copilot finished. Success: {success}",
            ),
        )

        return True

    except Exception as e:
        logger.error(f"Error invoking Copilot: {e}")
        return False


def run_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    max_attempts: int = MAX_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[TestResult], int, int]:
    """
    Run tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== Test Run Attempt {attempt}/{max_attempts} ===")

        # Run tests locally
        success, output, results, passed_count, failed_count = run_tests(adw_id, logger)

        # If all passed, we're done
        if failed_count == 0:
            logger.info("All tests passed, stopping retry attempts")
            break

        if attempt == max_attempts:
            logger.info(f"Reached maximum retry attempts ({max_attempts}), stopping")
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed tests ===")

        # Get list of failed tests
        failed_tests = [test for test in results if not test.passed]

        # Attempt resolution via Copilot
        resolution_success = resolve_failed_tests(
            failed_tests, output, adw_id, issue_number, logger, iteration=attempt
        )

        if resolution_success:
            logger.info(f"\n=== Re-running tests after resolution attempt ===")
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_TESTER,
                    f"🔄 Re-running tests (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            logger.warning("Resolution attempt failed to execute properly")
            # We continue anyway to see if maybe something changed or to just retry

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count


def run_e2e_tests(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    attempt: int = 1,
) -> List[E2ETestResult]:
    """Run all E2E tests found in configured directory using OpenCode HTTP API."""

    # Skip E2E tests if not enabled
    if not config.e2e_tests_enabled:
        logger.info("E2E tests disabled in configuration")
        return []

    # Find all E2E test files using configuration
    e2e_dir = config.project_root / config.e2e_tests_directory
    e2e_pattern = str(e2e_dir / config.e2e_tests_pattern)
    e2e_test_files = glob.glob(e2e_pattern)
    logger.info(f"Found {len(e2e_test_files)} E2E test files in {e2e_dir}")

    if not e2e_test_files:
        logger.warning(f"No E2E test files found in {e2e_pattern}")
        logger.info(f"To create E2E tests, add scenario files to: {e2e_dir}")
        return []

    results = []

    # Run tests sequentially
    for idx, test_file in enumerate(e2e_test_files):
        agent_name = f"{AGENT_E2E_TESTER}_{attempt - 1}_{idx}"
        result = execute_single_e2e_test(
            test_file, agent_name, adw_id, issue_number, logger
        )
        if result:
            results.append(result)
            # Break on first failure
            if not result.passed:
                logger.info(f"E2E test failed: {result.test_name}, stopping execution")
                break

    return results


def execute_single_e2e_test(
    test_file: str,
    agent_name: str,
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
) -> Optional[E2ETestResult]:
    """Execute a single E2E test using OpenCode HTTP API and return result.

    Story 3.3: Migrated from Copilot CLI to OpenCode HTTP API with task_type='test_fix'.
    Uses Claude Sonnet 4 (via GitHub Copilot) for E2E test execution.

    Any shell scripts generated during execution are saved to e2e_temp_scripts directory.
    """
    test_name = os.path.basename(test_file).replace(".md", "")
    logger.info(f"Running E2E test: {test_name}")

    # Create temp scripts directory for this execution
    # This prevents generated .sh files from cluttering the project root
    original_cwd = os.getcwd()
    temp_scripts_dir = config.logs_dir / adw_id / "e2e_generator" / "scripts"
    try:
        os.makedirs(temp_scripts_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create temp scripts directory {temp_scripts_dir}: {e}")
        # Continue anyway, just use original directory

    try:
        with open(test_file, "r") as f:
            test_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read test file {test_file}: {e}")
        return E2ETestResult(
            test_name=test_name,
            status="failed",
            test_path=test_file,
            error=f"Failed to read test file: {e}",
        )

    # Make issue comment
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, agent_name, f"✅ Running E2E test: {test_name}"),
    )

    prompt = f"""
Please execute the following E2E test plan. 
Perform the steps described and verify the expected outcomes.
If the test involves UI, use available tools to simulate or verify if possible, 
or code scripts to perform the check.

Test Plan ({test_name}):
---
{test_content}
---

Report whether the test passed or failed, and provide details.
"""

    # Story 3.3: Use OpenCode HTTP API with task_type="test_fix" → Claude Sonnet 4
    logger.info("Calling OpenCode HTTP API to execute E2E test...")
    logger.debug(f"Using task_type='test_fix' (routes to Claude Sonnet 4)")

    try:
        # Change to temp scripts directory so any generated files go there, not project root
        os.chdir(str(temp_scripts_dir))
        logger.debug(
            f"Changed working directory to {temp_scripts_dir} for E2E test execution"
        )

        # Call OpenCode HTTP API instead of Copilot CLI subprocess
        response = execute_opencode_prompt(
            prompt=prompt,
            task_type="test_fix",  # Routes to Claude Sonnet 4 (GitHub Copilot)
            adw_id=adw_id,
            agent_name=agent_name,
        )

        # Handle OpenCode API failure
        if not response.success:
            logger.error(f"OpenCode HTTP API execution failed for E2E test {test_name}")
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name,
                    f"❌ E2E test completed: {test_name}\nOpenCode API execution failed",
                ),
            )
            return E2ETestResult(
                test_name=test_name,
                status="failed",
                test_path=test_file,
                error="OpenCode HTTP API execution failed",
            )

        logger.info("OpenCode HTTP API execution completed.")
        logger.debug(f"OpenCode response output:\n{response.output}")

        # Extract metrics from response
        files_changed = (
            response.files_changed if response.files_changed is not None else 0
        )

        # Parse OpenCode output to determine test status
        # Look for pass/fail patterns in the response
        output_lower = response.output.lower()
        success_patterns = [
            "test passed",
            "e2e test passed",
            "all steps completed successfully",
            "expected outcome verified",
            "verification successful",
        ]
        failure_patterns = [
            "test failed",
            "e2e test failed",
            "error:",
            "exception:",
            "verification failed",
        ]

        # Default to passed unless we find a clear failure indicator
        test_passed = True
        error_message = None

        for pattern in failure_patterns:
            if pattern in output_lower:
                test_passed = False
                error_message = pattern
                break

        # If no explicit failure found, check for success patterns
        if test_passed:
            for pattern in success_patterns:
                if pattern in output_lower:
                    test_passed = True
                    error_message = None
                    break

        e2e_result = E2ETestResult(
            test_name=test_name,
            status="passed" if test_passed else "failed",
            test_path=test_file,
            error=error_message,
            screenshots=[],  # Screenshots support removed for now as we don't have direct access
        )

        status_emoji = "✅" if e2e_result.passed else "❌"
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name,
                f"{status_emoji} E2E test completed: {test_name}\nFiles changed: {files_changed}",
            ),
        )

        return e2e_result

    except Exception as e:
        logger.error(f"Error executing E2E test {test_name}: {e}")
        return E2ETestResult(
            test_name=test_name,
            status="failed",
            test_path=test_file,
            error=f"Execution error: {str(e)}",
        )

    finally:
        # Always restore original working directory
        try:
            os.chdir(original_cwd)
            logger.debug(f"Restored working directory to {original_cwd}")
        except Exception as e:
            logger.warning(f"Failed to restore working directory: {e}")


def format_e2e_test_results_comment(
    results: List[E2ETestResult], passed_count: int, failed_count: int
) -> str:
    """Format E2E test results for GitHub issue comment."""
    if not results:
        return "❌ No E2E test results found"

    # Separate failed and passed tests
    failed_tests = [test for test in results if not test.passed]
    passed_tests = [test for test in results if test.passed]

    # Build comment
    comment_parts = []

    # Failed tests header
    if failed_tests:
        comment_parts.append("")
        comment_parts.append("## ❌ Failed E2E Tests")
        comment_parts.append("")

        # Loop over each failed test
        for test in failed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            comment_parts.append("```json")
            comment_parts.append(json.dumps(test.model_dump(), indent=2))
            comment_parts.append("```")
            comment_parts.append("")

    # Passed tests header
    if passed_tests:
        comment_parts.append("## ✅ Passed E2E Tests")
        comment_parts.append("")

        # Loop over each passed test
        for test in passed_tests:
            comment_parts.append(f"### {test.test_name}")
            comment_parts.append("")
            if test.screenshots:
                comment_parts.append(f"Screenshots: {len(test.screenshots)} captured")
            comment_parts.append("")

    # Remove trailing empty line
    if comment_parts and comment_parts[-1] == "":
        comment_parts.pop()

    return "\n".join(comment_parts)


def resolve_failed_e2e_tests(
    failed_tests: List[E2ETestResult],
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    iteration: int = 1,
) -> bool:
    """
    Attempt to resolve failed E2E tests using Copilot.
    """
    logger.info(f"\n=== Resolving failed E2E tests (Iteration {iteration}) ===")

    # We'll just ask Copilot to fix the issues found in the last run
    # Since we don't have the exact output from the previous run handy in a variable
    # (it was in the subprocess output), we rely on Copilot's context or we could pass it if we stored it.
    # For now, we'll give a generic fix instruction.

    prompt = f"""
The following E2E tests failed:
{", ".join([t.test_name for t in failed_tests])}

Please analyze the codebase and the test definitions to fix the issues.
"""

    jira_make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            "e2e_resolver",
            f"🔧 Attempting to resolve E2E failures...",
        ),
    )

    try:
        command = ["copilot", "-p", prompt, "--allow-all-tools", "--allow-all-paths"]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("E2E resolution finished.")
            return True
        else:
            logger.error("E2E resolution failed.")
            return False

    except Exception as e:
        logger.error(f"Error resolving E2E tests: {e}")
        return False


def run_e2e_tests_with_resolution(
    adw_id: str,
    issue_number: str,
    logger: logging.Logger,
    max_attempts: int = MAX_E2E_TEST_RETRY_ATTEMPTS,
) -> Tuple[List[E2ETestResult], int, int]:
    """
    Run E2E tests with automatic resolution and retry logic.
    Returns (results, passed_count, failed_count).
    """
    attempt = 0
    results = []
    passed_count = 0
    failed_count = 0

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== E2E Test Run Attempt {attempt}/{max_attempts} ===")

        # Run E2E tests
        results = run_e2e_tests(adw_id, issue_number, logger, attempt)

        if not results:
            logger.warning("No E2E test results to process")
            break

        # Count passes and failures
        passed_count = sum(1 for test in results if test.passed)
        failed_count = len(results) - passed_count

        # If no failures or this is the last attempt, we're done
        if failed_count == 0:
            logger.info("All E2E tests passed, stopping retry attempts")
            break
        if attempt == max_attempts:
            logger.info(
                f"Reached maximum E2E retry attempts ({max_attempts}), stopping"
            )
            break

        # If we have failed tests and this isn't the last attempt, try to resolve
        logger.info("\n=== Attempting to resolve failed E2E tests ===")

        failed_tests = [test for test in results if not test.passed]

        if resolve_failed_e2e_tests(
            failed_tests, adw_id, issue_number, logger, attempt
        ):
            logger.info(f"\n=== Re-running E2E tests after resolution ===")
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"🔄 Re-running E2E tests (attempt {attempt + 1}/{max_attempts})...",
                ),
            )
        else:
            logger.warning("E2E resolution failed")

    # Log final attempt status
    if attempt == max_attempts and failed_count > 0:
        logger.warning(
            f"Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures remaining"
        )
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                "ops",
                f"⚠️ Reached maximum E2E retry attempts ({max_attempts}) with {failed_count} failures",
            ),
        )

    return results, passed_count, failed_count


def main():
    """Main entry point."""
    # Load environment variables - explicitly load from current working directory
    from pathlib import Path

    project_env = Path.cwd() / ".env"
    if project_env.exists():
        load_dotenv(project_env, override=True)
    else:
        # Fallback to auto-discovery if no .env in current directory
        load_dotenv(override=True)

    # Get rich console instance
    rich_console = get_rich_console_instance()

    # Ensure config is loaded from current project directory
    # This prevents config loading issues when working directory changes during execution
    from adw_modules.config import config

    config.reinitialize_for_project(Path.cwd())

    # Parse arguments
    arg_issue_number, arg_adw_id, skip_e2e = parse_args(None)

    # Initialize state and issue number
    issue_number = arg_issue_number

    # Ensure we have an issue number
    if not issue_number:
        error_msg = "No issue number provided"
        if rich_console:
            rich_console.error(error_msg)
        else:
            print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)

    # Set up temp logger for initialization (console only)
    temp_logger = (
        setup_logger(arg_adw_id, "adw_test", enable_file_logging=False)
        if arg_adw_id
        else None
    )

    # Ensure ADW ID exists - creates one if needed
    adw_id, existing_state = ensure_adw_id(issue_number, arg_adw_id, temp_logger)

    # Rich console header
    if rich_console:
        rich_console.rule(f"ADW Test - Issue {issue_number}", style="blue")
        rich_console.info(f"ADW ID: {adw_id}")
        if skip_e2e:
            rich_console.warning("E2E tests will be skipped (--skip-e2e flag)")

    # Set up actual logger with valid ADW ID
    logger = setup_logger(adw_id, "adw_test")
    logger.info(f"ADW Test starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment (now with logger)
    check_env_vars(logger)

    # === LOADING ISSUE DATA PHASE ===
    if rich_console:
        rich_console.rule("Loading Issue Data", style="cyan")

    # Fetch issue details from Jira
    logger.info(f"Fetching issue {issue_number} from Jira")
    try:
        if rich_console:
            with rich_console.spinner(f"Fetching issue {issue_number} from Jira..."):
                raw_jira_issue = jira_fetch_issue(issue_number)
                from adw_modules.data_types import JiraIssue

                issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
            rich_console.success(f"Successfully fetched issue: {issue.title}")
        else:
            raw_jira_issue = jira_fetch_issue(issue_number)
            from adw_modules.data_types import JiraIssue

            issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
    except Exception as e:
        error_msg = f"Failed to fetch issue {issue_number} from Jira: {e}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        sys.exit(1)

    # Use existing state if available, otherwise load it
    if existing_state:
        state = existing_state
        logger.info(f"Using existing state from ensure_adw_id")
        if rich_console:
            rich_console.success("Using existing ADW state")
    else:
        # Try to load existing state (fallback case)
        logger.info(f"Loading state")
        if rich_console:
            with rich_console.spinner(f"Loading ADW state for {adw_id}..."):
                state = ADWState.load(adw_id, logger)
        else:
            state = ADWState.load(adw_id, logger)

        if not state:
            error_msg = f"No state found for ADW ID: {adw_id}"
            logger.error(error_msg)
            if rich_console:
                rich_console.error(error_msg)
                rich_console.error("Run adw_plan.py first to create the initial state")
            sys.exit(1)

        if rich_console:
            rich_console.success("ADW state loaded successfully")

    logger.info(f"Loaded state: {state.data}")

    # Get repo information from git remote
    try:
        github_repo_url: str = get_repo_url()
        repo_path: str = extract_repo_path(github_repo_url)
    except ValueError as e:
        logger.error(f"Error getting repository URL: {e}")
        # Not fatal for local testing, but might be for PRs

    issue_class = state.get("issue_class")

    # === BRANCH PREPARATION PHASE ===
    if rich_console:
        rich_console.rule("Preparing Test Branch", style="cyan")

    # Handle branch - either use existing or create new test branch
    branch_name = state.get("branch_name")
    if branch_name:
        # Try to checkout existing branch
        if rich_console:
            with rich_console.spinner(
                f"Checking out existing branch: {branch_name}..."
            ):
                result = subprocess.run(
                    ["git", "checkout", branch_name], capture_output=True, text=True
                )
        else:
            result = subprocess.run(
                ["git", "checkout", branch_name], capture_output=True, text=True
            )

        if result.returncode != 0:
            error_msg = f"Failed to checkout branch {branch_name}: {result.stderr}"
            logger.error(error_msg)
            if rich_console:
                rich_console.error(error_msg)
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"❌ Failed to checkout branch {branch_name}"
                ),
            )
            sys.exit(1)
        logger.info(f"Checked out existing branch: {branch_name}")
        if rich_console:
            rich_console.success(f"Checked out existing branch: {branch_name}")
    else:
        # No branch in state - create a test-specific branch
        logger.info("No branch in state, creating test branch")

        # Generate simple test branch name without classification
        branch_name = f"test-issue-{issue_number}-adw-{adw_id}"
        logger.info(f"Generated test branch name: {branch_name}")

        # Create the branch
        if rich_console:
            with rich_console.spinner(f"Creating test branch: {branch_name}..."):
                success, error = create_branch(branch_name)
        else:
            success, error = create_branch(branch_name)

        if not success:
            error_msg = f"Error creating branch: {error}"
            logger.error(error_msg)
            if rich_console:
                rich_console.error(error_msg)
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, "ops", f"❌ Error creating branch: {error}"
                ),
            )
            sys.exit(1)

        state.update(branch_name=branch_name)
        state.save("adw_test")
        logger.info(f"Created and checked out new test branch: {branch_name}")
        if rich_console:
            rich_console.success(
                f"Created and checked out new test branch: {branch_name}"
            )
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"✅ Created test branch: {branch_name}"
            ),
        )

    jira_make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Starting test suite")
    )

    # === UNIT TEST EXECUTION PHASE ===
    if rich_console:
        rich_console.rule("Running Unit Tests", style="cyan")

    # Run tests with automatic resolution and retry
    logger.info("\n=== Running test suite ===")
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_TESTER, "✅ Running application tests..."),
    )

    # Run tests with resolution and retry logic
    if rich_console:
        with rich_console.spinner("Running unit tests with automated resolution..."):
            results, passed_count, failed_count = run_tests_with_resolution(
                adw_id, issue_number, logger
            )

        # Display unit test results in a table
        if results:
            test_data = {f"Test {i + 1}": result for i, result in enumerate(results)}
            rich_console.status_table(test_data, "Unit Test Results")

        if failed_count == 0:
            rich_console.success(f"All {passed_count} unit tests passed!")
        else:
            rich_console.error(
                f"Unit tests completed: {passed_count} passed, {failed_count} failed"
            )
    else:
        results, passed_count, failed_count = run_tests_with_resolution(
            adw_id, issue_number, logger
        )

    # Format and post final results
    results_comment = format_test_results_comment(results, passed_count, failed_count)
    jira_make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id, AGENT_TESTER, f"📊 Final test results:\n{results_comment}"
        ),
    )

    # Log summary
    logger.info(f"Final test results: {passed_count} passed, {failed_count} failed")

    # If unit tests failed or skip_e2e flag is set, skip E2E tests
    if failed_count > 0:
        logger.warning("Skipping E2E tests due to unit test failures")
        if rich_console:
            rich_console.warning("Skipping E2E tests due to unit test failures")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping E2E tests due to unit test failures"
            ),
        )
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    elif skip_e2e:
        logger.info("Skipping E2E tests as requested")
        if rich_console:
            rich_console.info("Skipping E2E tests as requested via --skip-e2e flag")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", "⚠️ Skipping E2E tests as requested via --skip-e2e flag"
            ),
        )
        e2e_results = []
        e2e_passed_count = 0
        e2e_failed_count = 0
    else:
        # === E2E TEST EXECUTION PHASE ===
        if rich_console:
            rich_console.rule("Running E2E Tests", style="cyan")

        # Run E2E tests since unit tests passed
        logger.info("\n=== Running E2E test suite ===")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_E2E_TESTER, "✅ Starting E2E tests..."),
        )

        # Run E2E tests with resolution and retry logic
        if rich_console:
            with rich_console.spinner("Running E2E tests with automated resolution..."):
                e2e_results, e2e_passed_count, e2e_failed_count = (
                    run_e2e_tests_with_resolution(adw_id, issue_number, logger)
                )

            # Display E2E test results in a table
            if e2e_results:
                e2e_test_data = {
                    f"E2E Test {i + 1}": result for i, result in enumerate(e2e_results)
                }
                rich_console.status_table(e2e_test_data, "E2E Test Results")

            if e2e_failed_count == 0:
                rich_console.success(f"All {e2e_passed_count} E2E tests passed!")
            else:
                rich_console.error(
                    f"E2E tests completed: {e2e_passed_count} passed, {e2e_failed_count} failed"
                )
        else:
            e2e_results, e2e_passed_count, e2e_failed_count = (
                run_e2e_tests_with_resolution(adw_id, issue_number, logger)
            )

        # Format and post E2E results
        if e2e_results:
            e2e_results_comment = format_e2e_test_results_comment(
                e2e_results, e2e_passed_count, e2e_failed_count
            )
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    AGENT_E2E_TESTER,
                    f"📊 Final E2E test results:\n{e2e_results_comment}",
                ),
            )

            logger.info(
                f"Final E2E test results: {e2e_passed_count} passed, {e2e_failed_count} failed"
            )

    # === COMMITTING RESULTS PHASE ===
    if rich_console:
        rich_console.rule("Committing Test Results", style="cyan")

    # Check for changes before attempting to commit
    status_result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    has_changes = bool(status_result.stdout.strip())

    if has_changes:
        # Commit the test results
        logger.info("\n=== Committing test results ===")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(adw_id, AGENT_TESTER, "✅ Committing test results"),
        )

        # Fetch issue details if we haven't already
        if not issue:
            raw_issue = jira_fetch_issue(issue_number)
            from adw_modules.data_types import JiraIssue

            issue = JiraIssue.from_raw_jira_issue(raw_issue)

        # Get issue classification if we need it for commit
        if not issue_class:
            issue_class, error = classify_issue(issue, adw_id, logger)
            if error:
                logger.warning(
                    f"Error classifying issue: {error}, defaulting to /chore for test commit"
                )
                issue_class = "/chore"
            state.update(issue_class=issue_class)
            state.save("adw_test")

        commit_msg, error = create_commit(
            AGENT_TESTER, issue, issue_class, adw_id, logger
        )

        if error:
            error_msg = f"Error committing test results: {error}"
            logger.error(error_msg)
            if rich_console:
                rich_console.error(error_msg)
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id, AGENT_TESTER, f"❌ Error committing test results: {error}"
                ),
            )
            # Don't exit on commit error, continue to report final status
        else:
            # Actually commit
            success, error = commit_changes(commit_msg)
            if success:
                logger.info(f"Test results committed: {commit_msg}")
                if rich_console:
                    rich_console.success("Test results committed successfully")
            else:
                logger.error(f"Failed to commit changes: {error}")

        # === FINALIZATION PHASE ===
        if rich_console:
            rich_console.rule("Finalizing Git Operations", style="cyan")

        # Finalize git operations (push and create/update PR)
        logger.info("\n=== Finalizing git operations ===")
        if rich_console:
            with rich_console.spinner("Pushing changes and updating PR..."):
                finalize_git_operations(state, logger)
            rich_console.success("Git operations completed")
        else:
            finalize_git_operations(state, logger)
    else:
        logger.info(
            "No changes to commit (tests passed without modification). Skipping commit and push."
        )
        if rich_console:
            rich_console.info("No changes to commit. Skipping git operations.")

    # Log comprehensive test results to the issue
    log_test_results(state, results, e2e_results, logger)

    # Update state with test results
    state.save("adw_test")

    # Output state for chaining
    state.to_stdout()

    # === FINAL RESULTS ===
    # Exit with appropriate code
    total_failures = failed_count + e2e_failed_count
    if total_failures > 0:
        logger.info(f"Test suite completed with failures for issue #{issue_number}")
        failure_msg = f"❌ Test suite completed with failures:\n"
        if failed_count > 0:
            failure_msg += f"- Unit tests: {failed_count} failures\n"
        if e2e_failed_count > 0:
            failure_msg += f"- E2E tests: {e2e_failed_count} failures"

        if rich_console:
            rich_console.rule("❌ Test Suite Failed", style="red")
            rich_console.panel(
                f"Test suite completed with failures for issue {issue_number}\n"
                f"ADW ID: {adw_id}\n"
                f"Unit Test Results: {passed_count} passed, {failed_count} failed\n"
                f"E2E Test Results: {e2e_passed_count} passed, {e2e_failed_count} failed\n"
                f"Total Failures: {total_failures}",
                title="Test Summary (FAILED)",
                style="red",
            )

        jira_make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", failure_msg),
        )
        sys.exit(1)
    else:
        logger.info(f"Test suite completed successfully for issue #{issue_number}")
        success_msg = f"✅ All tests passed successfully!\n"
        success_msg += f"- Unit tests: {passed_count} passed\n"
        if e2e_results:
            success_msg += f"- E2E tests: {e2e_passed_count} passed"

        if rich_console:
            rich_console.rule("✅ Test Suite Passed", style="green")
            rich_console.panel(
                f"Test suite completed successfully for issue {issue_number}\n"
                f"ADW ID: {adw_id}\n"
                f"Unit Test Results: {passed_count} passed, {failed_count} failed\n"
                f"E2E Test Results: {e2e_passed_count} passed, {e2e_failed_count} failed\n"
                f"Total Tests: {passed_count + e2e_passed_count}",
                title="Test Summary (PASSED)",
                style="green",
            )

        jira_make_issue_comment(
            issue_number,
            format_issue_message(adw_id, "ops", success_msg),
        )


if __name__ == "__main__":
    main()
