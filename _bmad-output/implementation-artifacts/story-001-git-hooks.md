---
id: story-001-git-hooks
title: Git Pre-commit Hook Integration
status: Ready for Dev
priority: High
---

# Story: Git Pre-commit Hook Integration

## Context
ADWS needs to support projects that enforce quality gates via git pre-commit hooks (e.g., husky, lint-staged). Currently, ADWS fails blindly if a hook blocks a commit. We need a workflow that detects these hooks, visualizes their execution, and provides an interactive resolution loop for failures.

## Goals
- Detect presence of git hooks during `adw setup`.
- Configure `has_pre_commit_hooks` in ADWS config.
- Visualize hook execution in ADWS console output.
- Implement an interactive "Fix/Report/Retry" loop when hooks fail.

## Tasks
- [x] **Task 1: Hook Discovery & Config**
  - [x] Update `adw_setup.py` (or equivalent setup logic) to check for `.husky`, `.pre-commit-config.yaml`, or `core.hooksPath`.
  - [x] Add `has_pre_commit_hooks` boolean to `ADWConfig` model and `.adw.yaml`.
  - [x] **Verification:** Run setup in a repo with/without hooks; verify config update.

- [x] **Task 2: Enhanced Commit Operation**
  - [x] Refactor `git_ops.commit_changes` to accept an interactive callback or handle failures more richly.
  - [x] Instead of returning simple bool/str, return a structured `CommitResult` object (success, output, hook_failure_detected).
  - [x] **Verification:** Unit test `commit_changes` with mocked git failures.

- [x] **Task 3: Console Visualization**
  - [x] Update `adw_build.py`, `adw_plan.py`, `adw_review.py` (wherever commits happen) to respect the `has_pre_commit_hooks` flag.
  - [x] If true, display a `rich` section "⚡ Running Pre-commit Hooks..." before committing.
  - [x] **Verification:** Run a workflow phase; verify console output styling.

- [x] **Task 4: Interactive Resolution Loop**
  - [x] Implement the "Fix/Report/Retry" logic in the agent workflow where commits occur.
  - [x] On failure:
    - [x] Parse stderr.
    - [x] Prompt user: (A)ttempt Fix, (R)eport & Abort, (T)ry again.
    - [x] (A) trigger agent to fix issues (limit 3 loops).
    - [x] (R) write failure log to `ai_docs/logs/...`.
  - [x] **Verification:** Simulate a lint failure; verify prompt and fix loop behavior.

## File List
- scripts/adw_modules/config.py
- scripts/adw_modules/git_ops.py
- scripts/adw_modules/rich_console.py
- scripts/adw_setup.py
- scripts/adw_build.py
- scripts/adw_plan.py
- scripts/adw_review.py
- scripts/adw_test.py
- scripts/adw_modules/hook_resolution.py (New)
- scripts/adw_modules/data_types.py

## Dev Agent Record
- [ ] Story Created
- Task 1 Complete: Implemented hook detection in `adw_setup.py` and added `has_pre_commit_hooks` to `config.py`. Added unit tests in `tests/test_hooks_detection.py`.
- Task 2 Complete: Refactored `commit_changes` to return `CommitResult`. Created unit tests in `tests/test_git_ops_commit.py`.
- Task 3 Complete: Updated all ADW scripts (`plan`, `build`, `test`, `review`) to respect `has_pre_commit_hooks` flag and handle `CommitResult`.
- Task 4 Complete: Implemented interactive resolution loop in `scripts/adw_modules/hook_resolution.py` and integrated it into all scripts. Added unit tests in `tests/test_hook_resolution.py`.

## Change Log
- **2026-02-03**: Implemented Git Pre-commit Hook Integration.
  - Added `has_pre_commit_hooks` configuration detected via `adw setup`.
  - Refactored `commit_changes` to return structured `CommitResult`.
  - Added interactive "Fix/Retry/Abort" loop for hook failures using OpenCode agent.
  - Updated all workflow scripts to support the new commit logic and visualization.

## Status
review
