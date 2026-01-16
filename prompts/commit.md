# Generate Git Commit

Based on the `Instructions` below, take the `Variables` and follow the `Run` section to create a git commit with a properly formatted message.

## Variables
agent_name: {agent_name}
issue_class: {issue_type}
issue: {issue_json}

## Instructions

- Generate a concise commit message in the format: `<issue_class>: <commit message>`
  - The `<commit message>` should be:
    - Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
    - 50 characters or less
    - Descriptive of the actual changes made
    - No period at the end
  - Examples:
    - `feat: add user authentication module`
    - `bug: fix login validation error`
    - `chore: update dependencies to latest versions`
- Extract context from the issue JSON to make the commit message relevant
- IMPORTANT: Return ONLY the generated commit message and absolutely nothing else. No conversational filler, no explanations, no markdown formatting around the commit message.

## Run

1. Run `git diff HEAD` to understand what changes have been made
2. Run `git add -A` to stage all changes
3. Run `git commit -m "<generated_commit_message>"` to create a commit
