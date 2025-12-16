#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest", "pydantic"]
# ///

"""Integration tests for Copilot output parsing with workflow operations."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.data_types import AgentPromptResponse
from adw_modules.copilot_output_parser import parse_copilot_output
from adw_modules.git_verification import get_file_changes
from adw_modules.plan_validator import cross_reference_plan_output
from adw_modules.jira_formatter import (
    format_implementation_summary,
    format_error_summary,
    format_metrics_only,
    format_validation_report
)
from adw_tests.fixtures import (
    SUCCESSFUL_OUTPUT,
    FAILED_OUTPUT,
    PARTIAL_OUTPUT,
    SAMPLE_PLAN,
)


class TestIntegrationParsingAndValidation:
    """Integration tests for parsing and validation workflow."""
    
    def test_end_to_end_successful_parsing(self):
        """Test complete flow for successful output."""
        # Parse output
        parsed = parse_copilot_output(SUCCESSFUL_OUTPUT)
        assert parsed.success is True
        
        # Validate plan
        plan_result = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        assert plan_result.executed_steps > 0
        
        # Format for Jira
        summary = format_implementation_summary(parsed, plan_result)
        assert "✅" in summary
        assert str(parsed.files_changed) in summary or parsed.files_changed == 0
    
    def test_end_to_end_failed_parsing(self):
        """Test complete flow for failed output."""
        # Parse output
        parsed = parse_copilot_output(FAILED_OUTPUT)
        assert parsed.success is False
        assert len(parsed.errors) > 0
        
        # Format for Jira
        error_msg = format_error_summary(parsed)
        assert "❌" in error_msg
        assert "failed" in error_msg.lower()
    
    def test_response_with_all_metrics(self):
        """Test response creation with all metrics."""
        response = AgentPromptResponse(
            output=SUCCESSFUL_OUTPUT,
            success=True,
            files_changed=8,
            lines_added=645,
            lines_removed=0,
            test_results="12/12 tests passed",
            warnings=[],
            errors=[],
            validation_status="passed"
        )
        
        assert response.files_changed == 8
        assert response.lines_added == 645
        assert response.validation_status == "passed"
        
        # Format for Jira
        summary = format_implementation_summary(response)
        assert "8" in summary
        assert "645" in summary
    
    def test_response_with_warnings_and_errors(self):
        """Test response with warnings and errors."""
        response = AgentPromptResponse(
            output=PARTIAL_OUTPUT,
            success=False,
            files_changed=5,
            lines_added=520,
            warnings=["File size larger than expected"],
            errors=["Build failed"],
            validation_status="partial"
        )
        
        summary = format_implementation_summary(response)
        assert "File size larger than expected" in summary
        assert "Build failed" in summary


class TestJiraFormatting:
    """Test Jira comment formatting functions."""
    
    def test_format_implementation_summary_success(self):
        """Test formatting of successful implementation."""
        response = AgentPromptResponse(
            output="Success",
            success=True,
            files_changed=3,
            lines_added=100,
            validation_status="passed"
        )
        
        summary = format_implementation_summary(response)
        assert "✅" in summary
        assert "Successfully" in summary
        assert "3" in summary
        assert "100" in summary
    
    def test_format_implementation_summary_failure(self):
        """Test formatting of failed implementation."""
        response = AgentPromptResponse(
            output="Failure",
            success=False,
            errors=["Permission denied"],
            validation_status="failed"
        )
        
        summary = format_implementation_summary(response)
        assert "❌" in summary
        assert "Failed" in summary
        assert "Permission denied" in summary
    
    def test_format_error_summary(self):
        """Test brief error summary formatting."""
        response = AgentPromptResponse(
            output="Test error output",
            success=False,
            validation_status="failed"
        )
        
        error_summary = format_error_summary(response)
        assert "❌" in error_summary
        assert "failed" in error_summary
    
    def test_format_metrics_only(self):
        """Test inline metrics formatting."""
        response = AgentPromptResponse(
            output="",
            success=True,
            files_changed=5,
            lines_added=200,
            lines_removed=50
        )
        
        metrics = format_metrics_only(response)
        assert "5 files" in metrics
        assert "+200 lines" in metrics
        assert "-50 lines" in metrics
    
    def test_format_validation_report(self):
        """Test detailed validation report formatting."""
        response = AgentPromptResponse(
            output="",
            success=True,
            files_changed=10,
            lines_added=500,
            test_results="50/50 tests passed",
            warnings=["Some warning"],
            validation_status="passed"
        )
        
        report = format_validation_report(response)
        assert "Validation Report" in report
        assert "✅" in report
        assert "10" in report
        assert "50/50" in report


class TestResponseCreationCompatibility:
    """Test backward compatibility of response creation."""
    
    def test_old_style_response_creation(self):
        """Test creating response with only old fields."""
        response = AgentPromptResponse(
            output="Test output",
            success=True
        )
        
        assert response.output == "Test output"
        assert response.success is True
        assert response.files_changed is None
        assert response.lines_added is None
    
    def test_mixed_field_response(self):
        """Test creating response with mix of old and new fields."""
        response = AgentPromptResponse(
            output="Mixed output",
            success=True,
            files_changed=5,
            validation_status="passed"
        )
        
        assert response.output == "Mixed output"
        assert response.success is True
        assert response.files_changed == 5
        assert response.validation_status == "passed"
        assert response.lines_added is None
    
    def test_response_with_optional_lists(self):
        """Test response with optional list fields."""
        response = AgentPromptResponse(
            output="",
            success=False,
            warnings=["Warning 1", "Warning 2"],
            errors=["Error 1"]
        )
        
        assert len(response.warnings) == 2
        assert len(response.errors) == 1


class TestParsingAndPlanValidationIntegration:
    """Test integration between parsing and plan validation."""
    
    def test_parser_and_plan_validation_together(self):
        """Test using parser output with plan validation."""
        # Parse the output
        parsed = parse_copilot_output(SUCCESSFUL_OUTPUT)
        
        # Use parsed data in plan validation
        plan_result = cross_reference_plan_output(SAMPLE_PLAN, SUCCESSFUL_OUTPUT)
        
        # Create response with both
        response = AgentPromptResponse(
            output=SUCCESSFUL_OUTPUT,
            success=parsed.success,
            files_changed=parsed.files_changed,
            lines_added=parsed.lines_added,
            lines_removed=parsed.lines_removed,
            test_results=parsed.test_results or None,
            warnings=parsed.warnings or None,
            errors=parsed.errors or None,
            validation_status=parsed.validation_status
        )
        
        # Verify combined result
        assert response.success is True
        assert response.validation_status == "passed"
        assert plan_result.total_steps > 0


class TestErrorHandling:
    """Test error handling in parsing and validation."""
    
    def test_parsing_malformed_output(self):
        """Test parsing handles malformed output gracefully."""
        malformed = "This is not structured output\n" * 100
        parsed = parse_copilot_output(malformed)
        
        # Should not crash, should return a result
        assert parsed is not None
        assert isinstance(parsed.success, bool)
    
    def test_response_with_empty_lists(self):
        """Test response creation with empty error/warning lists."""
        response = AgentPromptResponse(
            output="",
            success=True,
            errors=[],
            warnings=[]
        )
        
        assert response.errors == []
        assert response.warnings == []
        
        # Formatting should handle empty lists
        summary = format_implementation_summary(response)
        assert summary is not None
    
    def test_response_with_none_lists(self):
        """Test response creation with None for error/warning lists."""
        response = AgentPromptResponse(
            output="",
            success=True,
            errors=None,
            warnings=None
        )
        
        assert response.errors is None
        assert response.warnings is None
        
        # Formatting should handle None values
        summary = format_implementation_summary(response)
        assert summary is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
