#!/usr/bin/env python3
"""
Unit tests for Story 3.2: Refactor resolve_failed_tests() to use OpenCode HTTP API

Tests the migration from Copilot CLI to OpenCode HTTP API with Claude Sonnet 4,
verifying that test failure resolution is handled correctly through OpenCode HTTP API
and maintains backward compatibility with the test workflow.
"""

import logging
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import pytest

from scripts.adw_test import resolve_failed_tests
from scripts.adw_modules.data_types import AgentPromptResponse, TestResult


class TestStory32ResolveFailedTestsMigration:
    """Test suite for Story 3.2: resolve_failed_tests() migration to OpenCode HTTP API."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.adw_id = "test_adw_123"
        self.issue_number = "456"
        self.logger = MagicMock(spec=logging.Logger)

        # Sample test failure data
        self.failed_tests = [
            TestResult(
                test_name="test_example_fails",
                passed=False,
                error="AssertionError: Expected 5 but got 3",
            ),
            TestResult(
                test_name="test_another_failure",
                passed=False,
                error="ImportError: Module not found",
            ),
        ]

        self.test_output = """
FAILED test_example_fails
AssertionError: Expected 5 but got 3
File: src/example.py, Line 42

FAILED test_another_failure
ImportError: Module not found
File: src/utils.py, Line 15
        """.strip()

    def test_resolve_failed_tests_opencode_integration_success(self):
        """Test successful test failure resolution via OpenCode HTTP API."""
        # Mock successful OpenCode response
        mock_response = AgentPromptResponse(
            output="Fixed test_example_fails by correcting calculation. Fixed test_another_failure by adding import.",
            success=True,
            files_changed=2,
            lines_added=5,
            lines_removed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
                iteration=1,
            )

            # Verify OpenCode HTTP API called with correct parameters
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "test_fix"
            assert call_args[1]["adw_id"] == self.adw_id
            assert call_args[1]["agent_name"] == "test_resolver"
            assert self.test_output in call_args[1]["prompt"]
            assert "Fix a specific failing test" in call_args[1]["prompt"]

            # Verify successful return
            assert result is True

            # Verify logging
            self.logger.info.assert_any_call(
                "\n=== Attempting to resolve failures (Iteration 1) ==="
            )
            self.logger.info.assert_any_call(
                "Calling OpenCode HTTP API to fix tests..."
            )
            self.logger.debug.assert_any_call(
                "Using task_type='test_fix' (routes to Claude Sonnet 4)"
            )
            self.logger.info.assert_any_call("OpenCode HTTP API finished execution.")

    def test_resolve_failed_tests_opencode_api_failure(self):
        """Test handling of OpenCode HTTP API execution failure."""
        # Mock failed OpenCode response
        mock_response = AgentPromptResponse(
            output="Connection error to OpenCode server",
            success=False,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            result = resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
                iteration=2,
            )

            # Verify OpenCode HTTP API called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "test_fix"

            # Verify failure return
            assert result is False

            # Verify error logging
            self.logger.error.assert_any_call("OpenCode HTTP API execution failed")
            self.logger.info.assert_any_call(
                "Calling OpenCode HTTP API to fix tests..."
            )

            # Verify Jira comment about failure
            mock_jira.assert_any_call(
                self.issue_number,
                mock.ANY,  # format_issue_message result
            )

    def test_resolve_failed_tests_exception_handling(self):
        """Test exception handling during OpenCode HTTP API invocation."""
        # Mock exception during execute_opencode_prompt
        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                side_effect=Exception("Network timeout"),
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            result = resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
                iteration=1,
            )

            # Verify OpenCode HTTP API called
            mock_execute.assert_called_once()

            # Verify exception return
            assert result is False

            # Verify error logging
            self.logger.error.assert_any_call(
                "Error invoking OpenCode HTTP API: Network timeout"
            )

            # Verify Jira comment about exception
            mock_jira.assert_any_call(
                self.issue_number,
                mock.ANY,  # format_issue_message result
            )

    def test_resolve_failed_tests_files_changed_metric_extraction(self):
        """Test that files_changed metric is extracted from response."""
        # Mock response with files_changed=3
        mock_response = AgentPromptResponse(
            output="Fixed all test failures",
            success=True,
            files_changed=3,
            lines_added=12,
            lines_removed=4,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            result = resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify Jira comment contains files_changed metric
            jira_calls = mock_jira.call_args_list
            # Check for the success comment with files changed
            success_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if "Files changed: 3" in comment_text:
                    success_comment_found = True
                    break

            assert success_comment_found, (
                "Jira comment should contain 'Files changed: 3'"
            )

    def test_resolve_failed_tests_no_files_changed_fallback(self):
        """Test handling when files_changed is None in response."""
        # Mock response with files_changed=None (fallback to 0)
        mock_response = AgentPromptResponse(
            output="Fixed test failures",
            success=True,
            files_changed=None,  # No metrics from API
            lines_added=None,
            lines_removed=None,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            result = resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify success despite None metrics
            assert result is True

            # Verify Jira comment shows files_changed as 0
            jira_calls = mock_jira.call_args_list
            files_0_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if "Files changed: 0" in comment_text:
                    files_0_found = True
                    break

            assert files_0_found, (
                "Jira comment should show 'Files changed: 0' when None"
            )

    def test_resolve_failed_tests_multiple_iterations(self):
        """Test that multiple resolution iterations work correctly."""
        # Mock successful response for iteration 2
        mock_response = AgentPromptResponse(
            output="Fixed remaining test failures",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            # Simulate second iteration
            result = resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
                iteration=2,
            )

            # Verify iteration logged correctly
            self.logger.info.assert_any_call(
                "\n=== Attempting to resolve failures (Iteration 2) ==="
            )

            # Verify successful execution
            assert result is True
            mock_execute.assert_called_once()

    def test_resolve_failed_tests_task_type_routing(self):
        """Test that correct task_type is passed to OpenCode API."""
        mock_response = AgentPromptResponse(
            output="Fixed tests",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify task_type is "test_fix" (routes to Claude Sonnet 4)
            call_args = mock_execute.call_args[1]
            assert call_args["task_type"] == "test_fix"

    def test_resolve_failed_tests_agent_name(self):
        """Test that correct agent_name is passed to OpenCode API."""
        mock_response = AgentPromptResponse(
            output="Fixed tests",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify agent_name is "test_resolver"
            call_args = mock_execute.call_args[1]
            assert call_args["agent_name"] == "test_resolver"

    def test_resolve_failed_tests_prompt_content_includes_failure_output(self):
        """Test that test failure output is included in the prompt."""
        mock_response = AgentPromptResponse(
            output="Fixed tests",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify test output is in prompt
            call_args = mock_execute.call_args[1]
            assert self.test_output in call_args["prompt"]
            assert "FAILED test_example_fails" in call_args["prompt"]
            assert "AssertionError: Expected 5 but got 3" in call_args["prompt"]

    def test_resolve_failed_tests_jira_comment_on_attempt(self):
        """Test that Jira comment is made when attempting resolution."""
        mock_response = AgentPromptResponse(
            output="Fixed tests",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify Jira comment made for attempt
            assert mock_jira.call_count >= 1  # At least attempt comment made
            jira_calls = mock_jira.call_args_list

            # Check for attempt comment
            attempt_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if (
                    "Attempting to resolve" in comment_text
                    and "failed tests" in comment_text
                ):
                    attempt_comment_found = True
                    break

            assert attempt_comment_found, "Jira comment about attempt should be made"

    def test_resolve_failed_tests_jira_comment_on_success(self):
        """Test that Jira comment is made on successful resolution."""
        mock_response = AgentPromptResponse(
            output="Fixed tests",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify Jira comment made for success
            assert mock_jira.call_count >= 1
            jira_calls = mock_jira.call_args_list

            # Check for success comment
            success_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if (
                    "OpenCode API finished" in comment_text
                    and "Files changed:" in comment_text
                ):
                    success_comment_found = True
                    break

            assert success_comment_found, "Jira comment about success should be made"

    def test_resolve_failed_tests_empty_failed_tests_list(self):
        """Test handling of empty failed tests list."""
        mock_response = AgentPromptResponse(
            output="No failures to fix",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = resolve_failed_tests(
                failed_tests=[],  # Empty list
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Should still work even with empty list
            assert result is True

    def test_resolve_failed_tests_migration_verification(self):
        """Test that function no longer uses Copilot CLI."""
        mock_response = AgentPromptResponse(
            output="Fixed tests",
            success=True,
            files_changed=1,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment"),
            patch("adw_test.subprocess.run") as mock_subprocess,
        ):
            # Call resolve_failed_tests
            resolve_failed_tests(
                failed_tests=self.failed_tests,
                test_output=self.test_output,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify subprocess.run was NOT called (no Copilot CLI)
            # The function should use execute_opencode_prompt instead
            mock_subprocess.assert_not_called()

            # Verify OpenCode API was called instead
            self.logger.debug.assert_any_call(
                "Using task_type='test_fix' (routes to Claude Sonnet 4)"
            )
