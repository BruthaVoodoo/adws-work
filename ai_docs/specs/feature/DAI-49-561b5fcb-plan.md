# Feature: Align adw_review.py Console Output Phases with adw_build.py

## Feature Description
This feature standardizes the console output formatting and phase markers in `adw_review.py` to match the visual structure and user experience of `adw_build.py`. The feature ensures consistent CLI presentation across all ADW tools by implementing identical Rich console rules, spinners, and completion messages. This includes adding "Preparing Workspace", "Committing Changes", "Finalizing Git Operations", and "Completion" phases with proper styling and spinner usage for long-running operations.

## Agent Capability
This feature adds consistent CLI user experience capabilities to the ADW agent system, ensuring that all ADW tools present a unified and professional interface. The agent will provide standardized visual feedback during Git operations, workspace preparation, and build/review processes, improving user comprehension and system reliability perception.

## Problem Statement
Currently, `adw_review.py` and `adw_build.py` have inconsistent console output formatting, which creates a fragmented user experience. Users encounter different visual patterns, phase markers, and completion messages when using different ADW tools. This inconsistency reduces the professional feel of the CLI tools and can cause confusion about operation status and progress. The lack of standardized phase markers makes it difficult for users to understand where they are in the process and troubleshoot issues.

## Solution Statement
Implement a standardized console output system by aligning `adw_review.py` with the existing patterns in `adw_build.py`. This involves adding Rich console rules for each phase (Preparing Workspace, Committing Changes, Finalizing Git Operations, and Completion), implementing spinners for long-running operations, and updating completion messages to match the established format. The solution leverages the existing `utils/console.py` module and Rich library integration within the Strands Agents framework.

## Strands Agents Integration
This feature integrates with the Strands framework by:
- Utilizing the existing `utils/console.py` module that provides Rich console functionality
- Maintaining compatibility with the agent's logging and output systems
- Ensuring console output doesn't interfere with agent communication or multi-agent coordination
- Following the established patterns for CLI tool enhancement within the ADW agent ecosystem
- Preserving existing error handling and operation flow while enhancing visual presentation

## Relevant Files
Use these files to implement the feature:

- `ADW/adw_review.py` - Main file to be modified to align console output with adw_build.py patterns
- `ADW/adw_build.py` - Reference implementation for console output patterns and phase markers
- `ADW/utils/console.py` - Utility module providing Rich console functionality and standardized output methods
- `ADW/tests/test_adw_review.py` - Test file to be updated with new console output validation tests
- `ADW/tests/test_adw_build.py` - Reference for testing patterns and console output validation approaches

### New Files
- `ADW/tests/test_console_consistency.py` - New test file to validate console output consistency between adw_review.py and adw_build.py

## Implementation Plan
### Phase 1: Foundation
Analyze the existing console output patterns in `adw_build.py` and document the exact Rich console rules, spinner implementations, and completion message formats that need to be replicated in `adw_review.py`. Review the `utils/console.py` module to understand available helper functions and ensure proper Rich console integration.

### Phase 2: Core Implementation
Modify `adw_review.py` to add the four required phase markers (Preparing Workspace, Committing Changes, Finalizing Git Operations, and Completion) with identical styling to `adw_build.py`. Implement spinners for checkout, commit, and push operations, and update the final summary rule to match the "Build Complete" style.

### Phase 3: Integration
Validate that the console output changes don't break existing functionality, ensure proper error handling during console operations, and verify that the output maintains readability and professionalism across different terminal environments.

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

### Step 1: Analyze Reference Implementation
- Study the console output patterns in `adw_build.py` to identify exact Rich rule formats, styles, and spinner usage
- Document the specific `rich_console.rule()` calls and their parameters used in each phase
- Identify spinner implementation patterns for long-running Git operations

### Step 2: Update Preparing Workspace Phase
- Add `rich_console.rule("Preparing Workspace", style="cyan")` before the branch checkout step in `adw_review.py`
- Implement spinner for checkout operations using `rich_console.spinner`
- Ensure proper error handling during workspace preparation phase

### Step 3: Update Committing Changes Phase  
- Add `rich_console.rule("Committing Changes", style="cyan")` before the final review commit in `adw_review.py`
- Implement spinner for commit operations to match `adw_build.py` patterns
- Ensure the phase marker is placed specifically for the final commit outside the resolution loop

### Step 4: Update Finalizing Git Operations Phase
- Add `rich_console.rule("Finalizing Git Operations", style="cyan")` before the `finalize_git_operations` call
- Implement spinner for push operations using `rich_console.spinner`
- Maintain existing error handling and operation flow

### Step 5: Update Completion Phase
- Replace existing "Review Summary" rule with `rich_console.rule("✅ Review Complete", style="green")` for successful completion
- Add `rich_console.rule("❌ Review Failed", style="red")` for failed operations
- Ensure completion messages match the "Build Complete" style from `adw_build.py`

### Step 6: Create Unit Tests
- Create tests to validate each phase marker is displayed correctly
- Add tests for spinner implementation during Git operations
- Create tests for completion message formatting in both success and failure cases

### Step 7: Create Integration Tests
- Develop `ADW/tests/test_console_consistency.py` to validate output consistency between tools
- Add tests to verify console output doesn't break existing agent functionality
- Create tests for proper Rich console integration within the Strands framework

### Step 8: Update Existing Tests
- Modify `ADW/tests/test_adw_review.py` to account for new console output patterns
- Add assertions for phase markers in existing test cases
- Ensure all tests pass with the new console output implementation

## Testing Strategy
### Unit Tests
- Test each Rich console rule is called with correct parameters and styling
- Validate spinner implementation for checkout, commit, and push operations
- Test completion message formatting for both success and failure scenarios
- Verify console output doesn't interfere with existing functionality

### Integration Tests
- Test complete adw_review.py execution flow with new console output
- Validate consistency between adw_review.py and adw_build.py console patterns
- Test console output in different terminal environments and configurations
- Ensure proper integration with Strands Agents logging and output systems

### Edge Cases
- Test console output when Git operations fail or encounter errors
- Validate behavior when Rich console is not available or fails to initialize
- Test output formatting with very long branch names or commit messages
- Verify console output doesn't break when running in non-interactive environments

## Acceptance Criteria
- `adw_review.py` displays "Preparing Workspace" phase marker before branch checkout with cyan styling
- "Committing Changes" phase marker appears before final review commit with cyan styling
- "Finalizing Git Operations" phase marker shows before `finalize_git_operations` call with cyan styling
- Completion phase shows "✅ Review Complete" in green for success or "❌ Review Failed" in red for failure
- Spinners are implemented for checkout, commit, and push operations matching `adw_build.py` patterns
- All console output maintains existing functionality and error handling
- Console output is visually identical between `adw_review.py` and `adw_build.py` for equivalent operations
- All existing tests pass with new console output implementation

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

- `pytest tests/ -v` - Run all agent tests to validate the feature works with zero regressions
- `python ADW/adw_review.py --help` - Verify the script still functions correctly after console output changes
- `pytest ADW/tests/test_adw_review.py -v` - Run specific adw_review tests to ensure console changes don't break functionality
- `pytest ADW/tests/test_console_consistency.py -v` - Run new consistency tests between adw_review and adw_build console output
- `python -c "from ADW.utils.console import rich_console; rich_console.rule('Test', style='cyan')"` - Verify Rich console integration works correctly
- `python ADW/adw_build.py --help && python ADW/adw_review.py --help` - Compare help output to ensure both tools maintain consistent behavior

## Notes
- This feature focuses purely on visual consistency and user experience improvement without changing core functionality
- The implementation leverages existing Rich console patterns already established in the codebase
- All console output changes are designed to be backwards compatible and maintain existing error handling
- Future ADW tools should follow the same console output patterns established by this standardization effort
- Consider creating a shared console output utility function for future tools to maintain consistency automatically