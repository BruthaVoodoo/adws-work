# Jira Story: Refine adw_review.py Console Output Alignment

## Summary
Refine adw_review.py console output to strictly align with plan/build/test scripts.

## Description

**Story Format**
As a developer, I want the `adw_review.py` script to have the exact same visual structure (headers, phase markers, spinners) as the other ADW scripts, so that the CLI experience is completely seamless and predictable.

**Acceptance Criteria**
- **Initial Header**: Add the missing blue start-up rule: `rich_console.rule(f"ADW Review - Issue {issue_number}", style="blue")` immediately after `main()` start.
- **Phase Markers**: Add cyan rules (`rich_console.rule(..., style="cyan")`) for:
    - "Reviewing Implementation"
    - "Resolving Issues" (if entering resolution loop)
    - "Committing Results"
    - "Finalizing Git Operations"
- **Spinners**:
    - Wrap the `run_review` execution in a spinner (e.g., "Running AI review analysis...").
    - Wrap the patch creation and implementation steps within the resolution loop in spinners.
- **Resolution Loop Visibility**: Use `rich_console.step()` or clear formatting to distinguish between multiple issues being resolved in the loop.
- **Final Summary**: Ensure the final `Review Summary` panel matches the style of `Build Summary` and `Test Summary` (Green/Red styling, consistent metadata fields).

**Traceability To Epic**
- Epic: ADW System Maturation

**Optional (Recommended)**
- **Business Value**: Eliminates visual context switching costs for developers moving between workflow phases.
