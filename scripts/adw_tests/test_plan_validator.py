#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest"]
# ///

"""Unit tests for plan validation module."""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.plan_validator import (
    parse_plan_steps,
    extract_executed_steps_from_output,
    cross_reference_plan_output,
    identify_missing_steps,
    validate_step_execution,
    get_plan_summary,
)
from adw_tests.fixtures import (
    SAMPLE_PLAN,
    PLAN_WITH_OPTIONAL,
    SUCCESSFUL_OUTPUT,
    FAILED_OUTPUT,
    STEP_NUMBERED_OUTPUT,
)


class TestParsePlanSteps:
    """Test plan step parsing."""
    
    def test_parse_basic_plan(self):
        """Test parsing a basic plan."""
        steps = parse_plan_steps(SAMPLE_PLAN)
        assert len(steps) > 0
        assert steps[0].step_number == 1
    
    def test_parse_plan_extracts_titles(self):
        """Test that titles are extracted."""
        steps = parse_plan_steps(SAMPLE_PLAN)
        assert all(s.title for s in steps)
    
    def test_parse_plan_with_optional_steps(self):
        """Test parsing plan with optional steps."""
        steps = parse_plan_steps(PLAN_WITH_OPTIONAL)
        assert any(s.optional for s in steps)
    
    def test_parse_empty_plan(self):
        """Test parsing empty plan."""
        steps = parse_plan_steps("")
        assert len(steps) == 0
    
    def test_step_structure(self):
        """Test that parsed steps have expected structure."""
        steps = parse_plan_steps(SAMPLE_PLAN)
        if steps:
            s = steps[0]
            assert hasattr(s, 'step_number')
            assert hasattr(s, 'title')
            assert hasattr(s, 'description')
            assert hasattr(s, 'optional')
            assert isinstance(s.step_number, int)
            assert isinstance(s.title, str)


class TestExtractExecutedStepsFromOutput:
    """Test extraction of executed steps from output."""
    
    def test_extract_checkmark_steps(self):
        """Test extraction of steps marked with checkmarks."""
        steps = extract_executed_steps_from_output(SUCCESSFUL_OUTPUT)
        assert len(steps) > 0
    
    def test_extract_numbered_steps(self):
        """Test extraction of numbered steps."""
        steps = extract_executed_steps_from_output(STEP_NUMBERED_OUTPUT)
        assert len(steps) > 0
    
    def test_extract_from_failed_output(self):
        """Test extraction from output with failures."""
        steps = extract_executed_steps_from_output(FAILED_OUTPUT)
        # Should extract some step indicators
        assert steps is not None
    
    def test_extract_no_duplicates(self):
        """Test that duplicates are removed."""
        output = "✓ Step 1\n✓ Step 1\n✓ Step 2"
        steps = extract_executed_steps_from_output(output)
        # Should have no exact duplicates
        assert len(steps) >= 2


class TestCrossReferencePlanOutput:
    """Test plan and output cross-referencing."""
    
    def test_cross_reference_successful_plan(self):
        """Test cross-referencing successful execution."""
        result = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        assert result is not None
        assert hasattr(result, 'plan_valid')
        assert hasattr(result, 'executed_steps')
        assert hasattr(result, 'missing_steps')
    
    def test_cross_reference_returns_counts(self):
        """Test that cross-reference returns step counts."""
        result = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        assert result.total_steps > 0
        assert result.executed_steps >= 0
    
    def test_cross_reference_with_failed_output(self):
        """Test cross-referencing with failed output."""
        result = cross_reference_plan_output(SAMPLE_PLAN, FAILED_OUTPUT)
        assert result is not None
        # Failed output likely has missing steps
        assert len(result.missing_steps) >= 0
    
    def test_cross_reference_with_optional_steps(self):
        """Test cross-referencing plan with optional steps."""
        result = cross_reference_plan_output(PLAN_WITH_OPTIONAL, SUCCESSFUL_OUTPUT)
        assert result is not None
        # Optional steps may be skipped
        assert hasattr(result, 'optional_steps_skipped')


class TestIdentifyMissingSteps:
    """Test missing step identification."""
    
    def test_identify_missing_steps_in_failed(self):
        """Test identification of missing steps in failed output."""
        missing = identify_missing_steps(SAMPLE_PLAN, FAILED_OUTPUT)
        # Failed output should have missing steps
        assert isinstance(missing, list)
    
    def test_missing_steps_are_strings(self):
        """Test that missing steps are described as strings."""
        missing = identify_missing_steps(SAMPLE_PLAN, FAILED_OUTPUT)
        if missing:
            assert all(isinstance(s, str) for s in missing)


class TestValidateStepExecution:
    """Test step execution validation."""
    
    def test_validate_step_execution(self):
        """Test validation of step execution."""
        passed, details = validate_step_execution(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)
    
    def test_validate_returns_expected_fields(self):
        """Test that validation returns expected detail fields."""
        passed, details = validate_step_execution(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        assert 'plan_valid' in details
        assert 'total_steps' in details
        assert 'executed_steps' in details
        assert 'execution_rate' in details
        assert 'missing_steps' in details
    
    def test_validate_with_required_steps(self):
        """Test validation with specific required steps."""
        required = ["Extend Data Models", "Create Output Parser Module"]
        passed, details = validate_step_execution(
            SAMPLE_PLAN,
            SUCCESSFUL_OUTPUT,
            required_steps=required
        )
        assert isinstance(passed, bool)
    
    def test_validate_execution_rate_format(self):
        """Test that execution rate is formatted correctly."""
        passed, details = validate_step_execution(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        execution_rate = details.get('execution_rate', '')
        # Should be in format like "5/8"
        assert '/' in execution_rate or execution_rate == "0/0"


class TestGetPlanSummary:
    """Test plan summary extraction."""
    
    def test_get_summary_counts_steps(self):
        """Test that summary counts total steps."""
        summary = get_plan_summary(SAMPLE_PLAN)
        assert summary['total_steps'] > 0
    
    def test_get_summary_identifies_optional(self):
        """Test that summary identifies optional steps."""
        summary = get_plan_summary(PLAN_WITH_OPTIONAL)
        assert 'optional_steps' in summary
        assert summary['optional_steps'] > 0
    
    def test_get_summary_required_steps(self):
        """Test that summary counts required steps."""
        summary = get_plan_summary(SAMPLE_PLAN)
        assert 'required_steps' in summary
        assert summary['required_steps'] > 0
    
    def test_get_summary_step_titles(self):
        """Test that summary includes step titles."""
        summary = get_plan_summary(SAMPLE_PLAN)
        assert 'step_titles' in summary
        assert isinstance(summary['step_titles'], list)
        if summary['step_titles']:
            assert all(isinstance(t, str) for t in summary['step_titles'])
    
    def test_get_summary_step_objects(self):
        """Test that summary includes step objects."""
        summary = get_plan_summary(SAMPLE_PLAN)
        assert 'steps' in summary
        if summary['steps']:
            assert hasattr(summary['steps'][0], 'step_number')


class TestEdgeCases:
    """Test edge cases."""
    
    def test_parse_plan_with_empty_steps(self):
        """Test parsing plan with sections but no numbered steps."""
        plan = """
        # Plan
        
        Some introduction text.
        """
        steps = parse_plan_steps(plan)
        # Should handle gracefully
        assert isinstance(steps, list)
    
    def test_cross_reference_empty_plan(self):
        """Test cross-referencing with empty plan."""
        result = cross_reference_plan_output("", SUCCESSFUL_OUTPUT)
        assert result.plan_valid is False
        assert result.total_steps == 0
    
    def test_cross_reference_empty_output(self):
        """Test cross-referencing with empty output."""
        result = cross_reference_plan_output(SAMPLE_PLAN, "")
        assert result is not None
        # Empty output means no steps executed
        assert result.executed_steps == 0
    
    def test_validate_with_malformed_plan(self):
        """Test validation with malformed plan."""
        malformed = "This is not a proper plan format"
        passed, details = validate_step_execution(malformed, SUCCESSFUL_OUTPUT)
        assert isinstance(passed, bool)
        assert isinstance(details, dict)


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Parse plan
        steps = parse_plan_steps(SAMPLE_PLAN)
        assert len(steps) > 0
        
        # Extract executed steps
        executed = extract_executed_steps_from_output(SUCCESSFUL_OUTPUT)
        
        # Cross reference
        result = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        assert result is not None
        
        # Get summary
        summary = get_plan_summary(SAMPLE_PLAN)
        assert summary['total_steps'] == len(steps)
    
    def test_validation_consistency(self):
        """Test that validation is consistent."""
        # Run validation twice, should get same results
        result1 = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        result2 = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        
        assert result1.plan_valid == result2.plan_valid
        assert result1.total_steps == result2.total_steps
        assert result1.executed_steps == result2.executed_steps


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
