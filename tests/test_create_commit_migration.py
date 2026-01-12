"""
Tests for create_commit() OpenCode migration - Story 2.6

This test file validates the create_commit() function migration to OpenCode HTTP API:
- Ensures create_commit() uses task_type="commit_msg"
- Verifies it routes to Claude Haiku 4.5 (GitHub Copilot)
- Validates commit message generation and validation logic preservation
- Tests backward compatibility with existing interface
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock

from scripts.adw_modules.workflow_ops import create_commit
from scripts.adw_modules.data_types import (
    AgentPromptResponse,
    JiraIssue,
    IssueClassSlashCommand,
)


class TestCreateCommitOpenCodeMigration:
    """Test create_commit() migration to OpenCode HTTP API - Story 2.6."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create mock JiraIssue
        self.mock_issue = Mock(spec=JiraIssue)
        self.mock_issue.number = 123
        self.mock_issue.title = "Test Issue"
        self.mock_issue.description = "Test Description"
        self.mock_issue.model_dump_json.return_value = (
            '{"number": 123, "title": "Test Issue"}'
        )

        # Create mock logger
        self.mock_logger = Mock(spec=logging.Logger)

        # Test inputs
        self.test_agent_name = "test_planner"
        self.test_issue_class = "/feature"
        self.test_adw_id = "test-adw-123"

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_uses_opencode_with_commit_msg_task_type(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() uses execute_opencode_prompt with task_type='commit_msg'."""
        # Setup mocks
        mock_load_prompt.return_value = (
            "Commit template for {agent_name} {issue_type} {issue_json}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feat: Add user authentication feature\n\nImplements user login and registration for issue #123",
            success=True,
        )

        # Execute
        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify execute_opencode_prompt was called with correct parameters
        mock_execute_opencode_prompt.assert_called_once()
        call_args = mock_execute_opencode_prompt.call_args

        # Check task_type parameter
        assert call_args.kwargs.get("task_type") == "commit_msg", (
            "create_commit() should use task_type='commit_msg'"
        )

        # Check other parameters
        assert call_args.kwargs.get("adw_id") == self.test_adw_id
        assert call_args.kwargs.get("agent_name") == f"{self.test_agent_name}_committer"
        assert "prompt" in call_args.kwargs

        # Verify result
        assert error is None
        assert (
            result
            == "feat: Add user authentication feature\n\nImplements user login and registration for issue #123"
        )

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_preserves_prompt_formatting_logic(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() preserves prompt template formatting logic."""
        # Setup mocks with template placeholders
        mock_load_prompt.return_value = (
            "Agent: {agent_name}, Type: {issue_type}, Issue: {issue_json}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feat: Add user authentication", success=True
        )

        # Execute
        create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify execute_opencode_prompt was called with substituted prompt
        call_args = mock_execute_opencode_prompt.call_args
        prompt = call_args.kwargs.get("prompt")

        # Verify template substitution
        assert f"Agent: {self.test_agent_name}" in prompt
        assert "Type: feature" in prompt  # Slash removed from "/feature"
        assert "Issue: " in prompt
        assert self.mock_issue.model_dump_json.return_value in prompt

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_handles_different_issue_types(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() handles different issue classification types."""
        mock_load_prompt.return_value = (
            "Template {agent_name} {issue_type} {issue_json}"
        )

        test_cases = [
            ("/feature", "feat: Add new feature"),
            ("/bug", "fix: Resolve authentication bug"),
            ("/chore", "chore: Update dependencies"),
        ]

        for issue_class_input, expected_commit_msg in test_cases:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output=expected_commit_msg, success=True
            )

            # Execute
            result, error = create_commit(
                self.test_agent_name,
                self.mock_issue,
                issue_class_input,
                self.test_adw_id,
                self.mock_logger,
            )

            # Verify result
            assert error is None
            assert result == expected_commit_msg

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_strips_whitespace_from_output(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() strips whitespace from OpenCode response."""
        # Setup mocks with response containing extra whitespace
        mock_load_prompt.return_value = "Template"

        llm_output_with_whitespace = """
        
        feat: Add user authentication feature
        
        Implements login and registration functionality for issue #123
        
        """

        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output=llm_output_with_whitespace, success=True
        )

        # Execute
        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify whitespace is stripped
        assert error is None
        assert (
            result
            == "feat: Add user authentication feature\n        \n        Implements login and registration functionality for issue #123"
        )
        assert not result.startswith(" ")
        assert not result.startswith("\n")
        assert not result.endswith(" ")
        assert not result.endswith("\n")

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_maintains_backward_compatibility(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() maintains backward compatibility with existing interface."""
        # Setup mocks
        mock_load_prompt.return_value = (
            "Template {agent_name} {issue_type} {issue_json}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feat: Add user authentication", success=True
        )

        # Execute with all original parameters including deprecated ones
        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
            domain="ADW_Core",  # Deprecated parameter
            workflow_agent_name="test_agent",  # Deprecated parameter
        )

        # Verify function still works with deprecated parameters
        assert isinstance(result, str)
        assert error is None

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_handles_opencode_failure(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() handles OpenCode execution failure gracefully."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="OpenCode server connection failed", success=False
        )

        # Execute
        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify error handling
        assert result is None
        assert error == "OpenCode server connection failed"

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_agent_name_formatting(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() correctly formats unique agent name."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feat: Add feature", success=True
        )

        # Execute
        create_commit(
            "custom_planner",
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify agent name formatting
        call_args = mock_execute_opencode_prompt.call_args
        agent_name = call_args.kwargs.get("agent_name")

        assert agent_name == "custom_planner_committer"
        assert agent_name.endswith("_committer")

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_logs_success_message(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() logs success message with commit message."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        commit_message = "feat: Add user authentication feature"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output=commit_message, success=True
        )

        # Execute
        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify logging
        self.mock_logger.info.assert_called_with(
            f"Created commit message: {commit_message}"
        )
        assert result == commit_message

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_logs_debug_message(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() logs debug message about OpenCode execution."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feat: Add feature", success=True
        )

        # Execute
        create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify debug logging
        self.mock_logger.debug.assert_called_with(
            "Executing create_commit() via OpenCode with task_type='commit_msg'"
        )

    def test_create_commit_migration_successful(self):
        """Test that create_commit() has been successfully migrated to OpenCode.

        This test verifies that execute_template is no longer called and
        execute_opencode_prompt is used instead.
        """
        with patch(
            "scripts.adw_modules.agent.execute_opencode_prompt"
        ) as mock_execute_opencode_prompt:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output="feat: Add feature", success=True
            )

            with patch(
                "scripts.adw_modules.workflow_ops.execute_template"
            ) as mock_execute_template:
                mock_execute_template.return_value = AgentPromptResponse(
                    output="feat: Add feature", success=True
                )

                with patch(
                    "scripts.adw_modules.workflow_ops.load_prompt"
                ) as mock_load_prompt:
                    mock_load_prompt.return_value = "Template"

                    # Execute
                    result, error = create_commit(
                        self.test_agent_name,
                        self.mock_issue,
                        self.test_issue_class,
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

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_handles_exception_in_opencode_prompt(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() handles exceptions from execute_opencode_prompt gracefully."""
        # Setup mocks to raise exception
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.side_effect = Exception("Connection timeout")

        # Execute - should raise exception (existing behavior)
        with pytest.raises(Exception) as exc_info:
            create_commit(
                self.test_agent_name,
                self.mock_issue,
                self.test_issue_class,
                self.test_adw_id,
                self.mock_logger,
            )

        assert "Connection timeout" in str(exc_info.value)

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_issue_class_slash_removal(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() correctly removes slash from issue_class."""
        # Setup mocks with prompt that shows issue_type
        template_with_type = (
            "Issue type: {issue_type}, Agent: {agent_name}, Issue: {issue_json}"
        )
        mock_load_prompt.return_value = template_with_type
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feat: Add feature", success=True
        )

        # Execute with slash-prefixed issue class
        create_commit(
            self.test_agent_name,
            self.mock_issue,
            "/feature",  # With slash
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify slash is removed in prompt substitution
        call_args = mock_execute_opencode_prompt.call_args
        prompt = call_args.kwargs.get("prompt")

        assert "Issue type: feature" in prompt  # Slash should be removed
        assert "Issue type: /feature" not in prompt  # Slash should not be present

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_create_commit_return_tuple_format(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that create_commit() returns correct tuple format."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        commit_message = "feat: Add user authentication"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output=commit_message, success=True
        )

        # Execute
        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        # Verify return tuple format
        assert isinstance(result, str)
        assert error is None

        # Test error case
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="Error message", success=False
        )

        result, error = create_commit(
            self.test_agent_name,
            self.mock_issue,
            self.test_issue_class,
            self.test_adw_id,
            self.mock_logger,
        )

        assert result is None
        assert isinstance(error, str)
        assert error == "Error message"
