# OpenCode: Agents & Custom Workflows

OpenCode is not just a chatbot; it is a system of specialized agents. You can define your own agents with specific roles, prompts, and tool sets.

## Agent Types

1.  **Primary Agents:** The main interface (switchable via `TAB`).
    *   **Build:** Default. Full tool access.
    *   **Plan:** Restricted. Read-only. High-reasoning models.
2.  **Subagents:** Specialized workers invoked by Primary agents or via `@`.
    *   **General:** Multi-step reasoning.
    *   **Explore:** Fast code search.

## Configuring Agents

Agents can be defined in `opencode.json` or as standalone Markdown files in `.opencode/agents/`.

### JSON Configuration (In `opencode.json`)
```json
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for security and style",
      "mode": "subagent",
      "model": "anthropic/claude-sonnet-4-5",
      "temperature": 0.1,
      "prompt": "You are a rigid code reviewer. Focus on OWASP Top 10.",
      "tools": {
        "write": false,
        "edit": false,
        "bash": false
      }
    }
  }
}
```

### Markdown Configuration (The "Agent File")
Create `.opencode/agents/reviewer.md`:

```markdown
---
description: Reviews code for quality and best practices
mode: subagent
model: anthropic/claude-sonnet-4
temperature: 0.1
tools:
  write: false
  edit: false
  bash: false
---

# Identity
You are a Senior Technical Reviewer. 

# Guidelines
1. Do not fix code; only comment.
2. Check for type safety.
3. Ensure no secrets are hardcoded.
```

## Usage
To use the agent defined above:
```bash
@reviewer Check the auth_service.py file for security issues.
```

## `AGENTS.md` - The Project Constitution
The `AGENTS.md` file in the project root is **critical**. It is automatically loaded into the context of *every* agent.

**Best Practices for `AGENTS.md`:**
*   **Tech Stack:** Explicitly state languages and frameworks.
*   **Testing:** Command to run tests (e.g., `npm test`, `pytest`).
*   **Style:** Linting rules or formatting preferences.
*   **Directory Structure:** Key folders (e.g., "Source code is in `src/`, docs in `content/`").

**Example:**
```markdown
# Project Context
This is a Python 3.10 FastApi project.

# Rules
- Always type-hint functions.
- Use `pydantic` for data models.
- Run tests via `pytest`.
- Never modify `.env` files.
```
