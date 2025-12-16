#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pytest", "pydantic"]
# ///

"""Unit tests for Copilot output parser."""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adw_modules.copilot_output_parser import (
    parse_copilot_output,
    extract_keywords,
    extract_metrics,
    detect_errors_warnings,
    extract_test_results,
    extract_executed_steps,
)
from adw_tests.fixtures import (
    SUCCESSFUL_OUTPUT,
    FAILED_OUTPUT,
    PARTIAL_OUTPUT,
    EMPTY_OUTPUT,
    MINIMAL_SUCCESS,
    STEP_NUMBERED_OUTPUT,
    COMPLEX_METRICS_OUTPUT,
    VALIDATION_OUTPUT,
    MULTIPLE_ERRORS_OUTPUT,
    TEST_RESULTS_OUTPUT,
)


class TestExtractKeywords:
    """Test keyword extraction from output."""
    
    def test_extract_success_keywords(self):
        """Test extraction of success indicators."""
        keywords = extract_keywords(SUCCESSFUL_OUTPUT)
        assert keywords['success_indicators']
        assert '✓' in keywords['success_indicators'] or 'SUCCESS' in keywords['success_indicators']
    
    def test_extract_error_keywords(self):
        """Test extraction of error indicators."""
        keywords = extract_keywords(FAILED_OUTPUT)
        assert keywords['error_indicators']
        assert '✗' in keywords['error_indicators'] or 'ERROR' in keywords['error_indicators']
    
    def test_extract_warning_keywords(self):
        """Test extraction of warning indicators."""
        keywords = extract_keywords(PARTIAL_OUTPUT)
        assert keywords['warning_indicators']
    
    def test_empty_output_keywords(self):
        """Test keyword extraction with empty output."""
        keywords = extract_keywords(EMPTY_OUTPUT)
        assert keywords['success_indicators'] == []
        assert keywords['error_indicators'] == []


class TestExtractMetrics:
    """Test metrics extraction from output."""
    
    def test_extract_files_changed(self):
        """Test extraction of files changed metric."""
        files_changed, _, _ = extract_metrics(COMPLEX_METRICS_OUTPUT)
        assert files_changed > 0
    
    def test_extract_lines_added(self):
        """Test extraction of lines added metric."""
        _, lines_added, _ = extract_metrics(COMPLEX_METRICS_OUTPUT)
        assert lines_added > 0
    
    def test_extract_lines_removed(self):
        """Test extraction of lines removed metric."""
        _, _, lines_removed = extract_metrics(COMPLEX_METRICS_OUTPUT)
        assert lines_removed > 0
    
    def test_extract_metrics_from_successful_output(self):
        """Test metrics extraction from successful output."""
        files_changed, lines_added, lines_removed = extract_metrics(SUCCESSFUL_OUTPUT)
        assert files_changed == 8
        assert lines_added == 645
    
    def test_extract_metrics_empty(self):
        """Test metrics extraction with empty output."""
        files_changed, lines_added, lines_removed = extract_metrics(EMPTY_OUTPUT)
        assert files_changed == 0
        assert lines_added == 0
        assert lines_removed == 0


class TestDetectErrorsWarnings:
    """Test error and warning detection."""
    
    def test_detect_errors(self):
        """Test detection of error messages."""
        errors, _ = detect_errors_warnings(FAILED_OUTPUT)
        assert len(errors) > 0
        assert any('Permission' in e or 'ERROR' in e for e in errors)
    
    def test_detect_warnings(self):
        """Test detection of warning messages."""
        _, warnings = detect_errors_warnings(PARTIAL_OUTPUT)
        assert len(warnings) > 0
    
    def test_no_errors_in_success(self):
        """Test that successful output has no errors."""
        errors, _ = detect_errors_warnings(SUCCESSFUL_OUTPUT)
        # Should have minimal/no errors
        assert len(errors) == 0 or 'error' not in ' '.join(errors).lower()
    
    def test_multiple_errors(self):
        """Test detection of multiple error messages."""
        errors, _ = detect_errors_warnings(MULTIPLE_ERRORS_OUTPUT)
        assert len(errors) >= 2


class TestExtractTestResults:
    """Test test results extraction."""
    
    def test_extract_test_results(self):
        """Test extraction of test result summary."""
        results = extract_test_results(TEST_RESULTS_OUTPUT)
        assert 'test' in results.lower()
        assert any(num in results for num in ['29', 'passed'])
    
    def test_extract_test_results_from_success(self):
        """Test extraction from successful output."""
        results = extract_test_results(SUCCESSFUL_OUTPUT)
        assert 'test' in results.lower() or results == ""


class TestExtractExecutedSteps:
    """Test step execution extraction."""
    
    def test_extract_steps_with_checkmarks(self):
        """Test extraction of steps marked with checkmarks."""
        steps = extract_executed_steps(SUCCESSFUL_OUTPUT)
        assert len(steps) > 0
    
    def test_extract_numbered_steps(self):
        """Test extraction of numbered steps."""
        steps = extract_executed_steps(STEP_NUMBERED_OUTPUT)
        assert len(steps) > 0
    
    def test_extract_steps_from_failed(self):
        """Test extraction of partial steps from failed output."""
        steps = extract_executed_steps(FAILED_OUTPUT)
        # Should extract some step indicators even from failed output
        assert isinstance(steps, list)


class TestParseCopilotOutput:
    """Test full output parsing."""
    
    def test_parse_successful_output(self):
        """Test parsing of successful implementation output."""
        result = parse_copilot_output(SUCCESSFUL_OUTPUT)
        assert result.success is True
        assert result.validation_status == "passed"
        assert result.files_changed == 8
        assert result.lines_added == 645
        assert len(result.errors) == 0
    
    def test_parse_failed_output(self):
        """Test parsing of failed implementation output."""
        result = parse_copilot_output(FAILED_OUTPUT)
        assert result.success is False
        assert result.validation_status == "failed"
        assert len(result.errors) > 0
    
    def test_parse_partial_output(self):
        """Test parsing of output with warnings."""
        result = parse_copilot_output(PARTIAL_OUTPUT)
        assert result.validation_status in ["partial", "passed"]
        assert len(result.warnings) > 0
    
    def test_parse_empty_output(self):
        """Test parsing of empty output."""
        result = parse_copilot_output(EMPTY_OUTPUT)
        assert result.success is False
        assert result.validation_status == "empty"
    
    def test_parse_minimal_success(self):
        """Test parsing of minimal success message."""
        result = parse_copilot_output(MINIMAL_SUCCESS)
        assert result.success is True
    
    def test_parse_complex_output(self):
        """Test parsing of complex output with various metrics."""
        result = parse_copilot_output(COMPLEX_METRICS_OUTPUT)
        assert result.files_changed > 0
        assert result.lines_added > 0
    
    def test_parse_output_preserves_raw(self):
        """Test that parsing preserves raw output."""
        result = parse_copilot_output(SUCCESSFUL_OUTPUT)
        assert result.raw_output == SUCCESSFUL_OUTPUT
    
    def test_parse_validation_status_mapping(self):
        """Test that validation status is properly determined."""
        success_result = parse_copilot_output(SUCCESSFUL_OUTPUT)
        assert success_result.validation_status == "passed"
        
        failed_result = parse_copilot_output(FAILED_OUTPUT)
        assert failed_result.validation_status == "failed"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_parse_output_with_unicode(self):
        """Test parsing output with unicode characters."""
        output = "✓ Success ✔ Completed 🎉 Done"
        result = parse_copilot_output(output)
        assert result.success is True
    
    def test_parse_output_with_very_long_output(self):
        """Test parsing very large output files."""
        large_output = SUCCESSFUL_OUTPUT * 1000
        result = parse_copilot_output(large_output)
        assert result is not None
    
    def test_parse_output_with_special_characters(self):
        """Test parsing output with special characters."""
        output = "ERROR: Syntax error in file.py: missing ':' at line 42"
        result = parse_copilot_output(output)
        assert len(result.errors) > 0
    
    def test_extract_metrics_with_variations(self):
        """Test metrics extraction with different formats."""
        output = "Modified 5 files, added 100 lines, removed 50 lines"
        files, added, removed = extract_metrics(output)
        assert files > 0
        assert added > 0
        assert removed > 0
    
    def test_parse_None_output(self):
        """Test parsing behavior with edge cases."""
        # This should not crash
        result = parse_copilot_output("")
        assert result.success is False


class TestPerformance:
    """Test performance characteristics."""
    
    def test_large_log_performance(self):
        """Test that parsing completes within reasonable time."""
        import time
        large_output = SUCCESSFUL_OUTPUT * 1000
        
        start = time.time()
        result = parse_copilot_output(large_output)
        elapsed = time.time() - start
        
        # Should complete in under 5 seconds
        assert elapsed < 5.0
        assert result is not None
    
    def test_metrics_extraction_performance(self):
        """Test metrics extraction performance."""
        import time
        large_output = COMPLEX_METRICS_OUTPUT * 500
        
        start = time.time()
        files, added, removed = extract_metrics(large_output)
        elapsed = time.time() - start
        
        # Should complete quickly
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
