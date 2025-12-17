# Jira Story: Standardize adw_review.py Console Phases to Match Build Script

## Summary
Align `adw_review.py` console output phases (Workspace, Commit, Finalize) with `adw_build.py`.

## Description

**Story Format**
As a developer, I want the `adw_review.py` script to display the exact same visual "Phase" markers and structure as `adw_build.py`, so that the CLI experience is consistent across all ADW tools.

**Acceptance Criteria**
- **Preparing Workspace Phase**: Add `rich_console.rule("Preparing Workspace", style="cyan")` before the branch checkout step.
- **Committing Changes Phase**: Add `rich_console.rule("Committing Changes", style="cyan")` before the final review commit (specifically for the final commit outside the resolution loop).
- **Finalizing Git Operations Phase**: Add `rich_console.rule("Finalizing Git Operations", style="cyan")` before the final `finalize_git_operations` call.
- **Completion Phase**: Update the final summary rule to `rich_console.rule("✅ Review Complete", style="green")` (or "❌ Review Failed" in red) to match the "Build Complete" style, replacing the existing "Review Summary" rule.
- **Spinners**: Ensure `rich_console.spinner` is used for checkout, commit, and push operations, mirroring the implementation in `adw_build.py`.

**Traceability To Epic**
- Epic: ADW System Maturation

**Optional (Recommended)**
- **Business Value**: Enforces UI consistency across the ADW toolset, reducing user confusion and improving the professional feel of the CLI.
