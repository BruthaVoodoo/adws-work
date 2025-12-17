# Feature: Align `adw_review.py` console output phases (Workspace, Commit, Finalize) with `adw_build.py`

## Feature Description
This feature standardizes the visual console output phases in `adw_review.py` to match the exact same structure and styling as `adw_build.py`. The feature adds consistent visual phase markers using Rich console rules, spinners, and completion status indicators across all ADW CLI tools. This creates a unified user experience where developers see the same professional phase-based output structure regardless of which ADW tool they're using (build, review, etc.).

## Agent Capability
This feature adds a standardized console output capability to the ADW agent system, enabling consistent user interface patterns across all CLI tools. The agent will be able to provide clear visual feedback during multi-phase operations with professional styling, progress indicators, and status reporting that matches across different tool workflows.

## Problem Statement
Currently, `adw_review.py` and `adw_build.py` have inconsistent console output formatting and phase presentation. This creates a fragmented user experience where developers encounter different visual styles, phase markers, and completion indicators depending on which ADW tool they use. This inconsistency reduces the professional feel of the CLI toolset and can cause user confusion about operation status and progress.

## Solution Statement
Implement consistent Rich console formatting in `adw_review.py` that mirrors the exact phase structure used in `adw_build.py`. This includes adding cyan-styled phase rules for "Preparing Workspace", "Committing Changes", and "Finalizing Git Operations", along with green/red completion status rules. The solution will also ensure spinners are used consistently for long-running operations like checkout, commit, and push operations, creating a unified visual language across the ADW toolset.

## Strands Agents Integration
This feature integrates with the Strands framework by:
- Enhancing the console output capabilities of ADW agent tools to provide consistent user feedback
- Maintaining compatibility with existing agent workflows and handlers
- Supporting the agent's ability to provide clear status updates during multi-phase operations
- Ensuring the visual improvements don't interfere with the underlying agent processing logic
- Following the existing patterns established in the ADW agent architecture for UI consistency

## Relevant Files
Use these files to implement the feature:

- `adw_review.py` - Main file that needs console output alignment, requires adding phase rules and spinners to match `adw_build.py` structure
- `adw_build.py` - Reference implementation that contains the target console output patterns to replicate in the review script
- `utils/console_utils.py` - Contains shared console utilities and Rich console instance that both scripts should use consistently
- `utils/git_utils.py` - Contains git operations that need spinner integration during checkout, commit, and push operations

### New Files
- `tests/test_console_consistency.py` - New test file to validate console output consistency between adw_review.py and adw_build.py

## Implementation Plan
### Phase 1: Foundation
Analyze the existing console output patterns in `adw_build.py` to understand the exact Rich console rules, styling, and spinner usage that needs to be replicated. Document the specific phase markers, colors, and timing of when each visual element appears in the build workflow.

### Phase 2: Core Implementation
Modify `adw_review.py` to add the four required phase rules (Preparing Workspace, Committing Changes, Finalizing Git Operations, and Completion) with proper cyan and green/red styling. Integrate spinners for git operations and update the final summary rule to match the "Build Complete" pattern.

### Phase 3: Integration
Test the updated console output in `adw_review.py` to ensure it matches `adw_build.py` exactly, validate that all git operations show appropriate spinners, and confirm the visual consistency across both tools without breaking existing functionality.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyze Reference Implementation
- Study the exact console output patterns in `adw_build.py` 
- Document the specific Rich console rule calls, styling parameters, and spinner usage
- Identify the precise timing and placement of each phase marker in the build workflow
- Note the completion status formatting (green success, red failure patterns)

### Step 2: Create Console Output Tests
- Create `tests/test_console_consistency.py` to validate console output patterns
- Add tests that capture and compare console output between build and review scripts
- Implement test helpers to verify Rich console rule calls and styling
- Add tests for spinner usage during git operations

### Step 3: Add Preparing Workspace Phase
- Locate the branch checkout step in `adw_review.py`
- Add `rich_console.rule("Preparing Workspace", style="cyan")` before the checkout operation
- Ensure the spinner is properly used during the checkout process
- Test that the workspace preparation phase displays correctly

### Step 4: Add Committing Changes Phase  
- Identify the final review commit location (outside the resolution loop) in `adw_review.py`
- Add `rich_console.rule("Committing Changes", style="cyan")` before the final commit
- Integrate spinner usage for the commit operation
- Verify the commit phase appears at the correct workflow stage

### Step 5: Add Finalizing Git Operations Phase
- Locate the `finalize_git_operations` call in `adw_review.py`
- Add `rich_console.rule("Finalizing Git Operations", style="cyan")` before the finalize call
- Ensure spinners are used for push operations within the finalize function
- Test that the finalizing phase displays before git cleanup

### Step 6: Update Completion Phase
- Replace the existing "Review Summary" rule in `adw_review.py`
- Implement conditional completion rules: `rich_console.rule("✅ Review Complete", style="green")` for success
- Add `rich_console.rule("❌ Review Failed", style="red")` for failure cases
- Match the exact styling and emoji usage from `adw_build.py`

### Step 7: Validate Spinner Integration
- Audit all git operations in `adw_review.py` for consistent spinner usage
- Ensure checkout, commit, and push operations all show spinners
- Match the spinner timing and messaging patterns from `adw_build.py`
- Test spinner behavior during both successful and failed operations

### Step 8: Integration Testing
- Run both `adw_review.py` and `adw_build.py` side-by-side to compare output
- Validate that phase markers appear in the same visual style
- Confirm completion status formatting matches exactly
- Test error scenarios to ensure consistent failure reporting

## Testing Strategy
### Unit Tests
- Test that each phase rule is called with correct parameters (text and style)
- Validate that spinners are properly initialized and used for git operations
- Test completion rule selection logic (success vs failure scenarios)
- Verify console output formatting matches between scripts

### Integration Tests
- End-to-end testing of `adw_review.py` to ensure phase markers appear at correct workflow stages
- Cross-validation testing comparing console output between `adw_review.py` and `adw_build.py`
- Test git operation scenarios to validate spinner integration
- Workflow testing to ensure visual consistency doesn't break existing functionality

### Edge Cases
- Test console output during git operation failures (checkout, commit, push errors)
- Validate phase marker behavior when operations are interrupted
- Test console formatting with different terminal widths and capabilities
- Ensure proper cleanup of spinners and rules during error scenarios

## Acceptance Criteria
- `adw_review.py` displays "Preparing Workspace" phase rule in cyan before branch checkout
- "Committing Changes" phase rule appears in cyan before the final review commit
- "Finalizing Git Operations" phase rule shows in cyan before `finalize_git_operations`
- Completion phase shows "✅ Review Complete" in green for success or "❌ Review Failed" in red for failure
- All git operations (checkout, commit, push) use Rich console spinners consistently
- Console output visual structure matches `adw_build.py` exactly
- No existing functionality is broken by the console output changes
- All tests pass and validate the consistent console formatting

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `python adw_review.py --help` - Verify the script still functions and displays help correctly
- `python adw_build.py --help` - Confirm build script remains unaffected
- `pytest tests/test_console_consistency.py -v` - Run new console consistency tests
- `pytest tests/ -v` - Run all existing tests to validate zero regressions
- `python -c "import adw_review; import adw_build"` - Verify both scripts can be imported without errors
- `python adw_review.py --dry-run` - Test console output in dry-run mode if available
- `python adw_build.py --dry-run` - Compare console output patterns between scripts

## Notes
- This feature focuses purely on console output formatting and should not modify any underlying business logic
- The Rich console library is already in use by the codebase, so no new dependencies are required
- Consider extracting common console patterns into `utils/console_utils.py` for better maintainability
- Future ADW tools should follow this same phase-based console output pattern for consistency
- The feature supports the ADW System Maturation epic by improving the professional quality of the CLI toolset
- Monitor performance impact of additional console formatting, though Rich is generally performant