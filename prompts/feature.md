# Feature Planning

Create a new plan to implement a new feature in a project using the exact specified markdown `Plan Format`. Follow the `Instructions` to create the plan and use the `Relevant Files` section to focus on the right areas.

## Instructions

- IMPORTANT: You're writing a plan to implement a new feature or capability in this project that will add value to the codebase.
- IMPORTANT: The `Feature` describes the feature that will be implemented. Remember we're not implementing a new feature, we're creating a plan that will be used to implement the feature based on the `Plan Format` below.
- OUTPUT the complete plan as markdown following the exact `Plan Format` below.
- Replace every <placeholder> in the `Plan Format` with actual values. Add as much detail as needed to implement the feature successfully.
- Use your reasoning model: THINK HARD about the feature requirements, design, and implementation approach.
- Follow existing patterns and conventions in the codebase. Don't reinvent the wheel.
- Design for extensibility and maintainability within the project's framework.
- If you need a new library, use your project's package manager and be sure to report it in the `Notes` section of the `Plan Format`.
- Don't use decorators. Keep it simple.
- Start your research by reading the `README.md` file.

## Relevant Files

Focus on the following areas based on your project:

- `README.md` - Contains project overview and architecture.
- Source code directories (e.g., `src/`, `app/`, `frontend/`, `backend/`, `lib/`, etc.)
- Test directories (e.g., `tests/`, `test/`, `__tests__/`, `spec/`, etc.)
- Configuration files (e.g., `config/`, `.env.example`, `package.json`, `requirements.txt`, `pyproject.toml`, etc.)

Ignore all other files in the codebase.

## Plan Format

```md
# Feature: <feature name>

## Feature Description
<describe the feature in detail, including its purpose and value to the project>

## Feature Capability
<describe what new capability this feature adds to the project>

## Problem Statement
<clearly define the specific problem or opportunity this feature addresses>

## Solution Statement
<describe the proposed solution approach and how it integrates with the project>

## Framework Integration
<describe how this feature integrates with the project's framework, including:>
- Dependencies or libraries that need to be integrated (if applicable)
- API contracts or interfaces to implement (if applicable)
- Configuration changes needed (if applicable)
- Integration with existing services or components (if applicable)

## Relevant Files
Use these files to implement the feature:

<find and list the files that are relevant to the feature and describe why they are relevant in bullet points. If there are new files that need to be created to implement the feature, list them in an h3 'New Files' section.>

## Implementation Plan
### Phase 1: Foundation
<describe the foundational work needed before implementing the main feature>

### Phase 2: Core Implementation
<describe the main implementation work for the feature>

### Phase 3: Integration
<describe how the feature will integrate with existing functionality>

## Step by Step Tasks
IMPORTANT: Execute every step in order, top to bottom.

<list step by step tasks as h3 headers plus bullet points. Use as many h3 headers as needed to implement the feature. Order matters, start with the foundational shared changes required then move on to the specific implementation. Include creating tests throughout the implementation process.>

## Testing Strategy
### Unit Tests
<describe unit tests needed for the feature>

### Integration Tests
<describe integration tests needed to ensure the feature works with the project's framework>

### Edge Cases
<list edge cases that need to be tested>

## Acceptance Criteria
<list specific, measurable criteria that must be met for the feature to be considered complete>

## Validation Commands
Execute every command to validate the feature works correctly with zero regressions.

<list commands you'll use to validate with 100% confidence the feature is implemented correctly with zero regressions. Every command must execute without errors so be specific about what you want to run to validate the feature works as expected. Include commands to test the feature end-to-end.>

- `<test_command>` - Run all tests to validate the feature works with zero regressions
  (Replace `<test_command>` with your project's configured test command from ADWS/config.yaml)
- Any project-specific validation or deployment checks

## Notes
<optionally list any additional notes, future considerations, or context that are relevant to the feature that will be helpful to the developer>
```

## Placeholder Reference

The following placeholders will be replaced with actual Jira issue context:
- `{issue_key}` - The Jira issue key (e.g., "DAI-4")
- `{issue_title}` - The issue title/summary
- `{issue_description}` - The full issue description with requirements
- `{issue_labels}` - Comma-separated labels associated with the issue
- `{issue_state}` - Current state of the issue (e.g., "In Progress")

## Feature

**Issue:** {issue_key}
**Status:** {issue_state}
**Labels:** {issue_labels}

### Feature Title
{issue_title}

### Feature Description
{issue_description}

---

Describe the feature that needs to be implemented based on the issue context above. Include:
- What is the feature?
- What problem does it solve?
- What new capability does it add to the project?
- Who will benefit from this feature?

Then, generate the COMPLETE implementation plan following the exact `Plan Format` specified above.

**CRITICAL: Output ONLY the complete markdown plan starting with `# Feature:` as the first line. Include every section from Feature Description through Notes. Do not include any summary, introduction, or explanation text - only the markdown plan itself.**
