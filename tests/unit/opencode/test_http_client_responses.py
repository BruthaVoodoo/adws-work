"""Unit tests for OpenCodeHTTPClient - Response handling

Tests for response parsing, error handling, retry logic, and exponential backoff.
Story 1.2: API Communication with error handling and retries
"""

import pytest
import json
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from adw_modules.opencode_http_client import (
    OpenCodeHTTPClient,
    OpenCodeHTTPClientError,
    OpenCodeConnectionError,
    OpenCodeAuthenticationError,
)


class TestOpenCodeHTTPClientResponseErrors:
    """Test suite for send_prompt() error handling"""

    def test_send_prompt_raises_authentication_error_on_401(self):
        """
        AC 3: Given server returns HTTP error (401)
              When I call send_prompt()
              Then error is caught and re-raised with context
        """
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeAuthenticationError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

    def test_send_prompt_raises_authentication_error_on_403(self):
        """send_prompt() should raise OpenCodeAuthenticationError on 403"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeAuthenticationError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

    def test_send_prompt_raises_http_client_error_on_4xx(self):
        """send_prompt() should raise OpenCodeHTTPClientError on other 4xx"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeHTTPClientError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

    def test_send_prompt_does_not_retry_on_401(self):
        """send_prompt() should not retry on authentication errors (401)"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeAuthenticationError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        # Verify no retry (post called only once)
        assert mock_session.post.call_count == 1

    def test_send_prompt_does_not_retry_on_403(self):
        """send_prompt() should not retry on forbidden errors (403)"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeAuthenticationError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        # Verify no retry
        assert mock_session.post.call_count == 1

    def test_send_prompt_does_not_retry_on_404(self):
        """send_prompt() should not retry on client errors (404)"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeHTTPClientError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        # Verify no retry
        assert mock_session.post.call_count == 1

    def test_send_prompt_handles_json_decode_error(self):
        """send_prompt() should handle malformed JSON responses"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_response.text = "Not valid JSON"
        mock_session.post.return_value = mock_response
        client._session = mock_session

        with pytest.raises(OpenCodeHTTPClientError):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )


class TestOpenCodeHTTPClientRetryLogic:
    """Test suite for send_prompt() retry logic and exponential backoff"""

    def test_send_prompt_retries_on_timeout(self):
        """
        AC 2: Given network timeout occurs
              When I call send_prompt()
              Then exponential backoff retry logic activates and retries up to 3 times
        """
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        # First 2 calls timeout, 3rd succeeds
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}

        mock_session.post.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            mock_response,
        ]
        client._session = mock_session

        # Mock time.sleep to avoid actual delays during testing
        with patch("time.sleep"):
            result = client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        assert result is not None
        # Verify retry happened (post called 3 times)
        assert mock_session.post.call_count == 3

    def test_send_prompt_raises_timeout_error_after_max_retries(self):
        """send_prompt() should raise TimeoutError after MAX_RETRIES exhausted"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        # All calls timeout
        mock_session.post.side_effect = requests.exceptions.Timeout()
        client._session = mock_session

        # Mock time.sleep to avoid actual delays during testing
        with patch("time.sleep"):
            with pytest.raises(TimeoutError):
                client.send_prompt(
                    prompt="Hello", model_id="github-copilot/claude-sonnet-4"
                )

        # Verify all retries were attempted
        assert mock_session.post.call_count == client.MAX_RETRIES

    def test_send_prompt_retries_on_connection_error(self):
        """send_prompt() should retry on connection errors with exponential backoff"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}

        mock_session.post.side_effect = [
            requests.exceptions.ConnectionError(),
            requests.exceptions.ConnectionError(),
            mock_response,
        ]
        client._session = mock_session

        # Mock time.sleep to avoid actual delays during testing
        with patch("time.sleep"):
            result = client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        assert result is not None
        # Verify retry happened
        assert mock_session.post.call_count == 3

    def test_send_prompt_raises_connection_error_after_max_retries(self):
        """send_prompt() should raise ConnectionError after MAX_RETRIES exhausted"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_session.post.side_effect = requests.exceptions.ConnectionError(
            "Network unreachable"
        )
        client._session = mock_session

        # Mock time.sleep to avoid actual delays during testing
        with patch("time.sleep"):
            with pytest.raises(OpenCodeConnectionError):
                client.send_prompt(
                    prompt="Hello", model_id="github-copilot/claude-sonnet-4"
                )

        # Verify all retries were attempted
        assert mock_session.post.call_count == client.MAX_RETRIES

    def test_send_prompt_retries_on_server_error_500(self):
        """send_prompt() should retry on 5xx server errors"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}

        error_response = MagicMock()
        error_response.status_code = 500
        error_response.text = "Internal Server Error"

        mock_session.post.side_effect = [error_response, error_response, mock_response]
        client._session = mock_session

        # Mock time.sleep to avoid actual delays during testing
        with patch("time.sleep"):
            result = client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        assert result is not None
        assert mock_session.post.call_count == 3

    def test_send_prompt_raises_server_error_after_max_retries(self):
        """send_prompt() should raise error after MAX_RETRIES for 5xx errors"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        error_response = MagicMock()
        error_response.status_code = 503
        error_response.text = "Service Unavailable"
        mock_session.post.return_value = error_response
        client._session = mock_session

        # Mock time.sleep to avoid actual delays during testing
        with patch("time.sleep"):
            with pytest.raises(OpenCodeHTTPClientError):
                client.send_prompt(
                    prompt="Hello", model_id="github-copilot/claude-sonnet-4"
                )

        assert mock_session.post.call_count == client.MAX_RETRIES

    def test_send_prompt_uses_exponential_backoff_delays(self):
        """send_prompt() should use exponential backoff: 1s, 2s, 4s"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}

        mock_session.post.side_effect = [
            requests.exceptions.Timeout(),
            requests.exceptions.Timeout(),
            mock_response,
        ]
        client._session = mock_session

        sleep_durations = []

        def track_sleep(duration):
            sleep_durations.append(duration)

        with patch("time.sleep", side_effect=track_sleep):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        # Verify exponential backoff delays: 1s, 2s
        assert len(sleep_durations) == 2
        assert sleep_durations[0] == 1.0  # First retry: 1 * 2^0 = 1s
        assert sleep_durations[1] == 2.0  # Second retry: 1 * 2^1 = 2s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
