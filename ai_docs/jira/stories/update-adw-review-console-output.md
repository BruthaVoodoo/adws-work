# Jira Story: Update adw_review.py Console Output Styling

## Summary
Update adw_review.py console output to match ADW styling standards using Rich.

## Description

**Story Format**
As a developer using ADW, I want the `adw_review.py` script to use consistent rich console output and coloring, so that the user experience is uniform across all workflow steps.

**Acceptance Criteria**
- `adw_review.py` utilizes the `rich` library for console output instead of standard print statements.
- Log messages, headers, spinners, and panels match the visual style of `adw_plan.py`, `adw_build.py`, and `adw_test.py`.
- Review results (pass/fail, number of issues found) are displayed in a formatted summary panel at the end of execution.
- Error messages are displayed with appropriate `rich` error styling.

**Traceability To Epic**
- Epic: ADW System Maturation (see `ai_docs/jira/epics/adw-system-maturation.md`)

**Optional (Recommended)**
- **Business Value**: Improves developer experience and reduces cognitive load by providing consistent and readable visual feedback during the review process.
