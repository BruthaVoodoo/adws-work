# Bug Planning

Create a new plan to resolve a bug in a project using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` section to focus on the right areas.

## Instructions

- IMPORTANT: You're writing a plan to resolve a bug IN this project (not in the ADWS tooling itself) that will improve the codebase's performance and reliability.
- IMPORTANT: The `Bug` describes the issue that will be resolved. Remember we're not resolving the bug, we're creating a plan that will be used to resolve the bug based on the `Plan Format` below.
- You're writing a plan to resolve a bug. It should be thorough and precise so we fix the root cause and prevent regressions.
- Create a plan in the `ai_docs/logs/{adw_id}/phase_plan/` directory with filename: `{issue_number}-plan.md`.
- Use the plan format below to create the plan.
- Research the codebase to understand the bug, reproduce it, and put together a plan to fix it.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to fix the bug.
- Use your reasoning model: THINK HARD about the bug, its root cause, and the steps to fix it properly.
- IMPORTANT: Be surgical with your bug fix. Solve the bug at hand and don't fall off track.
- IMPORTANT: We want the minimal number of changes that will fix and address the bug.
- Don't use decorators. Keep it simple.
- If you need a new library, use your project's package manager and be sure to report it in the `Notes` section of the `Plan Format`.
- Start your research by reading the `README.md` file.

## Relevant Files

Focus on the following areas based on your project:

- `README.md` - Contains the project overview and architecture.
- Source code directories (e.g., `src/`, `app/`, `frontend/`, `backend/`, `lib/`, etc.)
- Test directories (e.g., `tests/`, `test/`, `__tests__/`, `spec/`, etc.)
- Configuration files (e.g., `config/`, `.env.example`, `package.json`, `requirements.txt`, `pyproject.toml`, etc.)

Ignore all other files in the codebase.

## Plan Format

```md
# Bug: <bug name>

## Bug Description
<describe the bug in detail, including symptoms and expected vs actual behavior>

## Problem Statement
<clearly define the specific problem that needs to be solved>

## Solution Statement
<describe the proposed solution approach to fix the bug>

## Steps to Reproduce
<list the exact steps to reproduce the bug>

## Root Cause Analysis
<analyze and explain the root cause of the bug>

## Framework Context
<explain how this bug relates to the project's framework or architecture, including:>
- Which components or modules are affected (if applicable)
- Impact on existing functionality or integrations (if applicable)
- Potential side effects or regressions to consider (if applicable)

## Relevant Files
Use these files to fix the bug:

<find and list the files that are relevant to the bug and describe why they are relevant in bullet points. If there are new files that need to be created to fix the bug, list them in an h3 'New Files' section.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. Use as many h3 headers as needed to fix the bug. Order matters, start with the foundational shared changes required to fix the bug then move on to the specific changes required to fix the bug. Include tests that will validate the bug is fixed with zero regressions.>

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

<list commands you'll use to validate with 100% confidence the bug is fixed with zero regressions. Every command must execute without errors so be specific about what you want to run to validate the bug is fixed with zero regressions. Include commands to reproduce the bug before and after the fix.>

- `<test_command>` - Run all tests to validate the bug is fixed with zero regressions
  (Replace `<test_command>` with your project's configured test command from ADWS/config.yaml)
- Any project-specific health checks or validation commands

## Notes
<optionally list any additional notes or context that are relevant to the bug that will be helpful to the developer>
```

## Variables
${input:issue_number:Paste jira issue number here}
${input:adw_id:Paste ADW ID here}
${input:issue_json:Paste issue JSON here}

## Placeholder Reference

The following placeholders will be replaced with actual Jira issue context:
- `{issue_key}` - The Jira issue key (e.g., "DAI-4")
- `{issue_title}` - The issue title/summary
- `{issue_description}` - The full issue description with requirements
- `{issue_labels}` - Comma-separated labels associated with the issue
- `{issue_state}` - Current state of the issue (e.g., "In Progress")

## Bug

**Issue:** {issue_key}
**Status:** {issue_state}
**Labels:** {issue_labels}

### Bug Title
{issue_title}

### Bug Description
{issue_description}

---

Describe the bug that needs to be fixed based on the issue context above. Include:
- What is the bug?
- When does it occur?
- What is the expected behavior?
- What is the actual behavior?
