"""
Root-level shared fixtures for all ADWS tests.

This conftest provides common fixtures used across unit and integration tests.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock
import logging


@pytest.fixture
def tmp_path():
    """Create and cleanup a temporary directory for tests.

    Yields:
        Path: Temporary directory path

    Note:
        Automatically cleans up after test completion.
    """
    import shutil

    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing.

    Returns:
        Mock: Mock logger with logging.Logger spec
    """
    return Mock(spec=logging.Logger)


@pytest.fixture
def temp_logs_dir():
    """Create temporary logs directory for testing.

    Yields:
        Path: Temporary logs directory path
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
