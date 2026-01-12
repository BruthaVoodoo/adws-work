"""
Integration test to verify OpenCodeHTTPClient can load configuration from .adw.yaml

Part of Story 1.10: Add OpenCode configuration to .adw.yaml
Tests the from_config() class method and integration with ADWConfig.
"""

import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

# Import the modules
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.adw_modules.opencode_http_client import OpenCodeHTTPClient
from scripts.adw_modules.config import ADWConfig


def test_opencode_client_from_config_default():
    """Test that OpenCodeHTTPClient.from_config() uses default configuration."""
    # Mock empty config to force defaults
    with patch("builtins.open"), patch("pathlib.Path.exists", return_value=False):
        # Create client using from_config()
        client = OpenCodeHTTPClient.from_config()

        # Verify it uses defaults
        assert client.server_url == "http://localhost:4096"
        assert client.timeout == 600.0  # Default heavy timeout
        assert client.lightweight_timeout == 60.0  # Default lightweight timeout
        assert client.api_key is None


def test_opencode_client_from_config_custom():
    """Test that OpenCodeHTTPClient.from_config() uses custom configuration."""
    # Create custom config
    config_data = {
        "opencode": {
            "server_url": "https://custom-opencode.example.com:8080",
            "timeout": 900,
            "lightweight_timeout": 120,
        }
    }

    with (
        patch("builtins.open", mock_open(read_data=yaml.dump(config_data))),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
    ):
        # Create fresh ADWConfig instance
        test_config = ADWConfig()

        # Mock the global config singleton
        with patch("scripts.adw_modules.opencode_http_client.config", test_config):
            # Create client using from_config()
            client = OpenCodeHTTPClient.from_config(api_key="test-api-key")

            # Verify it uses custom config values
            assert client.server_url == "https://custom-opencode.example.com:8080"
            assert client.timeout == 900.0
            assert client.lightweight_timeout == 120.0
            assert client.api_key == "test-api-key"


def test_opencode_client_from_config_with_real_config():
    """Test from_config() with actual .adw.yaml from the project."""
    # Use the real project configuration
    client = OpenCodeHTTPClient.from_config()

    # Verify it loaded expected values from the project's .adw.yaml
    assert isinstance(client.server_url, str)
    assert client.server_url.startswith("http")
    assert isinstance(client.timeout, (int, float))
    assert isinstance(client.lightweight_timeout, (int, float))

    # Should match the values in the project's .adw.yaml
    # (These are the values we expect based on our configuration file)
    assert client.server_url == "http://localhost:4096"
    assert client.timeout == 600.0
    assert client.lightweight_timeout == 60.0


def test_config_integration_all_properties():
    """Test that all OpenCode config properties are accessible."""
    # Create comprehensive config
    config_data = {
        "opencode": {
            "server_url": "http://comprehensive-test:9999",
            "models": {
                "heavy_lifting": "test-heavy-model",
                "lightweight": "test-light-model",
            },
            "timeout": 1200,
            "lightweight_timeout": 180,
            "max_retries": 5,
            "retry_backoff": 2.5,
            "reuse_sessions": True,
            "connection_timeout": 60,
            "read_timeout": 1000,
        }
    }

    with (
        patch("builtins.open", mock_open(read_data=yaml.dump(config_data))),
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
    ):
        # Create fresh ADWConfig instance
        test_config = ADWConfig()

        # Test all properties are accessible
        assert test_config.opencode_server_url == "http://comprehensive-test:9999"
        assert test_config.opencode_model_heavy_lifting == "test-heavy-model"
        assert test_config.opencode_model_lightweight == "test-light-model"
        assert test_config.opencode_timeout == 1200
        assert test_config.opencode_lightweight_timeout == 180
        assert test_config.opencode_max_retries == 5
        assert test_config.opencode_retry_backoff == 2.5
        assert test_config.opencode_reuse_sessions == True
        assert test_config.opencode_connection_timeout == 60
        assert test_config.opencode_read_timeout == 1000


# Helper function for mocking file content
def mock_open(read_data=""):
    """Mock open() function to return specific content."""
    from unittest.mock import mock_open as base_mock_open

    return base_mock_open(read_data=read_data)


if __name__ == "__main__":
    # Run the integration tests
    test_opencode_client_from_config_default()
    test_opencode_client_from_config_custom()
    test_opencode_client_from_config_with_real_config()
    test_config_integration_all_properties()
    print("✅ All integration tests passed!")
