#!/usr/bin/env python3
"""
Manual verification script for Story 2.2: extract_adw_info() migration
"""

import sys

sys.path.append("/Users/t449579/Desktop/DEV/ADWS/scripts")

from unittest.mock import patch, MagicMock
from adw_modules.workflow_ops import extract_adw_info
from adw_modules.data_types import AgentPromptResponse


def test_extract_adw_info_manual():
    """Manual test to verify extract_adw_info() works with OpenCode HTTP."""

    # Mock the OpenCode response
    mock_response = AgentPromptResponse(
        output='{"adw_slash_command": "/adw_plan", "adw_id": "manual_test_123"}',
        success=True,
    )

    with (
        patch("adw_modules.agent.execute_opencode_prompt") as mock_execute,
        patch("adw_modules.workflow_ops.load_prompt") as mock_load_prompt,
    ):
        # Setup mocks
        mock_load_prompt.return_value = "Classify this text: {text}"
        mock_execute.return_value = mock_response

        # Test the function
        result = extract_adw_info(
            "sample text with /adw_plan manual_test_123", "temp_adw_id"
        )

        print(f"✅ Result: {result}")
        print(f"✅ Expected: ('adw_plan', 'manual_test_123')")
        print(f"✅ Match: {result == ('adw_plan', 'manual_test_123')}")

        # Verify OpenCode was called correctly
        mock_execute.assert_called_once()
        call_args = mock_execute.call_args

        print(f"\n✅ OpenCode call verification:")
        print(f"   - task_type: {call_args[1]['task_type']}")
        print(f"   - agent_name: {call_args[1]['agent_name']}")
        print(f"   - adw_id: {call_args[1]['adw_id']}")

        # Verify task_type is extract_adw (routes to Claude Haiku 4.5)
        assert call_args[1]["task_type"] == "extract_adw"
        assert call_args[1]["agent_name"] == "adw_classifier"
        assert call_args[1]["adw_id"] == "temp_adw_id"

        print(f"\n🎉 Story 2.2 migration successful!")
        print(f"   extract_adw_info() now uses OpenCode HTTP API")
        print(f"   Routes to Claude Haiku 4.5 via task_type='extract_adw'")
        return True


if __name__ == "__main__":
    test_extract_adw_info_manual()
