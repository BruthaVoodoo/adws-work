# ADWS Documentation Index

Welcome to the comprehensive documentation for ADWS (AI Developer Workflow System), a portable Python 3.10+ autonomous development system that integrates with Jira, Bitbucket, and AWS Bedrock/proxy endpoints.

## Quick Navigation

### Getting Started
- **[README](../README.md)** - Project overview and basic usage
- **[AGENTS.md](../AGENTS.md)** - Development guidelines for agent coding
- **[Technology Stack](technology-stack.md)** - Technologies, libraries, and integration points

### Understanding the System

#### Architecture & Design
- **[Architecture](architecture.md)** - System design, 4-phase workflow, data flow
- **[Component Inventory](component-inventory.md)** - Complete module directory and purposes
- **[API Contracts](api-contracts.md)** - Integration details for Jira, AWS, Bitbucket

#### Data & Configuration
- **[Data Models](data-models.md)** - Pydantic models, types, validation
- **[Configuration System](../AGENTS.md#configuration-management)** - .adw.yaml, environment variables

### Development

- **[Development Guide](development-guide.md)** - How to run each phase, commands, workflows
- **[Test Architecture](test-architecture.md)** - Testing strategy, running tests, test patterns

## Document Summaries

### technology-stack.md
Overview of technologies, libraries, and external integrations. Includes dependency list, technology table, and environment variable requirements for Jira, AWS Bedrock, Bitbucket Cloud, and Git.

**Use this to understand:**
- What technologies power ADWS
- External dependencies and versions
- Integration point requirements
- Environment setup

### architecture.md
Complete system design documenting the 4-phase workflow (Plan → Build → Test → Review), component architecture, data flows, state management, and extension points.

**Use this to understand:**
- How the workflow phases work
- Component responsibilities
- Data flow between phases
- Error handling strategy
- How to extend the system

### component-inventory.md
Comprehensive inventory of all modules in the codebase, organized by function (config, state, agents, git, integrations, utilities, etc.). Includes dependencies and key functions for each module.

**Use this to understand:**
- What each module does
- Key functions in each module
- Module dependencies
- How modules relate to each other

### api-contracts.md
Detailed API contracts for external integrations including Jira, AWS Bedrock, Bitbucket Cloud, and Git. Documents request/response formats, authentication methods, and error handling.

**Use this to understand:**
- How to call each API
- Request/response formats
- Authentication requirements
- Rate limiting and timeouts
- Error handling patterns

### data-models.md
Complete reference for all Pydantic models used in ADWS including user models, issue models, agent requests/responses, test results, and state data. Shows model structure and usage examples.

**Use this to understand:**
- What data types exist
- Model structure and fields
- How to create instances
- Serialization/deserialization
- Validation rules

### development-guide.md
Practical guide for developers including installation, how to run each workflow phase, composable workflows, configuration management, testing, debugging, code style, and adding features.

**Use this to understand:**
- How to install and configure ADWS
- How to run each phase
- How to chain phases together
- How to debug issues
- Code style and standards
- How to add new features

### test-architecture.md
Testing strategy including test organization, how to run tests, test categories (unit, integration, format), mocking strategy, test patterns, coverage goals, and debugging failed tests.

**Use this to understand:**
- How tests are organized
- How to run tests
- Test patterns and fixtures
- How to write new tests
- Mocking external APIs
- Continuous integration

## Core Concepts

### ADW ID
A unique 8-character identifier (UUID prefix) that tracks a workflow run across all 4 phases. Example: `a1b2c3d4`

**Storage**: Embedded in state files and log directories

### Phases
1. **Plan**: Fetch issue, classify, create plan
2. **Build**: Implement plan, commit code
3. **Test**: Run tests, auto-resolve failures
4. **Review**: Review implementation, resolve issues

Each phase is independently executable and composable.

### State Management
Workflows maintain state across phases through:
1. **File persistence**: `ai_docs/logs/{adw_id}/adw_state.json`
2. **Piped input/output**: JSON via stdin/stdout for composable workflows
3. **Current git branch**: Always retrievable with `git rev-parse --abbrev-ref HEAD`

### Prompt Audit Trail
All LLM prompts are saved to `ai_docs/logs/{adw_id}/{agent_name}/prompts/` for debugging and audit purposes.

## Configuration Files

### .adw.yaml (Project Configuration)
```yaml
project_root: "."           # Project root directory
source_dir: "src"           # Source code directory
test_dir: "tests"           # Test directory
test_command: "uv run pytest"  # Command to run tests
docs_dir: "ai_docs"         # Logs and documentation directory
language: "python"          # Project language
```

### .env (Environment Variables)
Required:
- `JIRA_SERVER`, `JIRA_USERNAME`, `JIRA_API_TOKEN` (Jira)
- `AWS_ENDPOINT_URL`, `AWS_MODEL_KEY` (AI proxy) OR AWS credentials (direct)
- `BITBUCKET_WORKSPACE`, `BITBUCKET_REPO_NAME`, `BITBUCKET_API_TOKEN` (optional)

## Common Tasks

### Run Single Phase
```bash
uv run scripts/adw_plan.py PROJ-123
uv run scripts/adw_build.py PROJ-123 a1b2c3d4
uv run scripts/adw_test.py PROJ-123 a1b2c3d4
uv run scripts/adw_review.py PROJ-123 a1b2c3d4
```

### Chain Phases (Piped)
```bash
uv run scripts/adw_plan.py PROJ-123 | \
  uv run scripts/adw_build.py PROJ-123 | \
  uv run scripts/adw_test.py PROJ-123 | \
  uv run scripts/adw_review.py PROJ-123
```

### Debug a Phase
```bash
# View logs
tail -f ai_docs/logs/{adw_id}/{phase}/execution.log

# View prompts
ls ai_docs/logs/{adw_id}/{agent}/prompts/

# View state
cat ai_docs/logs/{adw_id}/adw_state.json
```

### Run Tests
```bash
uv run pytest                                    # All tests
uv run pytest tests/test_console_consistency.py # Single file
uv run pytest -v -s tests/test_file.py::test_func  # Single test with output
```

## Troubleshooting

### Missing Environment Variables
```bash
env | grep -E "JIRA_|AWS_|BITBUCKET_"
# Add missing variables to .env file
```

### Git Operations Fail
```bash
git status          # Check repository state
git remote -v       # Verify remote configuration
git branch -a       # List all branches
```

### Test Execution Fails
```bash
# Verify test command works
eval $(grep test_command .adw.yaml | sed 's/test_command: //')

# Check test directory exists
ls -la $(grep test_dir .adw.yaml | sed 's/test_dir: //')
```

### Copilot CLI Not Found
```bash
which copilot        # Verify installation
copilot --version    # Check version
```

## File Locations

### Source Code
```
scripts/
├── adw_plan.py              # Planning phase
├── adw_build.py             # Build phase
├── adw_test.py              # Test phase
├── adw_review.py            # Review phase
└── adw_modules/             # Shared modules
```

### Configuration
```
.adw.yaml                   # Project configuration
.env                        # Environment variables (ignored)
prompts/                    # LLM prompt templates
```

### Generated Artifacts
```
ai_docs/
└── logs/{adw_id}/
    ├── adw_state.json      # Persistent state
    ├── {phase}/
    │   └── execution.log   # Phase logs
    ├── {agent}/
    │   └── prompts/        # LLM prompts
    └── screenshots/        # Review screenshots
```

### Tests
```
tests/                      # Main test suite
scripts/adw_tests/         # Integration tests
```

## Key Classes & Functions

### Core Classes
- `ADWState`: Workflow state management
- `ADWConfig`: Configuration singleton
- `AgentPromptResponse`: LLM agent response
- `JiraIssue`: Jira issue model
- `ReviewResult`: Review phase result

### Key Functions
- `execute_template()`: Execute LLM prompt
- `create_branch()`: Create git branch
- `commit_changes()`: Commit to git
- `jira_fetch_issue()`: Fetch Jira issue
- `check_pr_exists()`: Check if PR exists

See [Component Inventory](component-inventory.md) for complete reference.

## Contact & Support

For issues, questions, or contributions:
1. Check relevant documentation section above
2. Review example code in test files
3. Check AGENTS.md for coding guidelines

## Document Maintenance

These documents are maintained alongside the codebase:
- **Last Updated**: January 7, 2026
- **Version**: 1.0 (Initial comprehensive documentation)

Updates should be made when:
- New modules are added
- API contracts change
- Configuration format changes
- Workflow steps change
- New features are added

---

## Quick Reference Tables

### Phase Summary

| Phase | Command | Inputs | Outputs | Key Features |
|-------|---------|--------|---------|--------------|
| Plan | `adw_plan.py PROJ-123` | Jira issue | State, branch, plan | Classification, LLM planning, PR creation |
| Build | `adw_build.py PROJ-123 ID` | Plan from state | Code changes | Implementation, git verification, PR update |
| Test | `adw_test.py PROJ-123 ID` | Test framework | Test results | Execution, auto-resolution, retries |
| Review | `adw_review.py PROJ-123 ID` | Spec file | Review result | Validation, screenshots, patch planning |

### Required Credentials

| Service | Variables | Required | Use Case |
|---------|-----------|----------|----------|
| Jira | `JIRA_*` (3 vars) | Yes | Issue tracking |
| Bedrock | AWS region + credentials | Conditional | Direct LLM execution |
| Proxy | `AWS_ENDPOINT_URL`, `AWS_MODEL_KEY` | Conditional | Custom LLM endpoint |
| Bitbucket | `BITBUCKET_*` (3 vars) | No | PR management |

### Test Summary

| Test Suite | Location | Purpose | Count |
|-----------|----------|---------|-------|
| Console Consistency | `tests/` | Output format validation | 2 files |
| Unit Tests | `scripts/adw_tests/` | Individual component testing | 8+ files |
| Integration Tests | `scripts/adw_tests/` | End-to-end workflow testing | 2+ files |

---

**ADWS Documentation Suite** - Comprehensive reference for understanding, developing, and operating the AI Developer Workflow System.
