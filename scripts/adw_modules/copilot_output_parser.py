"""Parser for unstructured Copilot CLI output.

This module analyzes Copilot CLI logs to extract structured data about
implementation success/failure, metrics, and executed steps.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class ParsedCopilotOutput:
    """Structured representation of parsed Copilot CLI output."""
    
    success: bool
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    test_results: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    validation_status: str = "unknown"
    executed_steps: List[str] = field(default_factory=list)
    raw_output: str = ""


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)


def extract_keywords(output: str) -> Dict[str, List[str]]:
    """Extract keyword indicators from output.
    
    Returns dict with keys: success_indicators, error_indicators, warning_indicators
    """
    success_keywords = ['✓', 'SUCCESS', 'successfully', 'completed', 'done', 'passed', 'Implementation Summary', 'Acceptance Criteria Met', 'All Validation Commands Pass', 'Implementation is complete and working perfectly']
    error_keywords = ['✗', 'ERROR', 'failed', 'error:', 'exception']
    warning_keywords = ['WARNING', 'warn', 'caution', '⚠']
    
    success_found = []
    errors_found = []
    warnings_found = []
    
    # Search for success indicators (case-insensitive for text)
    for keyword in success_keywords:
        if keyword in output or keyword.lower() in output.lower():
            success_found.append(keyword)
    
    # Search for error indicators
    for keyword in error_keywords:
        if keyword in output or keyword.lower() in output.lower():
            errors_found.append(keyword)
    
    # Search for warning indicators
    for keyword in warning_keywords:
        if keyword in output or keyword.lower() in output.lower():
            warnings_found.append(keyword)
    
    return {
        'success_indicators': success_found,
        'error_indicators': errors_found,
        'warning_indicators': warnings_found
    }


def extract_metrics(output: str) -> Tuple[int, int, int]:
    """Extract quantitative metrics from output.
    
    Returns (files_changed, lines_added, lines_removed)
    """
    files_changed = 0
    lines_added = 0
    lines_removed = 0
    
    # Try to find files changed metrics - look for patterns in this priority order
    patterns_files = [
        r'(\d+)\s+file changed(?:s)?', # From git commit summary: "1 file changed" or "5 files changed"
        r'-\s+Files?\s+[Cc]hanged:\s+(\d+)',  # From summary: "- Files changed: 8"
        r'Files\s+[Cc]hanged:\s+(\d+)',
        r'(\d+)\s+files?\s+changed',
        r'[Mm]odified\s+(\d+)\s+files?',
        r'(\d+)\s+files?\s+modified',
    ]
    
    for pattern in patterns_files:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            files_changed = int(matches[-1])
            break
            
    # Fallback: Count natural language indicators if no explicit number found
    if files_changed == 0:
        nl_patterns = [
            r'(?:Created|Updated|Modified|Wrote to|Edit)\s+(?:file\s+)?',
            r'File\s+(?:created|updated|modified|written|edited)',
            r'Writing\s+to\s+file',
            r'Edit\s+.*',
        ]
        count = 0
        for pattern in nl_patterns:
            count += len(re.findall(pattern, output, re.IGNORECASE))
        if count > 0:
            files_changed = count
    
    # Try to find lines added metrics
    patterns_added = [
        r'(\d+)\s+insertions?\(\+\)', # From git commit summary: "645 insertions(+)"
        r'-\s+Lines?\s+added:\s+(\d+)',  # From summary: "- Lines added: 645"
        r'Insertions?\(\+\):\s+(\d+)',
        r'(\d+)\s+lines?\s+added',
        r'[Aa]dded\s+(\d+)\s+lines?',
    ]
    
    for pattern in patterns_added:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            lines_added = int(matches[-1])
            break
    
    # Try to find lines removed metrics
    patterns_removed = [
        r'(\d+)\s+deletions?\(-\)', # From git commit summary: "350 deletions(-)"
        r'-\s+Lines?\s+removed:\s+(\d+)',  # From summary: "- Lines removed: 350"
        r'Deletions?\\[-\\]:\s+(\d+)',
        r'(\d+)\s+lines?\s+removed',
        r'[Rr]emoved\s+(\d+)\s+lines?',
    ]
    
    for pattern in patterns_removed:
        matches = re.findall(pattern, output, re.IGNORECASE)
        if matches:
            lines_removed = int(matches[-1])
            break
    
    return files_changed, lines_added, lines_removed


def detect_errors_warnings(output: str) -> Tuple[List[str], List[str]]:
    """Extract specific error and warning messages from output.
    
    Returns (errors, warnings)
    """
    errors = []
    warnings = []
    
    # Extract error lines - but exclude lines like "Errors: 0"
    error_patterns = [
        r'ERROR[:\s]+(.+?)(?:\n|$)',
        r'Error[:\s]+(.+?)(?:\n|$)',
        r'FAILED[:\s]+(.+?)(?:\n|$)',
        r'Failed[:\s]+(.+?)(?:\n|$)',
        r'Exception[:\s]+(.+?)(?:\n|$)',
    ]
    
    for pattern in error_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE)
        for m in matches:
            m = m.strip()
            # Filter out lines that are just counts (e.g., "0", "1")
            if m and not re.match(r'^\d+$', m):
                errors.append(m)
    
    # Extract warning lines
    warning_patterns = [
        r'WARNING[:\s]+(.+?)(?:\n|$)',
        r'Warn[:\s]+(.+?)(?:\n|$)',
        r'⚠[:\s]*(.+?)(?:\n|$)',
    ]
    
    for pattern in warning_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE)
        for m in matches:
            m = m.strip()
            # Filter out numeric counts
            if m and not re.match(r'^\d+$', m):
                warnings.append(m)
    
    return errors, warnings


def extract_test_results(output: str) -> str:
    """Extract test results summary from output."""
    # Look for test result patterns
    test_patterns = [
        r'(\d+)\s+(?:tests?|specs?)\s+(?:passed|failed)',
        r'Test Results?[:\s]*(.+?)(?:\n\n|$)',
        r'Tests?[:\s]*(.+?)(?:\n|$)',
    ]
    
    for pattern in test_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return ""


def extract_executed_steps(output: str) -> List[str]:
    """Extract list of executed steps from output."""
    steps = []
    
    # Look for step indicators
    step_patterns = [
        r'(?:Step|step)\s+(\d+).*?:?\s*(.+?)(?:\n|$)',
        r'(?:✓|✔|→|\*)\s*(.+?)(?:\n|$)',
    ]
    
    for pattern in step_patterns:
        matches = re.findall(pattern, output)
        steps.extend([m[1] if isinstance(m, tuple) else m for m in matches if m])
    
    return steps


def determine_validation_status(keywords: Dict[str, List[str]], 
                               errors: List[str],
                               warnings: List[str],
                               output: str) -> str:
    """Determine overall validation status based on parsed indicators."""
    has_success_indicators = bool(keywords['success_indicators'])
    has_error_indicators = bool(keywords['error_indicators'])
    has_actual_errors = bool(errors)

    # High-priority check for Copilot's explicit overall success message
    copilot_overall_success_phrases = [
        "Implementation Complete! ✅",
        "Implementation Complete",
        "Implementation Summary",
        "All Acceptance Criteria Met",
        "Implementation complete and working perfectly",
        "Plan analyzed and implemented",
    ]
    for phrase in copilot_overall_success_phrases:
        if phrase in output:
            return "passed"
    
    # If we have actual error messages (not just indicators), it failed
    if has_actual_errors:
        return "failed"
    
    # If we have explicit error indicators (like ✗), it failed
    if has_error_indicators and not has_success_indicators:
        return "failed"
    
    # If we have success indicators, check for warnings
    if has_success_indicators:
        if warnings:
            return "partial"
        else:
            return "passed"
    
    # Ambiguous case
    return "unknown"


def parse_copilot_output(output: str) -> ParsedCopilotOutput:
    """Parse unstructured Copilot CLI output into structured data.
    
    Args:
        output: Raw Copilot CLI output string
        
    Returns:
        ParsedCopilotOutput with extracted metrics and status
    """
    try:
        # DEBUG LOGGING (Local file in ADW/ai_docs/logs)
        # Assuming script is running from ADW/scripts, logs are in ../ai_docs/logs
        # but we don't have adw_id here easily. Let's just use /tmp if we can or print to stderr
        
        if not output or not output.strip():
            logger.warning("Empty output provided to parse_copilot_output")
            return ParsedCopilotOutput(
                success=False,
                validation_status="empty",
                raw_output=output
            )
        
        # Clean ANSI codes for robust parsing
        clean_output = strip_ansi(output)
        
        # Extract keywords and indicators
        keywords = extract_keywords(clean_output)
        
        # Extract quantitative metrics
        files_changed, lines_added, lines_removed = extract_metrics(clean_output)
        
        # Extract error and warning messages
        errors, warnings = detect_errors_warnings(clean_output)
        
        # Extract test results
        test_results = extract_test_results(clean_output)
        
        # Extract executed steps
        executed_steps = extract_executed_steps(clean_output)
        
        # Determine validation status
        validation_status = determine_validation_status(keywords, errors, warnings, clean_output)
        
        # Determine overall success
        success = validation_status == "passed" or (
            validation_status == "partial" and not errors
        )
        
        result = ParsedCopilotOutput(
            success=success,
            files_changed=files_changed,
            lines_added=lines_added,
            lines_removed=lines_removed,
            test_results=test_results,
            warnings=warnings or [],
            errors=errors or [],
            validation_status=validation_status,
            executed_steps=executed_steps,
            raw_output=output  # Keep original output for debugging
        )
        
        logger.debug(f"Parsed output: success={result.success}, "
                    f"files_changed={result.files_changed}, "
                    f"validation_status={result.validation_status}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing Copilot output: {e}")
        return ParsedCopilotOutput(
            success=False,
            validation_status="parse_error",
            errors=[str(e)],
            raw_output=output
        )