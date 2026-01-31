# OpenCode: Getting Started & Core Concepts

## Overview
OpenCode is an autonomous AI coding agent that operates as a senior developer interface. It supports a **Plan → Act → Verify** loop, allowing it to understand complex codebases, plan architectural changes, and implement code safely.

It operates in two main modes:
1.  **Plan Mode:** Safe, read-only analysis and strategy.
2.  **Build Mode:** Full access to filesystem and terminal for implementation.

## Installation

### Standard Installation
```bash
# MacOS / Linux
curl -fsSL https://opencode.ai/install | bash

# Node.js
npm install -g opencode-ai

# Homebrew
brew install anomalyco/tap/opencode
```

### Initial Setup (`/init`)
Every project should be initialized to help OpenCode understand the specific patterns and conventions of the repo.

1. Navigate to your project root.
2. Run `opencode`.
3. Type `/init`.

This generates an `AGENTS.md` file. **Commit this file.** It acts as the "Constitution" for the agent, defining specific project rules (e.g., "Always use TypeScript," "Tests must use Pytest").

## Interface Basics

### The TUI (Terminal User Interface)
OpenCode is primarily used via the terminal.

*   **Switch Agents:** Press `TAB` to toggle between **Build** (Execute) and **Plan** (Reasoning) modes.
*   **Context:** Use `@` to mention specific files, folders, or symbols.
*   **Commands:** Use `/` to access system commands (e.g., `/undo`, `/share`).

### Connection (`/connect`)
To connect LLM providers:
```bash
/connect
```
This launches an interactive menu to authenticate with OpenAI, Anthropic, AWS Bedrock, etc. Keys are stored securely in `~/.local/share/opencode/auth.json`.

## Core Workflow Loop
1.  **Analyze:** Switch to `Plan` mode. Ask OpenCode to analyze a problem.
2.  **Strategize:** It produces a plan. Refine this plan with natural language.
3.  **Implement:** Switch to `Build` mode (`TAB`). Command: "Execute the plan."
4.  **Verify:** OpenCode can run tests/linters if instructed (or if configured in `AGENTS.md`).
