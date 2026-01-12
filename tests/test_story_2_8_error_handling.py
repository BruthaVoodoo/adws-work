"""Tests for Story 2.8: Update error handling for planning operations.

This test file validates comprehensive error handling across all planning operations
as implemented in Epic 2, Story 2.8.
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from scripts.adw_modules.workflow_ops import extract_adw_info
from scripts.adw_modules.data_types import AgentPromptResponse


class TestStory28ErrorHandling:
    """Test comprehensive error handling for planning operations (Story 2.8)."""

    def setup_method(self):
        """Set up test logging to capture error messages."""
        self.log_messages = []

        # Create a test handler to capture log messages
        class TestLogHandler(logging.Handler):
            def __init__(self, messages_list):
                super().__init__()
                self.messages = messages_list

            def emit(self, record):
                self.messages.append(record)

        self.test_handler = TestLogHandler(self.log_messages)
        self.logger = logging.getLogger("adw_modules.workflow_ops")
        self.logger.addHandler(self.test_handler)
        self.logger.setLevel(logging.DEBUG)

    def teardown_method(self):
        """Clean up test logging."""
        self.logger.removeHandler(self.test_handler)

    def test_extract_adw_info_prompt_loading_error(self):
        """Test error handling when prompt loading fails in extract_adw_info()."""
        with patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt:
            mock_load_prompt.side_effect = FileNotFoundError("Prompt file not found")

            result = extract_adw_info("test text", "test_adw_id")

            assert result == (None, None)

            # Verify error was logged with helpful context
            error_logs = [msg for msg in self.log_messages if msg.levelname == "ERROR"]
            assert len(error_logs) >= 1
            assert (
                "Failed to load or format classify_adw prompt"
                in error_logs[0].getMessage()
            )
            assert "Prompt file not found" in error_logs[0].getMessage()

    def test_extract_adw_info_opencode_api_failure(self):
        """Test error handling when OpenCode API call fails in extract_adw_info()."""
        with (
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
            patch(
                "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
            ) as mock_execute,
        ):
            mock_load_prompt.return_value = "Test prompt: {text}"
            mock_execute.return_value = AgentPromptResponse(
                output="API failed", success=False
            )

            result = extract_adw_info("test text", "test_adw_id")

            assert result == (None, None)

            # Verify error was logged with helpful context
            error_logs = [msg for msg in self.log_messages if msg.levelname == "ERROR"]
            assert len(error_logs) >= 1
            assert (
                "OpenCode API call failed for ADW extraction"
                in error_logs[0].getMessage()
            )
            assert "API failed" in error_logs[0].getMessage()

    def test_extract_adw_info_json_parsing_error(self):
        """Test error handling when JSON parsing fails in extract_adw_info()."""
        with (
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
            patch(
                "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
            ) as mock_execute,
            patch("scripts.adw_modules.workflow_ops.parse_json") as mock_parse_json,
        ):
            mock_load_prompt.return_value = "Test prompt: {text}"
            mock_execute.return_value = AgentPromptResponse(
                output="Invalid JSON response", success=True
            )
            mock_parse_json.side_effect = ValueError("Invalid JSON format")

            result = extract_adw_info("test text", "test_adw_id")

            assert result == (None, None)

            # Verify error was logged with helpful context
            error_logs = [msg for msg in self.log_messages if msg.levelname == "ERROR"]
            assert len(error_logs) >= 1
            assert (
                "Failed to parse JSON from ADW classification response"
                in error_logs[0].getMessage()
            )
            assert "Invalid JSON format" in error_logs[0].getMessage()
            assert "Invalid JSON response" in error_logs[0].getMessage()

    def test_extract_adw_info_missing_json_fields(self):
        """Test error handling when required JSON fields are missing in extract_adw_info()."""
        with (
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
            patch(
                "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
            ) as mock_execute,
            patch("scripts.adw_modules.workflow_ops.parse_json") as mock_parse_json,
        ):
            mock_load_prompt.return_value = "Test prompt: {text}"
            mock_execute.return_value = AgentPromptResponse(
                output='{"some_field": "value"}', success=True
            )
            # Return dict that's missing expected fields
            mock_parse_json.return_value = {"some_field": "value"}

            result = extract_adw_info("test text", "test_adw_id")

            assert result == (None, None)

            # Verify warning was logged for invalid command
            warning_logs = [
                msg for msg in self.log_messages if msg.levelname == "WARNING"
            ]
            assert len(warning_logs) >= 1
            assert "Invalid or missing ADW command" in warning_logs[0].getMessage()

    def test_extract_adw_info_import_error(self):
        """Test error handling when OpenCode import fails in extract_adw_info()."""
        with patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt:
            mock_load_prompt.return_value = "Test prompt: {text}"

            # Mock import failure by patching the import inside the function
            with patch("builtins.__import__") as mock_import:
                mock_import.side_effect = ImportError("Module not found")

                # Capture stderr output
                import sys
                from io import StringIO

                captured_stderr = StringIO()

                with patch.object(sys, "stderr", captured_stderr):
                    result = extract_adw_info("test text", "test_adw_id")

                assert result == (None, None)

                # Since this uses print to stderr when logger unavailable, check stderr
                stderr_output = captured_stderr.getvalue()
                assert "Failed to import required OpenCode module" in stderr_output

    def test_extract_adw_info_unexpected_error(self):
        """Test error handling for unexpected errors in extract_adw_info()."""
        with patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt:
            # Cause an unexpected error by making load_prompt raise an unexpected exception
            mock_load_prompt.side_effect = RuntimeError("Unexpected system error")

            # Capture stderr output for unexpected errors
            import sys
            from io import StringIO

            captured_stderr = StringIO()

            with patch.object(sys, "stderr", captured_stderr):
                result = extract_adw_info("test text", "test_adw_id")

            assert result == (None, None)

            # Check that error context was included
            stderr_output = captured_stderr.getvalue()
            assert "Unexpected error during ADW extraction" in stderr_output
            assert "temp_adw_id=test_adw_id" in stderr_output
            assert "text_length=9" in stderr_output

    def test_extract_adw_info_successful_case_with_logging(self):
        """Test that successful extraction includes proper debug and info logging."""
        with (
            patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
            patch(
                "scripts.adw_modules.workflow_ops.execute_opencode_prompt"
            ) as mock_execute,
            patch("scripts.adw_modules.workflow_ops.parse_json") as mock_parse_json,
        ):
            mock_load_prompt.return_value = "Test prompt: {text}"
            mock_execute.return_value = AgentPromptResponse(
                output='{"adw_slash_command": "/adw_plan", "adw_id": "abc123"}',
                success=True,
            )
            mock_parse_json.return_value = {
                "adw_slash_command": "/adw_plan",
                "adw_id": "abc123",
            }

            result = extract_adw_info("test text for ADW", "temp_123")

            assert result == ("adw_plan", "abc123")

            # Verify debug logging was used appropriately
            debug_logs = [msg for msg in self.log_messages if msg.levelname == "DEBUG"]
            assert len(debug_logs) >= 3
            assert any(
                "Extracting ADW info from text (length: 17)" in msg.getMessage()
                for msg in debug_logs
            )
            assert any(
                "Calling OpenCode HTTP API" in msg.getMessage() for msg in debug_logs
            )
            assert any(
                "Parsing ADW extraction response" in msg.getMessage()
                for msg in debug_logs
            )

            # Verify info logging for success
            info_logs = [msg for msg in self.log_messages if msg.levelname == "INFO"]
            assert len(info_logs) >= 1
            assert (
                "Successfully extracted ADW info: command='adw_plan', id='abc123'"
                in info_logs[0].getMessage()
            )

    def test_error_message_consistency(self):
        """Test that error messages are consistent and include helpful context."""
        test_cases = [
            # (error_type, expected_message_pattern)
            ("prompt_load", "Failed to load or format classify_adw prompt"),
            ("api_call", "OpenCode API call failed for ADW extraction"),
            ("json_parse", "Failed to parse JSON from ADW classification response"),
            ("import", "Failed to import required OpenCode module"),
            ("unexpected", "Unexpected error during ADW extraction"),
        ]

        for error_type, expected_pattern in test_cases:
            # Test that each error type produces the expected message pattern
            with patch(
                "scripts.adw_modules.workflow_ops.load_prompt"
            ) as mock_load_prompt:
                if error_type == "prompt_load":
                    mock_load_prompt.side_effect = FileNotFoundError("Test error")
                else:
                    mock_load_prompt.return_value = "test prompt"

                # Clear previous log messages
                self.log_messages.clear()

                try:
                    extract_adw_info("test", "test_id")
                except Exception:
                    pass  # Expected for some error types

                # Check that error message contains expected pattern
                all_messages = [msg.getMessage() for msg in self.log_messages]
                if error_type in ["import", "unexpected"]:
                    # These go to stderr, check that too
                    continue  # Skip stderr checking in this test for simplicity
                else:
                    assert any(expected_pattern in msg for msg in all_messages), (
                        f"Expected '{expected_pattern}' in messages: {all_messages}"
                    )

    def test_logger_initialization(self):
        """Test that logger is properly initialized in error handling."""
        with patch("scripts.adw_modules.workflow_ops.load_prompt") as mock_load_prompt:
            mock_load_prompt.return_value = "Test prompt: {text}"

            # Clear previous log messages
            self.log_messages.clear()

            # Call function - should initialize logger
            extract_adw_info("test", "test_id")

            # Verify that debug logging was used (meaning logger was initialized)
            debug_logs = [msg for msg in self.log_messages if msg.levelname == "DEBUG"]
            assert len(debug_logs) >= 1
            assert "Extracting ADW info" in debug_logs[0].getMessage()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
