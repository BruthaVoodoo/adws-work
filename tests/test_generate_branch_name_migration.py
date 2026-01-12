"""
Tests for generate_branch_name() OpenCode migration - Story 2.5

This test file validates the generate_branch_name() function migration to OpenCode HTTP API:
- Ensures generate_branch_name() uses task_type="branch_gen"
- Verifies it routes to Claude Haiku 4.5 (GitHub Copilot)
- Validates branch name parsing and validation logic preservation
- Tests backward compatibility with existing interface
"""

import pytest
import logging
from unittest.mock import Mock, patch, MagicMock

from scripts.adw_modules.workflow_ops import generate_branch_name
from scripts.adw_modules.data_types import (
    AgentPromptResponse,
    GitHubIssue,
    IssueClassSlashCommand,
)


class TestGenerateBranchNameOpenCodeMigration:
    """Test generate_branch_name() migration to OpenCode HTTP API - Story 2.5."""

    def setup_method(self):
        """Setup test fixtures."""
        # Create mock GitHubIssue
        self.mock_issue = Mock(spec=GitHubIssue)
        self.mock_issue.number = 123
        self.mock_issue.title = "Test Issue"
        self.mock_issue.body = "Test Description"
        self.mock_issue.model_dump_json.return_value = '{"number": 123, "title": "Test Issue"}'

        # Create mock logger
        self.mock_logger = Mock(spec=logging.Logger)

        # Test inputs
        self.test_issue_class = "/feature"
        self.test_adw_id = "test-adw-123"

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_generate_branch_name_uses_opencode_with_branch_gen_task_type(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() uses execute_opencode_prompt with task_type='branch_gen'."""
        # Setup mocks
        mock_load_prompt.return_value = "Template with $1 $2 $3"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feature-issue-123-adw-test-adw-123-add-user-auth", success=True
        )

        # Execute
        result, error = generate_branch_name(
            self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
        )

        # Verify execute_opencode_prompt was called with correct parameters
        mock_execute_opencode_prompt.assert_called_once()
        call_args = mock_execute_opencode_prompt.call_args

        # Check task_type parameter
        assert call_args.kwargs.get("task_type") == "branch_gen", (
            "generate_branch_name() should use task_type='branch_gen'"
        )

        # Check other parameters
        assert call_args.kwargs.get("adw_id") == self.test_adw_id
        assert call_args.kwargs.get("agent_name") == "branch_generator"
        assert "prompt" in call_args.kwargs

        # Verify result
        assert error is None
        assert result == "feature-issue-123-adw-test-adw-123-add-user-auth"

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_generate_branch_name_preserves_branch_parsing_logic(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() preserves branch name parsing logic."""
        # Setup mocks with typical OpenCode response format
        mock_load_prompt.return_value = "Template"
        
        # Mock response with markdown formatting (which should be stripped)
        llm_output = """Based on the issue, I recommend this branch name:

**feature-issue-123-adw-test-adw-123-user-auth-system**

This follows the required format and describes the main feature being implemented."""
        
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output=llm_output, success=True
        )

        # Execute
        result, error = generate_branch_name(
            self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
        )

        # Verify markdown formatting is stripped correctly
        assert error is None
        assert result == "feature-issue-123-adw-test-adw-123-user-auth-system"
        assert "*" not in result  # Markdown bold markers should be stripped

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_generate_branch_name_handles_different_issue_types(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() handles different issue classification types."""
        mock_load_prompt.return_value = "Template with $1 $2 $3"
        
        test_cases = [
            ("/feature", "feature"),
            ("/bug", "bug"), 
            ("/chore", "chore"),
        ]
        
        for issue_class_input, expected_type in test_cases:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output=f"{expected_type}-issue-123-adw-test-adw-123-test-branch", 
                success=True
            )
            
            # Execute
            result, error = generate_branch_name(
                self.mock_issue, issue_class_input, self.test_adw_id, self.mock_logger
            )
            
            # Verify slash is removed and branch type is correct
            assert error is None
            assert result.startswith(expected_type + "-issue-")

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_generate_branch_name_prompt_substitution(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() correctly substitutes placeholders in prompt."""
        # Setup mocks
        mock_load_prompt.return_value = "Issue class: $1, ADW ID: $2, Issue data: $3"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feature-issue-123-adw-test-adw-123-test-branch", success=True
        )

        # Execute
        generate_branch_name(
            self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
        )

        # Verify execute_opencode_prompt was called with substituted prompt
        call_args = mock_execute_opencode_prompt.call_args
        prompt = call_args.kwargs.get("prompt")

        assert "Issue class: feature" in prompt  # $1 substituted with "feature" (slash removed)
        assert f"ADW ID: {self.test_adw_id}" in prompt  # $2 substituted
        assert "Issue data: " in prompt  # $3 substituted
        assert self.mock_issue.model_dump_json.return_value in prompt

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_generate_branch_name_maintains_backward_compatibility(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() maintains backward compatibility with existing interface."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="feature-issue-123-adw-test-adw-123-test-branch", success=True
        )

        # Execute with all original parameters including deprecated ones
        result, error = generate_branch_name(
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
    def test_generate_branch_name_handles_opencode_failure(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() handles OpenCode execution failure gracefully."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="OpenCode server error", success=False
        )

        # Execute
        result, error = generate_branch_name(
            self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
        )

        # Verify error handling
        assert result is None
        assert error == "OpenCode server error"

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_generate_branch_name_handles_unparseable_output(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() handles unparseable LLM output gracefully."""
        # Setup mocks
        mock_load_prompt.return_value = "Template"
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="I cannot determine a branch name from this request.", success=True
        )

        # Execute
        result, error = generate_branch_name(
            self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
        )

        # Verify parsing error handling
        assert result is None
        assert "Could not parse branch name from LLM output" in error
        assert "I cannot determine a branch name" in error

    def test_generate_branch_name_migration_successful(self):
        """Test that generate_branch_name() has been successfully migrated to OpenCode.

        This test verifies that execute_template is no longer called and
        execute_opencode_prompt is used instead.
        """
        with patch(
            "scripts.adw_modules.agent.execute_opencode_prompt"
        ) as mock_execute_opencode_prompt:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output="feature-issue-123-adw-test-adw-123-test-branch", success=True
            )

            with patch(
                "scripts.adw_modules.workflow_ops.execute_template"
            ) as mock_execute_template:
                mock_execute_template.return_value = AgentPromptResponse(
                    output="feature-issue-123-adw-test-adw-123-test-branch", success=True
                )

                with patch(
                    "scripts.adw_modules.workflow_ops.load_prompt"
                ) as mock_load_prompt:
                    mock_load_prompt.return_value = "Template"

                    # Execute
                    result, error = generate_branch_name(
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
    def test_generate_branch_name_regex_pattern_validation(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that generate_branch_name() regex pattern correctly validates branch names."""
        mock_load_prompt.return_value = "Template"
        
        # Test valid branch name patterns
        valid_patterns = [
            "feature-issue-123-adw-a1b2c3d4-user-auth",
            "bug-issue-456-adw-e5f6g7h8-fix-login",
            "chore-issue-789-adw-i9j0k1l2-update-deps",
            "**feature-issue-123-adw-test123-add-feature**",  # With markdown bold
        ]
        
        for pattern in valid_patterns:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output=pattern, success=True
            )
            
            result, error = generate_branch_name(
                self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
            )
            
            # Should successfully extract branch name
            assert result is not None
            assert error is None
            assert "*" not in result  # Markdown should be stripped

        # Test invalid patterns that should not match
        invalid_patterns = [
            "invalid-branch-name",
            "feature-123-missing-issue",
            "missing-adw-id-feature-issue-123",
            "completely different format",
        ]
        
        for pattern in invalid_patterns:
            mock_execute_opencode_prompt.return_value = AgentPromptResponse(
                output=pattern, success=True
            )
            
            result, error = generate_branch_name(
                self.mock_issue, self.test_issue_class, self.test_adw_id, self.mock_logger
            )
            
            # Should fail to parse
            assert result is None
            assert "Could not parse branch name from LLM output" in error
