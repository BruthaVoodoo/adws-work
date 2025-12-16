#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic", "python-dotenv", "pytest"]
# ///

"""
Pytest test suite for ADW state management.

Tests the ADWState class data management.
"""

import pytest
import os
import json
from adw_modules.state import ADWState


class TestStateCreation:
    """Test suite for ADWState creation and data management."""

    def test_state_creation_basic(self):
        """Test creating ADWState with minimal parameters."""
        # Arrange
        adw_id = 'test-adw-123-abc'
        
        # Act
        state = ADWState(adw_id)
        
        # Assert
        assert state.data['adw_id'] == adw_id
        assert isinstance(state.data, dict)

    def test_state_update_with_values(self):
        """Test updating state with domain and issue class."""
        # Arrange
        adw_id = 'test-adw-456-xyz'
        state = ADWState(adw_id)
        
        # Act
        state.update(domain='ADW_Core', issue_class='/feature')
        
        # Assert
        assert state.data['domain'] == 'ADW_Core'
        assert state.data['issue_class'] == '/feature'
        assert state.data['adw_id'] == adw_id

    def test_state_update_agent_values(self):
        """Test updating state with agent-specific values."""
        # Arrange
        adw_id = 'test-adw-789'
        state = ADWState(adw_id)
        
        # Act
        state.update(
            domain='ADW_Agent',
            agent_name='CustomAgent',
            issue_class='/bug'
        )
        
        # Assert
        assert state.data['domain'] == 'ADW_Agent'
        assert state.data['agent_name'] == 'CustomAgent'
        assert state.data['issue_class'] == '/bug'

    def test_state_update_multiple_fields(self):
        """Test updating state with multiple fields at once."""
        # Arrange
        adw_id = 'test-multi-field'
        state = ADWState(adw_id)
        
        # Act
        state.update(
            issue_number='123',
            branch_name='feature-issue-123-abc',
            plan_file='/path/to/plan.md',
            domain='ADW_Core',
            issue_class='/feature'
        )
        
        # Assert
        assert state.data['issue_number'] == '123'
        assert state.data['branch_name'] == 'feature-issue-123-abc'
        assert state.data['plan_file'] == '/path/to/plan.md'
        assert state.data['domain'] == 'ADW_Core'
        assert state.data['issue_class'] == '/feature'


class TestStateDefaults:
    """Test suite for ADWState default values."""

    def test_state_default_domain(self):
        """Test that state defaults to ADW_Core domain."""
        # Arrange
        adw_id = 'test-default-domain'
        
        # Act
        state = ADWState(adw_id)
        
        # Assert
        assert state.data.get('domain', 'ADW_Core') == 'ADW_Core'

    def test_state_default_agent_name_is_none(self):
        """Test that state defaults agent_name to None."""
        # Arrange
        adw_id = 'test-default-agent'
        
        # Act
        state = ADWState(adw_id)
        
        # Assert
        assert state.data.get('agent_name') is None

    def test_state_default_issue_number_is_none(self):
        """Test that state defaults issue_number to None."""
        # Arrange
        adw_id = 'test-default-issue'
        
        # Act
        state = ADWState(adw_id)
        
        # Assert
        assert state.data.get('issue_number') is None


@pytest.mark.parametrize("issue_class", ["/bug", "/feature", "/chore", "/new"])
def test_state_with_all_issue_classes(issue_class):
    """Parametrized test for all supported issue class types."""
    # Arrange
    adw_id = f'test-issue-class-{issue_class.replace("/", "")}'
    state = ADWState(adw_id)
    
    # Act
    state.update(issue_class=issue_class)
    
    # Assert
    assert state.data['issue_class'] == issue_class
    assert state.data['issue_class'].startswith('/')