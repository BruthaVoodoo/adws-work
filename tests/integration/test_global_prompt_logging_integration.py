"""
Integration tests for global prompt logging across all workflow phases.

Tests that execute_opencode_prompt() correctly calls save_prompt() for all
task types used in ADWS workflow phases (Plan, Build, Test, Review).

Story: Global Prompt Logging
Task: Test global prompt logging across all workflow phases
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, call

from scripts.adw_modules.agent import execute_opencode_prompt, save_prompt
from scripts.adw_modules.data_types import AgentPromptResponse


class TestGlobalPromptLoggingIntegration:
    """Test execute_opencode_prompt() calls save_prompt() for all task types."""

    # temp_logs_dir and mock_opencode_client fixtures provided by tests/integration/conftest.py

    def test_execute_opencode_prompt_calls_save_prompt_for_classify_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for classify task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Classify this issue"
            adw_id = "test_classify_001"
            agent_name = "issue_classifier"
            task_type = "classify"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify OpenCode was called
            assert result.success
            assert mock_opencode_client.send_prompt.called

            # Verify prompt was saved with correct task_type
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            assert expected_dir.exists()

            files = list(expected_dir.glob("classify_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text

    def test_execute_opencode_prompt_calls_save_prompt_for_plan_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for plan task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Create implementation plan"
            adw_id = "test_plan_001"
            agent_name = "sdlc_planner"
            task_type = "plan"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify prompt was saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("plan_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text

    def test_execute_opencode_prompt_calls_save_prompt_for_branch_gen_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for branch_gen task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Generate branch name"
            adw_id = "test_branch_001"
            agent_name = "branch_generator"
            task_type = "branch_gen"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify prompt was saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("branch_gen_*.txt"))
            assert len(files) == 1

    def test_execute_opencode_prompt_calls_save_prompt_for_implement_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for implement task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Implement user authentication feature"
            adw_id = "test_implement_001"
            agent_name = "implementor"
            task_type = "implement"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify prompt was saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("implement_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text

    def test_execute_opencode_prompt_calls_save_prompt_for_commit_msg_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for commit_msg task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Generate commit message"
            adw_id = "test_commit_001"
            agent_name = "commit_generator"
            task_type = "commit_msg"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify prompt was saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("commit_msg_*.txt"))
            assert len(files) == 1

    def test_execute_opencode_prompt_calls_save_prompt_for_test_fix_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for test_fix task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Fix failing tests"
            adw_id = "test_testfix_001"
            agent_name = "test_resolver"
            task_type = "test_fix"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify prompt was saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("test_fix_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text

    def test_execute_opencode_prompt_calls_save_prompt_for_review_task(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves prompt for review task type."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            prompt_text = "Review implementation quality"
            adw_id = "test_review_001"
            agent_name = "reviewer"
            task_type = "review"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify prompt was saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("review_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text

    def test_execute_opencode_prompt_saves_prompt_before_api_call(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test prompt is saved BEFORE OpenCode API call (for debugging failed calls)."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Make OpenCode fail
            mock_opencode_client.send_prompt.side_effect = Exception("API Error")

            prompt_text = "Test prompt"
            adw_id = "test_timing_001"
            agent_name = "agent"
            task_type = "classify"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Even though API failed, prompt should still be saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("classify_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text

    def test_full_workflow_simulation_creates_all_prompt_logs(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test full ADWS workflow creates expected directory structure."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            adw_id = "workflow_test_001"

            # Simulate Plan phase
            execute_opencode_prompt(
                "Classify issue", "classify", adw_id, "issue_classifier"
            )
            execute_opencode_prompt(
                "Generate branch", "branch_gen", adw_id, "branch_generator"
            )
            execute_opencode_prompt("Create plan", "plan", adw_id, "sdlc_planner")

            # Simulate Build phase
            execute_opencode_prompt(
                "Implement feature", "implement", adw_id, "implementor"
            )
            execute_opencode_prompt(
                "Generate commit", "commit_msg", adw_id, "commit_generator"
            )

            # Simulate Test phase
            execute_opencode_prompt("Fix tests", "test_fix", adw_id, "test_resolver")

            # Simulate Review phase
            execute_opencode_prompt("Review code", "review", adw_id, "reviewer")

            # Verify complete directory structure
            base_dir = temp_logs_dir / adw_id

            # Plan phase prompts
            assert base_dir / "issue_classifier" / "prompts" / "classify_*.txt"
            assert base_dir / "branch_generator" / "prompts" / "branch_gen_*.txt"
            assert base_dir / "sdlc_planner" / "prompts" / "plan_*.txt"

            # Build phase prompts
            assert base_dir / "implementor" / "prompts" / "implement_*.txt"
            assert base_dir / "commit_generator" / "prompts" / "commit_msg_*.txt"

            # Test phase prompts
            assert base_dir / "test_resolver" / "prompts" / "test_fix_*.txt"

            # Review phase prompts
            assert base_dir / "reviewer" / "prompts" / "review_*.txt"

            # Count total files
            all_prompts = list(base_dir.glob("*/prompts/*.txt"))
            assert len(all_prompts) == 7  # One per execute_opencode_prompt call

    def test_execute_opencode_prompt_with_unknown_adw_id_defaults_correctly(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() handles default adw_id='unknown'."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Call without explicit adw_id (uses default)
            result = execute_opencode_prompt(
                prompt="Test prompt",
                task_type="classify",
                # adw_id defaults to "unknown"
                agent_name="agent",
            )

            # Verify saved under "unknown" directory
            expected_dir = temp_logs_dir / "unknown" / "agent" / "prompts"
            assert expected_dir.exists()
            files = list(expected_dir.glob("classify_*.txt"))
            assert len(files) == 1

    def test_execute_opencode_prompt_preserves_large_prompts(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() saves large prompts completely."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Create large prompt (simulating real-world scenario with context)
            large_prompt = "Implement feature\n" + ("Context line\n" * 10000)
            adw_id = "large_prompt_001"
            agent_name = "implementor"
            task_type = "implement"

            result = execute_opencode_prompt(
                prompt=large_prompt,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify complete prompt saved
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("implement_*.txt"))
            assert len(files) == 1

            saved_content = files[0].read_text()
            assert saved_content == large_prompt
            assert len(saved_content) > 100000  # Verify size

    def test_execute_opencode_prompt_handles_special_characters_in_prompt(
        self, temp_logs_dir, mock_opencode_client
    ):
        """Test execute_opencode_prompt() handles prompts with special characters."""
        with patch("scripts.adw_modules.agent.config") as mock_config:
            mock_config.logs_dir = temp_logs_dir

            # Prompt with special characters
            prompt_text = "Review code:\n```python\ndef foo():\n    return 'test'\n```\n<xml>data</xml>"
            adw_id = "special_chars_001"
            agent_name = "agent"
            task_type = "review"

            result = execute_opencode_prompt(
                prompt=prompt_text,
                task_type=task_type,
                adw_id=adw_id,
                agent_name=agent_name,
            )

            # Verify content preserved exactly
            expected_dir = temp_logs_dir / adw_id / agent_name / "prompts"
            files = list(expected_dir.glob("review_*.txt"))
            assert len(files) == 1
            assert files[0].read_text() == prompt_text
