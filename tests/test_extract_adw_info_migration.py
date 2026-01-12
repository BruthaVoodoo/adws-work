"""
Tests for Story 2.2: Migrate extract_adw_info() to OpenCode lightweight model

This test verifies that extract_adw_info() correctly uses:
- OpenCode HTTP API instead of execute_template()
- task_type="extract_adw" which routes to Claude Haiku 4.5 (GitHub Copilot)
- Maintains backward compatibility with existing return format
"""

import pytest
from unittest.mock import patch, MagicMock
from scripts.adw_modules.workflow_ops import extract_adw_info
from scripts.adw_modules.data_types import AgentPromptResponse


class TestExtractAdwInfoMigration:
    """Test the migrated extract_adw_info() function."""

    def test_successful_extraction_with_opencode(self):
        """Test successful ADW extraction using OpenCode HTTP API."""
        # Mock the OpenCode response
        mock_response = AgentPromptResponse(
            output='{"adw_slash_command": "/adw_plan", "adw_id": "abc123def"}',
            success=True,
        )

        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            # Setup mocks
            mock_load_prompt.return_value = "Classify this text: {text}"
            mock_execute.return_value = mock_response

            # Test the function
            result = extract_adw_info("some text with /adw_plan abc123def", "temp_id")

            # Verify result
            assert result == ("adw_plan", "abc123def")

            # Verify OpenCode was called with correct parameters
            mock_execute.assert_called_once_with(
                prompt="Classify this text: some text with /adw_plan abc123def",
                task_type="extract_adw",  # Should route to Claude Haiku 4.5
                adw_id="temp_id",
                agent_name="adw_classifier",
            )

    def test_task_type_routes_to_lightweight_model(self):
        """Test that task_type='extract_adw' is used (routes to Claude Haiku 4.5)."""
        mock_response = AgentPromptResponse(
            output='{"adw_slash_command": "/adw_build", "adw_id": "test123"}',
            success=True,
        )

        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            mock_load_prompt.return_value = "Template: {text}"
            mock_execute.return_value = mock_response

            extract_adw_info("test input", "temp_id")

            # Verify the exact task_type is used
            call_args = mock_execute.call_args
            assert call_args[1]["task_type"] == "extract_adw"

    def test_handles_opencode_failure(self):
        """Test handling of OpenCode API failures."""
        mock_response = AgentPromptResponse(
            output="OpenCode connection failed", success=False
        )

        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            mock_load_prompt.return_value = "Template: {text}"
            mock_execute.return_value = mock_response

            result = extract_adw_info("test input", "temp_id")

            # Should return None values on failure
            assert result == (None, None)

    def test_handles_json_parse_error(self):
        """Test handling of malformed JSON response."""
        mock_response = AgentPromptResponse(
            output="This is not valid JSON", success=True
        )

        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            mock_load_prompt.return_value = "Template: {text}"
            mock_execute.return_value = mock_response

            result = extract_adw_info("test input", "temp_id")

            # Should handle JSON parse error gracefully
            assert result == (None, None)

    def test_validates_workflow_commands(self):
        """Test validation of valid workflow commands."""
        test_cases = [
            ("adw_plan", True),
            ("adw_build", True),
            ("adw_test", True),
            ("adw_plan_build", True),
            ("adw_plan_build_test", True),
            ("invalid_command", False),
            ("", False),
        ]

        for command, should_succeed in test_cases:
            mock_response = AgentPromptResponse(
                output=f'{{"adw_slash_command": "/{command}", "adw_id": "test123"}}',
                success=True,
            )

            with (
                patch(
                    "scripts.adw_modules.agent.execute_opencode_prompt"
                ) as mock_execute,
                patch(
                    "scripts.adw_modules.workflow_ops.load_prompt"
                ) as mock_load_prompt,
            ):
                mock_load_prompt.return_value = "Template: {text}"
                mock_execute.return_value = mock_response

                result = extract_adw_info("test input", "temp_id")

                if should_succeed:
                    assert result == (command, "test123")
                else:
                    assert result == (None, None)

    def test_removes_slash_from_command(self):
        """Test that leading slash is removed from ADW commands."""
        mock_response = AgentPromptResponse(
            output='{"adw_slash_command": "/adw_plan_build", "adw_id": "xyz789"}',
            success=True,
        )

        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            mock_load_prompt.return_value = "Template: {text}"
            mock_execute.return_value = mock_response

            result = extract_adw_info("test input", "temp_id")

            # Should return command without slash
            assert result == ("adw_plan_build", "xyz789")

    def test_handles_exception_during_execution(self):
        """Test handling of exceptions during OpenCode execution."""
        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            mock_load_prompt.return_value = "Template: {text}"
            mock_execute.side_effect = Exception("OpenCode server unavailable")

            result = extract_adw_info("test input", "temp_id")

            # Should handle exception gracefully
            assert result == (None, None)

    def test_backward_compatibility_maintained(self):
        """Test that the function maintains the same interface and behavior."""
        # This test ensures the function signature and return format haven't changed
        mock_response = AgentPromptResponse(
            output='{"adw_slash_command": "/adw_test", "adw_id": "compat123"}',
            success=True,
        )

        with (
            patch("scripts.adw_modules.agent.execute_opencode_prompt") as mock_execute,
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
        ):
            mock_load_prompt.return_value = "Template: {text}"
            mock_execute.return_value = mock_response

            # Function should accept same parameters as before
            result = extract_adw_info("test input", "temp_id")

            # Should return same tuple format as before
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert result == ("adw_test", "compat123")
