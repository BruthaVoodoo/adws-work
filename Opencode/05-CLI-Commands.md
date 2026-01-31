# OpenCode: CLI & Command Reference

## CLI Usage
`opencode [options] [initial prompt]`

### Flags
*   `--help`: Show help.
*   `--version`: Show version.
*   `--model <id>`: Force a specific model for this session.
*   `--agent <id>`: Start with a specific agent.

**Example:**
```bash
opencode --agent plan "Analyze the memory leak in worker.ts"
```

## System Commands (Inside TUI)

These commands are typed into the prompt input bar starting with `/`.

| Command | Description |
| :--- | :--- |
| `/init` | Initialize a new project (creates `AGENTS.md`). |
| `/connect` | Open the authentication manager for LLM providers. |
| `/models` | List and select available LLM models. |
| `/agent` | Switch, list, or create agents. |
| `/mode` | Switch between `primary` (Build) and `plan` modes. |
| `/undo` | Revert the last file change or action. |
| `/redo` | Redo a reverted action. |
| `/share` | Generate a URL to share the conversation context. |
| `/copy` | Copy the last message to clipboard. |
| `/clear` | Clear the current session context (preserves history visually). |
| `/exit` | Quit OpenCode. |

## Custom Commands

You can create macros/custom commands in `opencode.json`.

```json
{
  "command": {
    "test-coverage": {
      "description": "Run tests and check coverage",
      "template": "Run the full test suite with coverage. If coverage is below 80%, identify which files need more tests.",
      "agent": "build"
    },
    "refactor": {
      "description": "Refactor a specific component",
      "template": "Refactor the component $ARGUMENTS following Clean Code principles. Keep functions small.",
      "agent": "build"
    }
  }
}
```

**Usage:**
```bash
/test-coverage
/refactor user_auth.py
```

## Keyboard Shortcuts

| Key | Action |
| :--- | :--- |
| `TAB` | Toggle between Plan and Build modes. |
| `@` | Open Context Menu (Files, Symbols, Agents). |
| `Cmd+K` (or `Ctrl+K`) | Quick search/focus. |
| `Enter` | Send message. |
| `Shift+Enter` | New line in prompt. |
