"""
Tests for OpenCode integration in agent.py - Story 2.1

This test file validates the OpenCode HTTP integration in agent.py:
- execute_opencode_prompt() function
- convert_opencode_to_agent_response() function
- execute_template() refactor to use OpenCode HTTP client
- Backward compatibility with AgentTemplateRequest and AgentPromptResponse
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from scripts.adw_modules.agent import (
    execute_opencode_prompt,
    convert_opencode_to_agent_response,
    execute_template,
)
from scripts.adw_modules.data_types import (
    AgentPromptResponse,
    AgentTemplateRequest,
)


class TestExecuteOpenCodePrompt:
    """Test execute_opencode_prompt() function."""

    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    def test_execute_opencode_prompt_with_valid_inputs(
        self, mock_client_class, mock_get_model_limit, mock_count_tokens
    ):
        """Test successful execution with valid inputs."""
        # Setup token validation mocks
        mock_count_tokens.return_value = 1000  # Well within limit
        mock_get_model_limit.return_value = 128_000

        # Setup mock client instance
        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-haiku-4.5"

        # Mock successful response
        mock_response = {
            "parts": [{"type": "text", "content": "AI generated response"}],
            "success": True,
            "session_id": "test-session-123",
        }
        mock_client.send_prompt.return_value = mock_response

        # Execute
        result = execute_opencode_prompt(
            prompt="Test prompt",
            task_type="classify",
            adw_id="test123",
            agent_name="test_agent",
        )

        # Verify client creation and method calls
        mock_client_class.from_config.assert_called_once()
        mock_client.send_prompt.assert_called_once_with(
            prompt="Test prompt",
            task_type="classify",
            model_id=None,
            adw_id="test123",
            agent_name="test_agent",
            timeout=None,
        )

        # Verify response format
        assert isinstance(result, AgentPromptResponse)
        assert result.success is True
        assert "AI generated response" in result.output
        assert result.session_id == "test-session-123"

    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    def test_execute_opencode_prompt_with_model_override(
        self, mock_client_class, mock_get_model_limit, mock_count_tokens
    ):
        """Test execution with explicit model override."""
        # Setup token validation mocks
        mock_count_tokens.return_value = 1000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_response = {"parts": [], "success": True}
        mock_client.send_prompt.return_value = mock_response

        execute_opencode_prompt(
            prompt="Test",
            task_type="implement",
            model_id="github-copilot/claude-sonnet-4",
        )

        mock_client.send_prompt.assert_called_once_with(
            prompt="Test",
            task_type="implement",
            model_id="github-copilot/claude-sonnet-4",
            adw_id="unknown",
            agent_name="agent",
            timeout=None,
        )

    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    def test_execute_opencode_prompt_handles_client_error(
        self, mock_client_class, mock_get_model_limit, mock_count_tokens
    ):
        """Test error handling when OpenCode client fails."""
        # Setup token validation mocks
        mock_count_tokens.return_value = 1000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-haiku-4.5"
        mock_client.send_prompt.side_effect = ConnectionError(
            "OpenCode server unavailable"
        )

        result = execute_opencode_prompt(prompt="Test prompt", task_type="classify")

        assert isinstance(result, AgentPromptResponse)
        assert result.success is False
        assert "OpenCode execution error" in result.output
        assert "OpenCode server unavailable" in result.output

    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    def test_execute_opencode_prompt_with_all_parameters(
        self, mock_client_class, mock_get_model_limit, mock_count_tokens
    ):
        """Test execution with all optional parameters provided."""
        # Setup token validation mocks
        mock_count_tokens.return_value = 1000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_response = {"parts": [], "success": True}
        mock_client.send_prompt.return_value = mock_response

        execute_opencode_prompt(
            prompt="Complex prompt",
            task_type="review",
            adw_id="adw789",
            agent_name="review_agent",
            model_id="github-copilot/claude-sonnet-4",
        )

        # Verify all parameters passed correctly
        mock_client.send_prompt.assert_called_once_with(
            prompt="Complex prompt",
            task_type="review",
            model_id="github-copilot/claude-sonnet-4",
            adw_id="adw789",
            agent_name="review_agent",
            timeout=None,
        )


class TestConvertOpenCodeToAgentResponse:
    """Test convert_opencode_to_agent_response() function."""

    def test_convert_response_with_text_parts(self):
        """Test conversion with text parts."""
        mock_client = Mock()

        response_data = {
            "parts": [
                {"type": "text", "content": "First response"},
                {"type": "text", "content": "Second response"},
            ],
            "success": True,
            "session_id": "test-session-456",
        }

        result = convert_opencode_to_agent_response(response_data, mock_client)

        assert isinstance(result, AgentPromptResponse)
        assert result.success is True
        assert "First response" in result.output
        assert "Second response" in result.output
        assert result.session_id == "test-session-456"

    def test_convert_response_with_empty_parts(self):
        """Test conversion when no text parts are available."""
        mock_client = Mock()

        response_data = {
            "parts": [
                {"type": "tool_use", "tool": "edit", "input": {}},
                {"type": "tool_result", "output": "File edited"},
            ],
            "success": True,
        }

        result = convert_opencode_to_agent_response(response_data, mock_client)

        assert isinstance(result, AgentPromptResponse)
        assert result.success is False  # No text content means failure
        assert "No text response from OpenCode" in result.output

    def test_convert_response_with_metrics(self):
        """Test conversion includes estimated metrics."""
        mock_client = Mock()

        response_data = {
            "parts": [
                {"type": "text", "content": "Implementation complete"},
                {
                    "type": "code_block",
                    "language": "python",
                    "content": "def test():\n    pass\n",
                },
            ],
            "success": True,
        }

        result = convert_opencode_to_agent_response(response_data, mock_client)

        # Should have metrics from code analysis
        assert result.files_changed is not None or result.lines_added is not None

    def test_convert_response_handles_parsing_error(self):
        """Test error handling during response parsing."""
        mock_client = Mock()

        # Invalid response data - empty dict instead of None
        response_data = {}

        result = convert_opencode_to_agent_response(response_data, mock_client)

        assert isinstance(result, AgentPromptResponse)
        assert result.success is False
        assert "No text response from OpenCode" in result.output

    def test_convert_response_with_failure_status(self):
        """Test conversion when OpenCode response indicates failure."""
        mock_client = Mock()

        response_data = {
            "parts": [{"type": "text", "content": "Error occurred"}],
            "success": False,
            "session_id": "error-session",
        }

        result = convert_opencode_to_agent_response(response_data, mock_client)

        assert isinstance(result, AgentPromptResponse)
        assert result.success is False
        assert "Error occurred" in result.output
        assert result.session_id == "error-session"


class TestExecuteTemplateRefactor:
    """Test execute_template() refactor for OpenCode integration."""

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.agent.save_prompt")
    def test_execute_template_with_opus_model(
        self, mock_save_prompt, mock_execute_opencode
    ):
        """Test execute_template() with opus model (heavy lifting)."""
        mock_execute_opencode.return_value = AgentPromptResponse(
            output="Implementation complete", success=True
        )

        request = AgentTemplateRequest(
            agent_name="test_agent",
            prompt="Implement feature X",
            adw_id="test456",
            model="opus",
            workflow_agent_name="workflow",
        )

        result = execute_template(request)

        # Verify save_prompt called
        mock_save_prompt.assert_called_once_with(
            "Implement feature X",
            "test456",
            "test_agent",
            task_type="implement",
            workflow_agent_name="workflow",
        )

        # Verify execute_opencode_prompt called with implement task type
        mock_execute_opencode.assert_called_once_with(
            prompt="Implement feature X",
            task_type="implement",  # Heavy lifting task for opus
            adw_id="test456",
            agent_name="test_agent",
        )

        assert isinstance(result, AgentPromptResponse)
        assert result.success is True

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.agent.save_prompt")
    def test_execute_template_with_lightweight_model(
        self, mock_save_prompt, mock_execute_opencode
    ):
        """Test execute_template() with lightweight model."""
        mock_execute_opencode.return_value = AgentPromptResponse(
            output="Classification complete", success=True
        )

        request = AgentTemplateRequest(
            agent_name="classifier",
            prompt="Classify this issue",
            adw_id="test789",
            model="sonnet",  # Non-opus model (lightweight)
        )

        result = execute_template(request)

        # Verify execute_opencode_prompt called with classify task type
        mock_execute_opencode.assert_called_once_with(
            prompt="Classify this issue",
            task_type="classify",  # Lightweight task for non-opus
            adw_id="test789",
            agent_name="classifier",
        )

        assert isinstance(result, AgentPromptResponse)
        assert result.success is True

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.agent.save_prompt")
    def test_execute_template_backward_compatibility(
        self, mock_save_prompt, mock_execute_opencode
    ):
        """Test backward compatibility with existing AgentTemplateRequest format."""
        mock_execute_opencode.return_value = AgentPromptResponse(
            output="Response", success=True, files_changed=3, lines_added=50
        )

        request = AgentTemplateRequest(
            agent_name="test", prompt="Test prompt", adw_id="abc123", model="sonnet"
        )

        result = execute_template(request)

        # Should return AgentPromptResponse with all fields preserved
        assert isinstance(result, AgentPromptResponse)
        assert result.output == "Response"
        assert result.success is True
        assert result.files_changed == 3
        assert result.lines_added == 50

    @patch("scripts.adw_modules.agent.execute_opencode_prompt")
    @patch("scripts.adw_modules.agent.save_prompt")
    def test_execute_template_handles_execution_error(
        self, mock_save_prompt, mock_execute_opencode
    ):
        """Test execute_template() error handling."""
        mock_execute_opencode.return_value = AgentPromptResponse(
            output="OpenCode execution error: Server unavailable", success=False
        )

        request = AgentTemplateRequest(
            agent_name="test", prompt="Test prompt", adw_id="error123", model="opus"
        )

        result = execute_template(request)

        assert isinstance(result, AgentPromptResponse)
        assert result.success is False
        assert "OpenCode execution error" in result.output


class TestOpenCodeIntegrationEnd2End:
    """End-to-end integration tests."""

    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    def test_full_integration_classify_task(
        self, mock_client_class, mock_get_model_limit, mock_count_tokens
    ):
        """Test full integration for classification task."""
        # Setup token validation mocks
        mock_count_tokens.return_value = 500
        mock_get_model_limit.return_value = 128_000

        # Setup mock
        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-haiku-4.5"
        mock_client.send_prompt.return_value = {
            "parts": [{"type": "text", "content": "/feature"}],
            "success": True,
            "session_id": "classify-session",
        }

        # Create request
        request = AgentTemplateRequest(
            agent_name="issue_classifier",
            prompt="Classify: Add new user registration feature",
            adw_id="cls001",
            model="sonnet",  # Lightweight model
        )

        # Execute
        result = execute_template(request)

        # Verify OpenCode client was used correctly
        mock_client_class.from_config.assert_called_once()
        mock_client.send_prompt.assert_called_once_with(
            prompt="Classify: Add new user registration feature",
            task_type="classify",
            model_id=None,
            adw_id="cls001",
            agent_name="issue_classifier",
            timeout=None,
        )

        # Verify response
        assert result.success is True
        assert "/feature" in result.output
        assert result.session_id == "classify-session"

    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    def test_full_integration_implement_task(
        self, mock_client_class, mock_get_model_limit, mock_count_tokens
    ):
        """Test full integration for implementation task."""
        # Setup token validation mocks
        mock_count_tokens.return_value = 2000
        mock_get_model_limit.return_value = 128_000

        # Setup mock
        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-sonnet-4"
        mock_client.send_prompt.return_value = {
            "parts": [
                {"type": "text", "content": "Implementation completed successfully"},
                {"type": "tool_use", "tool": "edit", "input": {"path": "user.py"}},
                {"type": "tool_result", "output": "Created user.py with 25 lines"},
            ],
            "success": True,
            "session_id": "impl-session",
        }

        # Create request
        request = AgentTemplateRequest(
            agent_name="code_implementer",
            prompt="Implement user registration endpoint",
            adw_id="impl001",
            model="opus",  # Heavy lifting model
        )

        # Execute
        result = execute_template(request)

        # Verify task type mapping for opus
        mock_client.send_prompt.assert_called_once_with(
            prompt="Implement user registration endpoint",
            task_type="implement",  # Heavy lifting for opus
            model_id=None,
            adw_id="impl001",
            agent_name="code_implementer",
            timeout=None,
        )

        # Verify response includes metrics
        assert result.success is True
        assert "Implementation completed successfully" in result.output
        assert result.files_changed is not None or result.lines_added is not None
