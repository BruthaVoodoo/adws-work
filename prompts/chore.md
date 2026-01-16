# Chore Planning

Create a new plan to resolve a chore in a project using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` section to focus on the right areas.

## Instructions

- IMPORTANT: You're writing a plan to resolve a chore in this project that will add value to the codebase (e.g., refactoring, dependency updates, architecture improvements).
- IMPORTANT: The `Chore` describes the chore that will be resolved. Remember we're not resolving the chore, we're creating a plan that will be used to resolve the chore based on the `Plan Format` below.
- You're writing a plan to resolve a chore. It should be simple but thorough and precise so we don't miss anything or waste time with any second round of changes.
- Create a plan in `ai_docs/logs/{adw_id}/phase_plan/` directory with filename: `{issue_number}-plan.md`.
- Use the plan format below to create the plan.
- Research the codebase and put together a plan to accomplish the chore.
- IMPORTANT: Replace every <placeholder> in the `Plan Format` with the requested value. Add as much detail as needed to accomplish the chore.
- Use your reasoning model: THINK HARD about the plan and the steps to accomplish the chore.
- Start your research by reading the `README.md` file.

## Relevant Files

Focus on the following areas based on your project:

- `README.md` - Contains the project overview and instructions.
- Source code directories (e.g., `src/`, `app/`, `frontend/`, `backend/`, `lib/`, etc.)
- Test directories (e.g., `tests/`, `test/`, `__tests__/`, `spec/`, etc.)
- Configuration files (e.g., `config/`, `.env.example`, `package.json`, `requirements.txt`, `pyproject.toml`, etc.)
- Dependency files (e.g., `requirements.txt`, `package.json`, `Cargo.toml`, `go.mod`, etc.)

Ignore all other files in the codebase.

## Placeholder Reference

The following placeholders will be replaced with actual Jira issue context:
- `{issue_key}` - The Jira issue key (e.g., "DAI-4")
- `{issue_title}` - The issue title/summary
- `{issue_description}` - The full issue description with requirements
- `{issue_labels}` - Comma-separated labels associated with the issue
- `{issue_state}` - Current state of the issue (e.g., "In Progress")

## Plan Format

```md
# Chore: <chore name>

## Chore Description
<describe the chore in detail>

## Relevance to Project
<explain how this chore relates to maintaining or improving this project>

## Relevant Files
Use these files to resolve the chore:

<find and list the files that are relevant to the chore and describe why they are relevant in bullet points. If there are new files that need to be created to accomplish the chore, list them in an h3 'New Files' section.>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. Use as many h3 headers as needed to accomplish the chore. Order matters, start with foundational shared changes required to accomplish the chore then move on to the specific changes required to accomplish the chore. Your last step should be running the `Validation Commands` to validate the chore is complete with zero regressions.>

## Validation Commands
Execute every command to validate the chore is complete with zero regressions.

<list commands you'll use to validate with 100% confidence the chore is complete with zero regressions. Every command must execute without errors so be specific about what you want to run to validate the chore is complete with zero regressions. Don't validate with curl commands.>

- `<test_command>` - Run all tests to validate the chore is complete with zero regressions
  (Replace `<test_command>` with your project's configured test command from ADWS/config.yaml)

## Notes
<optionally list any additional notes or context that are relevant to the chore that will be helpful to the developer>
```

## Chore

**Issue:** {issue_key}
**Status:** {issue_state}
**Labels:** {issue_labels}

### Chore Title
{issue_title}

### Chore Description
{issue_description}

---

Describe the chore that needs to be resolved based on the issue context above. Include:
- What is the chore?
- Why is it needed?
- What will be improved or maintained?

Then, generate the COMPLETE implementation plan following the exact `Plan Format` specified above.

**CRITICAL: Output ONLY the complete markdown plan starting with `# Chore:` as the first line. Include every section from Chore Description through Notes. Do not include any summary, introduction, or explanation text - only the markdown plan itself.**
