# OpenCode: Configuration Reference

OpenCode uses a hierarchical configuration system. Settings are merged from multiple sources, allowing for organizational defaults, user preferences, and project-specific overrides.

## Configuration Locations (Precedence Order)

1.  **Project Config:** `opencode.json` (In project root - Overrides all)
2.  **Custom Config:** `OPENCODE_CONFIG` (Env var path)
3.  **Global Config:** `~/.config/opencode/opencode.json` (User defaults)
4.  **Remote Config:** `.well-known/opencode` (Org defaults)

## The `opencode.json` Schema

### Basic Structure
```json
{
  "$schema": "https://opencode.ai/config.json",
  "theme": "opencode",
  "model": "anthropic/claude-sonnet-4-5",
  "autoupdate": true,
  "editor": "code"
}
```

### Provider Configuration
OpenCode supports BYOK (Bring Your Own Key) for 75+ providers.

**Example: Configuring Anthropic & Local Options**
```json
{
  "provider": {
    "anthropic": {
      "options": {
        "timeout": 600000,
        "baseURL": "https://api.anthropic.com/v1" 
      }
    },
    "amazon-bedrock": {
        "options": {
            "region": "us-east-1",
            "profile": "default"
        }
    }
  }
}
```

### Security & Permissions
You can lock down specific tools globally or per-agent.

**Example: Require permission for file edits and specific bash commands**
```json
{
  "permission": {
    "edit": "ask",
    "bash": {
        "*": "ask",
        "ls": "allow",
        "git status": "allow",
        "git push": "deny"
    }
  }
}
```

### Watcher Settings
Configure what OpenCode ignores when indexing your project.
```json
{
  "watcher": {
    "ignore": ["node_modules/**", "dist/**", ".git/**", "**/*.log"]
  }
}
```

### Instructions (Global Rules)
Inject global documentation into every session context.
```json
{
  "instructions": [
    "CONTRIBUTING.md", 
    "docs/architecture.md", 
    ".cursor/rules/*.md"
  ]
}
```

## Environment Variables
You can reference env vars in your config using `{env:VAR_NAME}`.

```json
{
  "provider": {
    "openai": {
      "options": {
        "apiKey": "{env:OPENAI_API_KEY}"
      }
    }
  }
}
```
