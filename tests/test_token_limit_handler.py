"""Tests for token limit exceeded handling in adw_test.py"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from scripts.adw_modules.data_types import TokenLimitExceeded
from scripts.adw_test import handle_token_limit_exceeded
import logging


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def sample_exception():
    """Create a sample TokenLimitExceeded exception."""
    return TokenLimitExceeded(
        token_count=150000,
        model_limit=128000,
        overage_percentage=17.2,
        model_id="claude-sonnet-4-20250514",
    )


class TestHandleTokenLimitExceeded:
    """Test token limit exceeded error handling."""

    def test_abort_option_returns_false(self, sample_exception, mock_logger):
        """Test that choosing abort returns False with no prompt."""
        prompt = "test prompt content " * 1000

        with patch("builtins.input", return_value="2"):
            should_retry, truncated_prompt = handle_token_limit_exceeded(
                sample_exception, prompt, "test_adw_id", mock_logger
            )

        assert should_retry is False
        assert truncated_prompt is None

    def test_truncate_option_returns_truncated_prompt(
        self, sample_exception, mock_logger
    ):
        """Test that choosing truncate returns shortened prompt."""
        prompt = "test prompt content " * 10000  # ~200k chars

        with patch("builtins.input", return_value="1"):
            should_retry, truncated_prompt = handle_token_limit_exceeded(
                sample_exception, prompt, "test_adw_id", mock_logger
            )

        assert should_retry is True
        assert truncated_prompt is not None
        assert len(truncated_prompt) < len(prompt)
        assert "truncated due to token limit" in truncated_prompt

    def test_truncated_prompt_preserves_structure(self, sample_exception, mock_logger):
        """Test that truncation preserves beginning and end of prompt."""
        prompt = "START_CONTENT " + ("x" * 100000) + " END_CONTENT"

        with patch("builtins.input", return_value="1"):
            should_retry, truncated_prompt = handle_token_limit_exceeded(
                sample_exception, prompt, "test_adw_id", mock_logger
            )

        assert "START_CONTENT" in truncated_prompt
        assert "END_CONTENT" in truncated_prompt

    def test_invalid_input_prompts_again(self, sample_exception, mock_logger):
        """Test that invalid input prompts user again."""
        prompt = "test prompt"

        # Simulate invalid input followed by valid abort
        with patch("builtins.input", side_effect=["invalid", "99", "2"]):
            should_retry, truncated_prompt = handle_token_limit_exceeded(
                sample_exception, prompt, "test_adw_id", mock_logger
            )

        assert should_retry is False
        assert truncated_prompt is None

    def test_extreme_truncation_case(self, sample_exception, mock_logger):
        """Test truncation when reduction needed exceeds prompt length."""
        # Short prompt that needs extreme truncation
        prompt = "short prompt"

        with patch("builtins.input", return_value="1"):
            should_retry, truncated_prompt = handle_token_limit_exceeded(
                sample_exception, prompt, "test_adw_id", mock_logger
            )

        assert should_retry is True
        assert truncated_prompt is not None
        # Should keep first 1000 and last 1000 chars (or less for short prompts)
        assert (
            len(truncated_prompt) <= len(prompt) + 200
        )  # Allow for truncation message

    def test_error_message_formatting(self, sample_exception, mock_logger, capsys):
        """Test that error message displays all required information."""
        prompt = "test prompt"

        with patch("builtins.input", return_value="2"):
            handle_token_limit_exceeded(
                sample_exception, prompt, "test_adw_id", mock_logger
            )

        captured = capsys.readouterr()
        output = captured.out

        # Check all required fields are displayed
        assert "TOKEN LIMIT EXCEEDED" in output
        assert "150,000" in output  # token_count formatted
        assert "128,000" in output  # model_limit formatted
        assert "17.2%" in output  # overage_percentage
        assert "claude-sonnet-4" in output  # model_id
        assert "agents/test_adw_id/test_resolver/prompts/" in output  # saved path

        # Check options are displayed
        assert "Aggressive Truncation & Retry" in output
        assert "Abort Workflow" in output

    def test_truncation_targets_80_percent_of_limit(self, mock_logger):
        """Test that truncation aims for 80% of model limit."""
        exc = TokenLimitExceeded(
            token_count=100000,
            model_limit=80000,
            overage_percentage=25.0,
            model_id="test-model",
        )

        # Create prompt that's ~100k tokens (400k chars at 4 chars/token)
        prompt = "x" * 400000

        with patch("builtins.input", return_value="1"):
            should_retry, truncated_prompt = handle_token_limit_exceeded(
                exc, prompt, "test_adw_id", mock_logger
            )

        assert should_retry is True
        assert truncated_prompt is not None

        # Target is 80% of 80k = 64k tokens = ~256k chars
        # Truncated should be significantly smaller than original
        assert len(truncated_prompt) < len(prompt) * 0.7
