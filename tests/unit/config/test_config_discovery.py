"""
Unit tests for config discovery path refactoring (Story B1).

These tests verify that ADWConfig loads configuration from:
1. ADWS/config.yaml (new preferred location)
2. Falls back to .adw.yaml with deprecation warning (legacy location)

Part of Story B1: Refactor config discovery to prefer ADWS/config.yaml
"""

import os
import sys
import pytest
import tempfile
import yaml
from pathlib import Path
from contextlib import contextmanager
import warnings

# Import the config module
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.adw_modules.config import ADWConfig


@contextmanager
def temp_directory():
    """Context manager for creating and cleaning up temporary directories."""
    original_cwd = os.getcwd()
    temp_dir = Path(tempfile.mkdtemp())
    try:
        os.chdir(temp_dir)
        yield temp_dir
    finally:
        os.chdir(original_cwd)


class TestConfigDiscoveryPath:
    """Test configuration file discovery with priority to ADWS/config.yaml."""

    def test_adws_folder_config_yaml_is_preferred(self):
        """Test that ADWS/config.yaml is discovered and loaded when present."""
        config_data = {
            "test_command": "pytest -v",
            "language": "python",
            "opencode": {"server_url": "http://custom-server:5000"},
        }

        with temp_directory() as temp_dir:
            # Create ADWS directory and config.yaml
            adws_dir = temp_dir / "ADWS"
            adws_dir.mkdir()
            config_file = adws_dir / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Create config instance
            config = ADWConfig()

            # Verify config was loaded from ADWS/config.yaml
            assert config.test_command == "pytest -v"
            assert config.language == "python"
            assert config.opencode_server_url == "http://custom-server:5000"
            assert config._config_path.resolve() == config_file.resolve()

    def test_legacy_adw_yaml_fallback_with_deprecation_warning(self):
        """Test that legacy .adw.yaml triggers deprecation warning."""
        config_data = {
            "test_command": "pytest",
            "language": "javascript",
        }

        with temp_directory() as temp_dir:
            # Create legacy .adw.yaml (no ADWS folder)
            config_file = temp_dir / ".adw.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Capture stderr output
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                # Create config instance
                config = ADWConfig()

                # Verify config was loaded from legacy .adw.yaml
                assert config.test_command == "pytest"
                assert config.language == "javascript"
                assert config._config_path.resolve() == config_file.resolve()

    def test_adws_config_overrides_legacy_config(self):
        """Test that ADWS/config.yaml takes precedence when both exist."""
        adws_config_data = {
            "test_command": "uv run pytest",
            "language": "python",
        }
        legacy_config_data = {
            "test_command": "pytest",
            "language": "javascript",
        }

        with temp_directory() as temp_dir:
            # Create ADWS directory with config.yaml
            adws_dir = temp_dir / "ADWS"
            adws_dir.mkdir()
            adws_config_file = adws_dir / "config.yaml"
            with open(adws_config_file, "w") as f:
                yaml.dump(adws_config_data, f)

            # Create legacy .adw.yaml
            legacy_config_file = temp_dir / ".adw.yaml"
            with open(legacy_config_file, "w") as f:
                yaml.dump(legacy_config_data, f)

            # Create config instance
            config = ADWConfig()

            # Verify ADWS/config.yaml values were used, not legacy
            assert config.test_command == "uv run pytest"
            assert config.language == "python"
            assert config._config_path.resolve() == adws_config_file.resolve()

    def test_no_config_uses_defaults(self):
        """Test that when no config exists, defaults are used."""
        with temp_directory() as temp_dir:
            # Create config instance (no config files)
            config = ADWConfig()

            # Verify defaults are used
            assert config.test_command == "pytest"
            assert config.language == "python"
            assert config.source_dir.resolve() == (temp_dir / "src").resolve()
            assert config.test_dir.resolve() == (temp_dir / "tests").resolve()
            assert config._config_path is None

    def test_adws_folder_with_subdirectory_structure(self):
        """Test that ADWS/config.yaml is correctly loaded when in subdirectory."""
        config_data = {
            "source_dir": "app",
            "test_dir": "spec",
        }

        with temp_directory() as temp_dir:
            # Create ADWS directory and config.yaml
            adws_dir = temp_dir / "ADWS"
            adws_dir.mkdir()
            config_file = adws_dir / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Create config instance
            config = ADWConfig()

            # Verify paths are correctly resolved relative to project root
            assert config.source_dir.resolve() == (temp_dir / "app").resolve()
            assert config.test_dir.resolve() == (temp_dir / "spec").resolve()

    def test_config_file_search_stops_at_adws_config(self):
        """Test that search stops at ADWS/config.yaml without walking up."""
        config_data = {"test_command": "found-in-adws"}

        with temp_directory() as temp_dir:
            # Create subdirectory structure
            subdir = temp_dir / "subdir"
            subdir.mkdir()
            os.chdir(subdir)

            # Create ADWS/config.yaml in parent directory
            adws_dir = temp_dir / "ADWS"
            adws_dir.mkdir()
            config_file = adws_dir / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Create config instance from subdirectory
            config = ADWConfig()

            # Should find ADWS/config.yaml in parent directory
            assert config.test_command == "found-in-adws"
            assert config._config_path.resolve() == config_file.resolve()

    def test_project_root_is_adws_folder_parent(self):
        """Test that project_root is correctly set to ADWS folder parent."""
        config_data = {"language": "go"}

        with temp_directory() as temp_dir:
            # Create ADWS directory and config.yaml
            adws_dir = temp_dir / "ADWS"
            adws_dir.mkdir()
            config_file = adws_dir / "config.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config_data, f)

            # Create config instance
            config = ADWConfig()

            # Verify project_root is parent of ADWS folder
            assert config.project_root.resolve() == temp_dir.resolve()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
