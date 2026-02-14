"""
Shared fixtures for unit tests.

This conftest provides fixtures commonly used across unit test modules.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path


# Inherits fixtures from root conftest.py:
# - tmp_path
# - mock_logger
# - temp_logs_dir
