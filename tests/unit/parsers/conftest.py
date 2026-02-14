"""
Shared fixtures for parser tests.

This conftest provides fixtures for testing various parser implementations.
"""

import pytest
import json
import tempfile
import os
from typing import Dict, Any
from pathlib import Path


# Inherits fixtures from root conftest.py:
# - tmp_path
# - mock_logger
# - temp_logs_dir


@pytest.fixture
def create_test_json_file():
    """Factory fixture to create temporary JSON test files.

    Returns:
        Callable: Function that creates temp JSON file with given content

    Usage:
        def test_something(create_test_json_file):
            file_path = create_test_json_file({"key": "value"})
            # Use file_path for testing
            # File is automatically cleaned up
    """
    created_files = []

    def _create(content: Dict[Any, Any], suffix: str = ".json") -> str:
        """Create temp JSON file with content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            json.dump(content, f)
            temp_path = f.name
        created_files.append(temp_path)
        return temp_path

    yield _create

    # Cleanup
    for file_path in created_files:
        if os.path.exists(file_path):
            os.unlink(file_path)
