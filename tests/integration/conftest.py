"""
Shared fixtures for integration tests.

This conftest provides fixtures commonly used across integration test modules.
"""

import pytest
from unittest.mock import Mock, patch


# Inherits fixtures from root conftest.py:
# - tmp_path
# - mock_logger
# - temp_logs_dir


@pytest.fixture
def mock_opencode_client():
    """Mock OpenCodeHTTPClient for integration testing.

    Returns:
        Mock: Configured mock OpenCodeHTTPClient with send_prompt method
    """
    with patch("scripts.adw_modules.agent.OpenCodeHTTPClient") as mock_client_class:
        mock_client = Mock()
        mock_client_class.from_config.return_value = mock_client

        # Mock model selection for task types
        mock_client.get_model_for_task.return_value = "github-copilot/claude-sonnet-4"

        # Mock successful session-based response
        mock_client.send_prompt.return_value = {
            "parts": [{"type": "text", "content": "Mock response"}],
            "success": True,
            "session_id": "test_session_123",
        }

        yield mock_client
