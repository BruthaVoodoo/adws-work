"""
Shared fixtures for OpenCode module tests.

This conftest provides fixtures for testing OpenCode HTTP client and integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys


# Inherits fixtures from root conftest.py:
# - tmp_path
# - mock_logger
# - temp_logs_dir


@pytest.fixture
def mock_opencode_http_client():
    """Mock OpenCodeHTTPClient for unit testing.

    Returns:
        Mock: Mock client with common methods configured
    """
    mock_client = Mock()
    mock_client.session_id = "test_session_123"
    mock_client.server_url = "http://localhost:8000"
    mock_client.send_prompt.return_value = {
        "parts": [{"type": "text", "content": "Mock response"}],
        "success": True,
        "session_id": "test_session_123",
    }
    mock_client.close_session.return_value = None
    return mock_client


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for HTTP testing.

    Returns:
        Mock: Configured mock for requests.post
    """
    with patch("requests.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "parts": [{"type": "text", "content": "Success"}],
            "success": True,
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def sample_opencode_config():
    """Sample OpenCode configuration for testing.

    Returns:
        dict: Configuration dictionary
    """
    return {
        "server_url": "http://localhost:8000",
        "timeout": 30,
        "model_id": "claude-sonnet-4",
        "max_retries": 3,
    }
