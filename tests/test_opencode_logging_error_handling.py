"""
Unit tests for Story 1.6: Response logging and error handling functionality.

Tests the new logging functions (save_response_log, log_error_with_context)
and enhanced error handling in OpenCodeHTTPClient.
"""

import json
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest
import requests.exceptions

# Import the functions and classes to test
from scripts.adw_modules.opencode_http_client import (
    save_response_log,
    log_error_with_context,
    OpenCodeHTTPClient,
    OpenCodeHTTPClientError,
    OpenCodeAuthenticationError,
    OpenCodeConnectionError,
)


class TestSaveResponseLog:
    """Test save_response_log function - Story 1.6 AC: JSON file creation."""

    def test_save_response_log_basic_success(self):
        """Test basic successful response logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock config to point to temp directory
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Test data
                adw_id = "test1234"
                agent_name = "test_agent"
                response = {
                    "message": {"role": "assistant"},
                    "parts": [{"type": "text", "content": "Hello"}],
                }

                # Call function
                log_path = save_response_log(adw_id, agent_name, response)

                # Verify file was created
                assert log_path.exists()
                assert log_path.parent == Path(temp_dir) / adw_id / agent_name
                assert "response_" in log_path.name
                assert log_path.suffix == ".json"

                # Verify file contents
                with open(log_path, "r") as f:
                    log_data = json.load(f)

                assert log_data["adw_id"] == adw_id
                assert log_data["agent_name"] == agent_name
                assert log_data["response"] == response
                assert log_data["error_context"] is None
                assert "timestamp" in log_data
                assert "log_metadata" in log_data

    def test_save_response_log_with_optional_context(self):
        """Test response logging with all optional context fields."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                response = {"test": "data"}
                server_url = "http://test-server.com"
                model_id = "test-model"
                prompt_preview = "Test prompt preview..."

                log_path = save_response_log(
                    adw_id="test5678",
                    agent_name="context_agent",
                    response=response,
                    server_url=server_url,
                    model_id=model_id,
                    prompt_preview=prompt_preview,
                )

                # Verify context was saved
                with open(log_path, "r") as f:
                    log_data = json.load(f)

                assert log_data["server_url"] == server_url
                assert log_data["model_id"] == model_id
                assert log_data["prompt_preview"] == prompt_preview

    def test_save_response_log_error_context(self):
        """Test error response logging with error_context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                error_response = {"error": "Test error"}
                error_context = "Test operation failed with TimeoutError"

                log_path = save_response_log(
                    adw_id="error123",
                    agent_name="error_agent",
                    response=error_response,
                    error_context=error_context,
                )

                # Verify error log naming
                assert "error_response_" in log_path.name

                # Verify error context was saved
                with open(log_path, "r") as f:
                    log_data = json.load(f)

                assert log_data["error_context"] == error_context
                assert log_data["log_metadata"]["log_type"] == "error"

    def test_save_response_log_input_validation(self):
        """Test input validation for save_response_log."""
        response = {"test": "data"}

        # Test empty adw_id
        with pytest.raises(ValueError, match="adw_id must be a non-empty string"):
            save_response_log("", "agent", response)

        # Test None adw_id
        with pytest.raises(ValueError, match="adw_id must be a non-empty string"):
            save_response_log(None, "agent", response)  # type: ignore

        # Test empty agent_name
        with pytest.raises(ValueError, match="agent_name must be a non-empty string"):
            save_response_log("adw123", "", response)

        # Test None agent_name
        with pytest.raises(ValueError, match="agent_name must be a non-empty string"):
            save_response_log("adw123", None, response)  # type: ignore

    def test_save_response_log_directory_creation(self):
        """Test that log directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Directory shouldn't exist initially
                log_dir = Path(temp_dir) / "new_adw" / "new_agent"
                assert not log_dir.exists()

                # Call function
                log_path = save_response_log("new_adw", "new_agent", {"data": "test"})

                # Directory should be created
                assert log_dir.exists()
                assert log_path.parent == log_dir

    def test_save_response_log_config_fallback(self):
        """Test fallback behavior when config module is not available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock config to be None (fallback case)
            with patch("scripts.adw_modules.opencode_http_client.config", None):
                with patch(
                    "scripts.adw_modules.opencode_http_client.Path.cwd",
                    return_value=Path(temp_dir),
                ):
                    log_path = save_response_log(
                        "fallback123", "fallback_agent", {"test": "data"}
                    )

                    # Should use fallback path
                    expected_dir = (
                        Path(temp_dir)
                        / "ai_docs"
                        / "logs"
                        / "fallback123"
                        / "fallback_agent"
                    )
                    assert log_path.parent == expected_dir


class TestLogErrorWithContext:
    """Test log_error_with_context function - Story 1.6 AC: Error logging with context."""

    def test_log_error_with_context_basic(self):
        """Test basic error logging with context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Create test error
                test_error = ValueError("Test error message")

                # Call function
                log_path = log_error_with_context(
                    adw_id="error123",
                    agent_name="error_agent",
                    error=test_error,
                    operation="test_operation",
                )

                # Verify error log was created
                assert log_path.exists()
                assert "error_response_" in log_path.name

                # Verify error log contents
                with open(log_path, "r") as f:
                    log_data = json.load(f)

                assert (
                    log_data["error_context"]
                    == "test_operation failed with ValueError: Test error message"
                )
                assert log_data["response"]["error_type"] == "ValueError"
                assert log_data["response"]["error_message"] == "Test error message"
                assert log_data["response"]["operation"] == "test_operation"

    def test_log_error_with_context_full_details(self):
        """Test error logging with all context details."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                test_error = requests.exceptions.Timeout("Connection timed out")
                additional_context = {
                    "timeout": 30.0,
                    "attempt": 2,
                    "max_retries": 3,
                }

                log_path = log_error_with_context(
                    adw_id="timeout456",
                    agent_name="timeout_agent",
                    error=test_error,
                    operation="send_prompt",
                    server_url="http://test-server.com",
                    model_id="test-model",
                    prompt_preview="Test prompt...",
                    additional_context=additional_context,
                )

                # Verify full context was saved
                with open(log_path, "r") as f:
                    log_data = json.load(f)

                assert log_data["server_url"] == "http://test-server.com"
                assert log_data["model_id"] == "test-model"
                assert log_data["prompt_preview"] == "Test prompt..."
                assert log_data["response"]["additional_context"] == additional_context


class TestOpenCodeHTTPClientLogging:
    """Test enhanced error handling and logging in OpenCodeHTTPClient."""

    def setup_method(self):
        """Setup for each test method."""
        self.client = OpenCodeHTTPClient("http://test-server.com", api_key="test-key")

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_successful_response_logging(self, mock_session_class):
        """Test successful response logging when adw_id and agent_name provided."""
        # Setup mock session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant"},
            "parts": [],
        }
        mock_session.post.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Call send_prompt with logging context
                response = self.client.send_prompt(
                    prompt="Test prompt",
                    model_id="test-model",
                    adw_id="success123",
                    agent_name="success_agent",
                )

                # Verify response was returned
                assert response == {"message": {"role": "assistant"}, "parts": []}

                # Verify log file was created
                log_dir = Path(temp_dir) / "success123" / "success_agent"
                log_files = list(log_dir.glob("response_*.json"))
                assert len(log_files) == 1

                # Verify log contents
                with open(log_files[0], "r") as f:
                    log_data = json.load(f)

                assert log_data["adw_id"] == "success123"
                assert log_data["agent_name"] == "success_agent"
                assert log_data["response"] == {
                    "message": {"role": "assistant"},
                    "parts": [],
                }

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_authentication_error_logging(self, mock_session_class):
        """Test authentication error logging."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 401
        mock_session.post.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Call should raise authentication error
                with pytest.raises(OpenCodeAuthenticationError):
                    self.client.send_prompt(
                        prompt="Test prompt",
                        model_id="test-model",
                        adw_id="auth_error123",
                        agent_name="auth_agent",
                    )

                # Verify error log was created
                log_dir = Path(temp_dir) / "auth_error123" / "auth_agent"
                log_files = list(log_dir.glob("error_response_*.json"))
                assert len(log_files) == 1

                # Verify error log contents
                with open(log_files[0], "r") as f:
                    log_data = json.load(f)

                assert "Authentication failed" in log_data["error_context"]
                assert (
                    log_data["response"]["error_type"] == "OpenCodeAuthenticationError"
                )

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    @patch("scripts.adw_modules.opencode_http_client.time.sleep")  # Speed up test
    def test_send_prompt_timeout_retry_logging(self, mock_sleep, mock_session_class):
        """Test timeout error retry logging."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First call times out, second succeeds
        timeout_error = requests.exceptions.Timeout("Request timed out")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant"},
            "parts": [],
        }

        mock_session.post.side_effect = [timeout_error, mock_response]

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Call should succeed after retry
                response = self.client.send_prompt(
                    prompt="Test prompt",
                    model_id="test-model",
                    adw_id="retry123",
                    agent_name="retry_agent",
                )

                # Verify response was returned
                assert response == {"message": {"role": "assistant"}, "parts": []}

                # Verify both retry error log and success log were created
                log_dir = Path(temp_dir) / "retry123" / "retry_agent"
                error_logs = list(log_dir.glob("error_response_*.json"))
                success_logs = list(log_dir.glob("response_*.json"))

                assert len(error_logs) == 1  # Timeout retry error
                assert len(success_logs) == 1  # Final success

                # Verify retry error log
                with open(error_logs[0], "r") as f:
                    error_log = json.load(f)

                assert "send_prompt_timeout_retry" in error_log["error_context"]
                assert error_log["response"]["additional_context"]["attempt"] == 1

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    @patch("scripts.adw_modules.opencode_http_client.time.sleep")
    def test_send_prompt_max_retries_exceeded_logging(
        self, mock_sleep, mock_session_class
    ):
        """Test final timeout failure logging after max retries."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # All calls time out
        timeout_error = requests.exceptions.Timeout("Request timed out")
        mock_session.post.side_effect = timeout_error

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Call should raise TimeoutError after retries
                with pytest.raises(TimeoutError):
                    self.client.send_prompt(
                        prompt="Test prompt",
                        model_id="test-model",
                        adw_id="final_timeout123",
                        agent_name="timeout_agent",
                    )

                # Verify final failure log was created
                log_dir = Path(temp_dir) / "final_timeout123" / "timeout_agent"
                error_logs = list(log_dir.glob("error_response_*.json"))

                # Should have 1 final failure log (retry attempts are logged to stderr, not files)
                assert len(error_logs) == 1

                # Verify the final failure log content
                with open(error_logs[0], "r") as f:
                    final_log = json.load(f)

                assert "send_prompt_timeout_final" in final_log["error_context"]
                assert final_log["response"]["additional_context"]["total_retries"] == 3

    def test_send_prompt_no_logging_when_context_missing(self):
        """Test that no logging occurs when adw_id/agent_name not provided."""
        with patch(
            "scripts.adw_modules.opencode_http_client.requests.Session"
        ) as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "message": {"role": "assistant"},
                "parts": [],
            }
            mock_session.post.return_value = mock_response

            with tempfile.TemporaryDirectory() as temp_dir:
                with patch(
                    "scripts.adw_modules.opencode_http_client.config"
                ) as mock_config:
                    mock_config.logs_dir = Path(temp_dir)

                    # Call without logging context
                    response = self.client.send_prompt(
                        prompt="Test prompt",
                        model_id="test-model",
                        # No adw_id or agent_name provided
                    )

                    # Verify response was returned
                    assert response == {"message": {"role": "assistant"}, "parts": []}

                    # Verify no log files were created
                    log_files = list(Path(temp_dir).rglob("*.json"))
                    assert len(log_files) == 0

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_json_decode_error_logging(self, mock_session_class):
        """Test JSON decode error logging."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "Invalid JSON response"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
        mock_session.post.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Call should raise OpenCodeHTTPClientError
                with pytest.raises(OpenCodeHTTPClientError, match="Invalid JSON"):
                    self.client.send_prompt(
                        prompt="Test prompt",
                        model_id="test-model",
                        adw_id="json_error123",
                        agent_name="json_agent",
                    )

                # Verify error log was created
                log_dir = Path(temp_dir) / "json_error123" / "json_agent"
                log_files = list(log_dir.glob("error_response_*.json"))
                assert len(log_files) == 1

                # Verify error log contents
                with open(log_files[0], "r") as f:
                    log_data = json.load(f)

                assert "send_prompt_json_decode" in log_data["error_context"]
                assert (
                    "Invalid JSON response"
                    in log_data["response"]["additional_context"]["response_text"]
                )
