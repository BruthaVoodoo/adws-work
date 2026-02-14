"""Tests for AgentTemplateRequest model validation fix."""

import pytest
from scripts.adw_modules.data_types import AgentTemplateRequest


class TestAgentTemplateRequestModels:
    """Test AgentTemplateRequest model field validation."""

    def test_agent_template_request_accepts_heavy_model(self):
        """Test that AgentTemplateRequest accepts 'heavy' model value."""
        request = AgentTemplateRequest(
            agent_name="patch_planner",
            prompt="test prompt",
            adw_id="test_id",
            model="heavy",
        )
        assert request.model == "heavy"

    def test_agent_template_request_accepts_heavy_lifting_model(self):
        """Test that AgentTemplateRequest accepts 'heavy_lifting' model value."""
        request = AgentTemplateRequest(
            agent_name="patch_planner",
            prompt="test prompt",
            adw_id="test_id",
            model="heavy_lifting",
        )
        assert request.model == "heavy_lifting"

    def test_agent_template_request_accepts_sonnet_model(self):
        """Test that AgentTemplateRequest still accepts 'sonnet' model value."""
        request = AgentTemplateRequest(
            agent_name="patch_planner",
            prompt="test prompt",
            adw_id="test_id",
            model="sonnet",
        )
        assert request.model == "sonnet"

    def test_agent_template_request_accepts_opus_model(self):
        """Test that AgentTemplateRequest still accepts 'opus' model value."""
        request = AgentTemplateRequest(
            agent_name="patch_planner",
            prompt="test prompt",
            adw_id="test_id",
            model="opus",
        )
        assert request.model == "opus"

    def test_agent_template_request_defaults_to_sonnet(self):
        """Test that AgentTemplateRequest defaults to 'sonnet' when no model specified."""
        request = AgentTemplateRequest(
            agent_name="patch_planner", prompt="test prompt", adw_id="test_id"
        )
        assert request.model == "sonnet"

    def test_agent_template_request_rejects_invalid_model(self):
        """Test that AgentTemplateRequest rejects invalid model values."""
        with pytest.raises(ValueError) as exc_info:
            AgentTemplateRequest(
                agent_name="patch_planner",
                prompt="test prompt",
                adw_id="test_id",
                model="invalid_model",
            )

        error_msg = str(exc_info.value)
        assert (
            "Input should be 'sonnet', 'opus', 'heavy' or 'heavy_lifting'" in error_msg
        )

    def test_create_patch_plan_workflow_model_value(self):
        """Test the specific workflow that was failing in the review phase."""
        # This simulates the exact AgentTemplateRequest creation from workflow_ops.py:1075
        request = AgentTemplateRequest(
            agent_name="patch_planner",
            prompt="Create patch plan for review issues",
            adw_id="test_adw_id",
            model="heavy",  # This was the value causing validation error
            workflow_agent_name="test_workflow_agent",
        )

        assert request.agent_name == "patch_planner"
        assert request.model == "heavy"
        assert request.workflow_agent_name == "test_workflow_agent"
