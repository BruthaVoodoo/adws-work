# ADWS Detailed Documentation

This document provides a comprehensive reference for the ADWS (AI Developer Workflow System).

## Table of Contents

1.  [System Architecture](#system-architecture)
2.  [Configuration](#configuration)
3.  [Workflow Phases](#workflow-phases)
4.  [Component Inventory](#component-inventory)
5.  [Data Models](#data-models)
6.  [API Contracts](#api-contracts)
7.  [Development Guide](#development-guide)
8.  [Testing](#testing)

---

## System Architecture

ADWS operates on a modular, four-phase workflow designed to autonomously handle software development tasks.

### Core Workflow

```
[Issue (Jira/GitHub)] ──→ [Plan] ──→ [Build] ──→ [Test] ──→ [Review] ──→ [PR]
                            │          │          │           │
                            └─ State ──┴─ State ──┴─ State ───┘
                               (Persisted in ADWS/logs/)
```

1.  **Plan**: Analyzes the issue, classifies it (Feature/Bug/Chore), creates a git branch, and generates a detailed implementation plan.
2.  **Build**: executes the plan by generating code and committing changes.
3.  **Test**: Runs the project's test suite. If tests fail, it attempts to auto-resolve issues using LLM analysis.
4.  **Review**: Validates the implementation against the original plan and requirements.

### State Management

State is persisted across phases using JSON files located in `ADWS/logs/{adw_id}/adw_state.json`. This allows phases to be run sequentially or resumed at any point.

### Agent Execution

ADWS uses the **OpenCode HTTP API** to interact with LLMs (Claude Sonnet 4 for heavy lifting, Claude Haiku 4.5 for lightweight tasks). This provides a local, secure, and authenticated gateway to AI capabilities.

---

## Configuration

ADWS uses a self-contained configuration file located at `ADWS/config.yaml`.

### `ADWS/config.yaml` Reference

```yaml
# Source code directory (default: "src")
source_dir: "src"

# Tests directory (default: "tests")
test_dir: "tests"

# Test command (default: "pytest")
test_command: "uv run pytest"

# Logs/documentation directory (default: "ai_docs")
docs_dir: "ai_docs"

# Project language (default: "python")
language: "python"

# Repository Provider (bitbucket or github)
repo_provider: "github"

# Issue Tracker Provider (jira or github)
issue_provider: "jira"

# OpenCode configuration
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
  timeout: 600
  lightweight_timeout: 60
  max_retries: 3
  retry_backoff: 1.5
```

### Environment Variables (`.env`)

Create a `.env` file in your project root:

**Jira (if issue_provider="jira")**:
-   `JIRA_SERVER`: Base URL (e.g., `https://company.atlassian.net`)
-   `JIRA_USERNAME`: User email
-   `JIRA_API_TOKEN`: API Token

**Bitbucket (if repo_provider="bitbucket")**:
-   `BITBUCKET_WORKSPACE`: Workspace name
-   `BITBUCKET_REPO_NAME`: Repository name
-   `BITBUCKET_API_TOKEN`: App password

**GitHub (if repo_provider="github" or issue_provider="github")**:
-   Uses `gh` CLI authentication automatically.

---

## Workflow Phases

### 1. Plan (`adw_plan.py`)
-   **Input**: Issue Key (e.g., PROJ-123)
-   **Actions**:
    -   Fetches issue details.
    -   Classifies issue type.
    -   Creates a standardized feature branch.
    -   Generates an implementation plan (`specs/`).
    -   Creates a Pull Request.
-   **Output**: ADW ID, Plan File.

### 2. Build (`adw_build.py`)
-   **Input**: ADW ID, Issue Key.
-   **Actions**:
    -   Reads the plan file.
    -   Uses LLM to implement code changes.
    -   Verifies file changes.
    -   Commits changes to the feature branch.
-   **Output**: Implemented Code.

### 3. Test (`adw_test.py`)
-   **Input**: ADW ID, Issue Key.
-   **Actions**:
    -   Runs the configured `test_command`.
    -   Analyzes failures.
    -   Attempts auto-resolution (loop: fix -> test).
-   **Output**: Test Results, Fix Commits.

### 4. Review (`adw_review.py`)
-   **Input**: ADW ID, Issue Key.
-   **Actions**:
    -   Reviews code against the plan.
    -   Generates a review report.
    -   Can attempt patch fixes for identified issues.
-   **Output**: Review Report.

---

## Component Inventory

### Core Modules (`scripts/adw_modules/`)

-   **`config.py`**: Singleton configuration loader.
-   **`state.py`**: Manages persistent workflow state.
-   **`workflow_ops.py`**: Business logic for high-level operations (classify, plan, implement).
-   **`repo_ops.py`**: Facade for repository operations (supports Bitbucket/GitHub).
-   **`issue_ops.py`**: Facade for issue tracking (supports Jira/GitHub).
-   **`git_ops.py`**: Local git operations (branch, commit, push).
-   **`agent.py`**: Interface for LLM execution via OpenCode.
-   **`utils.py`**: General utilities (logging, ID generation).

### Integrations

-   **`repo/`**:
    -   `bitbucket.py`: Bitbucket API implementation.
    -   `github.py`: GitHub CLI (`gh`) implementation.
-   **`issue_tracker/`**:
    -   `jira.py`: Jira API implementation.
    -   `github.py`: GitHub Issues implementation.

---

## Data Models

ADWS uses Pydantic models for type safety. Defined in `scripts/adw_modules/data_types.py`.

-   **`ADWStateData`**: Persisted state (adw_id, issue_number, branch_name, etc.).
-   **`JiraIssue` / `GitHubIssue`**: Normalized issue representations.
-   **`AgentPromptResponse`**: Standardized LLM response format.
-   **`TestResult`**: Outcome of a test run.

---

## API Contracts

### Repository Provider Interface
Any repo provider must implement:
-   `get_credentials()`
-   `check_pr_exists(branch)`
-   `create_pull_request(...)`
-   `update_pull_request(...)`
-   `check_connectivity()`

### Issue Tracker Interface
Any issue provider must implement:
-   `fetch_issue(id)`
-   `add_comment(id, body)`
-   `add_attachment(id, path)`
-   `check_connectivity()`

---

## Development Guide

### Adding a New Phase
1.  Create `scripts/adw_newphase.py`.
2.  Load state: `state = ADWState.load(adw_id)`.
3.  Perform logic.
4.  Update state: `state.update(...)` and `state.save()`.

### Adding a New Provider
1.  Implement the interface in `scripts/adw_modules/repo/` or `issue_tracker/`.
2.  Register it in the corresponding `_ops.py` facade.
3.  Update `config.py` to allow the new provider name.

---

## Testing

### Running Tests
```bash
uv run pytest
```

### Test Structure
-   **`tests/`**: Core unit tests.
-   **`scripts/adw_tests/`**: Integration tests and health checks.

### Health Check
Run `adw setup` or `python -m scripts.adw_tests.health_check` to verify the environment, connectivity, and configuration.
