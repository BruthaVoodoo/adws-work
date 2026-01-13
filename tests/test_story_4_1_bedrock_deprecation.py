"""Tests for Story 4.1: Verify bedrock_agent.py deprecation notice."""

import os
import pytest


class TestStory41BedrockDeprecation:
    """Story 4.1: Mark bedrock_agent.py as deprecated."""

    def test_bedrock_agent_has_deprecation_notice(self):
        """Verify bedrock_agent.py has a clear deprecation notice at the top.

        AC: Given bedrock_agent.py file
             When it's opened
             Then clear deprecation notice is at top
        """
        # Read the bedrock_agent.py file
        file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "adw_modules",
            "bedrock_agent.py",
        )

        with open(file_path, "r") as f:
            content = f.read()

        # Verify deprecation notice exists in docstring
        assert "DEPRECATED" in content, "File should contain 'DEPRECATED' marker"

        # Verify key deprecation message elements
        assert "no longer used" in content.lower(), (
            "Deprecation notice should mention it's no longer used"
        )

        assert "OpenCode HTTP API" in content, (
            "Deprecation notice should mention OpenCode HTTP API as replacement"
        )

        assert "GitHub Copilot" in content, (
            "Deprecation notice should mention GitHub Copilot models"
        )

        # Verify it mentions the replacement module
        assert "scripts/adw_modules/agent.py" in content, (
            "Deprecation notice should reference the active implementation module"
        )

    def test_deprecation_notice_in_docstring(self):
        """Verify deprecation notice is in the module docstring (first lines)."""
        file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "adw_modules",
            "bedrock_agent.py",
        )

        with open(file_path, "r") as f:
            lines = f.readlines()

        # Module docstring should be in first ~20 lines
        first_section = "".join(lines[:20])

        # Verify DEPRECATED marker is in docstring
        assert "DEPRECATED" in first_section, (
            "Deprecation notice should be in module docstring"
        )

    def test_deprecation_notice_mentions_phase0(self):
        """Verify deprecation notice mentions Phase 0 (January 9, 2026)."""
        file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "adw_modules",
            "bedrock_agent.py",
        )

        with open(file_path, "r") as f:
            content = f.read()

        # Should reference Phase 0 and the date of deprecation
        assert "Phase 0" in content or "January 9, 2026" in content, (
            "Deprecation notice should reference Phase 0 and deprecation date"
        )

    def test_deprecation_notice_historical_reference(self):
        """Verify deprecation notice states module is kept for reference."""
        file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "adw_modules",
            "bedrock_agent.py",
        )

        with open(file_path, "r") as f:
            content = f.read()

        # Should mention it's kept for reference/historical purposes
        assert "reference" in content.lower() or "historical" in content.lower(), (
            "Deprecation notice should mention module is kept for reference/historical purposes"
        )
