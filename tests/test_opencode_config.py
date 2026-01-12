"""
Unit tests for OpenCode configuration loading in ADWConfig.

These tests verify that the ADWConfig class correctly loads and exposes
OpenCode HTTP API configuration from .adw.yaml files.

Part of Story 1.10: Add OpenCode configuration to .adw.yaml
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

# Import the config module
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.adw_modules.config import ADWConfig


class TestOpenCodeConfiguration:
    """Test OpenCode configuration loading and property access."""

    def test_opencode_server_url_default(self):
        """Test default OpenCode server URL when no config provided."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_server_url == "http://localhost:4096"

    def test_opencode_server_url_custom(self):
        """Test custom OpenCode server URL from config."""
        config_data = {
            "opencode": {"server_url": "https://my-opencode-server.com:8080"}
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert (
                        config.opencode_server_url
                        == "https://my-opencode-server.com:8080"
                    )

    def test_opencode_models_defaults(self):
        """Test default OpenCode model configuration."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    models = config.opencode_models
                    assert models["heavy_lifting"] == "github-copilot/claude-sonnet-4"
                    assert models["lightweight"] == "github-copilot/claude-haiku-4.5"

    def test_opencode_models_custom(self):
        """Test custom OpenCode model configuration."""
        config_data = {
            "opencode": {
                "models": {
                    "heavy_lifting": "custom-heavy-model",
                    "lightweight": "custom-light-model",
                }
            }
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    models = config.opencode_models
                    assert models["heavy_lifting"] == "custom-heavy-model"
                    assert models["lightweight"] == "custom-light-model"

    def test_opencode_model_heavy_lifting(self):
        """Test individual heavy lifting model property."""
        config_data = {
            "opencode": {"models": {"heavy_lifting": "github-copilot/gpt-4"}}
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_model_heavy_lifting == "github-copilot/gpt-4"

    def test_opencode_model_lightweight(self):
        """Test individual lightweight model property."""
        config_data = {
            "opencode": {"models": {"lightweight": "github-copilot/gpt-3.5-turbo"}}
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert (
                        config.opencode_model_lightweight
                        == "github-copilot/gpt-3.5-turbo"
                    )

    def test_opencode_timeout_default(self):
        """Test default OpenCode timeout value."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_timeout == 600

    def test_opencode_timeout_custom(self):
        """Test custom OpenCode timeout value."""
        config_data = {"opencode": {"timeout": 1200}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_timeout == 1200

    def test_opencode_lightweight_timeout_default(self):
        """Test default OpenCode lightweight timeout value."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_lightweight_timeout == 60

    def test_opencode_lightweight_timeout_custom(self):
        """Test custom OpenCode lightweight timeout value."""
        config_data = {"opencode": {"lightweight_timeout": 120}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_lightweight_timeout == 120

    def test_opencode_max_retries_default(self):
        """Test default OpenCode max retries value."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_max_retries == 3

    def test_opencode_max_retries_custom(self):
        """Test custom OpenCode max retries value."""
        config_data = {"opencode": {"max_retries": 5}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_max_retries == 5

    def test_opencode_retry_backoff_default(self):
        """Test default OpenCode retry backoff value."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_retry_backoff == 1.5

    def test_opencode_retry_backoff_custom(self):
        """Test custom OpenCode retry backoff value."""
        config_data = {"opencode": {"retry_backoff": 2.0}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_retry_backoff == 2.0

    def test_opencode_reuse_sessions_default(self):
        """Test default OpenCode session reuse setting."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_reuse_sessions == False

    def test_opencode_reuse_sessions_custom(self):
        """Test custom OpenCode session reuse setting."""
        config_data = {"opencode": {"reuse_sessions": True}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_reuse_sessions == True

    def test_opencode_connection_timeout_default(self):
        """Test default OpenCode connection timeout."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_connection_timeout == 30

    def test_opencode_connection_timeout_custom(self):
        """Test custom OpenCode connection timeout."""
        config_data = {"opencode": {"connection_timeout": 60}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_connection_timeout == 60

    def test_opencode_read_timeout_default(self):
        """Test default OpenCode read timeout."""
        with patch("builtins.open", mock_open(read_data="{}")):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_read_timeout == 600

    def test_opencode_read_timeout_custom(self):
        """Test custom OpenCode read timeout."""
        config_data = {"opencode": {"read_timeout": 900}}
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()
                    assert config.opencode_read_timeout == 900

    def test_comprehensive_opencode_config(self):
        """Test comprehensive OpenCode configuration with all keys."""
        config_data = {
            "opencode": {
                "server_url": "http://custom-server:9000",
                "models": {
                    "heavy_lifting": "custom-heavy",
                    "lightweight": "custom-light",
                },
                "timeout": 800,
                "lightweight_timeout": 90,
                "max_retries": 4,
                "retry_backoff": 1.8,
                "reuse_sessions": True,
                "connection_timeout": 45,
                "read_timeout": 750,
            }
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()

                    # Test all properties
                    assert config.opencode_server_url == "http://custom-server:9000"
                    assert config.opencode_model_heavy_lifting == "custom-heavy"
                    assert config.opencode_model_lightweight == "custom-light"
                    assert config.opencode_timeout == 800
                    assert config.opencode_lightweight_timeout == 90
                    assert config.opencode_max_retries == 4
                    assert config.opencode_retry_backoff == 1.8
                    assert config.opencode_reuse_sessions == True
                    assert config.opencode_connection_timeout == 45
                    assert config.opencode_read_timeout == 750

    def test_partial_opencode_config_with_defaults(self):
        """Test partial OpenCode config falls back to defaults for missing keys."""
        config_data = {
            "opencode": {
                "server_url": "http://partial-config:8000",
                "models": {
                    "heavy_lifting": "partial-heavy"
                    # lightweight missing - should use default
                },
                "timeout": 999,
                # other keys missing - should use defaults
            }
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()

                    # Test configured values
                    assert config.opencode_server_url == "http://partial-config:8000"
                    assert config.opencode_model_heavy_lifting == "partial-heavy"
                    assert config.opencode_timeout == 999

                    # Test default fallbacks
                    assert (
                        config.opencode_model_lightweight
                        == "github-copilot/claude-haiku-4.5"
                    )
                    assert config.opencode_lightweight_timeout == 60
                    assert config.opencode_max_retries == 3
                    assert config.opencode_retry_backoff == 1.5
                    assert config.opencode_reuse_sessions == False
                    assert config.opencode_connection_timeout == 30
                    assert config.opencode_read_timeout == 600

    def test_no_opencode_section_uses_all_defaults(self):
        """Test that missing opencode section uses all default values."""
        config_data = {
            "project_root": ".",
            "language": "python",
            # No opencode section
        }
        with patch("builtins.open", mock_open(read_data=yaml.dump(config_data))):
            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.is_file", return_value=True):
                    config = ADWConfig()

                    # All properties should return defaults
                    assert config.opencode_server_url == "http://localhost:4096"
                    assert (
                        config.opencode_model_heavy_lifting
                        == "github-copilot/claude-sonnet-4"
                    )
                    assert (
                        config.opencode_model_lightweight
                        == "github-copilot/claude-haiku-4.5"
                    )
                    assert config.opencode_timeout == 600
                    assert config.opencode_lightweight_timeout == 60
                    assert config.opencode_max_retries == 3
                    assert config.opencode_retry_backoff == 1.5
                    assert config.opencode_reuse_sessions == False
                    assert config.opencode_connection_timeout == 30
                    assert config.opencode_read_timeout == 600


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
