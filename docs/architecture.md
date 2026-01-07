# ADWS Architecture & Workflow Design

## System Overview

ADWS (AI Developer Workflow System) implements a 4-phase autonomous workflow for software development: Plan, Build, Test, and Review. Each phase is independently executable and composable through a shared state management system.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADW Workflow Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  [Issue] ──→ [Plan] ──→ [Build] ──→ [Test] ──→ [Review] ──→ [PR] │
│              │          │          │           │                │
│              └─ State ──┘          │           │                │
│                 Persistence        │           │                │
│                                    └─ State ───┘                │
│                                       Persistence               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Phase Scripts

#### adw_plan.py (Planning Phase)
**Responsibility**: Create implementation plan for issue

**Workflow**:
1. Fetch Jira issue by key
2. Classify issue type (/feature, /bug, /chore)
3. Create feature branch with standardized name
4. Generate implementation plan using LLM
5. Commit plan to repository
6. Create/update pull request
7. Post plan summary to Jira

**Inputs**:
- Jira issue key (e.g., PROJ-123)
- Optional ADW ID (generated if not provided)

**Outputs**:
- ADWState with: issue_number, branch_name, plan_file, issue_class
- Plan document in logs
- Git branch created
- Jira comment with plan summary
- Pull request created/updated

**Key Modules Used**:
- `workflow_ops.classify_issue()`
- `workflow_ops.build_plan()`
- `git_ops.create_branch()`
- `git_ops.commit_changes()`
- `git_ops.finalize_git_operations()`

#### adw_build.py (Build/Implementation Phase)
**Responsibility**: Implement the plan created in planning phase

**Workflow**:
1. Load ADWState from previous run or fetch by issue number
2. Find existing plan (from state or search)
3. Execute implementation using LLM
4. Verify git changes made
5. Commit implementation
6. Push and update PR
7. Post implementation summary to Jira

**Inputs**:
- Issue number
- ADW ID (from state)
- Optional target directory

**Outputs**:
- Implementation committed to feature branch
- Git statistics (files changed, lines added/removed)
- Jira comment with implementation summary
- Updated pull request

**Key Modules Used**:
- `state.ADWState.load()`
- `workflow_ops.implement_plan()`
- `git_verification.verify_git_changes()`
- `git_ops.commit_changes()`
- `git_ops.finalize_git_operations()`

#### adw_test.py (Testing Phase)
**Responsibility**: Execute test suite and resolve failures

**Workflow**:
1. Load ADWState or fetch issue details
2. Run application test suite
3. Report test results to Jira
4. If failed tests exist:
   - Parse failures using Copilot CLI
   - Attempt auto-resolution up to MAX_TEST_RETRY_ATTEMPTS
   - Re-run tests
5. Commit test results
6. Push and update PR

**Inputs**:
- Issue number
- ADW ID
- Optional --skip-e2e flag

**Outputs**:
- Test execution log
- Test results (passed/failed)
- Jira comment with test summary
- Fixed code if auto-resolution successful

**Special Requirements**:
- Copilot CLI must be installed and available in PATH
- Test command configured in .adw.yaml

**Key Modules Used**:
- `state.ADWState.load()`
- `copilot_output_parser.parse_copilot_output()`
- `git_ops.commit_changes()`
- `git_ops.finalize_git_operations()`

#### adw_review.py (Review Phase)
**Responsibility**: Review implementation against specification

**Workflow**:
1. Find spec file from current branch
2. Review implementation using LLM
3. Capture screenshots of critical functionality
4. If issues found and --skip-resolution not set:
   - Create patch plans for issues
   - Implement resolutions
   - Repeat until all issues resolved or max attempts reached
5. Commit review results
6. Push and update PR

**Inputs**:
- Issue number
- ADW ID
- Optional --skip-resolution flag

**Outputs**:
- Review result document
- Screenshots of functionality
- Jira comment with review summary
- Patch implementations if needed

**Special Requirements**:
- Copilot CLI must be installed

**Key Modules Used**:
- `workflow_ops.find_spec_file()`
- `workflow_ops.create_patch_plan()`
- `workflow_ops.implement_plan()`
- `git_ops.commit_changes()`
- `git_ops.finalize_git_operations()`

### 2. State Management

#### ADWState (scripts/adw_modules/state.py)
Manages workflow state across phases with three modes:

**Mode 1: File Persistence**
```python
state = ADWState("a1b2c3d4")
state.update(issue_number="123", branch_name="feature/123")
state.save()  # Writes to ai_docs/logs/a1b2c3d4/adw_state.json
```

**Mode 2: File Loading**
```python
state = ADWState.load("a1b2c3d4")  # Reads from file
```

**Mode 3: Piped Input/Output**
```python
# Piped input (from previous script)
state = ADWState.from_stdin()

# Piped output (to next script)
state.to_stdout()  # Writes JSON to stdout
```

**Supported Fields**:
- `adw_id`: Workflow ID (required)
- `issue_number`: Jira issue number
- `branch_name`: Git branch name
- `plan_file`: Path to plan document
- `issue_class`: Classification (/feature, /bug, /chore)
- `domain`: Domain type (ADW_Core, ADW_Agent)
- `agent_name`: Agent that last modified state

### 3. Agent/LLM Execution

#### Agent Execution Flow

```
AgentTemplateRequest
    ↓
agent.execute_template() or bedrock_agent.execute_template()
    ↓
invoke_model(prompt, model_id)
    ↓
API Call (Proxy or AWS Bedrock)
    ↓
AgentPromptResponse
    ├── output: str (generated text)
    ├── success: bool
    └── [optional metadata]
```

#### Two Execution Modes

**Mode 1: AWS Bedrock (Direct)**
```python
from adw_modules.bedrock_agent import execute_template
response = execute_template(request)  # Uses boto3
```
- Direct AWS API calls
- Requires AWS credentials in environment
- Models: Claude 3 Sonnet/Opus

**Mode 2: Proxy Endpoint**
```python
from adw_modules.agent import execute_template
response = execute_template(request)  # Uses HTTP proxy
```
- HTTP POST to custom endpoint
- Bearer token authentication
- Supports any OpenAI-compatible endpoint

### 4. Workflow Operations

#### Core Operations Module (scripts/adw_modules/workflow_ops.py)

**Issue Classification**
```python
classify_issue(issue, adw_id, logger) → (command, error)
```
- Uses LLM to classify issue as /feature, /bug, /chore, or /new
- Selects appropriate prompt template

**Plan Generation**
```python
build_plan(issue, command, adw_id, logger) → AgentPromptResponse
```
- Formats full issue context
- Loads prompt template for issue type
- Executes LLM with complete context
- Returns structured plan

**Implementation**
```python
implement_plan(plan, adw_id, logger) → AgentPromptResponse
```
- Reads generated plan
- Executes implementation using LLM
- Applies changes to codebase

**Branch Management**
```python
generate_branch_name(issue, command, adw_id) → str
```
- Creates standardized branch names
- Format: `feature/PROJ-123-slug-text`

**Pull Request Management**
```python
create_pull_request(branch_name, issue_number, state, logger) → (url, error)
check_pr_exists(branch_name) → Optional[dict]
update_pull_request(pr_id, title, description) → (success, error)
```

## Data Flow

### Planning Phase Data Flow
```
Jira Issue
    ↓
[Classify] ──→ Issue Classification
    ↓
[Generate Plan] ──→ LLM Prompt
    ↓
[Execute] ──→ Agent Response
    ↓
[Commit] ──→ Git Repository
    ↓
[Create PR] ──→ Bitbucket
    ↓
[Post Comment] ──→ Jira
    ↓
ADWState File
```

### Build Phase Data Flow
```
ADWState (or Issue Number)
    ↓
[Load State]
    ↓
[Find Plan]
    ↓
[Implement] ──→ LLM Prompt
    ↓
[Execute] ──→ Agent Response
    ↓
[Verify Changes] ──→ Git Diff
    ↓
[Commit] ──→ Git Repository
    ↓
[Push] ──→ Bitbucket
    ↓
[Update PR] ──→ Bitbucket
    ↓
[Post Comment] ──→ Jira
    ↓
ADWState File
```

## Composable Phases

Each phase can be executed independently or chained:

### Single Phase Execution
```bash
uv run adw_plan.py PROJ-123
uv run adw_build.py PROJ-123 a1b2c3d4
uv run adw_test.py PROJ-123 a1b2c3d4
uv run adw_review.py PROJ-123 a1b2c3d4
```

### Chained Execution (with piped state)
```bash
adw_plan.py PROJ-123 | adw_build.py PROJ-123 | adw_test.py PROJ-123 | adw_review.py PROJ-123
```

### File-based State (for recovery/resumption)
```bash
# First phase creates state
uv run adw_plan.py PROJ-123 a1b2c3d4

# Later phase loads state
uv run adw_build.py PROJ-123 a1b2c3d4  # Loads from file
```

## Configuration System

### ADWConfig (Singleton)
```python
from adw_modules.config import config

config.project_root      # Path to project root
config.source_dir        # Source code directory
config.test_dir          # Test directory
config.test_command      # Command to run tests
config.language          # Project language
config.logs_dir          # ai_docs/logs
```

**Loading Priority**:
1. Start from current working directory
2. Walk up directory tree
3. Look for `.adw.yaml`, `.adw.yml`, `.adw_config.yaml`, `.adw_config.yml`
4. Load first found or use defaults

### Default Values
```yaml
project_root: "."
source_dir: "src"
test_dir: "tests"
test_command: "pytest"
docs_dir: "ai_docs"
language: "python"
```

## Logging & Output

### Directory Structure
```
ai_docs/
└── logs/
    └── {adw_id}/
        ├── adw_state.json                      # Persistent state
        ├── adw_plan/
        │   └── execution.log
        ├── adw_build/
        │   └── execution.log
        ├── adw_test/
        │   └── execution.log
        ├── adw_review/
        │   └── execution.log
        ├── sdlc_planner/
        │   └── prompts/
        │       ├── feature_20240117_143022.txt
        │       └── ...
        ├── sdlc_implementor/
        │   └── prompts/
        │       ├── implement_20240117_143122.txt
        │       └── ...
        ├── issue_classifier/
        │   └── prompts/
        │       └── classify_issue_20240117_142922.txt
        └── ...
```

### Logging Features
- **Console Output**: Rich-formatted messages with colors
- **File Logging**: Detailed logs with timestamps
- **Prompt Audit Trail**: All LLM prompts saved with timestamps
- **Debug Logging**: Comprehensive debug output when needed

## Error Handling Strategy

### Error Types

**Configuration Errors**
- Missing environment variables → exit(1)
- Invalid .adw.yaml → warning + use defaults
- Missing prompt templates → ValueError

**API Errors**
- Jira connection → JiraException
- AWS/Bedrock → ClientError
- Bitbucket → requests.RequestException
- Generic → log and continue or exit based on criticality

**Git Errors**
- Branch creation failure → exit with error
- Commit failure → exit with error
- Push failure → exit with error

**LLM Execution Errors**
- Model invocation fails → AgentPromptResponse(success=False)
- Parsing failure → log error and return None
- Timeout → AgentPromptResponse with timeout message

### Error Propagation

1. **Critical Errors**: Exit immediately with error message
   - Missing credentials
   - Failed git operations
   - Jira connectivity

2. **Recoverable Errors**: Log and attempt recovery
   - Transient API failures
   - Parsing errors with fallback
   - Test failures (auto-resolve)

3. **Non-blocking Errors**: Log and continue
   - Optional field missing
   - Non-critical validation warning

## Extension Points

### Adding New Phases
1. Create new script in scripts/
2. Inherit state management from ADWState
3. Use workflow_ops for common operations
4. Follow phase script template pattern

### Adding New Agents
1. Create agent in adw_modules/
2. Implement execute_template(request) function
3. Register agent name in constants
4. Add prompts in prompts/

### Adding New Integrations
1. Create module in adw_modules/
2. Follow established patterns (get_client, API methods)
3. Use consistent error handling
4. Document in api-contracts.md

## Performance Considerations

### Optimization Points
- **LLM Calls**: 5-minute timeout for complex operations
- **Git Operations**: Local operations, no network overhead
- **Bitbucket API**: Minimize PR existence checks
- **Jira Comments**: Batch updates where possible (max 32KB)
- **State Persistence**: Lightweight JSON files

### Parallelization Opportunities
- Independent test execution
- Multiple file changes analysis
- Concurrent PR operations (not currently implemented)

---

**Last Updated**: January 7, 2026
