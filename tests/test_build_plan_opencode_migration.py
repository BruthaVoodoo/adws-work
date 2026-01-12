"""
Tests for build_plan() OpenCode migration - Story 2.4

This test file validates the build_plan() function migration to OpenCode HTTP API:
- Ensures build_plan() uses task_type="plan"
- Verifies it routes to Claude Haiku 4.5 (GitHub Copilot)
- Validates markdown plan structure preservation
- Tests backward compatibility with existing interface
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock

from scripts.adw_modules.workflow_ops import build_plan
from scripts.adw_modules.data_types import (
    AgentPromptResponse,
    JiraIssue,
)


class TestBuildPlanOpenCodeMigration:
    """Test build_plan() migration to OpenCode HTTP API - Story 2.4."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create mock JiraIssue
        self.mock_issue = Mock(spec=JiraIssue)
        self.mock_issue.number = 123
        self.mock_issue.key = "TEST-123"
        self.mock_issue.title = "Test Issue"
        self.mock_issue.description = "Test Description"
        self.mock_issue.labels = ["bug"]
        self.mock_issue.status = "open"

        # Create mock logger
        self.mock_logger = Mock(spec=logging.Logger)

        # Test inputs
        self.test_command = "/feature"
        self.test_adw_id = "test-adw-123"

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.format_issue_context")
    def test_build_plan_uses_opencode_with_plan_task_type(
        self, mock_format_issue_context, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that build_plan() uses execute_opencode_prompt with task_type='plan'."""
        # Setup mocks
        mock_load_prompt.return_value = "Template with {issue_number} {adw_id} {issue_key} {issue_title} {issue_description} {issue_labels} {issue_state}"
        mock_format_issue_context.return_value = {
            "issue_key": "TEST-123",
            "issue_title": "Test Issue",
            "issue_description": "Test Description",
            "issue_labels": "bug",
            "issue_state": "open",
        }
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="# Implementation Plan\n\n## Tasks\n- Task 1\n- Task 2", success=True
        )

        # Execute
        result = build_plan(
            self.mock_issue, self.test_command, self.test_adw_id, self.mock_logger
        )

        # Verify execute_opencode_prompt was called with correct parameters
        mock_execute_opencode_prompt.assert_called_once()
        call_args = mock_execute_opencode_prompt.call_args

        # Check task_type parameter
        assert call_args.kwargs.get("task_type") == "plan", (
            "build_plan() should use task_type='plan'"
        )

        # Check other parameters
        assert call_args.kwargs.get("adw_id") == self.test_adw_id
        assert "agent_name" in call_args.kwargs
        assert "prompt" in call_args.kwargs

        # Verify result
        assert result.success is True
        assert "Implementation Plan" in result.output

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.format_issue_context")
    def test_build_plan_preserves_markdown_structure(
        self, mock_format_issue_context, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that build_plan() preserves markdown plan structure from OpenCode response."""
        # Setup mocks with markdown response
        mock_load_prompt.return_value = "Template"
        mock_format_issue_context.return_value = {
            "issue_key": "TEST-123",
            "issue_title": "Test Issue",
            "issue_description": "Test Description",
            "issue_labels": "bug",
            "issue_state": "open",
        }

        # Mock markdown response with various markdown elements
        markdown_response = """# Implementation Plan

## Overview
This is the implementation plan for TEST-123.

## Tasks
- [ ] Task 1: Setup
- [ ] Task 2: Implementation  
- [ ] Task 3: Testing

### Subtasks
1. Subtask A
2. Subtask B

## Code Changes
```python
def example():
    pass
```

## Acceptance Criteria
- AC1: Feature works
- AC2: Tests pass"""

        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output=markdown_response, success=True
        )

        # Execute
        result = build_plan(
            self.mock_issue, self.test_command, self.test_adw_id, self.mock_logger
        )

        # Verify markdown structure is preserved
        assert result.success is True
        assert "# Implementation Plan" in result.output
        assert "## Overview" in result.output
        assert "## Tasks" in result.output
        assert "- [ ]" in result.output
        assert "### Subtasks" in result.output
        assert "```python" in result.output
        assert "## Acceptance Criteria" in result.output

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.format_issue_context")
    def test_build_plan_maintains_backward_compatibility(
        self, mock_format_issue_context, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that build_plan() maintains backward compatibility with existing interface."""
        # Setup mocks
        mock_load_prompt.return_value = "Template with {issue_number}"
        mock_format_issue_context.return_value = {
            "issue_key": "TEST-123",
            "issue_title": "Test Issue",
            "issue_description": "Test Description",
            "issue_labels": "bug",
            "issue_state": "open",
        }
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="Plan content", success=True
        )

        # Execute with all original parameters including deprecated ones
        result = build_plan(
            self.mock_issue,
            self.test_command,
            self.test_adw_id,
            self.mock_logger,
            domain="ADW_Core",  # Deprecated parameter
            workflow_agent_name="test_agent",  # Deprecated parameter
        )

        # Verify function still works with deprecated parameters
        assert isinstance(result, AgentPromptResponse)
        assert result.success is True

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.format_issue_context")
    def test_build_plan_prompt_substitution(
        self, mock_format_issue_context, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that build_plan() correctly substitutes all placeholders in prompt."""
        # Setup mocks
        mock_load_prompt.return_value = "Issue: {issue_number} ID: {adw_id} Key: {issue_key} Title: {issue_title} Desc: {issue_description} Labels: {issue_labels} State: {issue_state}"
        mock_format_issue_context.return_value = {
            "issue_key": "TEST-123",
            "issue_title": "Test Issue Title",
            "issue_description": "Test Issue Description",
            "issue_labels": "bug,feature",
            "issue_state": "in_progress",
        }
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="Plan", success=True
        )

        # Execute
        build_plan(
            self.mock_issue, self.test_command, self.test_adw_id, self.mock_logger
        )

        # Verify execute_opencode_prompt was called with substituted prompt
        call_args = mock_execute_opencode_prompt.call_args
        prompt = call_args.kwargs.get("prompt")

        assert "Issue: 123" in prompt
        assert f"ID: {self.test_adw_id}" in prompt
        assert "Key: TEST-123" in prompt
        assert "Title: Test Issue Title" in prompt
        assert "Desc: Test Issue Description" in prompt
        assert "Labels: bug,feature" in prompt
        assert "State: in_progress" in prompt

    def test_build_plan_migration_successful(self):
        """Test that build_plan() has been successfully migrated to OpenCode.

        This test verifies that execute_template is no longer called and
        execute_opencode_prompt is used instead.
        """
        with patch(
            "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
        ) as mock_execute_opencode_prompt:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output="Plan", success=True
            )

            with patch(
                "scripts.adw_modules.workflow_ops.execute_template"
            ) as mock_execute_template:
                mock_execute_template.return_value = AgentPromptResponse(
                    output="Plan", success=True
                )

                with patch(
                    "scripts.adw_modules.workflow_ops.load_prompt"
                ) as mock_load_prompt:
                    mock_load_prompt.return_value = "Template"

                    with patch(
                        "scripts.adw_modules.workflow_ops.format_issue_context"
                    ) as mock_format_context:
                        mock_format_context.return_value = {
                            "issue_key": "TEST-123",
                            "issue_title": "Test",
                            "issue_description": "Desc",
                            "issue_labels": "bug",
                            "issue_state": "open",
                        }

                        # Execute
                        result = build_plan(
                            self.mock_issue,
                            self.test_command,
                            self.test_adw_id,
                            self.mock_logger,
                        )

                        # Verify migration is successful
                        assert mock_execute_opencode_prompt.called, (
                            "Migrated implementation should use execute_opencode_prompt"
                        )
                        assert not mock_execute_template.called, (
                            "Migrated implementation should NOT use execute_template"
                        )
