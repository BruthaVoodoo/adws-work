"""
Test for copilot_output_parser.py deprecation notice (Story 4.2).

This test validates that copilot_output_parser.py contains a clear
deprecation notice following the same pattern as bedrock_agent.py.
"""

import pytest


def test_copilot_output_parser_file_exists():
    """Test that copilot_output_parser.py file exists."""
    import os

    file_path = "scripts/adw_modules/copilot_output_parser.py"
    assert os.path.exists(file_path), f"File not found: {file_path}"


def test_copilot_output_parser_has_deprecated_marker():
    """Test that copilot_output_parser.py contains DEPRECATED marker."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert "DEPRECATED" in content, "File should contain 'DEPRECATED' marker"


def test_copilot_output_parser_mentions_no_longer_used():
    """Test that deprecation notice mentions module is no longer used."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert "no longer used" in content.lower(), (
        "Deprecation notice should mention module is no longer used"
    )


def test_copilot_output_parser_references_opencode_api():
    """Test that deprecation notice references OpenCode HTTP API."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert "OpenCode" in content or "opencode" in content.lower(), (
        "Deprecation notice should reference OpenCode HTTP API"
    )


def test_copilot_output_parser_references_github_copilot():
    """Test that deprecation notice references GitHub Copilot."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert "GitHub Copilot" in content or "github copilot" in content.lower(), (
        "Deprecation notice should reference GitHub Copilot"
    )


def test_copilot_output_parser_references_active_implementation():
    """Test that deprecation notice points to active implementation."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert "opencode_http_client.py" in content or "OpenCodeHTTPClient" in content, (
        "Deprecation notice should reference active implementation (opencode_http_client.py)"
    )


def test_copilot_output_parser_mentions_phase_0():
    """Test that deprecation notice mentions Phase 0 decision."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert (
        "Phase 0" in content
        or "January 9, 2026" in content
        or "January 7, 2026" in content
    ), "Deprecation notice should mention Phase 0 decision date"


def test_copilot_output_parser_deprecation_in_docstring():
    """Test that deprecation notice is in module docstring (first ~20 lines)."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        lines = f.readlines()

    # Check first 20 lines for deprecation notice
    first_20_lines = "".join(lines[:20])
    assert "DEPRECATED" in first_20_lines, (
        "Deprecation notice should be in module docstring (first ~20 lines)"
    )


def test_copilot_output_parser_states_kept_for_reference():
    """Test that deprecation notice states module is kept for reference."""
    with open("scripts/adw_modules/copilot_output_parser.py", "r") as f:
        content = f.read()

    assert "reference" in content.lower() or "historical" in content.lower(), (
        "Deprecation notice should state module is kept for reference/historical purposes"
    )
