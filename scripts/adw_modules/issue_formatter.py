"""Utility module for formatting Jira issue context for LLM consumption.

This module provides functions to safely extract and format Jira issue details
for use in LLM prompts, including sanitization, truncation, and formatting.
"""

import logging
from typing import Optional, Dict, List, Any
from adw_modules.data_types import JiraIssue, JiraLabel


def sanitize_for_prompt(text: Optional[str], max_length: Optional[int] = None) -> str:
    """Sanitize text for safe inclusion in LLM prompts.
    
    Args:
        text: Text to sanitize. None values are converted to empty string.
        max_length: Optional maximum length to truncate to.
        
    Returns:
        Sanitized text string.
        
    Responsibility:
        - Handle None/empty strings gracefully
        - Preserve meaningful formatting (newlines, indentation)
        - Escape special characters that could break LLM parsing
        - Truncate if max_length specified
        - Add "(truncated)" indicator if text was truncated
    """
    if not text:
        return ""
    
    text = str(text)
    
    # Preserve structure but escape problematic characters
    # Replace multiple consecutive newlines with double newline
    text = text.replace("\r\n", "\n")  # Normalize line endings
    
    # Truncate if needed
    was_truncated = False
    if max_length and len(text) > max_length:
        text = text[:max_length]
        was_truncated = True
    
    # Add truncation indicator
    if was_truncated:
        text = text + "\n\n(content truncated)"
    
    return text


def format_labels_list(labels: Optional[List[JiraLabel]]) -> str:
    """Format issue labels as comma-separated string.
    
    Args:
        labels: List of JiraLabel objects. None is handled gracefully.
        
    Returns:
        Comma-separated label names string, or empty string if no labels.
        
    Responsibility:
        - Handle None/empty label lists
        - Extract label names safely
        - Return comma-separated format
    """
    if not labels:
        return ""
    
    try:
        label_names = [label.name for label in labels if hasattr(label, 'name')]
        return ", ".join(label_names)
    except Exception:
        return ""


def truncate_description(description: Optional[str], max_length: int = 10000) -> str:
    """Truncate description to maximum length with indicator.
    
    Args:
        description: The description text to truncate.
        max_length: Maximum length before truncation (default 10000).
        
    Returns:
        Truncated description with "(truncated)" indicator if needed.
    """
    if not description:
        return ""
    
    description = str(description)
    if len(description) <= max_length:
        return description
    
    # Try to truncate at a sentence boundary
    truncated = description[:max_length]
    last_period = truncated.rfind(".")
    if last_period > max_length * 0.8:  # Found period in last 20%
        truncated = truncated[:last_period + 1]
    
    return truncated + "\n\n(description truncated)"


def format_issue_context(
    issue: Optional[JiraIssue],
    logger: logging.Logger,
    max_description_length: int = 10000
) -> Dict[str, str]:
    """Extract and format issue context from JiraIssue object for LLM consumption.
    
    Args:
        issue: JiraIssue object with complete issue details. None is handled.
        logger: Logger instance for debug output and warnings.
        max_description_length: Maximum characters for description (default 10000).
        
    Returns:
        Dictionary with formatted issue context:
        {
            "issue_key": "DAI-4",
            "issue_title": "Update Dummy Agent to use Strands boilerplate...",
            "issue_description": "Overview\nWe need to update the Dummy Agent...",
            "issue_labels": "backend, strands-sdk",
            "issue_state": "In Progress"
        }
        
    Responsibility:
        - Validate issue object is not None
        - Safely extract issue.key, issue.title, issue.body, etc.
        - Sanitize and escape text safely
        - Truncate description if needed
        - Format labels as comma-separated string
        - Include issue state/status
        - Handle None values gracefully with warnings
        - Log warnings if data is missing
        - Return formatted dictionary
    """
    # Handle None issue
    if issue is None:
        logger.warning("Issue context is None, returning empty context")
        return {
            "issue_key": "UNKNOWN",
            "issue_title": "Unknown Issue",
            "issue_description": "No issue description available",
            "issue_labels": "",
            "issue_state": "Unknown"
        }
    
    # Extract and validate issue key
    try:
        issue_key = sanitize_for_prompt(issue.key) if hasattr(issue, 'key') else "UNKNOWN"
        if not issue_key:
            logger.warning("Issue key is empty")
            issue_key = "UNKNOWN"
    except Exception as e:
        logger.warning(f"Error extracting issue key: {e}")
        issue_key = "UNKNOWN"
    
    # Extract and validate issue title
    try:
        issue_title = sanitize_for_prompt(issue.title) if hasattr(issue, 'title') else ""
        if not issue_title:
            logger.warning(f"Issue {issue_key} has no title")
            issue_title = "Untitled Issue"
    except Exception as e:
        logger.warning(f"Error extracting issue title: {e}")
        issue_title = "Untitled Issue"
    
    # Extract and validate issue description
    try:
        issue_description = issue.body if hasattr(issue, 'body') else ""
        if not issue_description:
            logger.debug(f"Issue {issue_key} has no description body")
            issue_description = "No description provided"
        else:
            issue_description = truncate_description(issue_description, max_description_length)
    except Exception as e:
        logger.warning(f"Error extracting issue description: {e}")
        issue_description = "Error retrieving description"
    
    # Extract and validate labels
    try:
        labels_list = issue.labels if hasattr(issue, 'labels') else []
        issue_labels = format_labels_list(labels_list)
        if not issue_labels:
            logger.debug(f"Issue {issue_key} has no labels")
    except Exception as e:
        logger.warning(f"Error extracting issue labels: {e}")
        issue_labels = ""
    
    # Extract and validate issue state
    try:
        issue_state = sanitize_for_prompt(issue.state) if hasattr(issue, 'state') else "Unknown"
        if not issue_state:
            logger.warning(f"Issue {issue_key} has no state")
            issue_state = "Unknown"
    except Exception as e:
        logger.warning(f"Error extracting issue state: {e}")
        issue_state = "Unknown"
    
    # Log successful extraction
    logger.debug(f"Successfully formatted context for issue {issue_key}: "
                f"title={len(issue_title)} chars, "
                f"description={len(issue_description)} chars, "
                f"labels={issue_labels}, state={issue_state}")
    
    return {
        "issue_key": issue_key,
        "issue_title": issue_title,
        "issue_description": issue_description,
        "issue_labels": issue_labels,
        "issue_state": issue_state
    }
