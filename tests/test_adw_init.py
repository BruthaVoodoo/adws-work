"""
Integration tests for adw init command (Story B2).

These tests verify that `adw init` creates the ADWS folder
with correct structure, handles existing folders safely, and supports
--force flag with confirmation.

Part of Story B2: Implement `adw init` CLI command
"""

import os
import sys
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import shutil

# Import the init module
sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.adw_init import get_template_path, copy_template_with_safety, main


class TestAdwInit:
    """Test adw init command functionality."""

    def test_get_template_path(self):
        """Test that template path is correctly resolved."""
        template_path = get_template_path()
        assert template_path.name == "ADWS"
        assert template_path.parent.name == "adw_templates"
        assert template_path.exists()

    def test_init_creates_adws_folder(self, tmp_path):
        """Test that init creates ADWS folder with correct structure."""
        # Change to temp directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Run init
            main(force=False)

            # Verify ADWS folder created
            adws_dir = tmp_path / "ADWS"
            assert adws_dir.exists()
            assert adws_dir.is_dir()

            # Verify config.yaml exists
            config_file = adws_dir / "config.yaml"
            assert config_file.exists()
            assert config_file.is_file()

            # Verify logs directory exists
            logs_dir = adws_dir / "logs"
            assert logs_dir.exists()
            assert logs_dir.is_dir()

            # Verify README exists
            readme_file = adws_dir / "README.md"
            assert readme_file.exists()

            # Verify config has default values
            import yaml

            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)
                assert config_data is not None
                assert "language" in config_data
                assert "test_command" in config_data

        finally:
            os.chdir(original_cwd)

    def test_init_fails_on_existing_folder(self, tmp_path, capsys):
        """Test that init fails when ADWS folder already exists."""
        # Pre-create ADWS folder
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Run init - should fail
            with pytest.raises(SystemExit) as exc_info:
                main(force=False)

            assert exc_info.value.code == 1

            # Verify error message
            captured = capsys.readouterr()
            assert "already exists" in captured.out.lower()

        finally:
            os.chdir(original_cwd)

    def test_init_with_force_overwrites_existing(self, tmp_path, capsys):
        """Test that init with --force overwrites existing folder."""
        # Pre-create ADWS folder with old config
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()
        old_config = adws_dir / "config.yaml"
        old_config.write_text("old: config")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Mock user input to confirm overwrite
            with patch("builtins.input", return_value="y"):
                main(force=True)

            # Verify folder still exists
            assert adws_dir.exists()

            # Verify config was updated (not old config)
            new_config = adws_dir / "config.yaml"
            with open(new_config, "r") as f:
                content = f.read()
                assert "old: config" not in content
                assert "language:" in content  # Has default config

        finally:
            os.chdir(original_cwd)

    def test_init_with_force_declined_cancelled(self, tmp_path, capsys):
        """Test that init with --force can be cancelled."""
        # Pre-create ADWS folder
        adws_dir = tmp_path / "ADWS"
        adws_dir.mkdir()

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Mock user input to decline overwrite
            with patch("builtins.input", return_value="n"):
                with pytest.raises(SystemExit) as exc_info:
                    main(force=True)

            # Verify folder still exists (wasn't deleted)
            assert adws_dir.exists()

            # Verify cancellation message
            captured = capsys.readouterr()
            assert "cancelled" in captured.out.lower()
            assert exc_info.value.code == 0

        finally:
            os.chdir(original_cwd)

    def test_init_preserves_other_files(self, tmp_path):
        """Test that init doesn't affect other files in project."""
        # Create a test file in project root
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Run init
            main(force=False)

            # Verify test file still exists
            assert test_file.exists()
            assert test_file.read_text() == "test content"

            # Verify ADWS folder was created
            adws_dir = tmp_path / "ADWS"
            assert adws_dir.exists()

        finally:
            os.chdir(original_cwd)

    def test_init_creates_correct_directory_structure(self, tmp_path):
        """Test that init creates complete directory structure."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Run init
            main(force=False)

            adws_dir = tmp_path / "ADWS"

            # Verify expected files and directories
            expected_items = {
                "config.yaml",
                "README.md",
                "logs",
            }

            actual_items = {item.name for item in adws_dir.iterdir()}
            assert actual_items == expected_items

            # Verify logs directory is empty except for .gitkeep
            logs_dir = adws_dir / "logs"
            logs_items = [item.name for item in logs_dir.iterdir()]
            assert ".gitkeep" in logs_items

        finally:
            os.chdir(original_cwd)

    def test_init_idempotent(self, tmp_path):
        """Test that running init twice without --force doesn't overwrite."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # First init
            main(force=False)

            # Modify config
            adws_dir = tmp_path / "ADWS"
            config_file = adws_dir / "config.yaml"
            with open(config_file, "a") as f:
                f.write("\n# Custom comment\n")

            # Second init without force - should fail
            with pytest.raises(SystemExit) as exc_info:
                main(force=False)
            assert exc_info.value.code == 1

            # Verify config wasn't overwritten
            with open(config_file, "r") as f:
                content = f.read()
                assert "# Custom comment" in content

        finally:
            os.chdir(original_cwd)

    def test_init_outputs_helpful_messages(self, tmp_path, capsys):
        """Test that init outputs clear success messages."""
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Run init
            main(force=False)

            # Verify success messages
            captured = capsys.readouterr()

            assert "ADWS/ folder created" in captured.out
            assert "Location:" in captured.out
            assert "Config:" in captured.out
            assert "Next steps:" in captured.out
            assert "adw setup" in captured.out
            assert "adw plan" in captured.out

        finally:
            os.chdir(original_cwd)


@pytest.fixture
def tmp_path():
    """Create and cleanup a temporary directory for tests."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
