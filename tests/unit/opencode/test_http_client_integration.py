"""Unit tests for OpenCodeHTTPClient - Integration helpers

Tests for output parser functions and structured part extraction.
Story 1.5: Develop output parser for structured Part extraction
"""

import pytest
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from adw_modules.opencode_http_client import (
    extract_text_response,
    extract_tool_execution_details,
    estimate_metrics_from_parts,
)


class TestOutputParserFunctions:
    """Test suite for output parser functions - Story 1.5: Develop output parser for structured Part extraction"""

    def test_extract_text_response_empty_parts(self):
        """
        AC: Given empty parts list
            When I call extract_text_response(parts)
            Then it returns empty string
        """
        result = extract_text_response([])
        assert result == ""

        result = extract_text_response(None)
        assert result == ""

    def test_extract_text_response_single_text_part(self):
        """
        AC: Given a single text part
            When I call extract_text_response(parts)
            Then it returns the text content
        """
        parts = [{"type": "text", "content": "This is a test response."}]

        result = extract_text_response(parts)
        assert result == "This is a test response."

    def test_extract_text_response_multiple_text_parts(self):
        """
        AC: Given multiple text parts
            When I call extract_text_response(parts)
            Then all text parts are concatenated in order
        """
        parts = [
            {"type": "text", "content": "First line of text"},
            {"type": "tool_use", "content": "should be ignored"},
            {"type": "text", "content": "Second line of text"},
            {"type": "text", "content": "Third line of text"},
        ]

        result = extract_text_response(parts)
        expected = "First line of text\nSecond line of text\nThird line of text"
        assert result == expected

    def test_extract_text_response_mixed_part_types(self):
        """
        AC: Given parts with mixed types including text and code_block
            When I call extract_text_response(parts)
            Then text and code_block parts are included in result
        """
        parts = [
            {"type": "text", "content": "Start"},
            {"type": "tool_use", "tool": "edit", "content": "ignored"},
            {"type": "tool_result", "output": "ignored"},
            {"type": "text", "content": "Middle"},
            {"type": "code_block", "content": "code_content"},
            {"type": "text", "content": "End"},
        ]

        result = extract_text_response(parts)
        expected = "Start\nMiddle\ncode_content\nEnd"
        assert result == expected

    def test_extract_text_response_handles_whitespace(self):
        """Test that whitespace is properly handled and stripped"""
        parts = [
            {"type": "text", "content": "  Line with spaces  "},
            {"type": "text", "content": "\n\nLine with newlines\n\n"},
        ]

        result = extract_text_response(parts)
        expected = "Line with spaces\nLine with newlines"
        assert result == expected

    def test_extract_tool_execution_details_empty_parts(self):
        """
        AC: Given empty parts list
            When I call extract_tool_execution_details(parts)
            Then it returns zero counts and empty lists
        """
        result = extract_tool_execution_details([])
        expected = {
            "tool_use_count": 0,
            "tool_result_count": 0,
            "tools_used": [],
            "tool_executions": [],
            "total_tools": 0,
        }
        assert result == expected

    def test_extract_tool_execution_details_tool_use_parts(self):
        """
        AC: Given parts with tool_use types
            When I call extract_tool_execution_details(parts)
            Then tool_use_count and tools_used are correctly populated
        """
        parts = [
            {
                "type": "tool_use",
                "tool": "edit",
                "input": {"file": "test.py", "content": "code"},
            },
            {"type": "tool_use", "tool": "bash", "input": {"command": "pytest"}},
        ]

        result = extract_tool_execution_details(parts)
        assert result["tool_use_count"] == 2
        assert result["tool_result_count"] == 0
        assert set(result["tools_used"]) == {"edit", "bash"}
        assert result["total_tools"] == 2
        assert len(result["tool_executions"]) == 2

    def test_extract_tool_execution_details_tool_result_parts(self):
        """
        AC: Given parts with tool_result types
            When I call extract_tool_execution_details(parts)
            Then tool_result_count is correctly populated
        """
        parts = [
            {"type": "tool_result", "output": "File edited successfully"},
            {"type": "tool_result", "output": "Tests passed: 5/5"},
        ]

        result = extract_tool_execution_details(parts)
        assert result["tool_use_count"] == 0
        assert result["tool_result_count"] == 2
        assert result["tools_used"] == []
        assert result["total_tools"] == 2
        assert len(result["tool_executions"]) == 2

    def test_extract_tool_execution_details_mixed_tool_parts(self):
        """
        AC: Given parts with both tool_use and tool_result types
            When I call extract_tool_execution_details(parts)
            Then both counts and execution details are captured
        """
        parts = [
            {"type": "tool_use", "tool": "edit", "input": {"file": "test.py"}},
            {"type": "tool_result", "output": "File created successfully"},
            {
                "type": "text",
                "content": "Some text",  # Should be ignored
            },
            {"type": "tool_use", "tool": "bash", "input": {"command": "ls -la"}},
        ]

        result = extract_tool_execution_details(parts)
        assert result["tool_use_count"] == 2
        assert result["tool_result_count"] == 1
        assert set(result["tools_used"]) == {"edit", "bash"}
        assert result["total_tools"] == 3
        assert len(result["tool_executions"]) == 3

    def test_extract_tool_execution_details_duplicate_tools(self):
        """Test that duplicate tool names are not double-counted in tools_used"""
        parts = [
            {"type": "tool_use", "tool": "edit", "input": {"file": "file1.py"}},
            {"type": "tool_use", "tool": "edit", "input": {"file": "file2.py"}},
            {"type": "tool_use", "tool": "bash", "input": {"command": "test"}},
        ]

        result = extract_tool_execution_details(parts)
        assert result["tool_use_count"] == 3
        assert len(result["tools_used"]) == 2  # Only unique tools
        assert set(result["tools_used"]) == {"edit", "bash"}

    def test_estimate_metrics_from_parts_empty_parts(self):
        """
        AC: Given empty parts list
            When I call estimate_metrics_from_parts(parts)
            Then all metrics are zero
        """
        result = estimate_metrics_from_parts([])
        expected = {
            "files_changed": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "total_content_length": 0,
            "code_blocks": 0,
        }
        assert result == expected

    def test_estimate_metrics_from_parts_code_blocks(self):
        """
        AC: Given code_block parts
            When I call estimate_metrics_from_parts(parts)
            Then code_blocks count is incremented and lines estimated
        """
        parts = [
            {
                "type": "code_block",
                "content": "def hello():\n    print('Hello World')\n    return True",
            },
            {"type": "code_block", "content": "import os\nimport sys"},
        ]

        result = estimate_metrics_from_parts(parts)
        assert result["code_blocks"] == 2
        assert result["lines_added"] > 0
        assert result["total_content_length"] > 0

    def test_estimate_metrics_from_parts_file_paths(self):
        """
        AC: Given tool_result parts with file paths
            When I call estimate_metrics_from_parts(parts)
            Then files_changed is correctly estimated
        """
        parts = [
            {
                "type": "tool_result",
                "output": "Created file: src/main.py\nUpdated file: tests/test_main.py",
            },
            {"type": "text", "content": "Modified: config.yaml and setup.py"},
        ]

        result = estimate_metrics_from_parts(parts)
        assert result["files_changed"] > 0

    def test_estimate_metrics_from_parts_deletion_patterns(self):
        """
        AC: Given content with deletion patterns
            When I call estimate_metrics_from_parts(parts)
            Then lines_removed is estimated
        """
        parts = [
            {
                "type": "tool_result",
                "output": "Removed old function\nDeleted deprecated file\n// TODO: remove this line",
            }
        ]

        result = estimate_metrics_from_parts(parts)
        assert result["lines_removed"] > 0

    def test_estimate_metrics_comprehensive_example(self):
        """
        AC: Given realistic mix of parts with file operations
            When I call estimate_metrics_from_parts(parts)
            Then all metrics are reasonably estimated
        """
        parts = [
            {
                "type": "tool_use",
                "tool": "edit",
                "input": {"file": "src/models/user.py"},
            },
            {
                "type": "tool_result",
                "output": "File: src/models/user.py\nCreated new User class with following methods:\ndef __init__(self):\n    pass\ndef get_name(self):\n    return self.name",
            },
            {
                "type": "code_block",
                "content": "class User:\n    def __init__(self, name):\n        self.name = name\n    \n    def get_name(self):\n        return self.name",
            },
            {"type": "text", "content": "Also updating tests in tests/test_user.py"},
        ]

        result = estimate_metrics_from_parts(parts)

        # Should detect at least the mentioned files
        assert result["files_changed"] >= 1
        # Should estimate some lines added from the code content
        assert result["lines_added"] > 0
        # Should count the code block
        assert result["code_blocks"] == 1
        # Should have significant content length
        assert result["total_content_length"] > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
