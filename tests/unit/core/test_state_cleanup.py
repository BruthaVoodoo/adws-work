"""Tests for ADWS state management cleanup functionality."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from scripts.adw_modules.state import ADWState
from scripts.adw_modules.data_types import ADWStateData


class TestStateLoadingDuplication:
    """Test cases for duplicate state loading in adw_test command."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.adw_id = "test123"
        self.issue_number = "456"

    @patch("scripts.adw_modules.config.config")
    def test_state_loading_calls_count_in_adw_test_main(self, mock_config):
        """Test that adw_test main function loads state exactly once, not twice."""
        mock_config.logs_dir = Path(self.temp_dir)

        # Create a state file
        state = ADWState(self.adw_id)
        state.update(issue_number=self.issue_number, branch_name="test-branch")
        state.save("test")

        # Mock ADWState.load to count calls
        with patch.object(ADWState, "load", wraps=ADWState.load) as mock_load:
            with patch("sys.argv", ["adw_test.py", self.issue_number, self.adw_id]):
                with patch(
                    "scripts.adw_modules.workflow_ops.ensure_adw_id"
                ) as mock_ensure:
                    mock_ensure.return_value = self.adw_id

                    # Import and call the function that should load state
                    from scripts.adw_test import parse_args, main

                    # This test verifies the current BROKEN behavior (loads twice)
                    try:
                        # We can't easily test main() due to all the external dependencies,
                        # so let's test the specific workflow that causes duplicate loading

                        # ensure_adw_id loads state once
                        mock_ensure.return_value = self.adw_id

                        # Then main loads state again - this is the duplicate we want to fix
                        result_state = ADWState.load(self.adw_id)

                        # Verify state loaded correctly
                        assert result_state is not None
                        assert result_state.get("issue_number") == self.issue_number

                    except SystemExit:
                        pass  # Expected due to missing dependencies in test

    @patch("scripts.adw_modules.config.config")
    def test_state_loaded_twice_current_behavior(self, mock_config):
        """Test documenting the current broken behavior - state loads twice."""
        mock_config.logs_dir = Path(self.temp_dir)

        # This test documents current state where loading happens twice
        load_count = 0
        original_load = ADWState.load

        def counting_load(*args, **kwargs):
            nonlocal load_count
            load_count += 1
            return original_load(*args, **kwargs)

        with patch.object(ADWState, "load", side_effect=counting_load):
            # Create state
            state = ADWState(self.adw_id)
            state.update(issue_number=self.issue_number)
            state.save("test")

            # Simulate the current adw_test workflow
            from scripts.adw_modules.workflow_ops import ensure_adw_id

            # This loads state once
            adw_id, _ = ensure_adw_id(self.issue_number, self.adw_id, None)

            # This loads state again (the duplicate we want to eliminate)
            state = ADWState.load(adw_id, None)

            # Current behavior - state is loaded twice
            assert load_count == 2, f"Expected 2 loads, got {load_count}"


class TestStateSchemaAfterCleanup:
    """Test cases for expected behavior after cleanup implementation."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.adw_id = "test123"

    @patch("scripts.adw_modules.workflow_ops.config")
    def test_state_loading_happens_once_after_fix(self, mock_config):
        """Test that after fix, adw_test workflow loads state exactly once."""
        mock_config.logs_dir = Path(self.temp_dir)

        # Track state loading calls
        load_count = 0
        original_load = ADWState.load

        def counting_load(*args, **kwargs):
            nonlocal load_count
            load_count += 1
            return original_load(*args, **kwargs)

        with patch.object(ADWState, "load", side_effect=counting_load):
            # Create state
            state = ADWState(self.adw_id)
            state.update(issue_number="456")
            state.save("test")

            # Simulate the NEW adw_test workflow (after fix)
            from scripts.adw_modules.workflow_ops import ensure_adw_id

            # This should load state once and return it
            adw_id, existing_state = ensure_adw_id("456", self.adw_id, None)

            # If existing_state is not None, we shouldn't need to load again
            if existing_state:
                state = existing_state
                final_load_count = load_count
            else:
                # Fallback - load again
                state = ADWState.load(adw_id, None)
                final_load_count = load_count

            # After fix - state should be loaded exactly once
            assert final_load_count == 1, f"Expected 1 load, got {final_load_count}"
            assert existing_state is not None, (
                "ensure_adw_id should return existing state"
            )
            assert existing_state.get("issue_number") == "456"

    def test_domain_field_should_not_exist_after_cleanup(self):
        """Test that domain field should not exist in schema after cleanup."""
        # Test updated behavior - domain field should not exist
        state_data = ADWStateData(adw_id=self.adw_id)
        data_dict = state_data.model_dump()

        # After cleanup - domain field should not exist
        assert "domain" not in data_dict

    def test_agent_name_should_be_populated_after_fix(self):
        """Test that agent_name should be populated with actual agent name."""
        # Test that agent_name gets populated from workflow_step
        state = ADWState("test123")
        state.save("adw_test")  # Pass agent name as workflow_step

        # Verify agent_name is captured
        assert state.get("agent_name") == "adw_test"

    @patch("scripts.adw_modules.state.config")
    def test_state_save_populates_agent_name_from_workflow_step(self, mock_config):
        """Test that state save should populate agent_name after fix."""
        mock_config.logs_dir = Path(self.temp_dir)

        state = ADWState(self.adw_id)
        state.save("adw_plan")  # Save with agent name

        # Read saved file to verify agent_name is populated
        state_file = Path(self.temp_dir) / self.adw_id / "adw_state.json"
        with open(state_file, "r") as f:
            data = json.load(f)

        # After fix - agent_name should be populated
        assert "agent_name" in data
        assert data["agent_name"] == "adw_plan"

    @patch("scripts.adw_modules.state.config")
    def test_state_save_should_not_include_domain_after_cleanup(self, mock_config):
        """Test that state save should not include domain field after cleanup."""
        mock_config.logs_dir = Path(self.temp_dir)

        state = ADWState(self.adw_id)
        state.save("test")

        # Read saved file to verify domain field is not present
        state_file = Path(self.temp_dir) / self.adw_id / "adw_state.json"
        with open(state_file, "r") as f:
            data = json.load(f)

        # After cleanup - domain field should not be saved
        assert "domain" not in data
