"""
Tests for save_prompt() task_type parameter update.

Tests the updated save_prompt() function that uses task_type parameter
instead of regex extraction from prompt text for filename prefix.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from scripts.adw_modules.agent import save_prompt


class TestSavePromptTaskType:
    """Test save_prompt() with task_type parameter."""

    @pytest.fixture
    def temp_logs_dir(self):
        """Create temporary logs directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_save_prompt_with_task_type_classify(self, temp_logs_dir, capsys):
        """Test save_prompt() uses task_type='classify' in filename."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Classify this issue into feature or bug"
            adw_id = "test_001"
            agent_name = "issue_classifier"
            task_type = "classify"

            save_prompt(
                prompt=prompt_text,
                adw_id=adw_id,
                agent_name=agent_name,
                task_type=task_type,
            )

            # Verify directory structure
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            assert expected_dir.exists()

            # Verify file created with task_type prefix
            files = list(expected_dir.glob("classify_*.txt"))
            assert len(files) == 1
            assert files[0].name.startswith("classify_")

            # Verify content
            content = files[0].read_text()
            assert content == prompt_text

            # Verify console output
            captured = capsys.readouterr()
            assert "Saved prompt to:" in captured.out
            assert "classify_" in captured.out

    def test_save_prompt_with_task_type_implement(self, temp_logs_dir, capsys):
        """Test save_prompt() uses task_type='implement' in filename."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Implement user authentication feature"
            adw_id = "test_002"
            agent_name = "implementor"
            task_type = "implement"

            save_prompt(
                prompt=prompt_text,
                adw_id=adw_id,
                agent_name=agent_name,
                task_type=task_type,
            )

            # Verify file created with implement prefix
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("implement_*.txt"))
            assert len(files) == 1
            assert files[0].name.startswith("implement_")

    def test_save_prompt_with_task_type_plan(self, temp_logs_dir):
        """Test save_prompt() uses task_type='plan' in filename."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            save_prompt(
                prompt="Create implementation plan",
                adw_id="test_003",
                agent_name="planner",
                task_type="plan",
            )

            expected_dir = temp_logs_dir / "test_003" / "planner" / "prompts"
            files = list(expected_dir.glob("plan_*.txt"))
            assert len(files) == 1

    def test_save_prompt_with_task_type_test_fix(self, temp_logs_dir):
        """Test save_prompt() uses task_type='test_fix' in filename."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            save_prompt(
                prompt="Fix failing test",
                adw_id="test_004",
                agent_name="test_resolver",
                task_type="test_fix",
            )

            expected_dir = temp_logs_dir / "test_004" / "test_resolver" / "prompts"
            files = list(expected_dir.glob("test_fix_*.txt"))
            assert len(files) == 1

    def test_save_prompt_with_task_type_review(self, temp_logs_dir):
        """Test save_prompt() uses task_type='review' in filename."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            save_prompt(
                prompt="Review implementation quality",
                adw_id="test_005",
                agent_name="reviewer",
                task_type="review",
            )

            expected_dir = temp_logs_dir / "test_005" / "reviewer" / "prompts"
            files = list(expected_dir.glob("review_*.txt"))
            assert len(files) == 1

    def test_save_prompt_default_task_type(self, temp_logs_dir):
        """Test save_prompt() uses default task_type='prompt' when not specified."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Call without task_type parameter
            save_prompt(
                prompt="Generic prompt",
                adw_id="test_006",
                agent_name="generic_agent",
            )

            expected_dir = temp_logs_dir / "test_006" / "generic_agent" / "prompts"
            files = list(expected_dir.glob("prompt_*.txt"))
            assert len(files) == 1

    def test_save_prompt_creates_directory_structure(self, temp_logs_dir):
        """Test save_prompt() creates full directory hierarchy if missing."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Directory doesn't exist yet
            expected_dir = temp_logs_dir / "test_007" / "new_agent" / "prompts"
            assert not expected_dir.exists()

            save_prompt(
                prompt="Test prompt",
                adw_id="test_007",
                agent_name="new_agent",
                task_type="classify",
            )

            # Directory should now exist
            assert expected_dir.exists()
            assert list(expected_dir.glob("classify_*.txt"))

    def test_save_prompt_multiple_calls_unique_timestamps(self, temp_logs_dir):
        """Test multiple save_prompt() calls create files (may share timestamp if rapid)."""
        import time

        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            adw_id = "test_008"
            agent_name = "agent"
            task_type = "implement"

            # Save multiple prompts with slight delays to ensure unique timestamps
            save_prompt("First prompt", adw_id, agent_name, task_type)
            time.sleep(1.1)  # Ensure timestamp changes (format is YYYYMMDD_HHMMSS)
            save_prompt("Second prompt", adw_id, agent_name, task_type)
            time.sleep(1.1)
            save_prompt("Third prompt", adw_id, agent_name, task_type)

            # Verify all three files exist
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = sorted(expected_dir.glob("implement_*.txt"))
            assert len(files) == 3

            # Verify each has correct content
            assert files[0].read_text() == "First prompt"
            assert files[1].read_text() == "Second prompt"
            assert files[2].read_text() == "Third prompt"

    def test_save_prompt_ignores_prompt_content_for_filename(self, temp_logs_dir):
        """Test save_prompt() uses task_type regardless of prompt content."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Prompt starts with /command pattern (old regex would extract this)
            prompt_text = "/classify this is the old format with command prefix"

            save_prompt(
                prompt=prompt_text,
                adw_id="test_009",
                agent_name="agent",
                task_type="implement",  # Different from prompt content
            )

            expected_dir = temp_logs_dir / "test_009" / "agent" / "prompts"

            # Should use task_type='implement', NOT extracted '/classify'
            files = list(expected_dir.glob("implement_*.txt"))
            assert len(files) == 1

            # Should NOT create file with classify prefix
            classify_files = list(expected_dir.glob("classify_*.txt"))
            assert len(classify_files) == 0

    def test_save_prompt_preserves_full_prompt_content(self, temp_logs_dir):
        """Test save_prompt() saves complete prompt including any command prefixes."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "/classify\nThis is a multi-line\nprompt with command prefix"

            save_prompt(
                prompt=prompt_text,
                adw_id="test_010",
                agent_name="agent",
                task_type="classify",
            )

            expected_dir = temp_logs_dir / "test_010" / "agent" / "prompts"
            files = list(expected_dir.glob("classify_*.txt"))

            # Verify full content preserved
            content = files[0].read_text()
            assert content == prompt_text
            assert "/classify\n" in content
