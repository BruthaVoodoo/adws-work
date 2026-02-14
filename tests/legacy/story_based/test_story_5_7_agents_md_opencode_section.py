"""
Story 5.7: Test that AGENTS.md contains OpenCode HTTP Server Setup section

Acceptance Criteria:
- Given AGENTS.md file
  When it's reviewed
  Then new section "OpenCode HTTP Server Setup" exists with installation, startup, authentication, configuration, verification, and troubleshooting
"""

import os
from pathlib import Path
import pytest


class TestStory57AgentsmdUpdate:
    """Test suite for Story 5.7 - AGENTS.md OpenCode HTTP Server Setup section"""

    @pytest.fixture
    def agents_md_path(self):
        """Path to AGENTS.md file"""
        # Get project root (assuming this test is run from project root)
        return Path(__file__).parent.parent / "AGENTS.md"

    def test_agents_md_exists(self, agents_md_path):
        """Verify AGENTS.md file exists"""
        assert agents_md_path.exists(), f"AGENTS.md not found at {agents_md_path}"

    def test_opencode_section_exists(self, agents_md_path):
        """Verify 'OpenCode HTTP Server Setup' section exists in AGENTS.md"""
        content = agents_md_path.read_text()
        assert "## OpenCode HTTP Server Setup" in content, (
            "Missing '## OpenCode HTTP Server Setup' section in AGENTS.md"
        )

    def test_opencode_section_has_installation(self, agents_md_path):
        """Verify OpenCode section has installation subsection"""
        content = agents_md_path.read_text()
        # Check for installation-related content
        assert "Installation" in content or "install" in content.lower(), (
            "OpenCode section missing installation instructions"
        )

    def test_opencode_section_has_startup(self, agents_md_path):
        """Verify OpenCode section has startup subsection"""
        content = agents_md_path.read_text()
        # Check for startup-related content
        assert (
            "Startup" in content
            or "start" in content.lower()
            or "serve" in content.lower()
        ), "OpenCode section missing startup instructions"

    def test_opencode_section_has_authentication(self, agents_md_path):
        """Verify OpenCode section has authentication subsection"""
        content = agents_md_path.read_text()
        # Check for authentication-related content
        assert (
            "Authentication" in content
            or "auth" in content.lower()
            or "login" in content.lower()
        ), "OpenCode section missing authentication instructions"

    def test_opencode_section_has_configuration(self, agents_md_path):
        """Verify OpenCode section has configuration subsection"""
        content = agents_md_path.read_text()
        # Check for configuration-related content
        assert (
            "Configuration" in content
            or "config" in content.lower()
            or ".adw.yaml" in content
        ), "OpenCode section missing configuration instructions"

    def test_opencode_section_has_verification(self, agents_md_path):
        """Verify OpenCode section has verification subsection"""
        content = agents_md_path.read_text()
        # Check for verification-related content
        assert (
            "Verification" in content
            or "verify" in content.lower()
            or "health" in content.lower()
        ), "OpenCode section missing verification instructions"

    def test_opencode_section_has_troubleshooting(self, agents_md_path):
        """Verify OpenCode section has troubleshooting subsection"""
        content = agents_md_path.read_text()
        # Check for troubleshooting-related content
        assert (
            "Troubleshooting" in content
            or "troubleshoot" in content.lower()
            or "common issues" in content.lower()
        ), "OpenCode section missing troubleshooting instructions"

    def test_opencode_section_mentions_opencode(self, agents_md_path):
        """Verify OpenCode section mentions OpenCode explicitly"""
        content = agents_md_path.read_text()
        # Count occurrences of "OpenCode"
        opencode_count = content.count("OpenCode")
        assert opencode_count >= 5, (
            f"OpenCode section should mention OpenCode multiple times (found {opencode_count} occurrences)"
        )

    def test_opencode_section_includes_server_url(self, agents_md_path):
        """Verify OpenCode section mentions server URL configuration"""
        content = agents_md_path.read_text()
        assert (
            "server_url" in content
            or "server-url" in content
            or "http://localhost:4096" in content
        ), "OpenCode section missing server URL configuration"

    def test_opencode_section_includes_models(self, agents_md_path):
        """Verify OpenCode section mentions model configuration"""
        content = agents_md_path.read_text()
        assert "models" in content.lower() and (
            "haiku" in content.lower() or "sonnet" in content.lower()
        ), "OpenCode section missing model configuration (Haiku/Sonnet)"

    def test_opencode_section_is_before_common_patterns(self, agents_md_path):
        """Verify OpenCode section is placed before Common Patterns section"""
        content = agents_md_path.read_text()
        opencode_section_pos = content.find("## OpenCode HTTP Server Setup")
        common_patterns_pos = content.find("## Common Patterns")
        assert opencode_section_pos > 0, "OpenCode section not found"
        assert common_patterns_pos > 0, "Common Patterns section not found"
        assert opencode_section_pos < common_patterns_pos, (
            "OpenCode section should be before Common Patterns section"
        )

    def test_opencode_section_has_meaningful_content(self, agents_md_path):
        """Verify OpenCode section has meaningful content (not just headers)"""
        content = agents_md_path.read_text()
        # Extract OpenCode section
        opencode_start = content.find("## OpenCode HTTP Server Setup")
        assert opencode_start > 0, "OpenCode section not found"

        # Find next section header (## or #)
        next_section_pos = content.find("\n## ", opencode_start + 1)
        if next_section_pos == -1:
            # OpenCode section is at the end
            opencode_content = content[opencode_start:]
        else:
            opencode_content = content[opencode_start:next_section_pos]

        # Check content length (should be at least 500 characters for meaningful section)
        assert len(opencode_content) >= 500, (
            f"OpenCode section too short ({len(opencode_content)} characters, expected >= 500)"
        )
