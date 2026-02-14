"""
Test suite for Story 1.4: Build model routing logic with task-aware selection

Tests the intelligent model routing functionality that automatically selects
appropriate models based on task types.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from scripts.adw_modules.opencode_http_client import (
    OpenCodeHTTPClient,
    MODEL_LIGHTWEIGHT,
    MODEL_HEAVY_LIFTING,
    TASK_TYPE_TO_MODEL,
)


class TestModelRouting:
    """Test model routing logic - Story 1.4"""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = OpenCodeHTTPClient(
            server_url="http://localhost:4096", api_key="test-key"
        )

    def test_get_model_for_task_classify_returns_lightweight_model(self):
        """
        Story 1.4 AC: Given task_type = "classify"
        When I call get_model_for_task(task_type)
        Then it returns MODEL_LIGHTWEIGHT ("github-copilot/claude-haiku-4.5")
        """
        result = OpenCodeHTTPClient.get_model_for_task("classify")
        assert result == MODEL_LIGHTWEIGHT
        assert result == "github-copilot/claude-haiku-4.5"

    def test_get_model_for_task_implement_returns_heavy_model(self):
        """
        Story 1.4 AC: Given task_type = "implement"
        When I call get_model_for_task(task_type)
        Then it returns MODEL_HEAVY_LIFTING ("github-copilot/claude-sonnet-4")
        """
        result = OpenCodeHTTPClient.get_model_for_task("implement")
        assert result == MODEL_HEAVY_LIFTING
        assert result == "github-copilot/claude-sonnet-4"

    def test_all_nine_task_types_have_correct_model_mapping(self):
        """
        Story 1.4 AC: Given all 9 task types
        When I validate model routing for each
        Then heavy tasks get Claude Sonnet 4 (GitHub Copilot), lightweight tasks get Claude Haiku 4.5 (GitHub Copilot)
        """
        # Lightweight tasks
        lightweight_tasks = [
            "classify",
            "extract_adw",
            "plan",
            "branch_gen",
            "commit_msg",
            "pr_creation",
        ]

        # Heavy lifting tasks
        heavy_tasks = ["implement", "test_fix", "review"]

        # Verify lightweight tasks use haiku model
        for task_type in lightweight_tasks:
            result = OpenCodeHTTPClient.get_model_for_task(task_type)
            assert result == MODEL_LIGHTWEIGHT, (
                f"Task {task_type} should use lightweight model"
            )
            assert "claude-haiku-4.5" in result, (
                f"Task {task_type} should use Claude Haiku 4.5"
            )
            assert "github-copilot/" in result, (
                f"Task {task_type} should use GitHub Copilot"
            )

        # Verify heavy tasks use sonnet model
        for task_type in heavy_tasks:
            result = OpenCodeHTTPClient.get_model_for_task(task_type)
            assert result == MODEL_HEAVY_LIFTING, (
                f"Task {task_type} should use heavy lifting model"
            )
            assert "claude-sonnet-4" in result, (
                f"Task {task_type} should use Claude Sonnet 4"
            )
            assert "github-copilot/" in result, (
                f"Task {task_type} should use GitHub Copilot"
            )

        # Verify we have exactly 9 task types
        assert len(lightweight_tasks) + len(heavy_tasks) == 9
        assert len(TASK_TYPE_TO_MODEL) == 9

    def test_get_model_for_task_raises_error_for_unsupported_task(self):
        """Test that unsupported task types raise ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            OpenCodeHTTPClient.get_model_for_task("unsupported_task")

        error_msg = str(exc_info.value)
        assert "unsupported_task" in error_msg
        assert "Supported task types:" in error_msg
        # Verify all 9 supported task types are listed
        for task_type in TASK_TYPE_TO_MODEL.keys():
            assert task_type in error_msg

    def test_get_all_task_types_returns_complete_mapping(self):
        """Test get_all_task_types returns copy of task type mapping."""
        result = OpenCodeHTTPClient.get_all_task_types()

        # Should be a dict
        assert isinstance(result, dict)

        # Should have 9 entries
        assert len(result) == 9

        # Should contain all expected task types
        expected_tasks = [
            "classify",
            "extract_adw",
            "plan",
            "branch_gen",
            "commit_msg",
            "pr_creation",
            "implement",
            "test_fix",
            "review",
        ]
        for task_type in expected_tasks:
            assert task_type in result

        # Should be a copy (modifying it doesn't affect original)
        result["new_task"] = "new_model"
        assert "new_task" not in TASK_TYPE_TO_MODEL

    def test_is_lightweight_task_correctly_identifies_lightweight_tasks(self):
        """Test is_lightweight_task correctly identifies tasks using lightweight model."""
        lightweight_tasks = [
            "classify",
            "extract_adw",
            "plan",
            "branch_gen",
            "commit_msg",
            "pr_creation",
        ]
        heavy_tasks = ["implement", "test_fix", "review"]

        for task_type in lightweight_tasks:
            assert OpenCodeHTTPClient.is_lightweight_task(task_type), (
                f"{task_type} should be lightweight"
            )

        for task_type in heavy_tasks:
            assert not OpenCodeHTTPClient.is_lightweight_task(task_type), (
                f"{task_type} should not be lightweight"
            )

        # Unsupported task should return False
        assert not OpenCodeHTTPClient.is_lightweight_task("unsupported")

    def test_is_heavy_lifting_task_correctly_identifies_heavy_tasks(self):
        """Test is_heavy_lifting_task correctly identifies tasks using heavy model."""
        lightweight_tasks = [
            "classify",
            "extract_adw",
            "plan",
            "branch_gen",
            "commit_msg",
            "pr_creation",
        ]
        heavy_tasks = ["implement", "test_fix", "review"]

        for task_type in heavy_tasks:
            assert OpenCodeHTTPClient.is_heavy_lifting_task(task_type), (
                f"{task_type} should be heavy lifting"
            )

        for task_type in lightweight_tasks:
            assert not OpenCodeHTTPClient.is_heavy_lifting_task(task_type), (
                f"{task_type} should not be heavy lifting"
            )

        # Unsupported task should return False
        assert not OpenCodeHTTPClient.is_heavy_lifting_task("unsupported")

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_with_task_type_automatically_selects_model(
        self, mock_session_class
    ):
        """Test send_prompt with task_type parameter automatically selects appropriate model."""
        # Mock the session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "model": "github-copilot/claude-haiku-4.5",
            },
            "parts": [{"type": "text", "content": "Test response"}],
        }
        mock_session.post.return_value = mock_response

        # Test with lightweight task
        result = self.client.send_prompt(prompt="Test prompt", task_type="classify")

        # Verify request was made with correct model
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["model_id"] == MODEL_LIGHTWEIGHT

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_with_task_type_heavy_selects_heavy_model(
        self, mock_session_class
    ):
        """Test send_prompt with heavy task type selects heavy lifting model."""
        # Mock the session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "model": "github-copilot/claude-sonnet-4"},
            "parts": [{"type": "text", "content": "Test response"}],
        }
        mock_session.post.return_value = mock_response

        # Test with heavy task
        result = self.client.send_prompt(prompt="Test prompt", task_type="implement")

        # Verify request was made with correct model
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["model_id"] == MODEL_HEAVY_LIFTING

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_model_id_takes_precedence_over_task_type(
        self, mock_session_class
    ):
        """Test that explicit model_id takes precedence over task_type."""
        # Mock the session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "model": "custom-model"},
            "parts": [{"type": "text", "content": "Test response"}],
        }
        mock_session.post.return_value = mock_response

        # Provide both model_id and task_type
        explicit_model = "custom-model"
        result = self.client.send_prompt(
            prompt="Test prompt",
            model_id=explicit_model,
            task_type="classify",  # Would normally select lightweight model
        )

        # Verify explicit model_id was used, not the task_type selection
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        request_body = call_args[1]["json"]
        assert request_body["model_id"] == explicit_model
        assert request_body["model_id"] != MODEL_LIGHTWEIGHT

    def test_send_prompt_raises_error_when_neither_model_id_nor_task_type_provided(
        self,
    ):
        """Test that send_prompt raises ValueError when neither model_id nor task_type is provided."""
        with pytest.raises(ValueError) as exc_info:
            self.client.send_prompt(prompt="Test prompt")

        error_msg = str(exc_info.value)
        assert "Either model_id or task_type must be provided" in error_msg

    def test_send_prompt_raises_error_for_invalid_task_type(self):
        """Test that send_prompt raises ValueError for invalid task_type."""
        with pytest.raises(ValueError) as exc_info:
            self.client.send_prompt(prompt="Test prompt", task_type="invalid_task")

        error_msg = str(exc_info.value)
        assert "Unsupported task_type: invalid_task" in error_msg

    def test_task_type_to_model_constants_are_correct(self):
        """Test that the model constants have correct values."""
        assert MODEL_LIGHTWEIGHT == "github-copilot/claude-haiku-4.5"
        assert MODEL_HEAVY_LIFTING == "github-copilot/claude-sonnet-4"

    def test_task_type_mapping_is_comprehensive(self):
        """Test that TASK_TYPE_TO_MODEL mapping is complete and correct."""
        expected_mapping = {
            # Lightweight tasks
            "classify": "github-copilot/claude-haiku-4.5",
            "extract_adw": "github-copilot/claude-haiku-4.5",
            "plan": "github-copilot/claude-haiku-4.5",
            "branch_gen": "github-copilot/claude-haiku-4.5",
            "commit_msg": "github-copilot/claude-haiku-4.5",
            "pr_creation": "github-copilot/claude-haiku-4.5",
            # Heavy lifting tasks
            "implement": "github-copilot/claude-sonnet-4",
            "test_fix": "github-copilot/claude-sonnet-4",
            "review": "github-copilot/claude-sonnet-4",
        }

        assert TASK_TYPE_TO_MODEL == expected_mapping

    @patch("scripts.adw_modules.opencode_http_client.requests.Session")
    def test_send_prompt_with_task_type_uses_correct_timeout(self, mock_session_class):
        """Test that task_type automatically selects appropriate timeout."""
        # Mock the session and response
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "role": "assistant",
                "model": "github-copilot/claude-haiku-4.5",
            },
            "parts": [{"type": "text", "content": "Test response"}],
        }
        mock_session.post.return_value = mock_response

        # Test with lightweight task (should use lightweight_timeout)
        self.client.send_prompt(prompt="Test prompt", task_type="classify")

        # Verify timeout was set correctly for haiku model
        call_args = mock_session.post.call_args
        assert call_args[1]["timeout"] == self.client.lightweight_timeout

        # Reset mock
        mock_session.post.reset_mock()

        # Test with heavy task (should use regular timeout)
        self.client.send_prompt(prompt="Test prompt", task_type="implement")

        # Verify timeout was set correctly for sonnet model
        call_args = mock_session.post.call_args
        assert call_args[1]["timeout"] == self.client.timeout


class TestModelRoutingEdgeCases:
    """Test edge cases and error conditions for model routing."""

    def test_empty_task_type_raises_error(self):
        """Test that empty task_type raises appropriate error."""
        with pytest.raises(ValueError):
            OpenCodeHTTPClient.get_model_for_task("")

    def test_none_task_type_raises_error(self):
        """Test that None task_type raises appropriate error."""
        with pytest.raises(ValueError):
            OpenCodeHTTPClient.get_model_for_task(None)  # type: ignore

    def test_model_routing_functions_are_static(self):
        """Test that model routing functions can be called without instantiation."""
        # Should be able to call without creating an instance
        result = OpenCodeHTTPClient.get_model_for_task("classify")
        assert result == MODEL_LIGHTWEIGHT

        result = OpenCodeHTTPClient.is_lightweight_task("plan")
        assert result is True

        result = OpenCodeHTTPClient.is_heavy_lifting_task("implement")
        assert result is True

    def test_all_task_types_mapping_consistency(self):
        """Test consistency between different model routing functions."""
        all_tasks = OpenCodeHTTPClient.get_all_task_types()

        for task_type, expected_model in all_tasks.items():
            # get_model_for_task should return same model
            actual_model = OpenCodeHTTPClient.get_model_for_task(task_type)
            assert actual_model == expected_model

            # is_lightweight_task should be consistent
            is_lightweight = OpenCodeHTTPClient.is_lightweight_task(task_type)
            expected_lightweight = expected_model == MODEL_LIGHTWEIGHT
            assert is_lightweight == expected_lightweight

            # is_heavy_lifting_task should be consistent
            is_heavy = OpenCodeHTTPClient.is_heavy_lifting_task(task_type)
            expected_heavy = expected_model == MODEL_HEAVY_LIFTING
            assert is_heavy == expected_heavy

            # A task should be either lightweight OR heavy, not both or neither
            assert is_lightweight != is_heavy, (
                f"Task {task_type} should be either lightweight or heavy, not both"
            )
