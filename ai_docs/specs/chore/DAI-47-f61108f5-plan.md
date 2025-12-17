# Chore: Refine adw_review.py console output to strictly align with plan/build/test scripts

## Chore Description
This chore involves standardizing the console output formatting of the `adw_review.py` script to match the visual structure and user experience of other ADW workflow scripts (plan, build, test). The current implementation lacks consistent headers, phase markers, spinners, and summary formatting that are present in the other scripts, creating a fragmented CLI experience for developers.

The chore will enhance the developer experience by:
- Adding a consistent blue startup header rule
- Implementing cyan phase marker rules for major workflow stages
- Wrapping long-running operations in spinners for better feedback
- Improving visibility of the resolution loop with clear formatting
- Standardizing the final summary panel with consistent styling and metadata

This improves maintainability by creating a unified visual language across all ADW scripts, reducing cognitive load when switching between different workflow phases.

## Relevance to Agent Framework
This chore enhances the ADW (AI-Driven Workflow) system which appears to be built on the Strands Agents framework. Consistent CLI output formatting is crucial for agent-based workflows as it:
- Provides clear feedback during automated processes
- Maintains user trust through predictable visual patterns
- Supports debugging and monitoring of agent operations
- Ensures the review phase integrates seamlessly with other workflow phases in the agent pipeline

The standardization directly supports the agent's ability to provide reliable, user-friendly automation while maintaining compatibility with the overall ADW system architecture.

## Relevant Files
Use these files to resolve the chore:

- `adw_review.py` - The main script that needs console output refinement to match other ADW scripts
- `adw_plan.py` - Reference implementation for consistent header, phase marker, and spinner patterns
- `adw_build.py` - Reference implementation for build summary styling and console formatting
- `adw_test.py` - Reference implementation for test summary styling and spinner usage
- `ADW/shared/console.py` or similar - Shared console utilities and rich_console instance used across ADW scripts
- `requirements.txt` or `pyproject.toml` - To verify rich library dependency for console formatting

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyze Current Console Formatting Patterns
- Examine `adw_plan.py`, `adw_build.py`, and `adw_test.py` to identify the exact formatting patterns used
- Document the specific rich console methods, styles, and structure for headers, phase markers, spinners, and summaries
- Identify the shared console utilities and imports used across these scripts

### Step 2: Review Current adw_review.py Implementation
- Analyze the current `adw_review.py` script structure and console output points
- Identify where the missing elements should be added: startup header, phase markers, spinners, and summary formatting
- Map the current workflow phases to the required cyan rule markers

### Step 3: Implement Initial Header
- Add the blue startup rule `rich_console.rule(f"ADW Review - Issue {issue_number}", style="blue")` immediately after `main()` function start
- Ensure proper rich console import and setup matches other ADW scripts

### Step 4: Add Phase Marker Rules
- Implement cyan rules for "Reviewing Implementation" phase before review execution
- Add "Resolving Issues" cyan rule when entering the resolution loop
- Add "Committing Results" cyan rule before git commit operations
- Add "Finalizing Git Operations" cyan rule for final git operations

### Step 5: Implement Spinner Feedback
- Wrap the `run_review` execution in a spinner with text "Running AI review analysis..."
- Add spinners around patch creation and implementation steps within the resolution loop
- Ensure spinners properly handle success/failure states

### Step 6: Enhance Resolution Loop Visibility
- Implement `rich_console.step()` or clear formatting to distinguish between multiple issues being resolved
- Add progress indicators for loop iterations if multiple issues are processed

### Step 7: Standardize Final Summary Panel
- Modify the final "Review Summary" panel to match "Build Summary" and "Test Summary" styling
- Implement consistent Green/Red styling based on review results
- Add consistent metadata fields matching other summary panels

### Step 8: Test Console Output Integration
- Run `adw_review.py` with various scenarios to verify visual consistency
- Compare output side-by-side with other ADW scripts to ensure seamless visual experience

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

- `python adw_review.py --help` - Verify script still functions and help output is clean
- `python adw_review.py [test-issue-number]` - Run actual review to validate all console formatting appears correctly
- `pytest tests/ -v` - Run all agent tests to validate the chore is complete with zero regressions
- `python -c "import adw_review; print('Import successful')"` - Verify no import errors from console formatting changes
- `python adw_plan.py --help && python adw_build.py --help && python adw_test.py --help` - Ensure other scripts still work (regression check)

## Notes
- Pay close attention to the exact rich console styling patterns (colors, formatting) used in existing scripts to ensure pixel-perfect consistency
- The resolution loop visibility enhancement may require conditional formatting based on whether multiple issues are being processed
- Consider adding configuration options for console output verbosity if the enhanced formatting becomes too verbose for automated scenarios
- Ensure all console formatting changes are backwards compatible and don't break any existing automation that may parse the output