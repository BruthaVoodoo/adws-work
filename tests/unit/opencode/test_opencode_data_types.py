"""Tests for OpenCode data types in data_types.py"""

import pytest
from datetime import datetime
from typing import Dict, Any, Optional

from scripts.adw_modules.data_types import (
    OpenCodePart,
    OpenCodeMessageInfo,
    OpenCodeResponse,
)


class TestOpenCodePart:
    """Test OpenCodePart model for individual response parts."""

    def test_text_part_creation(self):
        """Test creating a text part."""
        part = OpenCodePart(type="text", content="This is some text content")

        assert part.type == "text"
        assert part.content == "This is some text content"
        assert part.tool is None
        assert part.input is None
        assert part.output is None

    def test_tool_use_part_creation(self):
        """Test creating a tool_use part with tool and input."""
        part = OpenCodePart(
            type="tool_use",
            content="Using file write tool",
            tool="write",
            input={"path": "/test/file.py", "content": "print('hello')"},
        )

        assert part.type == "tool_use"
        assert part.content == "Using file write tool"
        assert part.tool == "write"
        assert part.input == {"path": "/test/file.py", "content": "print('hello')"}
        assert part.output is None

    def test_tool_result_part_creation(self):
        """Test creating a tool_result part with output."""
        part = OpenCodePart(
            type="tool_result",
            content="Tool execution result",
            output="File written successfully",
        )

        assert part.type == "tool_result"
        assert part.content == "Tool execution result"
        assert part.output == "File written successfully"
        assert part.tool is None
        assert part.input is None

    def test_code_block_part_creation(self):
        """Test creating a code_block part."""
        part = OpenCodePart(
            type="code_block", content="def hello():\n    return 'world'"
        )

        assert part.type == "code_block"
        assert part.content == "def hello():\n    return 'world'"
        assert part.tool is None
        assert part.input is None
        assert part.output is None

    def test_part_from_dict_with_alias(self):
        """Test creating part from dict with alias field mapping."""
        part_data = {
            "type": "tool_use",
            "content": "Using edit tool",
            "tool": "edit",
            "input": {"file": "test.py", "changes": "add function"},
        }

        part = OpenCodePart(**part_data)

        assert part.type == "tool_use"
        assert part.content == "Using edit tool"
        assert part.tool == "edit"
        assert part.input == {"file": "test.py", "changes": "add function"}

    def test_part_type_validation(self):
        """Test that part type is properly validated."""
        # Valid types should work
        valid_types = ["text", "tool_use", "tool_result", "code_block"]
        for valid_type in valid_types:
            part = OpenCodePart(type=valid_type, content="test content")
            assert part.type == valid_type


class TestOpenCodeMessageInfo:
    """Test OpenCodeMessageInfo model for message metadata."""

    def test_message_info_creation(self):
        """Test creating message info with required fields."""
        msg_info = OpenCodeMessageInfo(
            role="assistant", model="github-copilot/claude-sonnet-4"
        )

        assert msg_info.role == "assistant"
        assert msg_info.model == "github-copilot/claude-sonnet-4"
        assert msg_info.timestamp is None
        assert msg_info.token_usage is None

    def test_message_info_with_optional_fields(self):
        """Test creating message info with optional fields."""
        timestamp = datetime.now()
        token_usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }

        msg_info = OpenCodeMessageInfo(
            role="assistant",
            model="github-copilot/claude-haiku-4.5",
            timestamp=timestamp,
            token_usage=token_usage,
        )

        assert msg_info.role == "assistant"
        assert msg_info.model == "github-copilot/claude-haiku-4.5"
        assert msg_info.timestamp == timestamp
        assert msg_info.token_usage == token_usage

    def test_message_info_from_dict(self):
        """Test creating message info from dict."""
        msg_data = {
            "role": "user",
            "model": "github-copilot/claude-sonnet-4",
            "timestamp": "2026-01-09T15:30:00Z",
            "token_usage": {"prompt_tokens": 200, "completion_tokens": 100},
        }

        msg_info = OpenCodeMessageInfo(**msg_data)

        assert msg_info.role == "user"
        assert msg_info.model == "github-copilot/claude-sonnet-4"
        assert msg_info.token_usage == {"prompt_tokens": 200, "completion_tokens": 100}


class TestOpenCodeResponse:
    """Test OpenCodeResponse model for full API responses."""

    def test_response_creation_with_parts(self):
        """Test creating response with message and parts."""
        parts = [
            OpenCodePart(type="text", content="Hello, I'll help you with that."),
            OpenCodePart(
                type="tool_use",
                content="Using write tool",
                tool="write",
                input={"path": "test.py", "content": "print('test')"},
            ),
            OpenCodePart(
                type="tool_result",
                content="Tool result",
                output="File written successfully",
            ),
        ]

        message = OpenCodeMessageInfo(
            role="assistant", model="github-copilot/claude-sonnet-4"
        )

        response = OpenCodeResponse(message=message, parts=parts)

        assert response.message.role == "assistant"
        assert response.message.model == "github-copilot/claude-sonnet-4"
        assert len(response.parts) == 3
        assert response.parts[0].type == "text"
        assert response.parts[1].type == "tool_use"
        assert response.parts[2].type == "tool_result"
        assert response.session_id is None
        assert response.success is True  # default value

    def test_response_with_session_id(self):
        """Test creating response with session ID."""
        parts = [OpenCodePart(type="text", content="Simple response")]
        message = OpenCodeMessageInfo(
            role="assistant", model="github-copilot/claude-haiku-4.5"
        )

        response = OpenCodeResponse(
            message=message, parts=parts, session_id="uuid-session-123", success=True
        )

        assert response.session_id == "uuid-session-123"
        assert response.success is True

    def test_response_from_api_dict(self):
        """Test creating response from API response dict."""
        api_response = {
            "message": {
                "role": "assistant",
                "model": "github-copilot/claude-sonnet-4",
                "timestamp": "2026-01-09T15:30:00Z",
            },
            "parts": [
                {"type": "text", "content": "I'll implement the function for you."},
                {
                    "type": "tool_use",
                    "content": "Writing code",
                    "tool": "edit",
                    "input": {"file": "main.py", "changes": "add new function"},
                },
            ],
            "session_id": "session-456",
            "success": True,
        }

        response = OpenCodeResponse(**api_response)

        assert response.message.role == "assistant"
        assert response.message.model == "github-copilot/claude-sonnet-4"
        assert len(response.parts) == 2
        assert response.parts[0].type == "text"
        assert response.parts[0].content == "I'll implement the function for you."
        assert response.parts[1].type == "tool_use"
        assert response.parts[1].tool == "edit"
        assert response.session_id == "session-456"
        assert response.success is True

    def test_empty_parts_list(self):
        """Test response with empty parts list."""
        message = OpenCodeMessageInfo(
            role="assistant", model="github-copilot/claude-haiku-4.5"
        )

        response = OpenCodeResponse(message=message, parts=[])

        assert len(response.parts) == 0
        assert response.success is True

    def test_response_failure_case(self):
        """Test response with success=False."""
        message = OpenCodeMessageInfo(
            role="assistant", model="github-copilot/claude-sonnet-4"
        )
        parts = [OpenCodePart(type="text", content="Error occurred")]

        response = OpenCodeResponse(message=message, parts=parts, success=False)

        assert response.success is False
        assert response.parts[0].content == "Error occurred"


class TestOpenCodeDataTypesIntegration:
    """Test integration between OpenCode data types."""

    def test_complex_response_parsing(self):
        """Test parsing a complex response with multiple part types."""
        complex_response_data = {
            "message": {
                "role": "assistant",
                "model": "github-copilot/claude-sonnet-4",
                "token_usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 300,
                    "total_tokens": 450,
                },
            },
            "parts": [
                {
                    "type": "text",
                    "content": "I'll help you implement the feature. Let me start by creating the necessary files.",
                },
                {
                    "type": "tool_use",
                    "content": "Creating new file",
                    "tool": "write",
                    "input": {
                        "path": "src/feature.py",
                        "content": "def new_feature():\n    pass",
                    },
                },
                {
                    "type": "tool_result",
                    "content": "File creation result",
                    "output": "File src/feature.py created successfully",
                },
                {
                    "type": "code_block",
                    "content": "def test_new_feature():\n    assert new_feature() is not None",
                },
                {
                    "type": "tool_use",
                    "content": "Writing test file",
                    "tool": "write",
                    "input": {
                        "path": "tests/test_feature.py",
                        "content": "def test_new_feature():\n    assert new_feature() is not None",
                    },
                },
                {
                    "type": "tool_result",
                    "content": "Test file creation result",
                    "output": "File tests/test_feature.py created successfully",
                },
            ],
            "session_id": "complex-session-789",
            "success": True,
        }

        response = OpenCodeResponse(**complex_response_data)

        # Verify message
        assert response.message.role == "assistant"
        assert response.message.model == "github-copilot/claude-sonnet-4"
        assert response.message.token_usage["total_tokens"] == 450

        # Verify parts
        assert len(response.parts) == 6

        # Text part
        assert response.parts[0].type == "text"
        assert "implement the feature" in response.parts[0].content

        # First tool_use
        assert response.parts[1].type == "tool_use"
        assert response.parts[1].tool == "write"
        assert response.parts[1].input["path"] == "src/feature.py"

        # First tool_result
        assert response.parts[2].type == "tool_result"
        assert "created successfully" in response.parts[2].output

        # Code block
        assert response.parts[3].type == "code_block"
        assert "def test_new_feature" in response.parts[3].content

        # Second tool_use
        assert response.parts[4].type == "tool_use"
        assert response.parts[4].tool == "write"
        assert response.parts[4].input["path"] == "tests/test_feature.py"

        # Second tool_result
        assert response.parts[5].type == "tool_result"
        assert "test_feature.py created successfully" in response.parts[5].output

        # Verify session and success
        assert response.session_id == "complex-session-789"
        assert response.success is True

    def test_type_safety_and_autocomplete_support(self):
        """Test that the models provide proper type hints for IDE support."""
        # Create instances using type hints
        part: OpenCodePart = OpenCodePart(type="text", content="test")
        message: OpenCodeMessageInfo = OpenCodeMessageInfo(
            role="user", model="test-model"
        )
        response: OpenCodeResponse = OpenCodeResponse(message=message, parts=[part])

        # Verify type annotations work
        assert isinstance(part.type, str)
        assert isinstance(part.content, str)
        assert part.tool is None or isinstance(part.tool, str)
        assert part.input is None or isinstance(part.input, dict)
        assert part.output is None or isinstance(part.output, str)

        assert isinstance(message.role, str)
        assert isinstance(message.model, str)

        assert isinstance(response.parts, list)
        assert isinstance(response.success, bool)
