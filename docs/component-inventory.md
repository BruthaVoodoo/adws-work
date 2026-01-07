# ADWS Component Inventory

## Module Organization

All modules are located in `scripts/adw_modules/` unless otherwise noted.

## Configuration & State Management

### config.py
**Purpose**: Load and provide access to project configuration

**Key Classes**:
- `ADWConfig`: Singleton configuration loader
  - `project_root`: Project root directory
  - `source_dir`: Source code directory
  - `test_dir`: Test directory
  - `ai_docs_dir`: Documentation directory
  - `logs_dir`: Logs directory
  - `test_command`: Test execution command
  - `language`: Project language

**Key Functions**:
- `_load()`: Load config from .adw.yaml walking up directory tree
- Properties for all configuration values

**Dependencies**: yaml, pathlib, os

---

### state.py
**Purpose**: Manage workflow state across phases

**Key Classes**:
- `ADWState`: Persistent and transient state container
  - `update()`: Update state with key-value pairs
  - `get()`: Retrieve value from state
  - `save()`: Write state to JSON file
  - `load()`: Load state from JSON file (class method)
  - `from_stdin()`: Load state from piped input
  - `to_stdout()`: Write state to stdout

**Key Features**:
- File-based persistence: `ai_docs/logs/{adw_id}/adw_state.json`
- Piped input/output for composable workflows
- State validation with ADWStateData model

**Dependencies**: json, os, sys, logging, pydantic

---

## Data Types & Models

### data_types.py
**Purpose**: Define all Pydantic models for type safety

**User Models**:
- `GitHubUser`: GitHub user (id, login, name, is_bot)
- `JiraUser`: Jira user (login from displayName)

**Label Models**:
- `GitHubLabel`: GitHub label (id, name, color, description)
- `JiraLabel`: Jira label (name)

**Issue Models**:
- `GitHubIssue`: Complete GitHub issue
- `GitHubIssueListItem`: Simplified GitHub issue for lists
- `JiraIssue`: Jira issue with custom from_raw_jira_issue() method

**Comment Models**:
- `GitHubComment`: GitHub comment with author and timestamps

**Metadata Models**:
- `GitHubMilestone`: GitHub milestone

**Agent Models**:
- `AgentPromptResponse`: LLM agent response (output, success, metadata)
- `AgentTemplateRequest`: LLM agent request (agent_name, prompt, adw_id, model)

**Test Result Models**:
- `TestResult`: Individual test result
- `E2ETestResult`: End-to-end test result with status property

**Review Models**:
- `ReviewIssue`: Individual review issue (description, severity, resolution)
- `ReviewResult`: Complete review result (success, review_issues, screenshots)

**State Models**:
- `ADWStateData`: Persistent state schema (adw_id, issue_number, branch_name, etc.)

**Type Definitions**:
- `IssueClassSlashCommand`: Literal["/chore", "/bug", "/feature", "/new"]
- `ADWWorkflow`: Literal for workflow types (adw_plan, adw_build, adw_test, etc.)

**Dependencies**: pydantic, datetime, typing

---

## Agent/LLM Execution

### agent.py
**Purpose**: Execute prompts against custom proxy endpoint

**Key Functions**:
- `save_prompt()`: Save prompt to audit trail
- `invoke_model()`: HTTP POST to proxy endpoint
- `execute_template()`: Execute AgentTemplateRequest

**Features**:
- Bearer token authentication
- OpenAI-compatible response format
- 300-second timeout
- Prompt audit trail to logs/{adw_id}/{agent_name}/prompts/

**Environment Variables**:
- `AWS_ENDPOINT_URL`: Custom endpoint URL
- `AWS_MODEL_KEY`: Bearer token
- `AWS_MODEL`: Model selection (optional)

**Dependencies**: requests, json, os, datetime, dotenv

---

### bedrock_agent.py
**Purpose**: Execute prompts against AWS Bedrock

**Key Functions**:
- `get_bedrock_client()`: Initialize boto3 Bedrock client
- `save_prompt()`: Save prompt to audit trail
- `invoke_model()`: Invoke Claude 3 model on Bedrock
- `execute_template()`: Execute AgentTemplateRequest

**Features**:
- Direct AWS API integration
- Support for Sonnet and Opus models
- Temperature: 0.1 (deterministic)
- Max tokens: 4096

**Environment Variables**:
- `AWS_ENDPOINT_URL`: Optional custom endpoint
- `AWS_MODEL`: Model selection
- AWS credentials (via boto3)

**Dependencies**: boto3, botocore, json, os, datetime, dotenv

---

## Git & VCS Operations

### git_ops.py
**Purpose**: Git operations (branch, commit, push)

**Key Functions**:
- `get_current_branch()`: Get current git branch
- `create_branch()`: Create and checkout new branch
- `commit_changes()`: Stage and commit changes
- `push_branch()`: Push branch to remote
- `finalize_git_operations()`: Push, create/update PR, post Jira comment

**Features**:
- Idempotent commit (no-op if no changes)
- Automatic fallback if branch exists
- Integrated PR and Jira management
- Branch switching to main on completion

**Dependencies**: subprocess, logging, jira_ops, bitbucket_ops

---

### git_verification.py
**Purpose**: Verify and analyze git changes

**Key Functions**:
- `verify_git_changes()`: Check for valid changes (not on main, staged changes)
- `get_file_changes()`: Extract file stats from git diff

**Features**:
- Returns (files_changed, lines_added, lines_removed)
- Validates branch state before operations

**Dependencies**: subprocess, logging

---

## Issue Tracking Integration

### jira.py
**Purpose**: Jira API client

**Key Functions**:
- `get_jira_client()`: Initialize Jira client
- `jira_fetch_issue()`: Fetch issue by key
- `jira_make_issue_comment()`: Add comment (with 32KB truncation)
- `jira_add_attachment()`: Add file attachment

**Features**:
- HTTP Basic Auth with API tokens
- Automatic comment truncation with warning
- File existence validation

**Environment Variables**:
- `JIRA_SERVER`: Server URL
- `JIRA_USERNAME`: Username
- `JIRA_API_TOKEN`: API token

**Dependencies**: jira library, os

---

### jira_formatter.py
**Purpose**: Format Jira issues for display

**Key Functions**:
- Format Jira issue details for console output
- Pretty-print issue information

**Used By**: Various scripts for display

---

## Repository Management

### bitbucket_ops.py
**Purpose**: Bitbucket Cloud API operations

**Key Functions**:
- `get_bitbucket_credentials()`: Load credentials from environment
- `get_repo_url()`: Construct repository URL
- `extract_repo_path()`: Parse repo path from URL
- `check_pr_exists()`: Search for existing PR by branch
- `create_pull_request()`: Create new PR
- `update_pull_request()`: Update PR title/description

**Features**:
- Bearer token authentication
- Handles both HTTPS and SSH URLs
- Returns PR ID and URL
- Paginated PR search with state filtering

**Environment Variables**:
- `BITBUCKET_WORKSPACE`: Workspace name
- `BITBUCKET_REPO_NAME`: Repository name
- `BITBUCKET_API_TOKEN`: API token

**Dependencies**: requests, os, urllib.parse, json

---

## Workflow Operations

### workflow_ops.py
**Purpose**: Core workflow business logic

**Key Functions**:

**Classification & Planning**:
- `classify_issue()`: Use LLM to classify issue type
- `build_plan()`: Generate implementation plan
- `generate_branch_name()`: Create standardized branch name
- `extract_adw_info()`: Parse ADW workflow and ID from text

**Implementation & Review**:
- `implement_plan()`: Use LLM to implement plan
- `create_patch_plan()`: Create patch for review issues
- `find_spec_file()`: Locate specification file

**PR Management**:
- `create_pull_request()`: Create new PR
- `create_commit()`: Create commit message

**Utilities**:
- `format_issue_message()`: Format messages with ADW tracking
- `ensure_adw_id()`: Generate or use provided ADW ID

**Agent Constants**:
- `AGENT_PLANNER`: "sdlc_planner"
- `AGENT_IMPLEMENTOR`: "sdlc_implementor"
- `AGENT_CLASSIFIER`: "issue_classifier"
- `AGENT_PLAN_FINDER`: "plan_finder"
- `AGENT_BRANCH_GENERATOR`: "branch_generator"
- `AGENT_PR_CREATOR`: "pr_creator"

**Dependencies**: subprocess, json, re, os, agent, bitbucket_ops, state, utils

---

## Utilities

### utils.py
**Purpose**: General-purpose utilities

**Key Functions**:
- `make_adw_id()`: Generate 8-character UUID
- `setup_logger()`: Create logger with file and console handlers
- `get_logger()`: Get existing logger by ADW ID
- `get_rich_console_instance()`: Get singleton RichConsole
- `parse_json()`: Parse JSON with markdown code block support
- `load_prompt()`: Load prompt template from prompts/ directory
- `get_test_command()`: Get test command from config

**Features**:
- Type-generic JSON parsing
- Support for JSON wrapped in markdown code blocks
- Rich console integration
- Dual logging (console + file)

**Dependencies**: json, logging, re, sys, uuid, config, rich_console

---

### rich_console.py
**Purpose**: Console output styling and management

**Key Classes**:
- `RichConsole`: Wrapper around rich.console.Console
  - `print()`: Print with styling
  - `rule()`: Draw horizontal rule
  - `panel()`: Render panel
  - `info()`, `success()`, `warning()`, `error()`: Styled messages
  - `step()`: Step header
  - `spinner()`: Progress spinner context manager
  - `print_table()`: Print table
  - `status_table()`: Print status table from dict

**Functions**:
- `get_rich_console()`: Get singleton instance
- `create_rich_console()`: Create new instance

**Features**:
- Custom ADW theme colors
- Fallback to plain print if rich unavailable
- Consistent message styling across phases

**Dependencies**: rich library (optional), sys

---

### issue_formatter.py
**Purpose**: Format issue context for LLM consumption

**Key Functions**:
- `format_issue_context()`: Extract and format issue details
- Format issue information from GitHub/Jira issues

**Used By**: build_plan() for context injection

---

## Validation & Parsing

### plan_validator.py
**Purpose**: Validate generated plans

**Key Functions**:
- `cross_reference_plan_output()`: Validate plan against issue
- Verify plan completeness and consistency

**Used By**: Plan validation after generation

---

### copilot_output_parser.py
**Purpose**: Parse Copilot CLI output

**Key Functions**:
- `parse_copilot_output()`: Parse structured output from Copilot
- Extract test results, fixes, and metadata from Copilot responses

**Used By**: adw_test.py, adw_review.py for result parsing

---

### issue_formatter.py
**Purpose**: Format issues for agent consumption

**Key Functions**:
- `format_issue_context()`: Extract full issue context
- Returns dictionary with: issue_key, issue_title, issue_description, issue_labels, issue_state

---

## Phase Scripts

Located in `scripts/`:

### adw_plan.py
**Purpose**: Planning phase

**Workflow**:
1. Fetch Jira issue
2. Classify issue
3. Create branch
4. Generate plan
5. Commit plan
6. Create/update PR
7. Post Jira comment

**Requires**: Jira credentials

---

### adw_build.py
**Purpose**: Build/implementation phase

**Workflow**:
1. Load state
2. Find plan
3. Implement plan
4. Verify changes
5. Commit implementation
6. Push and update PR
7. Post Jira comment

**Requires**: Jira credentials, previous plan

---

### adw_test.py
**Purpose**: Test execution phase

**Workflow**:
1. Load state
2. Run tests
3. Parse results
4. Auto-resolve failures (up to 4 attempts)
5. Commit test fixes
6. Push and update PR
7. Post Jira comment

**Requires**: Copilot CLI, test command configured

---

### adw_review.py
**Purpose**: Review phase

**Workflow**:
1. Find spec file
2. Review implementation
3. Capture screenshots
4. Auto-resolve issues (up to 3 attempts)
5. Commit review results
6. Push and update PR
7. Post Jira comment

**Requires**: Copilot CLI, spec file on branch

---

## Testing Infrastructure

Located in `tests/` and `scripts/adw_tests/`:

### Test Files
- `test_console_consistency.py`: Console output format validation
- `test_parsing_functions.py`: Data parsing tests
- `test_copilot_output_parser.py`: Copilot output parsing tests
- `test_datatypes.py`: Pydantic model validation tests
- `test_git_verification.py`: Git operation tests
- `test_integration_workflow.py`: End-to-end workflow tests
- `test_plan_validator.py`: Plan validation tests
- `test_review_workflow.py`: Review workflow tests
- `test_rich_console.py`: Console output tests
- `test_state.py`: State management tests

### Fixtures
- `fixtures.py`: Test data and fixtures
- `health_check.py`: System health verification

---

## Prompt Templates

Located in `prompts/`:

- `bug.md`: Bug fix planning prompt
- `feature.md`: Feature implementation prompt
- `chore.md`: Chore/maintenance prompt
- `implement.md`: Implementation execution prompt
- `review.md`: Review prompt
- `classify_issue.md`: Issue classification prompt
- `generate_branch_name.md`: Branch name generation prompt
- `resolve_failed_tests.md`: Test failure resolution prompt
- `review_patch.md`: Review patch creation prompt
- Plus others for specific use cases

---

## Dependency Graph

```
Phase Scripts (adw_*.py)
    ↓
workflow_ops.py (core business logic)
    ├─→ agent.py or bedrock_agent.py (LLM execution)
    ├─→ git_ops.py (git operations)
    ├─→ bitbucket_ops.py (PR management)
    ├─→ jira.py (issue tracking)
    ├─→ state.py (state management)
    ├─→ utils.py (utilities)
    ├─→ git_verification.py (git analysis)
    ├─→ issue_formatter.py (issue formatting)
    ├─→ plan_validator.py (plan validation)
    └─→ copilot_output_parser.py (output parsing)

config.py (singleton configuration)
    ↓
Shared by all modules

data_types.py (models)
    ↓
Used by all modules for validation

rich_console.py (console output)
    ↓
Used by all modules for styled output
```

---

**Last Updated**: January 7, 2026
