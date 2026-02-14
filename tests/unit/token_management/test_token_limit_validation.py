"""
Tests for token limit validation in execute_opencode_prompt() - Token Management Feature

Tests the pre-flight token validation that prevents API calls when prompts
exceed model token limits.

Acceptance Criteria:
- execute_opencode_prompt() counts tokens before API call
- Checks against target model's limit
- Raises TokenLimitExceeded if prompt exceeds limit
- Logs to prompt log file with token details
- Exception includes: token_count, model_limit, overage_percentage
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from datetime import datetime

from scripts.adw_modules.agent import execute_opencode_prompt
from scripts.adw_modules.data_types import TokenLimitExceeded, AgentPromptResponse


class TestTokenLimitValidation:
    """Test token limit validation in execute_opencode_prompt()."""

    @patch("scripts.adw_modules.agent.save_prompt")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    def test_token_limit_not_exceeded_allows_execution(
        self,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
        mock_save_prompt,
    ):
        """Test that prompts within token limit execute normally."""
        # Setup: prompt is within limit
        mock_count_tokens.return_value = 50_000  # Well within limit
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-sonnet-4"

        mock_response = {
            "parts": [{"type": "text", "content": "Success"}],
            "success": True,
        }
        mock_client.send_prompt.return_value = mock_response

        # Execute
        result = execute_opencode_prompt(
            prompt="Test prompt within limit",
            task_type="classify",
            adw_id="test123",
            agent_name="test_agent",
        )

        # Verify: No exception raised, API called
        assert result.success is True
        mock_client.send_prompt.assert_called_once()
        mock_save_prompt.assert_called_once()

    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_token_limit_exceeded_raises_exception(
        self,
        mock_makedirs,
        mock_file,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
    ):
        """Test that exceeding token limit raises TokenLimitExceeded."""
        # Setup: prompt exceeds limit
        mock_count_tokens.return_value = 184_000  # Exceeds 128K limit
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-sonnet-4"

        # Execute and verify exception
        with pytest.raises(TokenLimitExceeded) as exc_info:
            execute_opencode_prompt(
                prompt="Very long prompt that exceeds limit" * 10000,
                task_type="implement",
                adw_id="test123",
                agent_name="test_agent",
            )

        # Verify exception details
        exc = exc_info.value
        assert exc.token_count == 184_000
        assert exc.model_limit == 128_000
        assert exc.overage_percentage > 0
        assert exc.model_id == "github-copilot/claude-sonnet-4"
        assert "184,000" in exc.message
        assert "128,000" in exc.message

    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_token_limit_exceeded_logs_to_file(
        self,
        mock_makedirs,
        mock_file,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
    ):
        """Test that token limit errors are logged to prompt file."""
        # Setup
        mock_count_tokens.return_value = 150_000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-haiku-4.5"

        # Execute
        with pytest.raises(TokenLimitExceeded):
            execute_opencode_prompt(
                prompt="Long prompt",
                task_type="plan",
                adw_id="adw999",
                agent_name="planner",
            )

        # Verify log file was created
        mock_makedirs.assert_called()
        mock_file.assert_called()

        # Verify log content includes key details
        written_content = "".join(
            call.args[0] for call in mock_file().write.call_args_list
        )
        assert "TOKEN LIMIT EXCEEDED" in written_content
        assert "150,000" in written_content
        assert "128,000" in written_content
        assert "github-copilot/claude-haiku-4.5" in written_content
        assert "Long prompt" in written_content

    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    def test_token_limit_validation_uses_correct_model(
        self,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
    ):
        """Test that token validation uses the correct model for limit lookup."""
        mock_count_tokens.return_value = 180_000
        mock_get_model_limit.return_value = 200_000  # Opus has 200K limit

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-opus-4"

        mock_response = {
            "parts": [{"type": "text", "content": "Success"}],
            "success": True,
        }
        mock_client.send_prompt.return_value = mock_response

        # Execute with task that uses opus (200K limit)
        result = execute_opencode_prompt(
            prompt="Large prompt",
            task_type="review",  # Review uses heavy model
            adw_id="test123",
        )

        # Should succeed because 180K < 200K
        assert result.success is True
        mock_get_model_limit.assert_called_with("github-copilot/claude-opus-4")

    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_token_limit_with_explicit_model_id(
        self,
        mock_makedirs,
        mock_file,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
    ):
        """Test token validation with explicit model_id override."""
        mock_count_tokens.return_value = 150_000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client

        # Execute with explicit model override
        with pytest.raises(TokenLimitExceeded) as exc_info:
            execute_opencode_prompt(
                prompt="Test prompt",
                task_type="classify",
                model_id="github-copilot/claude-sonnet-4",
                adw_id="test123",
            )

        # Verify correct model was used for validation
        exc = exc_info.value
        assert exc.model_id == "github-copilot/claude-sonnet-4"
        mock_get_model_limit.assert_called_with("github-copilot/claude-sonnet-4")

    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    def test_overage_percentage_calculation(
        self,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
    ):
        """Test that overage percentage is calculated correctly."""
        # Setup: 184K tokens vs 128K limit = 43.75% overage
        mock_count_tokens.return_value = 184_000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-sonnet-4"

        with pytest.raises(TokenLimitExceeded) as exc_info:
            execute_opencode_prompt(
                prompt="Test",
                task_type="implement",
                adw_id="test123",
            )

        exc = exc_info.value
        # (184000 - 128000) / 128000 * 100 = 43.75%
        assert abs(exc.overage_percentage - 43.75) < 0.01

    @patch("scripts.adw_modules.agent.save_prompt")
    @patch("scripts.adw_modules.agent.OpenCodeHTTPClient")
    @patch("scripts.adw_modules.agent.get_model_limit")
    @patch("scripts.adw_modules.agent.count_tokens")
    def test_no_api_call_when_limit_exceeded(
        self,
        mock_count_tokens,
        mock_get_model_limit,
        mock_client_class,
        mock_save_prompt,
    ):
        """Test that API is NOT called when token limit is exceeded."""
        mock_count_tokens.return_value = 200_000
        mock_get_model_limit.return_value = 128_000

        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client
        mock_client.get_model_for_task.return_value = "github-copilot/claude-sonnet-4"

        with pytest.raises(TokenLimitExceeded):
            execute_opencode_prompt(
                prompt="Test",
                task_type="implement",
                adw_id="test123",
            )

        # Verify: API was never called
        mock_client.send_prompt.assert_not_called()
        # Regular prompt save should not happen either (only error log)
        mock_save_prompt.assert_not_called()


class TestTokenLimitExceededException:
    """Test TokenLimitExceeded exception class."""

    def test_exception_attributes(self):
        """Test that exception stores all required attributes."""
        exc = TokenLimitExceeded(
            token_count=150_000,
            model_limit=128_000,
            overage_percentage=17.19,
            model_id="github-copilot/claude-sonnet-4",
        )

        assert exc.token_count == 150_000
        assert exc.model_limit == 128_000
        assert exc.overage_percentage == 17.19
        assert exc.model_id == "github-copilot/claude-sonnet-4"
        assert "150,000" in str(exc)
        assert "128,000" in str(exc)

    def test_exception_custom_message(self):
        """Test exception with custom message."""
        custom_msg = "Custom error message"
        exc = TokenLimitExceeded(
            token_count=100,
            model_limit=50,
            overage_percentage=100.0,
            model_id="test-model",
            message=custom_msg,
        )

        assert str(exc) == custom_msg
        assert exc.message == custom_msg

    def test_exception_default_message_format(self):
        """Test default exception message formatting."""
        exc = TokenLimitExceeded(
            token_count=184_000,
            model_limit=128_000,
            overage_percentage=43.75,
            model_id="github-copilot/claude-sonnet-4",
        )

        message = str(exc)
        assert "184,000" in message
        assert "128,000" in message
        assert "43." in message  # Accept 43.7% or 43.8% (rounding)
        assert "github-copilot/claude-sonnet-4" in message
