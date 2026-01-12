"""Unit tests for create_pull_request() migration to OpenCode HTTP API - Story 2.7."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from scripts.adw_modules.workflow_ops import create_pull_request, AGENT_PR_CREATOR
from scripts.adw_modules.data_types import AgentPromptResponse, GitHubIssue
from scripts.adw_modules.state import ADWState


class TestCreatePullRequestMigration:
    """Test create_pull_request() migration to OpenCode HTTP API with Claude Haiku 4.5 - Story 2.7."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.mock_state = Mock(spec=ADWState)
        self.mock_state.get.side_effect = lambda key, default=None: {
            "plan_file": "/path/to/plan.md",
            "adw_id": "test-adw-123",
            "issue_number": "42",
        }.get(key, default)

        self.branch_name = "feature-issue-42-adw-test-123"
        # Create a properly formed GitHubIssue with all required fields using aliases
        from scripts.adw_modules.data_types import GitHubUser
        from datetime import datetime

        self.issue = GitHubIssue(
            number=42,
            title="Test Issue",
            body="Test issue body",
            state="open",
            author=GitHubUser(login="testuser"),
            assignees=[],
            labels=[],
            milestone=None,
            comments=[],
            createdAt=datetime.now(),
            updatedAt=datetime.now(),
            closedAt=None,
            url="https://github.com/test/repo/issues/42",
        )

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.parse_json")
    @patch("scripts.adw_modules.workflow_ops.check_pr_exists")
    @patch("scripts.adw_modules.workflow_ops.bb_create_pr")
    def test_successful_pr_creation_via_opencode(
        self,
        mock_bb_create_pr,
        mock_check_pr_exists,
        mock_parse_json,
        mock_load_prompt,
        mock_execute_opencode_prompt,
    ):
        """Test successful PR creation using OpenCode HTTP API with task_type='pr_creation'."""
        # Mock dependencies
        mock_load_prompt.return_value = (
            "Template: {branch_name}, {issue_number}, {plan_file}, {adw_id}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output='{"title": "Test PR Title", "description": "Test PR Description"}',
            success=True,
        )
        mock_parse_json.return_value = {
            "title": "Test PR Title",
            "description": "Test PR Description",
        }
        mock_check_pr_exists.return_value = False
        mock_bb_create_pr.return_value = ("https://bitbucket.org/test/pr/1", None)

        # Execute function
        result_url, error = create_pull_request(
            self.branch_name, self.issue, self.mock_state, self.mock_logger
        )

        # Verify OpenCode HTTP API integration
        mock_execute_opencode_prompt.assert_called_once_with(
            prompt="Template: feature-issue-42-adw-test-123, 42, /path/to/plan.md, test-adw-123",
            task_type="pr_creation",  # Should route to Claude Haiku 4.5
            adw_id="test-adw-123",
            agent_name=AGENT_PR_CREATOR,
        )

        # Verify successful result
        assert result_url == "https://bitbucket.org/test/pr/1"
        assert error is None

        # Verify Bitbucket integration calls
        mock_check_pr_exists.assert_called_once_with(self.branch_name)
        mock_bb_create_pr.assert_called_once_with(
            self.branch_name, "Test PR Title", "Test PR Description"
        )

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.parse_json")
    @patch("scripts.adw_modules.workflow_ops.check_pr_exists")
    @patch("scripts.adw_modules.workflow_ops.update_pull_request")
    def test_successful_pr_update_via_opencode(
        self,
        mock_update_pull_request,
        mock_check_pr_exists,
        mock_parse_json,
        mock_load_prompt,
        mock_execute_opencode_prompt,
    ):
        """Test successful PR update when PR already exists."""
        # Mock dependencies for existing PR scenario
        mock_load_prompt.return_value = (
            "Template: {branch_name}, {issue_number}, {plan_file}, {adw_id}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output='{"title": "Updated PR Title", "description": "Updated PR Description"}',
            success=True,
        )
        mock_parse_json.return_value = {
            "title": "Updated PR Title",
            "description": "Updated PR Description",
        }
        mock_check_pr_exists.return_value = True  # PR exists
        mock_update_pull_request.return_value = (
            "https://bitbucket.org/test/pr/1",
            None,
        )

        # Execute function
        result_url, error = create_pull_request(
            self.branch_name, self.issue, self.mock_state, self.mock_logger
        )

        # Verify OpenCode integration
        mock_execute_opencode_prompt.assert_called_once_with(
            prompt="Template: feature-issue-42-adw-test-123, 42, /path/to/plan.md, test-adw-123",
            task_type="pr_creation",  # Should route to Claude Haiku 4.5
            adw_id="test-adw-123",
            agent_name=AGENT_PR_CREATOR,
        )

        # Verify successful result
        assert result_url == "https://bitbucket.org/test/pr/1"
        assert error is None

        # Verify update instead of create
        mock_check_pr_exists.assert_called_once_with(self.branch_name)
        mock_update_pull_request.assert_called_once_with(
            self.branch_name, "Updated PR Title", "Updated PR Description"
        )

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_opencode_api_failure_handling(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test error handling when OpenCode API fails."""
        # Mock OpenCode failure
        mock_load_prompt.return_value = (
            "Template: {branch_name}, {issue_number}, {plan_file}, {adw_id}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="OpenCode API Error: Connection failed",
            success=False,
        )

        # Execute function
        result_url, error = create_pull_request(
            self.branch_name, self.issue, self.mock_state, self.mock_logger
        )

        # Verify error handling
        assert result_url is None
        assert error == "OpenCode API Error: Connection failed"

        # Verify OpenCode was called with correct parameters
        mock_execute_opencode_prompt.assert_called_once_with(
            prompt="Template: feature-issue-42-adw-test-123, 42, /path/to/plan.md, test-adw-123",
            task_type="pr_creation",
            adw_id="test-adw-123",
            agent_name=AGENT_PR_CREATOR,
        )

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.parse_json")
    def test_invalid_json_response_handling(
        self, mock_parse_json, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test error handling when OpenCode returns invalid JSON."""
        # Mock invalid JSON response
        mock_load_prompt.return_value = (
            "Template: {branch_name}, {issue_number}, {plan_file}, {adw_id}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="Invalid JSON response",
            success=True,
        )
        mock_parse_json.side_effect = ValueError("Invalid JSON")

        # Execute function
        result_url, error = create_pull_request(
            self.branch_name, self.issue, self.mock_state, self.mock_logger
        )

        # Verify error handling
        assert result_url is None
        assert error is not None
        assert "Failed to parse PR data from AI response: Invalid JSON" in error
        assert "Response preview: Invalid JSON response" in error

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    @patch("scripts.adw_modules.workflow_ops.parse_json")
    def test_missing_required_fields_handling(
        self, mock_parse_json, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test error handling when OpenCode response is missing required fields."""
        # Mock response missing title
        mock_load_prompt.return_value = (
            "Template: {branch_name}, {issue_number}, {plan_file}, {adw_id}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output='{"description": "Only description provided"}',
            success=True,
        )
        mock_parse_json.return_value = {"description": "Only description provided"}

        # Execute function
        result_url, error = create_pull_request(
            self.branch_name, self.issue, self.mock_state, self.mock_logger
        )

        # Verify error handling
        assert result_url is None
        assert error is not None
        assert "AI response missing 'title' or 'description' fields" in error

    def test_task_type_routing_verification(self):
        """Test that task_type='pr_creation' correctly routes to Claude Haiku 4.5."""
        with patch(
            "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
        ) as mock_execute:
            with patch("scripts.adw_modules.workflow_ops.load_prompt"):
                # Mock API failure to avoid full execution, we just want to verify the call
                mock_execute.return_value = AgentPromptResponse(
                    output="Connection failed", success=False
                )

                # Execute function
                create_pull_request(
                    self.branch_name, self.issue, self.mock_state, self.mock_logger
                )

                # Verify task_type parameter for model routing
                mock_execute.assert_called_once()
                args, kwargs = mock_execute.call_args

                # Verify task_type is set correctly for lightweight model routing
                assert "task_type" in kwargs
                assert kwargs["task_type"] == "pr_creation"

    def test_backward_compatibility_preserved(self):
        """Test that return format and behavior match pre-migration expectations."""
        with patch(
            "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
        ) as mock_execute:
            with patch("scripts.adw_modules.workflow_ops.load_prompt"):
                with patch("scripts.adw_modules.workflow_ops.parse_json") as mock_parse:
                    with patch(
                        "scripts.adw_modules.workflow_ops.check_pr_exists"
                    ) as mock_check:
                        with patch(
                            "scripts.adw_modules.workflow_ops.bb_create_pr"
                        ) as mock_create:
                            # Mock successful scenario
                            mock_execute.return_value = AgentPromptResponse(
                                output='{"title": "Test", "description": "Test"}',
                                success=True,
                            )
                            mock_parse.return_value = {
                                "title": "Test",
                                "description": "Test",
                            }
                            mock_check.return_value = False  # No existing PR
                            mock_create.return_value = ("https://pr.url", None)

                            # Execute and verify return format
                            result_url, error = create_pull_request(
                                self.branch_name,
                                self.issue,
                                self.mock_state,
                                self.mock_logger,
                            )

                            # Return format should be (pr_url, error_message) tuple
                            assert isinstance(result_url, str)
                            assert error is None

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    @patch("scripts.adw_modules.workflow_ops.load_prompt")
    def test_migration_no_longer_uses_execute_template(
        self, mock_load_prompt, mock_execute_opencode_prompt
    ):
        """Test that migration no longer calls execute_template() - uses OpenCode instead."""
        # Mock to avoid full execution
        mock_load_prompt.return_value = (
            "Template: {branch_name}, {issue_number}, {plan_file}, {adw_id}"
        )
        mock_execute_opencode_prompt.return_value = AgentPromptResponse(
            output="API Error", success=False
        )

        with patch(
            "scripts.adw_modules.workflow_ops.execute_template"
        ) as mock_execute_template:
            # Execute function
            create_pull_request(
                self.branch_name, self.issue, self.mock_state, self.mock_logger
            )

            # Verify execute_template() is NOT called (migration complete)
            mock_execute_template.assert_not_called()

            # Verify execute_opencode_prompt() IS called (new integration)
            mock_execute_opencode_prompt.assert_called_once()

    def test_prompt_formatting_preservation(self):
        """Test that prompt template formatting logic is preserved during migration."""
        with patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt:
            with patch(
                "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
            ) as mock_execute:
                # Mock template with placeholders
                mock_load_prompt.return_value = "Branch: {branch_name}, Issue: {issue_number}, Plan: {plan_file}, ADW: {adw_id}"
                mock_execute.return_value = AgentPromptResponse(
                    output="Error", success=False
                )

                # Execute function
                create_pull_request(
                    self.branch_name, self.issue, self.mock_state, self.mock_logger
                )

                # Verify prompt was formatted correctly
                mock_execute.assert_called_once()
                args, kwargs = mock_execute.call_args

                # Check formatted prompt content
                formatted_prompt = kwargs["prompt"]
                assert "Branch: feature-issue-42-adw-test-123" in formatted_prompt
                assert "Issue: 42" in formatted_prompt
                assert "Plan: /path/to/plan.md" in formatted_prompt
                assert "ADW: test-adw-123" in formatted_prompt
