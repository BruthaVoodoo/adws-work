"""Unit tests for OpenCodeHTTPClient - Core functionality

Tests for session management, connection, requests, timeouts, and context manager support.
Story 1.1: Create OpenCodeHTTPClient class with session management
"""

import pytest
import uuid
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


class TestOpenCodeHTTPClientSessionManagement:
    """Test suite for OpenCodeHTTPClient session management - Story 1.1 AC"""

    def test_instantiate_with_server_url_creates_session_with_unique_id(self):
        """
        AC 1: Given an OpenCode server is running
               When I instantiate OpenCodeHTTPClient with server URL
               Then it successfully creates a new session with a unique session ID
        """
        server_url = "http://localhost:8000"

        client = OpenCodeHTTPClient(server_url=server_url)

        # Verify client is created
        assert client is not None
        # Verify session_id is set and is unique (UUID format)
        assert client.session_id is not None
        assert isinstance(client.session_id, str)
        # Session ID should be a valid UUID
        try:
            uuid.UUID(client.session_id)
        except ValueError:
            pytest.fail(f"Session ID {client.session_id} is not a valid UUID")

    def test_session_ids_are_unique_across_instances(self):
        """Verify that each OpenCodeHTTPClient instance gets a unique session ID"""
        server_url = "http://localhost:8000"

        client1 = OpenCodeHTTPClient(server_url=server_url)
        client2 = OpenCodeHTTPClient(server_url=server_url)

        assert client1.session_id != client2.session_id

    def test_close_session_properly_closes_and_cleans_up(self):
        """
        AC 2: Given an active session exists
               When I call close_session()
               Then the session is properly closed and cleaned up
        """
        server_url = "http://localhost:8000"

        client = OpenCodeHTTPClient(server_url=server_url)
        session_id = client.session_id

        # Verify session exists before closing
        assert client.session_id is not None

        # Close session
        client.close_session()

        # Verify session is cleaned up
        assert client.session_id is None

    def test_invalid_credentials_raises_authentication_error(self):
        """
        AC 3: Given invalid credentials
               When I attempt to create a session
               Then an authentication error is raised with helpful message
        """
        server_url = "http://localhost:8000"
        invalid_api_key = "invalid_key_12345"

        with pytest.raises(Exception) as exc_info:
            client = OpenCodeHTTPClient(server_url=server_url, api_key=invalid_api_key)
            # Attempt to verify connection would happen on init or first call
            client._verify_connection()

        # Check for helpful error message
        assert "authentication" in str(exc_info.value).lower() or "401" in str(
            exc_info.value
        )

    def test_server_url_stored_correctly(self):
        """Verify that server URL is stored and accessible"""
        server_url = "http://opencode.example.com:9000"

        client = OpenCodeHTTPClient(server_url=server_url)

        assert client.server_url == server_url

    def test_multiple_sessions_can_be_managed_independently(self):
        """Verify that multiple client instances manage independent sessions"""
        server_url = "http://localhost:8000"

        client1 = OpenCodeHTTPClient(server_url=server_url)
        client2 = OpenCodeHTTPClient(server_url=server_url)

        session_id_1 = client1.session_id
        session_id_2 = client2.session_id

        # Close first session
        client1.close_session()

        # Verify first is closed but second still active
        assert client1.session_id is None
        assert client2.session_id == session_id_2

        # Close second session
        client2.close_session()
        assert client2.session_id is None

    def test_session_created_with_default_timeout(self):
        """Verify session is created with default timeout value"""
        server_url = "http://localhost:8000"

        client = OpenCodeHTTPClient(server_url=server_url)

        assert client.timeout is not None
        assert isinstance(client.timeout, (int, float))
        assert client.timeout > 0

    def test_session_created_with_custom_timeout(self):
        """Verify session can be created with custom timeout"""
        server_url = "http://localhost:8000"
        custom_timeout = 60

        client = OpenCodeHTTPClient(server_url=server_url, timeout=custom_timeout)

        assert client.timeout == custom_timeout

    def test_api_key_optional_for_public_servers(self):
        """Verify that API key is optional for public/non-auth servers"""
        server_url = "http://localhost:8000"

        # Should not raise without api_key
        client = OpenCodeHTTPClient(server_url=server_url)

        assert client is not None
        assert client.session_id is not None


class TestOpenCodeHTTPClientErrorHandling:
    """Test error handling for OpenCodeHTTPClient"""

    def test_empty_server_url_raises_error(self):
        """Verify that empty server URL raises error"""
        with pytest.raises(ValueError) as exc_info:
            client = OpenCodeHTTPClient(server_url="")

        assert (
            "server_url" in str(exc_info.value).lower()
            or "url" in str(exc_info.value).lower()
        )

    def test_none_server_url_raises_error(self):
        """Verify that None server URL raises error"""
        with pytest.raises(TypeError):
            client = OpenCodeHTTPClient(server_url=None)

    def test_invalid_server_url_format_raises_error(self):
        """Verify that invalid URL format raises error"""
        with pytest.raises(ValueError) as exc_info:
            client = OpenCodeHTTPClient(server_url="not a url")

        assert (
            "url" in str(exc_info.value).lower()
            or "http" in str(exc_info.value).lower()
        )


class TestOpenCodeHTTPClientContextManager:
    """Test context manager support for OpenCodeHTTPClient"""

    def test_can_be_used_as_context_manager(self):
        """Verify that client supports context manager protocol"""
        server_url = "http://localhost:8000"

        with OpenCodeHTTPClient(server_url=server_url) as client:
            assert client.session_id is not None

        # Session should be closed after exiting context
        assert client.session_id is None

    def test_context_manager_closes_on_exception(self):
        """Verify that session is closed even if exception occurs in context"""
        server_url = "http://localhost:8000"

        try:
            with OpenCodeHTTPClient(server_url=server_url) as client:
                session_id = client.session_id
                assert session_id is not None
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Session should still be closed
        assert client.session_id is None


class TestOpenCodeHTTPClientSendPromptCore:
    """Test suite for send_prompt() core functionality - Story 1.2: API Communication"""

    def test_send_prompt_with_valid_inputs_returns_structured_response(self):
        """
        AC 1: Given a valid prompt and model ID
              When I call send_prompt()
              Then a structured OpenCodeResponse is returned with Message + Parts
        """
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_response = {
            "message": {
                "content": "Hello, world!",
                "role": "assistant",
            },
            "parts": [
                {"type": "text", "content": "Hello, world!"},
                {"type": "tool_use", "tool": "grep", "input": {"pattern": "test"}},
            ],
        }

        mock_session = MagicMock()
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_session.post.return_value = mock_http_response
        client._session = mock_session

        result = client.send_prompt(
            prompt="Hello", model_id="github-copilot/claude-sonnet-4"
        )

        assert result is not None
        assert "message" in result
        assert "parts" in result
        assert isinstance(result["parts"], list)

    def test_send_prompt_validates_prompt_parameter(self):
        """send_prompt() should validate that prompt is a non-empty string"""
        client = OpenCodeHTTPClient(server_url="http://localhost:8000")

        # Test with empty string
        with pytest.raises(ValueError):
            client.send_prompt(prompt="", model_id="github-copilot/claude-sonnet-4")

        # Test with None
        with pytest.raises(ValueError):
            client.send_prompt(prompt=None, model_id="github-copilot/claude-sonnet-4")

        # Test with non-string
        with pytest.raises(ValueError):
            client.send_prompt(prompt=123, model_id="github-copilot/claude-sonnet-4")

    def test_send_prompt_validates_model_id_parameter(self):
        """send_prompt() should validate that model_id is a non-empty string"""
        client = OpenCodeHTTPClient(server_url="http://localhost:8000")

        # Test with empty string
        with pytest.raises(ValueError):
            client.send_prompt(prompt="Hello", model_id="")

        # Test with None
        with pytest.raises(ValueError):
            client.send_prompt(prompt="Hello", model_id=None)

        # Test with non-string
        with pytest.raises(ValueError):
            client.send_prompt(prompt="Hello", model_id=123)

    def test_send_prompt_uses_lightweight_timeout_for_haiku_model(self):
        """send_prompt() should use lightweight_timeout for Haiku models"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(
            server_url=server_url,
            timeout=30.0,
            lightweight_timeout=10.0,
        )

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(prompt="Hello", model_id="github-copilot/claude-haiku-4.5")

        # Verify lightweight_timeout was used
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs["timeout"] == 10.0

    def test_send_prompt_uses_heavy_timeout_for_sonnet_model(self):
        """send_prompt() should use default timeout for Sonnet models"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(
            server_url=server_url,
            timeout=30.0,
            lightweight_timeout=10.0,
        )

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(prompt="Hello", model_id="github-copilot/claude-sonnet-4")

        # Verify default timeout was used
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs["timeout"] == 30.0

    def test_send_prompt_with_custom_timeout_override(self):
        """send_prompt() should accept optional timeout parameter"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(
            server_url=server_url,
            timeout=30.0,
            lightweight_timeout=10.0,
        )

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(
            prompt="Hello",
            model_id="github-copilot/claude-sonnet-4",
            timeout=60.0,
        )

        # Verify custom timeout was used
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs["timeout"] == 60.0

    def test_send_prompt_includes_session_id_in_headers(self):
        """send_prompt() should include session_id in request headers"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(prompt="Hello", model_id="github-copilot/claude-sonnet-4")

        # Verify session_id was included in headers
        call_kwargs = mock_session.post.call_args[1]
        headers = call_kwargs["headers"]
        assert "X-Session-ID" in headers
        assert headers["X-Session-ID"] == client.session_id

    def test_send_prompt_includes_api_key_if_provided(self):
        """send_prompt() should include API key in Authorization header"""
        server_url = "http://localhost:8000"
        api_key = "test_key_12345"
        client = OpenCodeHTTPClient(server_url=server_url, api_key=api_key)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(prompt="Hello", model_id="github-copilot/claude-sonnet-4")

        # Verify API key was included in headers
        call_kwargs = mock_session.post.call_args[1]
        headers = call_kwargs["headers"]
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {api_key}"

    def test_send_prompt_request_includes_prompt_and_model(self):
        """send_prompt() should include prompt and model_id in request body"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        prompt_text = "This is my test prompt"
        model_id = "github-copilot/claude-sonnet-4"

        client.send_prompt(prompt=prompt_text, model_id=model_id)

        # Verify request body
        call_kwargs = mock_session.post.call_args[1]
        request_body = call_kwargs["json"]
        assert request_body["prompt"] == prompt_text
        assert request_body["model_id"] == model_id

    def test_send_prompt_posts_to_correct_endpoint(self):
        """send_prompt() should POST to /api/v1/prompt endpoint"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(prompt="Hello", model_id="github-copilot/claude-sonnet-4")

        # Verify endpoint
        call_args = mock_session.post.call_args[0]
        endpoint = call_args[0]
        assert endpoint == "http://localhost:8000/api/v1/prompt"

    def test_send_prompt_sets_content_type_header(self):
        """send_prompt() should set Content-Type: application/json header"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response
        client._session = mock_session

        client.send_prompt(prompt="Hello", model_id="github-copilot/claude-sonnet-4")

        # Verify Content-Type header
        call_kwargs = mock_session.post.call_args[1]
        headers = call_kwargs["headers"]
        assert headers["Content-Type"] == "application/json"

    def test_send_prompt_creates_session_if_not_exists(self):
        """send_prompt() should create a session if one doesn't exist"""
        server_url = "http://localhost:8000"
        client = OpenCodeHTTPClient(server_url=server_url)

        # Session should not exist yet
        assert client._session is None

        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"content": "test"}, "parts": []}
        mock_session.post.return_value = mock_response

        with patch("requests.Session", return_value=mock_session):
            client.send_prompt(
                prompt="Hello", model_id="github-copilot/claude-sonnet-4"
            )

        # Session should now exist
        assert client._session is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
