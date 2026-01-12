#!/usr/bin/env python3
"""
Unit tests for Story 3.1: Refactor implement_plan() to use OpenCode HTTP API

Tests the migration from Copilot CLI to OpenCode HTTP API with Claude Sonnet 4,
verifying that implementation results are correctly extracted from OpenCode Parts
and maintain backward compatibility with AgentPromptResponse.
"""

import os
import tempfile
import unittest.mock as mock
from unittest.mock import MagicMock, patch, mock_open
import pytest
import logging

from scripts.adw_modules.workflow_ops import (
    implement_plan,
    parse_opencode_implementation_output,
)
from scripts.adw_modules.data_types import AgentPromptResponse
from scripts.adw_modules.copilot_output_parser import ParsedCopilotOutput


class TestStory31ImplementPlanMigration:
    """Test suite for Story 3.1: implement_plan() migration to OpenCode HTTP API."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.plan_file = os.path.join(self.temp_dir, "test_plan.md")
        self.plan_content = """
# Implementation Plan

## Step by Step Tasks

1. Create new file `src/example.py`
2. Add function `def hello_world()`
3. Write unit tests
4. Run validation commands
        """.strip()

        # Create plan file
        with open(self.plan_file, "w") as f:
            f.write(self.plan_content)

        self.adw_id = "test_adw_123"
        self.target_dir = self.temp_dir
        self.logger = MagicMock(spec=logging.Logger)

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_implement_plan_opencode_integration_success(self):
        """Test successful implementation via OpenCode HTTP API."""
        # Mock successful OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation completed successfully. Created src/example.py with hello_world function. All tests passing.",
            success=True,
            files_changed=2,
            lines_added=15,
            lines_removed=0,
        )

        # Mock git verification
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 2
        mock_git_changeset.total_additions = 15
        mock_git_changeset.total_deletions = 0

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 4
        mock_plan_validation.total_steps = 4
        mock_plan_validation.missing_steps = []

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch(
                "scripts.adw_modules.workflow_ops.get_file_changes",
                return_value=mock_git_changeset,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.cross_reference_plan_output",
                return_value=mock_plan_validation,
            ),
        ):
            result = implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

            # Verify OpenCode HTTP API called with correct parameters
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "implement"
            assert call_args[1]["adw_id"] == self.adw_id
            assert call_args[1]["agent_name"] == "sdlc_implementor"
            assert (
                "I am an AI assistant. I will help you implement a software development plan."
                in call_args[1]["prompt"]
            )
            assert self.plan_content in call_args[1]["prompt"]

            # Verify successful response
            assert isinstance(result, AgentPromptResponse)
            assert result.success is True
            assert result.files_changed == 2
            assert result.lines_added == 15
            assert result.lines_removed == 0
            assert result.validation_status == "passed"

            # Verify logging
            self.logger.debug.assert_any_call(
                "Executing implement_plan() via OpenCode with task_type='implement'"
            )
            self.logger.info.assert_any_call("OpenCode HTTP API execution completed.")

    def test_implement_plan_opencode_api_failure(self):
        """Test handling of OpenCode HTTP API execution failure."""
        # Mock failed OpenCode response
        mock_response = AgentPromptResponse(
            output="Connection error to OpenCode server", success=False
        )

        with patch(
            "scripts.adw_modules.agent.execute_opencode_prompt",
            return_value=mock_response,
        ):
            result = implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

        with patch(
            "scripts.adw_modules.agent.execute_opencode_prompt",
            return_value=mock_response,
        ):
            result = implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

            # Verify failure response
            assert isinstance(result, AgentPromptResponse)
            assert result.success is False
            assert result.validation_status == "failed"
            assert result.errors == ["OpenCode HTTP API execution failed"]

            # Verify error logging
            self.logger.error.assert_any_call("OpenCode HTTP API execution failed")

    def test_implement_plan_file_not_found(self):
        """Test handling when plan file doesn't exist."""
        non_existent_file = "/path/to/nonexistent/plan.md"

        result = implement_plan(
            plan_file=non_existent_file,
            adw_id=self.adw_id,
            logger=self.logger,
            target_dir=self.target_dir,
        )

        # Verify error response
        assert isinstance(result, AgentPromptResponse)
        assert result.success is False
        assert f"Plan file not found: {non_existent_file}" in result.output

    def test_implement_plan_working_directory_change(self):
        """Test that working directory is changed and restored correctly."""
        original_cwd = os.getcwd()
        different_target_dir = tempfile.mkdtemp()

        try:
            # Mock successful OpenCode response
            mock_response = AgentPromptResponse(
                output="Implementation completed", success=True
            )

            with (
                patch(
                    "scripts.adw_modules.agent.execute_opencode_prompt",
                    return_value=mock_response,
                ),
                patch("scripts.adw_modules.workflow_ops.get_file_changes"),
                patch("scripts.adw_modules.workflow_ops.cross_reference_plan_output"),
            ):
                result = implement_plan(
                    plan_file=self.plan_file,
                    adw_id=self.adw_id,
                    logger=self.logger,
                    target_dir=different_target_dir,
                )

                # Verify working directory was restored
                assert os.getcwd() == original_cwd

                # Verify logging of directory change
                self.logger.debug.assert_any_call(
                    f"Changed working directory to: {different_target_dir}"
                )
                self.logger.debug.assert_any_call(
                    f"Restored working directory to: {original_cwd}"
                )

        finally:
            import shutil

            shutil.rmtree(different_target_dir, ignore_errors=True)

    def test_implement_plan_git_verification_failure_with_recovery(self):
        """Test recovery when OpenCode analysis fails but git shows changes."""
        # Mock OpenCode response with unclear success indicators
        # API call succeeds (success=True) but output doesn't have clear success markers
        mock_response = AgentPromptResponse(
            output="Some implementation output without clear success indicators",
            success=True,  # API call succeeded, but analysis unclear
            files_changed=None,  # No metrics from response
            lines_added=None,
            lines_removed=None,
        )

        # Mock git verification showing actual changes
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 3  # But git shows files changed
        mock_git_changeset.total_additions = 25
        mock_git_changeset.total_deletions = 5

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 2
        mock_plan_validation.total_steps = 4
        mock_plan_validation.missing_steps = ["Step 3", "Step 4"]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.get_file_changes",
                return_value=mock_git_changeset,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.cross_reference_plan_output",
                return_value=mock_plan_validation,
            ),
        ):
            result = implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

            # Verify recovery due to git changes
            assert result.success is True  # Recovered to success
            assert result.validation_status == "passed"  # Status updated

            # Verify recovery logging
            self.logger.info.assert_any_call(
                "Outcome: OpenCode analysis inconclusive, but Git verification confirms 3 files changed. Marking implementation as successful."
            )

    def test_implement_plan_exception_handling(self):
        """Test handling of unexpected exceptions during execution."""
        with patch(
            "scripts.adw_modules.agent.execute_opencode_prompt",
            side_effect=Exception("Unexpected error"),
        ):
            result = implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

            # Verify error response
            assert isinstance(result, AgentPromptResponse)
            assert result.success is False
            assert result.validation_status == "error"
            assert "Unexpected error" in result.output

            # Verify error logging
            self.logger.error.assert_any_call(
                "An unexpected error occurred during OpenCode execution: Unexpected error"
            )

    def test_parse_opencode_implementation_output_success_patterns(self):
        """Test OpenCode output parsing for success patterns."""
        success_outputs = [
            "Implementation Complete",
            "All validation commands pass",
            "Successfully implemented the feature",
            "✓ Implementation complete",
            "✅ Task completed",
            "Implementation is complete and working",
            "Task finished successfully",
        ]

        for output in success_outputs:
            parsed = parse_opencode_implementation_output(output)
            assert parsed.success is True, f"Failed to detect success in: {output}"
            assert parsed.validation_status == "passed"

    def test_parse_opencode_implementation_output_error_patterns(self):
        """Test OpenCode output parsing for error patterns."""
        error_outputs = [
            "Error: Failed to create file",
            "Failed to execute command",
            "Exception: Invalid syntax",
            "❌ Implementation failed",
            "✗ Task failed",
        ]

        for output in error_outputs:
            parsed = parse_opencode_implementation_output(output)
            assert len(parsed.errors) > 0, f"Failed to detect errors in: {output}"

    def test_parse_opencode_implementation_output_metrics_extraction(self):
        """Test extraction of file and line metrics from OpenCode output."""
        output_with_metrics = """
        Implementation completed successfully.
        
        Summary:
        - 3 files changed
        - 45 insertions
        - 12 deletions
        
        All tests passing.
        """

        parsed = parse_opencode_implementation_output(output_with_metrics)
        assert parsed.files_changed == 3
        assert parsed.lines_added == 45
        assert parsed.lines_removed == 12
        assert parsed.success is True

    def test_parse_opencode_implementation_output_empty_input(self):
        """Test parsing of empty or None input."""
        # Test empty string
        parsed = parse_opencode_implementation_output("")
        assert parsed.success is False
        assert parsed.validation_status == "unknown"
        assert parsed.files_changed == 0

        # Test with some file changes but no explicit success
        output_with_files = (
            "Working on implementation... 2 files changed, 10 insertions"
        )
        parsed = parse_opencode_implementation_output(output_with_files)
        assert parsed.success is True  # Should be marked successful due to file changes
        assert parsed.files_changed == 2
        assert parsed.lines_added == 10

    def test_implement_plan_migration_verification(self):
        """Test that migration correctly uses OpenCode instead of Copilot CLI."""
        # Mock successful OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation completed via OpenCode", success=True
        )

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_opencode,
            patch("scripts.adw_modules.workflow_ops.get_file_changes"),
            patch("scripts.adw_modules.workflow_ops.cross_reference_plan_output"),
            patch("subprocess.run") as mock_subprocess,
        ):
            result = implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

            # Verify OpenCode was called (migration successful)
            mock_opencode.assert_called_once()

            # Verify Copilot CLI was NOT called (old implementation)
            mock_subprocess.assert_not_called()

            # Verify task type routing
            call_args = mock_opencode.call_args
            assert call_args[1]["task_type"] == "implement"

            assert result.success is True

    def test_implement_plan_prompt_formatting(self):
        """Test that the prompt is correctly formatted for OpenCode."""
        mock_response = AgentPromptResponse(
            output="Implementation completed", success=True
        )

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch("scripts.adw_modules.workflow_ops.get_file_changes"),
            patch("scripts.adw_modules.workflow_ops.cross_reference_plan_output"),
        ):
            implement_plan(
                plan_file=self.plan_file,
                adw_id=self.adw_id,
                logger=self.logger,
                target_dir=self.target_dir,
            )

            # Verify prompt formatting
            call_args = mock_execute.call_args
            prompt = call_args[1]["prompt"]

            # Check key prompt elements
            assert (
                "I am an AI assistant. I will help you implement a software development plan."
                in prompt
            )
            assert (
                "Use the available tools to read files, write files, and execute commands"
                in prompt
            )
            assert self.plan_content in prompt
            assert (
                "Now, please proceed with the implementation using the available tools."
                in prompt
            )

            # Verify OpenCode-specific instructions (not Copilot CLI)
            assert "copilot" not in prompt.lower()
            assert "Commit your changes as you go" not in prompt  # Removed for OpenCode
