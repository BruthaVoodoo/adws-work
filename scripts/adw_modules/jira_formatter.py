"""Formatting utilities for Jira comments with implementation details.

This module provides functions to format rich implementation summaries
with specific metrics, errors, and warnings for Jira issue comments.
"""

from typing import Optional, List
from .data_types import AgentPromptResponse


def format_implementation_summary(
    response: AgentPromptResponse, plan_validation=None
) -> str:
    """Format implementation response as a rich Jira comment.

    Args:
        response: AgentPromptResponse with parsed metrics
        plan_validation: Optional plan validation result

    Returns:
        Formatted markdown string suitable for Jira comment
    """
    lines = []

    # Header
    if response.success:
        lines.append("## ✅ Implementation Completed Successfully")
    else:
        lines.append("## ❌ Implementation Failed")

    lines.append("")

    # Validation Status
    if response.validation_status:
        status_icons = {
            "passed": "✅ Passed",
            "failed": "❌ Failed",
            "partial": "⚠️ Partial",
            "unknown": "❓ Unknown",
            "empty": "⚠️ No Output",
        }
        status_text = status_icons.get(
            response.validation_status, response.validation_status
        )
        lines.append(f"**Validation Status:** {status_text}")
        lines.append("")

    # Metrics Summary
    if response.files_changed is not None or response.lines_added is not None:
        lines.append("### Implementation Metrics")

        if response.files_changed is not None:
            lines.append(f"- **Files Changed:** {response.files_changed}")

        if response.lines_added is not None:
            lines.append(f"- **Lines Added:** {response.lines_added}")

        if response.lines_removed is not None:
            lines.append(f"- **Lines Removed:** {response.lines_removed}")

        if response.test_results:
            lines.append(f"- **Test Results:** {response.test_results}")

        lines.append("")

    # Plan Validation Details
    if plan_validation:
        lines.append("### Plan Execution")
        lines.append(
            f"- **Steps Executed:** {plan_validation.executed_steps}/{plan_validation.total_steps}"
        )

        if plan_validation.missing_steps:
            lines.append(
                f"- **Missing Steps:** {', '.join(plan_validation.missing_steps)}"
            )

        if plan_validation.optional_steps_skipped:
            lines.append(
                f"- **Optional Steps Skipped:** {', '.join(plan_validation.optional_steps_skipped)}"
            )

        lines.append("")

    # Warnings
    if response.warnings:
        lines.append("### ⚠️ Warnings")
        for warning in response.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    # Errors
    if response.errors:
        lines.append("### 🔴 Errors")
        for error in response.errors:
            lines.append(f"- {error}")
        lines.append("")

    # Raw output preview (first 500 chars if needed)
    if not response.success and response.output and len(response.output) > 0:
        lines.append("### Implementation Output (Preview)")
        preview = response.output[:500]
        if len(response.output) > 500:
            preview += "\n... (truncated)"
        lines.append("```")
        lines.append(preview)
        lines.append("```")
        lines.append("")

    return "\n".join(lines).strip()


def format_error_summary(response: AgentPromptResponse) -> str:
    """Format a concise error summary for Jira comments.

    Args:
        response: AgentPromptResponse with error details

    Returns:
        Brief error summary
    """
    if response.success:
        return "✅ Implementation succeeded"

    error_msg = "❌ Implementation failed"

    if response.validation_status:
        error_msg += f" ({response.validation_status})"

    if response.errors:
        error_msg += f": {response.errors[0]}"
    elif response.output:
        # Use first line of output as error
        first_line = response.output.split("\n")[0][:100]
        error_msg += f": {first_line}"

    return error_msg


def format_metrics_only(response: AgentPromptResponse) -> str:
    """Format only metrics for inline comments.

    Args:
        response: AgentPromptResponse with metrics

    Returns:
        Single-line metrics summary
    """
    metrics = []

    if response.files_changed is not None:
        metrics.append(f"{response.files_changed} files")

    if response.lines_added is not None:
        metrics.append(f"+{response.lines_added} lines")

    if response.lines_removed is not None:
        metrics.append(f"-{response.lines_removed} lines")

    if metrics:
        return " | ".join(metrics)

    return "No metrics available"


def format_validation_report(
    response: AgentPromptResponse, plan_validation=None
) -> str:
    """Format a detailed validation report.

    Args:
        response: AgentPromptResponse with validation data
        plan_validation: Optional plan validation result

    Returns:
        Detailed validation report
    """
    lines = []

    lines.append("## Validation Report")
    lines.append("")

    # Overall Status
    lines.append("### Overall Status")
    status_emoji = "✅" if response.success else "❌"
    lines.append(f"{status_emoji} **{response.validation_status or 'unknown'}**")
    lines.append("")

    # Code Metrics
    lines.append("### Code Changes")
    lines.append(f"| Metric | Value |")
    lines.append("|--------|-------|")

    files = response.files_changed or 0
    lines.append(f"| Files Changed | {files} |")

    added = response.lines_added or 0
    lines.append(f"| Lines Added | {added} |")

    removed = response.lines_removed or 0
    lines.append(f"| Lines Removed | {removed} |")

    lines.append("")

    # Test Results
    if response.test_results:
        lines.append("### Test Results")
        lines.append(response.test_results)
        lines.append("")

    # Issues
    all_issues = []
    if response.errors:
        all_issues.extend([(f"🔴 ERROR", e) for e in response.errors])
    if response.warnings:
        all_issues.extend([(f"⚠️ WARNING", w) for w in response.warnings])

    if all_issues:
        lines.append("### Issues Found")
        for issue_type, issue_text in all_issues:
            lines.append(f"- {issue_type}: {issue_text}")
        lines.append("")

    # Plan Execution if provided
    if plan_validation:
        lines.append("### Plan Execution")
        lines.append(
            f"- Steps: {plan_validation.executed_steps}/{plan_validation.total_steps}"
        )
        if plan_validation.missing_steps:
            lines.append(f"- Missing: {', '.join(plan_validation.missing_steps)}")
        lines.append("")

    return "\n".join(lines).strip()
