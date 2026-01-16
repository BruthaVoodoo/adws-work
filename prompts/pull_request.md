# Pull Request Generation

Generate a pull request title and description for completed work.

**CRITICAL: Your ENTIRE response must be ONLY a valid JSON object. NO markdown, NO code blocks, NO explanations.**

## JSON Object Requirements

Create a JSON object with exactly these two fields:
- "title" - A concise PR title (max 80 characters)
- "description" - A detailed description explaining the changes

The description must include:
- Summary of what was implemented
- Link to Jira issue: {issue_number}
- Link to plan file: {plan_file}
- Key technical decisions

## Context

- Branch Name: {branch_name}
- Jira Issue: {issue_number}
- Plan File: {plan_file}
- Workflow ID: {adw_id}

## Valid Output Example

{"title": "DAI-4: Implement user authentication module", "description": "Implements user authentication with JWT tokens and secure password hashing.\\n\\nChanges:\\n- Added authentication endpoints to API\\n- Implemented login and registration functionality\\n- Added password hashing with bcrypt\\n- Added JWT token generation and validation\\n- Updated database schema with users table\\n\\nLinks:\\n- JIRA Issue: DAI-4\\n- Implementation Plan: ai_docs/logs/da1b2c3d4/phase_plan/DAI-4-plan.md"}

## Absolute Rules

1. Response MUST be a valid JSON object only - no markdown, no backticks, no explanation text
2. Start with `{` and end with `}`
3. Use proper JSON escaping for special characters
4. Title must be under 80 characters
5. Description should be useful for code reviewers
6. Always include the issue number and plan file path in the description
7. Do NOT wrap response in markdown code blocks
8. Do NOT add any text before or after the JSON object
