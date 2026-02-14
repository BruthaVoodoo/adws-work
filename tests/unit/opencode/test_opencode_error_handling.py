"""
Unit tests for OpenCode error handling functionality (Story 1.6).

Tests enhanced error handling and logging in OpenCodeHTTPClient
for various error scenarios (authentication, timeout, JSON decode, etc).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
import pytest
import requests.exceptions

from scripts.adw_modules.opencode_http_client import (
    OpenCodeHTTPClient,
    OpenCodeHTTPClientError,
    OpenCodeAuthenticationError,
)


class TestOpenCodeHTTPClientErrorHandling:
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

        # Session creation returns 401
        mock_auth_response = Mock()
        mock_auth_response.status_code = 401
        mock_session.post.return_value = mock_auth_response

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch(
                "scripts.adw_modules.opencode_http_client.config"
            ) as mock_config:
                mock_config.logs_dir = Path(temp_dir)

                # Call should raise OpenCodeHTTPClientError (session creation fails)
                with pytest.raises(
                    OpenCodeHTTPClientError, match="Failed to create session"
                ):
                    self.client.send_prompt(
                        prompt="Test prompt",
                        model_id="test-model",
                        adw_id="auth_error123",
                        agent_name="auth_agent",
                    )

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    @patch("scripts.adw_modules.opencode_http_client.time.sleep")  # Speed up test
    def test_send_prompt_timeout_retry_logging(self, mock_sleep, mock_session_class):
        """Test timeout error retry logging."""
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Session creation succeeds
        mock_session_response = Mock()
        mock_session_response.status_code = 200
        mock_session_response.json.return_value = {"id": "session-123"}

        # First message times out, second succeeds
        timeout_error = requests.exceptions.Timeout("Request timed out")
        mock_success_response = Mock()
        mock_success_response.status_code = 200
        mock_success_response.json.return_value = {
            "info": {"role": "assistant"},
            "parts": [],
        }

        mock_session.post.side_effect = [
            mock_session_response,
            timeout_error,
            mock_success_response,
        ]

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
                assert response["message"] == {"role": "assistant"}
                assert response["parts"] == []

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

        # Session creation succeeds
        mock_session_response = Mock()
        mock_session_response.status_code = 200
        mock_session_response.json.return_value = {"id": "session-123"}

        # Message returns invalid JSON
        mock_message_response = Mock()
        mock_message_response.status_code = 200
        mock_message_response.text = "Invalid JSON response"
        mock_message_response.json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "doc", 0
        )

        mock_session.post.side_effect = [mock_session_response, mock_message_response]

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
