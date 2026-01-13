#!/usr/bin/env python3
"""
Unit tests for Story 3.8: Test git fallback validation with OpenCode responses

Tests verify that git fallback validation works correctly with OpenCode responses,
ensuring reliable change validation when OpenCode analysis is inconclusive but
git shows actual changes were made.
"""

import os
import tempfile
import unittest.mock as mock
from unittest.mock import MagicMock, patch
import pytest
import logging

from scripts.adw_modules.workflow_ops import (
    implement_plan,
)
from scripts.adw_modules.data_types import AgentPromptResponse
from scripts.adw_modules.copilot_output_parser import ParsedCopilotOutput


class TestStory38GitFallbackValidation:
    """Test suite for Story 3.8: git fallback validation with OpenCode responses."""

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

    def test_git_fallback_validates_changes_when_opencode_fails(self):
        """Test git fallback validation when OpenCode analysis fails but git shows changes."""
        # Mock OpenCode response - response.success must be True to reach parsing logic
        # Parser will detect failure from text output
        mock_response = AgentPromptResponse(
            output="Error during implementation - unclear what happened",
            success=True,  # API call succeeded (parsing determines actual success)
            files_changed=None,
            lines_added=None,
            lines_removed=None,
        )

        # Mock parser to return failed analysis (simulates text-based failure detection)
        mock_parsed = ParsedCopilotOutput(
            success=False,  # Parser detected failure from text
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            validation_status="failed",
            raw_output="Error during implementation - unclear what happened",
        )

        # Mock git verification showing actual changes were made
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 3
        mock_git_changeset.total_additions = 45
        mock_git_changeset.total_deletions = 0

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 2
        mock_plan_validation.total_steps = 4
        mock_plan_validation.missing_steps = [
            "Write unit tests",
            "Run validation commands",
        ]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ) as mock_execute,
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
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

            # Verify OpenCode HTTP API called with correct parameters
            mock_execute.assert_called_once()
            call_kwargs = mock_execute.call_args.kwargs
            assert call_kwargs["task_type"] == "implement"
            assert call_kwargs["adw_id"] == self.adw_id

            # Git fallback should override OpenCode failure
            assert result.success is True, (
                "Git fallback should mark implementation as successful when git shows changes"
            )
            assert result.validation_status == "passed", (
                "Git fallback should set validation_status to 'passed'"
            )

            # Verify info message about git fallback was logged
            info_calls = [str(call) for call in self.logger.info.call_args_list]
            assert any(
                "Git verification confirms" in str(call) for call in info_calls
            ), "Should log git fallback confirmation message"

    def test_git_fallback_uses_git_metrics_when_opencode_fails(self):
        """Test git fallback uses git metrics when OpenCode analysis fails."""
        # Mock OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation unclear - no clear success indicators",
            success=True,  # API call succeeded
            files_changed=None,  # No metrics from OpenCode response
            lines_added=None,
            lines_removed=None,
        )

        # Mock parser to return unknown/failure status
        mock_parsed = ParsedCopilotOutput(
            success=False,  # Parser couldn't determine success from text
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            validation_status="unknown",
            raw_output="Implementation unclear - no clear success indicators",
        )

        # Mock git verification with specific metrics
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 5
        mock_git_changeset.total_additions = 120
        mock_git_changeset.total_deletions = 30

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 3
        mock_plan_validation.total_steps = 5
        mock_plan_validation.missing_steps = ["Run validation commands"]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
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

            # Git fallback should override and mark as successful
            assert result.success is True, (
                "Git fallback should mark as successful when git shows changes"
            )
            assert result.validation_status == "passed", (
                "Git fallback should set validation_status to 'passed'"
            )

    def test_git_fallback_does_not_override_successful_opencode(self):
        """Test git fallback does NOT override when OpenCode analysis is successful."""
        # Mock successful OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation completed successfully. All tests passing.",
            success=True,  # OpenCode API succeeded
            files_changed=2,
            lines_added=15,
            lines_removed=0,
        )

        # Mock parser to return success
        mock_parsed = ParsedCopilotOutput(
            success=True,  # Parser detected success from text
            files_changed=2,
            lines_added=15,
            lines_removed=0,
            validation_status="passed",
            raw_output="Implementation completed successfully. All tests passing.",
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
            ),
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
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

            # OpenCode success should NOT be overridden
            assert result.success is True, "OpenCode success should remain True"
            assert result.validation_status == "passed", (
                "Validation status should remain 'passed'"
            )

            # Should use OpenCode metrics
            assert result.files_changed == 2, "Should use OpenCode files_changed metric"
            assert result.lines_added == 15, "Should use OpenCode lines_added metric"
            assert result.lines_removed == 0, "Should use OpenCode lines_removed metric"

    def test_git_fallback_does_not_trigger_with_no_changes(self):
        """Test git fallback does NOT trigger when no git changes exist."""
        # Mock OpenCode response
        mock_response = AgentPromptResponse(
            output="No implementation occurred",
            success=True,
            files_changed=None,
            lines_added=None,
            lines_removed=None,
        )

        # Mock parser to return failure
        mock_parsed = ParsedCopilotOutput(
            success=False,  # Parser detected failure
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            validation_status="failed",
            raw_output="No implementation occurred",
        )

        # Mock git verification showing NO changes
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 0  # No changes
        mock_git_changeset.total_additions = 0
        mock_git_changeset.total_deletions = 0

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 0
        mock_plan_validation.total_steps = 4
        mock_plan_validation.missing_steps = [
            "Create new file",
            "Add function",
            "Write unit tests",
            "Run validation commands",
        ]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
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

            # Git fallback should NOT trigger - implementation should remain failed
            assert result.success is False, (
                "Git fallback should NOT trigger when no git changes exist"
            )
            assert result.validation_status != "passed", (
                "Validation status should not be 'passed' when no changes"
            )

    def test_git_fallback_with_multiple_files_changed(self):
        """Test git fallback correctly handles multiple files changed."""
        # Mock OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation unclear but files created",
            success=True,
            files_changed=None,
        )

        # Mock parser to return unknown status
        mock_parsed = ParsedCopilotOutput(
            success=False,  # Parser couldn't determine success
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            validation_status="unknown",
            raw_output="Implementation unclear but files created",
        )

        # Mock git verification showing multiple files changed
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 10
        mock_git_changeset.total_additions = 250
        mock_git_changeset.total_deletions = 50

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 8
        mock_plan_validation.total_steps = 12
        mock_plan_validation.missing_steps = ["Update documentation", "Add comments"]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
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

            # Git fallback should trigger and mark as successful
            assert result.success is True, (
                "Git fallback should mark as successful when git shows changes"
            )
            assert result.validation_status == "passed", (
                "Git fallback should set validation_status to 'passed'"
            )

            # Verify git verification was logged
            info_calls = [str(call) for call in self.logger.info.call_args_list]
            assert any("Git verification:" in str(call) for call in info_calls), (
                "Should log git verification details"
            )

    def test_git_fallback_logs_verification_details(self):
        """Test git fallback logs verification details correctly."""
        # Mock OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation unclear",
            success=True,
        )

        # Mock parser to return unknown status
        mock_parsed = ParsedCopilotOutput(
            success=False,
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            validation_status="unknown",
            raw_output="Implementation unclear",
        )

        # Mock git verification with specific details
        mock_git_changeset = MagicMock()
        mock_git_changeset.total_files_changed = 7
        mock_git_changeset.total_additions = 100
        mock_git_changeset.total_deletions = 20

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 4
        mock_plan_validation.total_steps = 6
        mock_plan_validation.missing_steps = ["Update tests"]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
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

            # Verify git verification details were logged
            info_calls = [str(call) for call in self.logger.info.call_args_list]
            git_verification_logged = any(
                "Git verification:" in str(call)
                and "7 files changed" in str(call)
                and "100 additions" in str(call)
                and "20 deletions" in str(call)
                for call in info_calls
            )
            assert git_verification_logged, (
                "Should log detailed git verification metrics"
            )

    def test_git_fallback_handles_git_error_gracefully(self):
        """Test git fallback handles git errors gracefully."""
        # Mock OpenCode response
        mock_response = AgentPromptResponse(
            output="Implementation unclear",
            success=True,
            files_changed=None,
        )

        # Mock parser to return unknown status
        mock_parsed = ParsedCopilotOutput(
            success=False,
            files_changed=0,
            lines_added=0,
            lines_removed=0,
            validation_status="unknown",
            raw_output="Implementation unclear",
        )

        mock_plan_validation = MagicMock()
        mock_plan_validation.executed_steps = 2
        mock_plan_validation.total_steps = 4
        mock_plan_validation.missing_steps = ["Write tests", "Run validation"]

        with (
            patch(
                "scripts.adw_modules.agent.execute_opencode_prompt",
                return_value=mock_response,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.parse_opencode_implementation_output",
                return_value=mock_parsed,
            ),
            patch(
                "scripts.adw_modules.workflow_ops.get_file_changes",
                side_effect=Exception("Git command failed"),  # Git error
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

            # Should NOT trigger git fallback when git errors occur
            assert result.success is False, (
                "Should remain failed when git verification fails"
            )

            # Warning should be logged
            warning_calls = [str(call) for call in self.logger.warning.call_args_list]
            assert any(
                "Could not verify git changes" in str(call) for call in warning_calls
            ), "Should log warning about git verification failure"
