#!/usr/bin/env python3
"""
Unit tests for Story 3.3: Refactor execute_single_e2e_test() to use OpenCode HTTP API

Tests the migration from Copilot CLI to OpenCode HTTP API with Claude Sonnet 4,
verifying that E2E test execution is handled correctly through OpenCode HTTP API
and maintains backward compatibility with E2E test workflow.
"""

import logging
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import pytest
import tempfile
import os

from scripts.adw_test import execute_single_e2e_test
from scripts.adw_modules.data_types import AgentPromptResponse, E2ETestResult


class TestStory33ExecuteSingleE2ETestMigration:
    """Test suite for Story 3.3: execute_single_e2e_test() migration to OpenCode HTTP API."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.adw_id = "test_adw_123"
        self.issue_number = "456"
        self.agent_name = "e2e_test_runner_0_0"
        self.logger = MagicMock(spec=logging.Logger)

        # Create a temporary test file
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_example.md")
        with open(self.test_file, "w") as f:
            f.write("""
# E2E Test: User Registration Flow

## Steps:
1. Navigate to registration page
2. Fill in valid user data
3. Submit registration form
4. Verify user is created in database
5. Verify confirmation email is sent

## Expected Outcome:
User should be successfully registered with confirmation email sent.
""")

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_execute_single_e2e_test_opencode_integration_success(self):
        """Test successful E2E test execution via OpenCode HTTP API."""
        # Mock successful OpenCode response
        mock_response = AgentPromptResponse(
            output="E2E test passed: User registration flow completed successfully. All steps verified.",
            success=True,
            files_changed=0,
            lines_added=0,
            lines_removed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify OpenCode HTTP API called with correct parameters
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "test_fix"
            assert call_args[1]["adw_id"] == self.adw_id
            assert call_args[1]["agent_name"] == self.agent_name
            # Check for key phrases in prompt (case-insensitive)
            prompt_lower = call_args[1]["prompt"].lower()
            assert "execute the following e2e test plan" in prompt_lower
            assert "user registration flow" in prompt_lower

            # Verify result structure
            assert result is not None
            assert isinstance(result, E2ETestResult)
            assert result.test_name == "test_example"
            assert result.test_path == self.test_file
            assert result.status == "passed"
            assert result.passed is True
            assert result.error is None

            # Verify logging
            self.logger.info.assert_any_call("Running E2E test: test_example")
            self.logger.info.assert_any_call("OpenCode HTTP API execution completed.")

    def test_execute_single_e2e_test_opencode_integration_failure(self):
        """Test E2E test failure via OpenCode HTTP API."""
        # Mock OpenCode response with test failure
        mock_response = AgentPromptResponse(
            output="E2E test failed: Step 3 - Registration form submission failed with 500 error.",
            success=True,  # OpenCode executed successfully, but test failed
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify OpenCode HTTP API called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "test_fix"

            # Verify result structure for failed test
            assert result is not None
            assert isinstance(result, E2ETestResult)
            assert result.test_name == "test_example"
            assert result.status == "failed"
            # Just verify error is set and test failed (flexible check)
            assert result.error is not None

    def test_execute_single_e2e_test_opencode_api_failure(self):
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
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify OpenCode HTTP API called
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "test_fix"

            # Verify result structure for API failure
            assert result is not None
            assert isinstance(result, E2ETestResult)
            assert result.test_name == "test_example"
            assert result.status == "failed"
            assert result.passed is False
            assert result.error is not None

            # Verify error logging
            self.logger.error.assert_any_call(
                "OpenCode HTTP API execution failed for E2E test test_example"
            )

    def test_execute_single_e2e_test_exception_handling(self):
        """Test exception handling during OpenCode HTTP API invocation."""
        # Mock exception during execute_opencode_prompt
        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                side_effect=Exception("Network timeout"),
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify OpenCode HTTP API called
            mock_execute.assert_called_once()

            # Verify result structure for exception
            assert result is not None
            assert isinstance(result, E2ETestResult)
            assert result.test_name == "test_example"
            assert result.status == "failed"
            # Just verify error exists (content may vary)
            assert result.error is not None
            assert "error" in result.error.lower() or "failed" in result.error.lower()

            # Verify error logging (flexible match)
            assert self.logger.error.call_count > 0

    def test_execute_single_e2e_test_files_changed_metric_extraction(self):
        """Test that files_changed metric is extracted from response."""
        # Mock response with files_changed=2
        mock_response = AgentPromptResponse(
            output="E2E test passed. Fixed 2 issues found during execution.",
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
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify result is successful
            assert result.passed is True

            # Verify Jira comment contains files_changed metric
            jira_calls = mock_jira.call_args_list
            success_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if "Files changed: 2" in comment_text:
                    success_comment_found = True
                    break

            assert success_comment_found, (
                "Jira comment should contain 'Files changed: 2'"
            )

    def test_execute_single_e2e_test_no_files_changed_fallback(self):
        """Test handling when files_changed is None in response."""
        # Mock response with files_changed=None (fallback to 0)
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=None,  # No metrics from API
            lines_added=None,
            lines_removed=None,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify result is successful despite None metrics
            assert result.passed is True

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

    def test_execute_single_e2e_test_task_type_routing(self):
        """Test that correct task_type is passed to OpenCode API."""
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify task_type is "test_fix" (routes to Claude Sonnet 4)
            call_args = mock_execute.call_args[1]
            assert call_args["task_type"] == "test_fix"

    def test_execute_single_e2e_test_agent_name(self):
        """Test that correct agent_name is passed to OpenCode API."""
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify agent_name is passed correctly
            call_args = mock_execute.call_args[1]
            assert call_args["agent_name"] == self.agent_name

    def test_execute_single_e2e_test_prompt_content(self):
        """Test that E2E test content is included in prompt."""
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify E2E test content is in prompt (case-insensitive, whitespace-tolerant)
            call_args = mock_execute.call_args
            prompt = call_args[1]["prompt"]
            prompt_lower = prompt.lower()
            assert "execute the following e2e test plan" in prompt_lower
            assert "user registration flow" in prompt_lower
            assert "navigate to registration page" in prompt_lower
            assert "verify user is created in database" in prompt_lower

    def test_execute_single_e2e_test_jira_comment_on_start(self):
        """Test that Jira comment is made when starting E2E test."""
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify Jira comment made for test start
            assert mock_jira.call_count >= 1
            jira_calls = mock_jira.call_args_list

            # Check for start comment
            start_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if (
                    "Running E2E test" in comment_text
                    and "test_example" in comment_text
                ):
                    start_comment_found = True
                    break

            assert start_comment_found, "Jira comment about test start should be made"

    def test_execute_single_e2e_test_jira_comment_on_success(self):
        """Test that Jira comment is made on successful test completion."""
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify Jira comment made for completion
            assert mock_jira.call_count >= 2  # Start + completion

            # Check for completion comment with ✅ emoji
            jira_calls = mock_jira.call_args_list
            completion_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if (
                    "E2E test completed" in comment_text
                    and "Files changed:" in comment_text
                ):
                    completion_comment_found = True
                    break

            assert completion_comment_found, (
                "Jira comment about test completion should be made"
            )

    def test_execute_single_e2e_test_jira_comment_on_failure(self):
        """Test that Jira comment is made on failed test."""
        mock_response = AgentPromptResponse(
            output="E2E test failed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch("scripts.adw_test.jira_make_issue_comment") as mock_jira,
        ):
            execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Check for failure comment with ❌ emoji
            jira_calls = mock_jira.call_args_list
            failure_comment_found = False
            for call_obj in jira_calls:
                comment_text = str(call_obj)
                if (
                    "E2E test completed" in comment_text
                    and "Files changed:" in comment_text
                ):
                    failure_comment_found = True
                    break

            assert failure_comment_found, (
                "Jira comment about test completion should be made (even for failures)"
            )

    def test_execute_single_e2e_test_file_read_failure(self):
        """Test handling of test file read failure."""
        # Test with non-existent file
        non_existent_file = "/tmp/non_existent_test.md"

        with (
            patch("scripts.adw_test.execute_opencode_prompt"),
            patch("scripts.adw_test.jira_make_issue_comment"),
        ):
            result = execute_single_e2e_test(
                test_file=non_existent_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify result indicates failure
            assert result is not None
            assert result.status == "failed"
            assert result.error is not None
            # Check that error message contains "failed to read" (flexible)
            assert "failed to read" in result.error.lower()

            # Verify error logging (flexible match)
            assert self.logger.error.call_count > 0

    def test_execute_single_e2e_test_migration_verification(self):
        """Test that function no longer uses Copilot CLI subprocess."""
        mock_response = AgentPromptResponse(
            output="E2E test passed.",
            success=True,
            files_changed=0,
        )

        with (
            patch(
                "scripts.adw_test.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_test.jira_make_issue_comment"),
            patch("scripts.adw_test.subprocess.run") as mock_subprocess,
        ):
            # Call execute_single_e2e_test
            result = execute_single_e2e_test(
                test_file=self.test_file,
                agent_name=self.agent_name,
                adw_id=self.adw_id,
                issue_number=self.issue_number,
                logger=self.logger,
            )

            # Verify subprocess.run was NOT called (no Copilot CLI)
            # The function should use execute_opencode_prompt instead
            mock_subprocess.assert_not_called()

            # Verify OpenCode API was called instead
            assert result is not None
            self.logger.info.assert_any_call("OpenCode HTTP API execution completed.")
