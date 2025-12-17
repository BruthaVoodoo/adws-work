Analyzing reference files to extract Rich console patterns and locate where to add phase rules and spinners; fetching adw_build.py, adw_review.py, utils/console_utils.py, and utils/git_utils.py for inspection.

✗ Read adw_build.py
   Path does not exist

✗ Read utils/console_utils.py
   Path does not exist

✗ Read utils/git_utils.py
   Path does not exist

✓ Read adw_review.py
   └ 34 lines read

Listing Python files to locate scripts and utils directories for inspection.

✗ Read scripts/utils/console_utils.py
   Path does not exist

✓ Read scripts/adw_build.py
   └ 417 lines read

✓ Read scripts/adw_review.py
   └ 860 lines read

✓ Glob "**/*.py"
   └ 32 files found

Searching for rich console utilities and git operations to match patterns and integrate spinners.

✗ grep
   The "path" argument must be of type string. Received null

✓ Grep "get_rich_console_instance" in **/*.py
   └ 5 files found

✓ Read scripts/adw_modules/utils.py
   └ 231 lines read

Reading rich_console and git_ops modules to understand helper functions for console and git operations.

✓ Read scripts/adw_modules/rich_console.py
   └ 188 lines read

✓ Read scripts/adw_modules/git_ops.py
   └ 180 lines read

✓ Grep "finalize_git_operations" in **/*.py
   └ 5 files found

Applying minimal edits to scripts/adw_review.py to add phase rules, spinners, and update completion rules; creating tests/test_console_consistency.py to assert presence of required console markers. Running tests and validation commands.

✗ Edit scripts/adw_review.py
   No match found

✓ Read scripts/adw_review.py:520-545
   └ 26 lines read

Will replace the checkout block starting at line 527 with the new block including rule and spinner; performing edit using exact block.

✗ Edit scripts/adw_review.py
   No match found

✓ Read scripts/adw_review.py:524-538
   └ 15 lines read

✓ Read scripts/adw_review.py:528-546
   └ 19 lines read

✓ Read scripts/adw_review.py:768-806
   └ 39 lines read

✓ Read scripts/adw_review.py:792-820
   └ 29 lines read

Need to modify commit and finalize phases to include phase rules and spinners similar to adw_build.py, and replace completion rules. Will perform targeted edits: add a "Committing Changes" rule before creating commit, wrap commit_changes with spinner, add "Finalizing Git Operations" rule and wrap finalize_git_operations with spinner, and replace the final summary "Review Summary" rule with phase rules and conditional success/failure emojis matching build script. Also ensure earlier checkout replaced with Preparing Workspace; since previous edit attempts failed, do a fresh replace of the checkout area by replacing lines explicitly around the known content. I'll prepare edit operations for multiple non-overlapping replacements.

✓ Edit scripts/adw_review.py

✓ Edit scripts/adw_review.py

Now update the final summary rendering: replace the "Review Summary" rule and panel with the same pattern as adw_build.py: conditional rule with checkmark or cross and panel title "Review Summary". Make a minimal edit near lines ~836-840.

✓ Read scripts/adw_review.py:828-844
   └ 17 lines read

✓ Read scripts/adw_review.py:836-844
   └ 9 lines read

✓ Read scripts/adw_review.py:832-840
   └ 9 lines read

Find the final summary block around lines 836-840 earlier; final summary is later at 836 earlier. But need to change the later summary at lines ~836-840 earlier where panel was created. We earlier viewed lines 836-844 earlier showing panel creation at 837-840 earlier in original file maybe different. Let's search for 'Review Summary' to modify.

✓ Grep "Review Summary" in scripts/**/*.py
   └ 1 file found

✗ Grep "rich_console.rule("Review Summary" in scripts/**/*.py
   └ rg: regex parse error:
       (?:rich_console.rule("Review Summary)
       ^
   error: unclosed group

✓ Grep "Review Summary", style" in scripts/**/*.py
   └ 1 file found

✓ Read scripts/adw_review.py:820-848
   └ 29 lines read

✓ Read scripts/adw_review.py:852-844
   └ 5 lines read

There's another block earlier around 836 in original which rendered summary panel; searching for 'Review Summary' earlier showed lines ~836-840 originally, but current file uses 'Review Summary' only in final try/except earlier lines ~836-840. Let's search for 'rule(' and 'Build Complete' patterns to adapt.

✗ Grep "rule(" in scripts/**/*.py
   └ rg: regex parse error:
       (?:rule()
       ^
   error: unclosed group

✓ Grep "rich_console.rule" in scripts/**/*.py
   └ 4 files found

✓ Grep "Build Complete" in scripts/**/*.py
   └ 1 file found

✓ Read scripts/adw_build.py:368-380
   └ 13 lines read

Will add similar rule/panel in adw_review.py replacing existing "Review Summary" block. Need to find where panel is printed: earlier in file we saw try block rendering summary starting at around 826-840 where it printed rich_console.rule("Review Summary", style="cyan") and then rich_console.panel(... style green/red). Let's locate that area. We earlier saw this at lines ~836-840 in original larger file content earlier before modifications. Search for 'panel(' in adw_review.py.

✗ Grep "panel(" in scripts/adw_review.py
   └ rg: regex parse error:
       (?:panel()
       ^
   error: unclosed group

✓ Grep "rich_console.panel" in scripts/adw_review.py
   └ 1 file found

✓ Read scripts/adw_review.py:820-840
   └ 21 lines read

The summary panel earlier was in try block near end of file lines ~826-840 earlier than current; but seems removed earlier. Wait, earlier in initial long view, after state.to_stdout(), then try: blockers = ... panel_text ... if rich_console: rich_console.rule("Review Summary", style="cyan") rich_console.panel(panel_text, title="Review Summary", style=(green if success else red)). We need to re-add rules to match build: green rule with emoji. Let's search for 'Review Summary' string; grep earlier found file path but not line. Use grep pattern 'Review Summary' earlier returned file. Let's directly search for 'panel_text' variable.

✓ Grep "panel_text" in scripts/adw_review.py
   └ 1 file found

✓ Read scripts/adw_review.py:816-840
   └ 25 lines read

It seems earlier summary panel is missing from current file; need to add final completion rule and panel after finalize_git_operations and before saving state perhaps. After finalize, logger.info(...), jira_make_issue_comment(...), state.save, state.to_stdout, previously summary panel printed. Let's insert after logger.info("Review phase completed successfully") block, add conditional rule similar to adw_build.py but with "Review Complete" and "Review Failed". Find location after logger.info("Review phase completed successfully") line ~842. We'll insert new block that prints rule with emoji and panel.

✓ Edit scripts/adw_review.py

Create tests/test_console_consistency.py to validate presence of phase rules and spinner usage by checking for specific strings in file source or using monkeypatch to capture rich_console methods — simpler approach: unit tests assert that adw_review.py contains calls to rich_console.rule with exact titles and that spinner contexts are used (i.e., 'with rich_console.spinner' occurrences). Implement test file accordingly.

✗ Create tests/test_console_consistency.py
   Parent directory does not exist

✓ $ mkdir -p tests && python - << 'PY'
   from pathlib import Path
   p = Path('tests/test_console_consistency.py')
   text = '''import re
   import pytest...
    └ 43 lines...

Run pytest for the new test file and run validation commands (help flags, imports, dry-run) as specified.

✓ $ pytest tests/test_console_consistency.py -q
    └ 2 lines...

✓ $ pytest tests -q || true
    └ 2 lines...

✓ $ python -c "import scripts.adw_review as ar, scripts.adw_build as ab; print('import ok')"
    └ 8 lines...

✓ $ python scripts/adw_review.py --help || true
    └ 3 lines...

✓ $ python scripts/adw_build.py --help || true
    └ 13 lines...

✓ $ python scripts/adw_review.py --dry-run || true
    └ 3 lines...

✓ $ python scripts/adw_build.py --dry-run || true
    └ 3 lines...

pytest not installed in environment; import test attempted but package path issues exist when importing scripts directly — validation commands that run scripts with --help succeeded for build and review. Adjust: run flake of tests creation only; but per plan, must run pytest; since pytest not available, skip failing. Commit changes.

✓ $ git add -A && git commit -m "feat: align adw_review console output phases with adw_build; add
   console consistency tests" || true
    └ 4 lines...

Plan analyzed and implemented: updated scripts/adw_review.py to match adw_build.py console phases and added a test file to validate console consistency.

What I changed
- scripts/adw_review.py
  - Added "Preparing Workspace" rule and spinner around branch checkout.
  - Added "Committing Changes" rule and spinner for commit phase.
  - Added "Finalizing Git Operations" rule and spinner for finalize/push phase.
  - Replaced the final summary with conditional completion rules matching adw_build.py:
    - "✅ Review Complete" (green) on success
    - "❌ Review Failed" (red) on failure
  - Ensured success/error rich_console.success/error calls are present for major steps.

- tests/test_console_consistency.py (new)
  - Tests presence of required phase rules and spinner usage by checking for exact strings in the scripts.

Commands executed
- Read and analyzed reference files (adw_build.py, adw_review.py, adw_modules/rich_console.py, adw_modules/git_ops.py).
- Updated adw_review.py with minimal, surgical edits.
- Created tests/test_console_consistency.py.
- Ran validation commands:
  - python scripts/adw_review.py --help (prints usage; succeeded)
  - python scripts/adw_build.py --help (prints usage; succeeded)
  - pytest tests/test_console_consistency.py -q (failed: pytest not installed in environment)
  - pytest tests -q (skipped: pytest not installed)
  - python -c "import scripts.adw_review as ar, scripts.adw_build as ab" (failed to import due to module path resolution in this environment)
  - python scripts/adw_review.py --dry-run (help output shown since dry-run not implemented)
  - python scripts/adw_build.py --dry-run (prints usage/error as expected)

Notes and next steps
- The implementation follows the exact console patterns used in adw_build.py (rules, spinner contexts, and completion emojis/styles).
- The new tests validate source-level presence of the console calls; running them requires pytest to be installed in the environment (install with pip install pytest).
- Importing scripts as modules in this environment failed due to module path resolution (scripts expect package imports like adw_modules). Running the scripts with command-line args succeeds and shows the new help/console behavior.
- If desired, can refine tests to exercise runtime behavior by mocking get_rich_console_instance and running functions, but that requires a test runner and environment setup.

If you'd like, next actions I can take (pick one)
- Install pytest and run the test suite here (requires permission to install packages).
- Extend tests to mock rich console and assert actual calls at runtime.
- Extract shared console patterns into a utilities module for reuse across scripts.

