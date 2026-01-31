# OpenCode: MCP & Skills (Extensibility)

OpenCode's power lies in its ability to connect to external tools via the **Model Context Protocol (MCP)** and define reusable behaviors via **Skills**.

## Model Context Protocol (MCP)

MCP allows OpenCode to "see" and "act" on external systems (databases, issue trackers, specialized APIs).

### Configuring MCP Servers (`opencode.json`)

#### Remote MCP (e.g., Sentry, Jira)
OpenCode handles OAuth automatically for supported remote servers.
```json
{
  "mcp": {
    "sentry": {
      "type": "remote",
      "url": "https://mcp.sentry.dev/mcp",
      "enabled": true
    }
  }
}
```

#### Local MCP (e.g., Database, Filesystem)
Run a local binary or script as a tool provider.
```json
{
  "mcp": {
    "postgres": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-postgres"],
      "environment": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/db"
      }
    }
  }
}
```

### Usage
Once configured, simply instruct the agent:
> "Check **Sentry** for the latest errors in the payment module."

---

## Agent Skills (`SKILL.md`)

Skills are on-demand instruction sets. Unlike `AGENTS.md` (which is always loaded), Skills are only loaded when the agent decides it needs them or when requested.

### Directory Structure
Skills must be placed in: `.opencode/skills/<skill-name>/SKILL.md`

### Anatomy of a `SKILL.md`

**Example: `.opencode/skills/deploy-aws/SKILL.md`**

```markdown
---
name: deploy-aws
description: Instructions for deploying the stack to AWS ECS
license: MIT
metadata:
  audience: devops
---

# Deployment Workflow

## Prerequisites
1. Ensure AWS credentials are set.
2. Build the Docker image.

## Steps
1. Run `aws ecr get-login-password...`
2. Push image to `123456789.dkr.ecr.us-east-1.amazonaws.com/repo`.
3. Force new deployment on ECS Service `api-prod`.
```

### How it Works
1. OpenCode sees `deploy-aws` in its list of available skills.
2. If you ask "Deploy this to prod", the agent calls the `skill()` tool with `deploy-aws`.
3. The content of `SKILL.md` is loaded into the context.
4. The agent executes the specific steps defined in the skill.

### Permissions for Skills
You can control access to skills in `opencode.json`:
```json
{
  "permission": {
    "skill": {
      "deploy-*": "ask",    // Ask before loading deployment skills
      "internal-*": "deny", // Hide internal skills
      "*": "allow"          // Allow everything else
    }
  }
}
```
