# ADWS Migration Plan: Complete AI System Migration to OpenCode

**Status**: Plan (REVISED - Complete AI Migration)  
**Created**: January 6, 2026  
**Revised**: January 6, 2026  
**Scope**: Replace ALL custom LLM integrations (Bedrock + custom proxy) with OpenCode HTTP API + smart model routing  
**Estimated Complexity**: High  
**Estimated Effort**: 40-50 hours

---

## Executive Summary

This plan outlines the **complete migration of ALL AI operations** in the ADWS (AI Developer Workflow System) from:
- **FROM**: AWS Bedrock (custom endpoint) + Custom HTTP Proxy
- **TO**: OpenCode HTTP Server API with intelligent model routing

The system currently uses:
1. **Custom proxy agent** (`agent.py`) - For planning, classification, branch generation, commit messages, PR creation
2. **Copilot CLI** - For code execution (implementation, test fixing, reviews)

**New Approach**: Consolidate everything into OpenCode with model-aware routing:
- ✅ **Claude Sonnet 4.5** - Heavy code lifting (implementation, test fixing, reviews)
- ✅ **GPT-4o mini** - Lightweight tasks (planning, classification, document creation)
- ✅ Single unified HTTP API interface
- ✅ Structured Message/Part responses (no regex parsing)
- ✅ Better error handling and type safety
- ⚠️ Requires running `opencode serve` in background

### Key Changes

- **Integration Method**: Use `opencode serve` HTTP API for ALL AI operations
- **Model Routing**: Dynamic model selection based on task type
- **Connection**: Python `requests` library to call REST endpoints
- **Output Format**: Structured Message + Part array (not text or JSON events)
- **Parsing**: Extract data from Part types (text, tool_use, tool_result) - no regex needed
- **Integration Points**: 9 direct LLM invocations + Copilot CLI for code execution
- **Configuration**: HTTP server endpoint, per-task model selection, timeout settings

---

## 1. Current Architecture Analysis

### 1.1 Current AI Integration Points (9 LLM invocations)

| File | Function | Model | Task Type | Frequency |
|------|----------|-------|-----------|-----------|
| `workflow_ops.py:51-88` | `extract_adw_info()` | sonnet | Classification | Low |
| `workflow_ops.py:91-138` | `classify_issue()` | sonnet | Classification | High |
| `workflow_ops.py:141-196` | `build_plan()` | sonnet | Planning/Analysis | High |
| `workflow_ops.py:349-397` | `generate_branch_name()` | sonnet | Lightweight text | Medium |
| `workflow_ops.py:400-438` | `create_commit()` | sonnet | Lightweight text | Medium |
| `workflow_ops.py:441-540` | `create_pull_request()` | sonnet | Lightweight text | Medium |
| `workflow_ops.py:200-346` | `implement_plan()` | N/A (Copilot CLI) | Heavy code lifting | High |
| `adw_test.py:402-440` | `resolve_failed_tests()` | N/A (Copilot CLI) | Heavy code lifting | High |
| `adw_review.py:110-150` | `run_review()` | N/A (Copilot CLI) | Heavy code lifting | Medium |

### 1.2 Current LLM Backend Architecture

**Custom HTTP Proxy** (`agent.py` → `invoke_model()`):
- Endpoint: `AWS_ENDPOINT_URL` from `.env`
- Auth: `AWS_MODEL_KEY` bearer token
- Models: Hardcoded to Anthropic Claude 3 (Sonnet or Opus)
- Format: OpenAI-compatible (`messages` + `choices` format)
- Used by: All planning/classification/lightweight tasks

**AWS Bedrock** (`bedrock_agent.py` → deprecated):
- Endpoint: AWS Bedrock runtime (optional custom endpoint)
- Auth: AWS credentials
- Models: Anthropic Claude 3 (Sonnet or Opus)
- Status: **NOT CURRENTLY USED** (legacy code)

**Copilot CLI** (`workflow_ops.py::implement_plan()`):
- Command: `copilot -p <prompt> --allow-all-tools --allow-all-paths`
- Output: Natural language text (requires regex parsing via `copilot_output_parser.py`)
- Used by: Code implementation, test fixing, reviews
- Parsing: Fragile regex patterns for metrics extraction

### 1.3 Task Categorization for Model Routing

**Claude Sonnet 4.5** (Heavy lifting):
- Code implementation (implement_plan)
- Test failure resolution (resolve_failed_tests)
- Code review (run_review)
- Estimated tokens/cost: High

**GPT-4o mini** (Lightweight):
- Issue classification (classify_issue, extract_adw_info)
- Plan generation (build_plan) - planning is relatively lightweight
- Branch name generation (generate_branch_name)
- Commit message creation (create_commit)
- PR title/description (create_pull_request)
- Estimated tokens/cost: Low

### 1.4 Current Dependencies & Constraints

**Environment Variables**:
- `AWS_ENDPOINT_URL` - Custom proxy endpoint (REMOVE)
- `AWS_MODEL_KEY` - Custom proxy auth key (REMOVE)
- `AWS_MODEL` - Model override (REMOVE)
- `JIRA_SERVER`, `JIRA_USERNAME`, `JIRA_API_TOKEN` - Keep
- `BITBUCKET_WORKSPACE`, `BITBUCKET_REPO_NAME`, `BITBUCKET_API_TOKEN` - Keep

**Code Dependencies**:
- `agent.py` - Will be refactored to use OpenCode HTTP client
- `bedrock_agent.py` - Will be deprecated (contains duplicated code)
- `copilot_output_parser.py` - Will be refactored for structured Part parsing
- `workflow_ops.py` - Heavy refactoring for all LLM calls
- `adw_test.py`, `adw_review.py` - Update to use OpenCode HTTP API

---

## 2. OpenCode HTTP Server Analysis & Model Configuration

### 2.1 OpenCode Server Capabilities

| Aspect | Details |
|--------|---------|
| **Server Start** | `opencode serve --port 4096` |
| **API Type** | REST/HTTP with OpenAPI 3.1 spec |
| **Connection** | Python `requests` library to localhost:4096 |
| **Authentication** | Via `opencode auth login` or env vars (one-time) |
| **Session Management** | Sessions created and stored on server |
| **Output Format** | Structured Message + Part array (type-safe) |
| **Model Support** | Anthropic Claude (Sonnet, Opus), OpenAI (GPT-4, GPT-4o mini), others |

### 2.2 Supported Models & Pricing Tiers

**Claude Sonnet 4.5** (Heavy lifting):
- Model ID in OpenCode: `anthropic/claude-3-5-sonnet-20241022` OR `anthropic/claude-sonnet-4.5` (if available)
- Use for: Code implementation, test fixing, code reviews
- Cost: ~$3/M input, ~$15/M output (estimate)
- Latency: 2-5 seconds typical

**GPT-4o mini** (Lightweight):
- Model ID in OpenCode: `openai/gpt-4o-mini`
- Use for: Classification, planning, doc creation, branch names, commit messages
- Cost: ~$0.15/M input, ~$0.60/M output (estimate)
- Latency: 1-2 seconds typical

**Note**: Model IDs are in format `provider/model-name`. Verify exact IDs with OpenCode docs.

### 2.3 OpenCode HTTP API for Messages

**Create/Send Message**:
```http
POST /session/{id}/message
Content-Type: application/json

{
  "parts": [
    {
      "type": "text",
      "text": "Your prompt here"
    }
  ],
  "model": "anthropic/claude-3-5-sonnet-20241022"
}
```

**Response**:
```json
{
  "info": {
    "id": "msg-123",
    "sessionID": "sess-456",
    "createdAt": "2026-01-06T13:45:00Z",
    "role": "assistant",
    "status": "done"
  },
  "parts": [
    {
      "type": "text",
      "text": "I've implemented the feature..."
    },
    {
      "type": "tool_use",
      "tool": "bash",
      "input": {
        "command": "npm test"
      }
    },
    {
      "type": "tool_result",
      "tool": "bash",
      "output": "Tests passed: 42/42"
    }
  ]
}
```

**Advantages over current system**:
- ✅ Structured, typed response objects
- ✅ Clear Part type discrimination (text, tool_use, tool_result)
- ✅ No regex pattern matching needed
- ✅ Complete execution audit trail available
- ✅ Better error handling with HTTP status codes
- ✅ Flexible model selection per task
- ✅ No dependency on custom proxies or AWS Bedrock

---

## 3. Migration Strategy with Feature Flags (Safety-First Approach)

### 3.1 Critical Safety Mechanism: Feature Flags

**Problem Statement**: During migration, we could reach a point where ADWS can't fix itself if OpenCode integration is incomplete or broken.

**Solution**: Implement feature flags that allow instant rollback to old system.

```yaml
# .adw.yaml - Feature flags for safe migration
migration:
  # Enable OpenCode HTTP for different operation types
  use_opencode_for_lightweight: false  # Planning/classification (Epic 2)
  use_opencode_for_heavy_lifting: false  # Code execution (Epic 3)
  
  # Emergency override to disable OpenCode entirely
  disable_opencode: false  # Set to true if system breaks
```

**How it works**:
1. Each LLM operation checks its feature flag before executing
2. If flag is `false`, use old system (custom proxy or Copilot)
3. If flag is `true`, use OpenCode HTTP client
4. If OpenCode breaks, flip `disable_opencode: true` → system reverts to old backends
5. No code changes needed, just config change

**Implementation pattern**:
```python
def implement_plan(...) -> AgentPromptResponse:
    if config.migration.use_opencode_for_heavy_lifting:
        # NEW PATH: OpenCode HTTP
        return execute_opencode_prompt(...)
    else:
        # OLD PATH: Copilot CLI (still works)
        return subprocess.run(["copilot", "-p", prompt])
```

---

### 3.2 High-Level Approach (5 Epics = 43 Stories)

Based on JIRA_EPICS_AND_STORIES.md, organized as:

**Epic 1: HTTP Client Infrastructure (Phase 1 - 6-8 hours, CRITICAL PATH)**
- Create OpenCodeHTTPClient class with session management
- Implement HTTP communication layer
- Add data types (OpenCodeResponse, OpenCodePart)
- Build model routing logic (task-aware selection)
- Develop output parser for Part extraction
- Add response logging and error handling
- Implement retry logic with exponential backoff
- Write comprehensive unit tests (50+ tests)
- Add OpenCode configuration to .adw.yaml
- **Output**: Isolated infrastructure, no breaking changes

**Epic 2: Planning & Classification Operations (Phase 2 - 6-8 hours, depends on Epic 1)**
- Refactor agent.py execute_template() for OpenCode HTTP
- Migrate extract_adw_info() → GPT-4o mini
- Migrate classify_issue() → GPT-4o mini
- Migrate build_plan() → GPT-4o mini
- Migrate generate_branch_name() → GPT-4o mini
- Migrate create_commit() → GPT-4o mini
- Migrate create_pull_request() → GPT-4o mini
- Update error handling
- Write integration tests
- **Feature Flag**: `use_opencode_for_lightweight`
- **Can overlap**: With Epic 3

**Epic 3: Code Execution Operations (Phase 3 - 8-10 hours, depends on Epic 1)**
- Refactor implement_plan() → Claude Sonnet 4.5
- Refactor resolve_failed_tests() → Claude Sonnet 4.5
- Refactor execute_single_e2e_test() → Claude Sonnet 4.5
- Refactor run_review() → Claude Sonnet 4.5
- Update error handling in adw_test.py
- Update error handling in adw_review.py
- Write integration tests
- Test git fallback validation
- **Feature Flag**: `use_opencode_for_heavy_lifting`
- **Can overlap**: With Epic 2

**Epic 4: Cleanup & Deprecated Code (Phase 4 - 2-3 hours, depends on Epics 2 & 3)**
- Mark bedrock_agent.py as deprecated
- Mark copilot_output_parser.py as deprecated
- Remove AWS environment variable validation
- Update health_check.py for OpenCode
- Remove Copilot CLI checks
- **Only after**: Both lightweight and heavy lifting are stable

**Epic 5: Testing, Validation & Documentation (Phase 5 - 10-12 hours, final)**
- Write unit tests for HTTP client (30+ tests)
- Write unit tests for output parser (20+ tests)
- Write integration tests for planning operations
- Write integration tests for code execution operations
- Write regression tests for all 9 LLM operations
- Performance comparison vs old system
- Update AGENTS.md with OpenCode section
- Create comprehensive MIGRATION_GUIDE.md
- Update .adw.yaml with examples
- Update README.md setup instructions
- Write troubleshooting guide
- **Must complete last**: Validates everything

---

### 3.3 Implementation Details

---

## 4. Implementation Details

### 4.1 New Module: `opencode_http_client.py`

**Location**: `scripts/adw_modules/opencode_http_client.py`

**Responsibilities**:
- Connect to running OpenCode HTTP server
- Create and manage sessions
- Send prompts with model selection
- Retrieve structured responses
- Parse Message/Part objects
- Extract execution details from Parts
- Handle model-aware routing

**Key Functions**:

```python
class OpenCodeHTTPClient:
    """HTTP client for OpenCode server API with model routing."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:4096",
        timeout_seconds: int = 600,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize HTTP client."""
        self.base_url = base_url
        self.timeout = timeout_seconds
        self.logger = logger or logging.getLogger(__name__)
    
    def check_connection(self) -> bool:
        """Verify server is running and accessible."""
        pass
    
    def create_session(self, title: Optional[str] = None) -> str:
        """Create new OpenCode session. Returns session ID."""
        pass
    
    def send_prompt(
        self,
        session_id: str,
        prompt: str,
        model: str,  # "anthropic/claude-3-5-sonnet-20241022" or "openai/gpt-4o-mini"
    ) -> "OpenCodeResponse":
        """
        Send prompt to session with specified model, get structured response.
        
        Args:
            session_id: OpenCode session ID
            prompt: The instruction/prompt text
            model: Model to use (e.g., "anthropic/claude-3-5-sonnet-20241022" for heavy lifting,
                   "openai/gpt-4o-mini" for lightweight tasks)
        
        Returns:
            OpenCodeResponse with Message + Parts
        """
        pass
    
    def close_session(self, session_id: str) -> bool:
        """Close and cleanup session."""
        pass

# Model selection constants
MODEL_HEAVY_LIFTING = "anthropic/claude-3-5-sonnet-20241022"  # Code implementation, reviews
MODEL_LIGHTWEIGHT = "openai/gpt-4o-mini"  # Planning, classification, doc creation

def get_model_for_task(task_type: str) -> str:
    """
    Get appropriate model for task type.
    
    Args:
        task_type: One of "classify", "plan", "implement", "test_fix", "review", 
                   "branch_gen", "commit_msg", "pr_creation", "extract_adw"
    
    Returns:
        Model ID string for OpenCode
    """
    heavy_tasks = {"implement", "test_fix", "review"}
    return MODEL_HEAVY_LIFTING if task_type in heavy_tasks else MODEL_LIGHTWEIGHT

def check_opencode_server_available(
    server_url: str = "http://localhost:4096"
) -> bool:
    """Check if OpenCode server is running."""
    pass

def execute_opencode_prompt(
    prompt: str,
    task_type: str,  # Used to determine model
    working_dir: str = ".",
    server_url: str = "http://localhost:4096",
    model_override: Optional[str] = None,  # Allow explicit model selection
    timeout_seconds: int = 600,
    logger: Optional[logging.Logger] = None,
) -> "OpenCodeResponse":
    """
    Execute prompt via OpenCode HTTP API with intelligent model selection.
    
    This is the main entry point for executing prompts.
    Uses get_model_for_task() unless model_override is provided.
    """
    pass
```

### 4.2 New Data Types: `data_types.py`

**Location**: Add to `scripts/adw_modules/data_types.py`

```python
class OpenCodePart(BaseModel):
    """Individual part of OpenCode message response."""
    
    type: str  # "text", "tool_use", "tool_result", "code_block"
    text: Optional[str] = None
    tool: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    language: Optional[str] = None
    code: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)

class OpenCodeMessageInfo(BaseModel):
    """Metadata about OpenCode message."""
    
    id: str
    sessionID: str
    createdAt: str
    role: str  # "user" or "assistant"
    status: str  # "done", "running", etc.
    
    model_config = ConfigDict(populate_by_name=True)

class OpenCodeResponse(BaseModel):
    """Response from OpenCode HTTP API."""
    
    info: OpenCodeMessageInfo
    parts: List[OpenCodePart]
    
    model_config = ConfigDict(populate_by_name=True)
    
    def get_text_response(self) -> str:
        """Extract main text response from parts."""
        pass
    
    def count_tool_uses(self) -> int:
        """Count tool_use parts in response."""
        pass
    
    def get_tool_results(self) -> List[Dict[str, Any]]:
        """Extract all tool_result parts as dicts."""
        pass
    
    def estimate_files_changed(self) -> int:
        """Estimate files changed from tool outputs (heuristic)."""
        pass
```

### 4.3 Output Parser: `opencode_output_parser.py`

**Location**: `scripts/adw_modules/opencode_output_parser.py`

**Strategy**: Extract metrics from Part types (much simpler than regex)

```python
def extract_text_response(
    parts: List[OpenCodePart]
) -> str:
    """Extract all text parts and concatenate."""
    pass

def extract_tool_execution_details(
    parts: List[OpenCodePart]
) -> Dict[str, Any]:
    """
    Extract tool execution details from Parts.
    
    Counts tool_use and tool_result occurrences.
    Extracts output/errors from tool_result parts.
    """
    pass

def estimate_metrics_from_parts(
    parts: List[OpenCodePart],
    fallback_git_count: int = 0,
) -> Dict[str, Any]:
    """
    Estimate execution metrics from Parts.
    
    Returns:
        dict with files_changed, lines_added, lines_removed
    """
    # Heuristic: count tool uses as proxy for complexity
    # Extract regex patterns from tool_result outputs if available
    # Fallback to git count if heuristic unreliable
    pass

def convert_to_agent_response(
    opencode_response: OpenCodeResponse,
    fallback_git_count: int = 0,
) -> AgentPromptResponse:
    """
    Convert OpenCode response to AgentPromptResponse.
    Maintains backward compatibility with existing code.
    """
    text = extract_text_response(opencode_response.parts)
    tools = extract_tool_execution_details(opencode_response.parts)
    metrics = estimate_metrics_from_parts(
        opencode_response.parts,
        fallback_git_count
    )
    
    return AgentPromptResponse(
        output=text,
        success=opencode_response.info.status == "done",
        files_changed=metrics.get("files_changed", fallback_git_count),
        lines_added=metrics.get("lines_added", 0),
        lines_removed=metrics.get("lines_removed", 0),
        errors=metrics.get("errors", []),
        warnings=metrics.get("warnings", []),
    )

def save_response_log(
    adw_id: str,
    agent_name: str,
    response: OpenCodeResponse,
    logger: Optional[logging.Logger] = None,
) -> Path:
    """
    Save OpenCode response to log file.
    
    Location: ai_docs/logs/<adw_id>/<agent_name>/response_<timestamp>.json
    """
    pass
```

### 4.4 Configuration

**Location**: `.adw.yaml`

```yaml
# OpenCode HTTP Server configuration
opencode:
  # Server connection
  server_url: "http://localhost:4096"
  
  # Model selection per task type
  models:
    # Heavy lifting: code implementation, test fixing, code reviews
    heavy_lifting: "anthropic/claude-3-5-sonnet-20241022"
    
    # Lightweight: planning, classification, document creation
    lightweight: "openai/gpt-4o-mini"
  
  # Execution options
  timeout: 600  # seconds (10 minutes for code execution)
  lightweight_timeout: 60  # seconds (1 minute for planning/classification)
  max_retries: 3
  
  # Session management
  reuse_sessions: false  # Create new session for each execution
  
  # Note: Requires running: opencode serve --port 4096
  requires_server: true
```

**Location**: `AGENTS.md` (Setup Section)

```markdown
## OpenCode HTTP Server Setup

OpenCode must be running as a background HTTP server.

### 1. Installation

```bash
# Install OpenCode CLI
brew install opencode
# OR: npm install -g opencode-ai
```

### 2. Start Server

```bash
# Terminal 1: Start OpenCode HTTP server
opencode serve --port 4096

# Output will show: Server running at http://localhost:4096
```

### 3. Authentication (One-time)

```bash
# Terminal 2: Authenticate
opencode auth login

# Select provider:
# - Anthropic (for Claude Sonnet 4.5)
# - OpenAI (for GPT-4o mini)
# - Others as needed
# Paste API key when prompted
```

### 4. Configure ADWS

Edit `.adw.yaml`:

```yaml
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "anthropic/claude-3-5-sonnet-20241022"
    lightweight: "openai/gpt-4o-mini"
  timeout: 600
  lightweight_timeout: 60
```

### 5. Verify Setup

```bash
# Check server is responding
curl http://localhost:4096/global/health

# Expected output:
# {"healthy":true,"version":"..."}
```

### Model Configuration Notes

**Claude Sonnet 4.5 Setup**:
1. Get API key from Anthropic console (https://console.anthropic.com)
2. Run: `opencode auth login` and select Anthropic
3. Paste API key
4. Verify with: `opencode config list`

**GPT-4o mini Setup**:
1. Get API key from OpenAI (https://platform.openai.com/api-keys)
2. Run: `opencode auth login` and select OpenAI
3. Paste API key
4. Verify with: `opencode config list`

### Troubleshooting

- **Connection refused**: Make sure `opencode serve` is running
- **401 Unauthorized**: Run `opencode auth login` to authenticate
- **Model not found**: Verify model name with `opencode config list`
- **Timeout errors**: Increase `timeout` value in `.adw.yaml`
- **Stuck requests**: Restart server with `opencode serve --port 4096`

See [OpenCode Documentation](https://opencode.ai/docs/cli/) for more details.
```

### 4.5 Refactoring `workflow_ops.py::implement_plan()`

**Current Implementation** (lines 203-340):
- Loads plan file
- Creates prompt with plan content
- Invokes Copilot CLI with `-p` flag
- Parses output with regex patterns
- Verifies changes with git

**New Implementation**:

```python
def implement_plan(
    plan_file: str,
    adw_id: str,
    target_dir: str = ".",
    logger: Optional[logging.Logger] = None,
) -> AgentPromptResponse:
    """
    Implement the plan using OpenCode HTTP API with structured output parsing.
    """
    logger = logger or logging.getLogger(__name__)
    
    # Load plan
    try:
        with open(plan_file, "r") as f:
            plan_content = f.read()
    except FileNotFoundError:
        error_msg = f"Plan file not found: {plan_file}"
        logger.error(error_msg)
        return AgentPromptResponse(output=error_msg, success=False)
    
    # Create prompt (same as before)
    prompt = _build_implementation_prompt(plan_content)
    
    # Check OpenCode server availability
    server_url = config.opencode.get("server_url", "http://localhost:4096")
    if not check_opencode_server_available(server_url):
        error_msg = f"OpenCode server not responding at {server_url}"
        logger.error(error_msg)
        return AgentPromptResponse(output=error_msg, success=False)
    
    # Execute with OpenCode
    logger.info(f"Executing plan via OpenCode: {plan_file}")
    try:
        opencode_response = execute_opencode_prompt(
            prompt=prompt,
            working_dir=target_dir,
            server_url=server_url,
            model=config.opencode.get("model"),
            timeout_seconds=config.opencode.get("timeout", 600),
            logger=logger,
        )
    except TimeoutError:
        error_msg = "OpenCode execution timeout"
        logger.error(error_msg)
        return AgentPromptResponse(output=error_msg, success=False)
    except Exception as e:
        error_msg = f"OpenCode execution failed: {e}"
        logger.error(error_msg)
        return AgentPromptResponse(output=error_msg, success=False)
    
    # Verify with git (fallback validation)
    git_verified = False
    files_changed_in_git = 0
    try:
        git_changeset = get_file_changes(cwd=target_dir)
        files_changed_in_git = git_changeset.total_files_changed
        logger.info(f"Git verification: {files_changed_in_git} files changed")
        git_verified = True
    except Exception as e:
        logger.warning(f"Could not verify git changes: {e}")
    
    # Log response for debugging
    save_response_log(adw_id, "sdlc_implementor", opencode_response, logger)
    
    # Build final response
    final_response = convert_to_agent_response(
        opencode_response,
        fallback_git_count=files_changed_in_git,
    )
    
    # Override success if git verification available
    final_response.success = final_response.success or (
        git_verified and files_changed_in_git > 0
    )
    
    return final_response
```

### 4.6 Error Handling Updates

**Changes to `adw_test.py` and `adw_review.py`**:

Replace:
```python
if not shutil.which("copilot"):
    error_msg = "The 'copilot' command was not found..."
    sys.exit(1)
```

With:
```python
from scripts.adw_modules.opencode_http_client import check_opencode_server_available
from scripts.adw_modules.config import config

server_url = config.opencode.get("server_url", "http://localhost:4096")
if not check_opencode_server_available(server_url):
    error_msg = f"OpenCode server not running at {server_url}"
    print(error_msg, file=sys.stderr)
    print("", file=sys.stderr)
    print("Start OpenCode server with:", file=sys.stderr)
    print("  opencode serve --port 4096", file=sys.stderr)
    sys.exit(1)
```

---

## 5. Migration Path

### Phase 1: HTTP Client Infrastructure (6-8 hours)

**Critical Path Item**: Must complete before other phases

**Tasks**:
- [ ] Create `opencode_http_client.py` module:
  - [ ] `OpenCodeHTTPClient` class for HTTP communication
  - [ ] Model routing logic (`get_model_for_task()`)
  - [ ] `check_opencode_server_available()` function
  - [ ] `execute_opencode_prompt()` main entry point with task-aware model selection
  - [ ] Connection retry logic with exponential backoff
  - [ ] Error handling for HTTP failures (connection, timeout, auth, validation)
  
- [ ] Create `opencode_output_parser.py` module:
  - [ ] Part extraction functions (text, tool_use, tool_result)
  - [ ] Metric estimation from Parts
  - [ ] `convert_to_agent_response()` bridge function for backward compatibility
  - [ ] Response logging to JSON
  - [ ] Handle edge cases (empty responses, malformed JSON, missing metrics)

- [ ] Add data types to `data_types.py`:
  - [ ] `OpenCodePart`
  - [ ] `OpenCodeMessageInfo`
  - [ ] `OpenCodeResponse`
  - [ ] Methods for extracting data from Parts
  
- [ ] Update `config.py`:
  - [ ] Add OpenCode server configuration loading
  - [ ] Add model mapping configuration
  - [ ] Validate server URL on startup
  - [ ] Provide helpful error messages if server not available

- [ ] Unit tests:
  - [ ] `test_http_client.py` (~250 lines)
  - [ ] `test_output_parser.py` (~200 lines)
  - [ ] Test with mock HTTP responses
  - [ ] Edge cases and error handling
  - [ ] Model routing logic verification

**Files to Create**:
- `scripts/adw_modules/opencode_http_client.py` (~300 lines)
- `scripts/adw_modules/opencode_output_parser.py` (~250 lines)
- `scripts/adw_tests/test_http_client.py` (~250 lines)
- `scripts/adw_tests/test_output_parser.py` (~200 lines)

**Critical Success Metrics**:
- [ ] HTTP client successfully connects to OpenCode server
- [ ] Messages can be sent and responses parsed
- [ ] Part types are correctly identified
- [ ] Model routing selects correct model based on task type
- [ ] Metrics estimated from Parts
- [ ] All tests pass (minimum 50 tests)

### Phase 2: Refactor AI Planning/Classification Operations (6-8 hours)

**Critical Path Item**: Depends on Phase 1

Refactor `agent.py::execute_template()` and all workflow_ops.py LLM calls to use OpenCode HTTP client:

**Tasks**:
- [ ] Refactor `agent.py::execute_template()`:
  - [ ] Replace custom proxy with OpenCode HTTP client
  - [ ] Add model parameter handling
  - [ ] Update error handling
  - [ ] Keep backward compatibility with existing calls
  
- [ ] Update `workflow_ops.py::extract_adw_info()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="extract_adw"
  - [ ] Model: lightweight (GPT-4o mini)
  
- [ ] Update `workflow_ops.py::classify_issue()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="classify"
  - [ ] Model: lightweight (GPT-4o mini)
  - [ ] Verify classification parsing still works
  
- [ ] Update `workflow_ops.py::build_plan()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="plan"
  - [ ] Model: lightweight (GPT-4o mini)
  - [ ] Verify plan format still correct
  
- [ ] Update `workflow_ops.py::generate_branch_name()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="branch_gen"
  - [ ] Model: lightweight (GPT-4o mini)
  
- [ ] Update `workflow_ops.py::create_commit()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="commit_msg"
  - [ ] Model: lightweight (GPT-4o mini)
  
- [ ] Update `workflow_ops.py::create_pull_request()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="pr_creation"
  - [ ] Model: lightweight (GPT-4o mini)

**Files to Modify**:
- `scripts/adw_modules/agent.py` (refactor execute_template)
- `scripts/adw_modules/workflow_ops.py` (update all LLM calls)

**Key Success Metrics**:
- [ ] All 6 planning/classification functions execute via OpenCode
- [ ] Correct models selected (all lightweight except where heavy lifting needed)
- [ ] No regressions in classification/planning functionality
- [ ] Proper logging of all interactions
- [ ] Error messages guide users to fix issues

### Phase 3: Refactor Code Execution Operations (8-10 hours)

**Critical Path Item**: Depends on Phase 1

Replace Copilot CLI with OpenCode HTTP API for code operations:

**Tasks**:
- [ ] Refactor `workflow_ops.py::implement_plan()`:
  - [ ] Replace Copilot CLI with `execute_opencode_prompt()`
  - [ ] Use task_type="implement" → Model: Claude Sonnet 4.5
  - [ ] Parse response Parts for implementation details
  - [ ] Keep git verification as fallback
  - [ ] Use `convert_to_agent_response()` for response building
  - [ ] Add comprehensive logging and error handling
  - [ ] Test with sample plans
  
- [ ] Refactor `adw_test.py::resolve_failed_tests()`:
  - [ ] Replace Copilot CLI with `execute_opencode_prompt()`
  - [ ] Use task_type="test_fix" → Model: Claude Sonnet 4.5
  - [ ] Parse response Parts for error details
  - [ ] Extract files changed for Jira comment
  - [ ] Update error reporting
  
- [ ] Refactor `adw_test.py::execute_single_e2e_test()`:
  - [ ] Update to use OpenCode HTTP API
  - [ ] Use task_type="test_fix" → Model: Claude Sonnet 4.5
  - [ ] Add structured parsing (currently just checks exit code)
  - [ ] Extract test metrics from response
  
- [ ] Refactor `adw_test.py::resolve_failed_e2e_tests()`:
  - [ ] Use `execute_opencode_prompt()` with task_type="test_fix"
  - [ ] Model: Claude Sonnet 4.5
  - [ ] Use structured response parsing
  - [ ] Improve error reporting
  
- [ ] Refactor `adw_review.py::run_review()`:
  - [ ] Replace Copilot CLI invocation with `execute_opencode_prompt()`
  - [ ] Use task_type="review" → Model: Claude Sonnet 4.5
  - [ ] Parse response Parts for review findings
  - [ ] Build ReviewResult object from parsed data
  - [ ] Handle review-specific metrics

**Files to Modify**:
- `scripts/adw_modules/workflow_ops.py` (implement_plan function)
- `scripts/adw_test.py` (4 functions: resolve_failed_tests, execute_single_e2e_test, resolve_failed_e2e_tests)
- `scripts/adw_review.py` (run_review function)

**Key Success Metrics**:
- [ ] All 5 code execution functions use OpenCode with Claude Sonnet 4.5
- [ ] Structured Part parsing replaces Copilot text parsing
- [ ] Git fallback still works for validation
- [ ] Error messages are helpful
- [ ] Proper logging of all interactions
- [ ] No regressions in functionality

### Phase 4: Cleanup & Validation (2-3 hours)

**Tasks**:
- [ ] Deprecate old code:
  - [ ] Mark `bedrock_agent.py` as deprecated (unused legacy code)
  - [ ] Mark `copilot_output_parser.py` as deprecated
  - [ ] Add deprecation notices at top of files
  - [ ] Keep files for reference only
  
- [ ] Remove old environment variable checks:
  - [ ] Remove `AWS_ENDPOINT_URL` validation
  - [ ] Remove `AWS_MODEL_KEY` validation
  - [ ] Remove `AWS_MODEL` usage
  - [ ] Update adw_test.py and adw_review.py copilot checks
  - [ ] Replace with OpenCode server checks
  
- [ ] Validate response logging:
  - [ ] Verify logs created in correct locations
  - [ ] Check JSON format is correct
  - [ ] Test with multiple executions

**Files to Modify**:
- `scripts/adw_modules/bedrock_agent.py` (add deprecation notice)
- `scripts/adw_modules/copilot_output_parser.py` (add deprecation notice)
- `scripts/adw_test.py` (remove copilot checks)
- `scripts/adw_review.py` (remove copilot checks)
- `scripts/adw_modules/health_check.py` (update checks)

### Phase 5: Testing, Validation & Documentation (10-12 hours)

**Critical Path Item**: Must validate all 9 LLM operations

**Testing Tasks**:
- [ ] Unit Tests (4-5 hours):
  - [ ] Test HTTP client with mock server responses
  - [ ] Test all Part parsing functions
  - [ ] Test response conversion
  - [ ] Test model routing logic
  - [ ] Edge cases (timeout, connection error, malformed response, empty response)
  - [ ] Minimum 60 tests
  
- [ ] Integration Tests (4-5 hours):
  - [ ] Test all 6 planning/classification functions (lightweight model)
  - [ ] Test all 3 code execution functions (heavy model)
  - [ ] Test with real OpenCode server (requires real API keys)
  - [ ] Test model selection per task
  - [ ] Test timeout behavior
  - [ ] Test error recovery
  
- [ ] Validation (2 hours):
  - [ ] Verify all 9 LLM operations work correctly
  - [ ] Check git fallback works
  - [ ] Verify response logs created
  - [ ] Performance testing (compare with old system)
  - [ ] Cost estimation (lightweight vs heavy models)

**Documentation Tasks** (2-3 hours):
- [ ] Update `AGENTS.md`:
  - [ ] Document OpenCode HTTP server setup
  - [ ] Document model selection strategy
  - [ ] Document task types and models
  - [ ] Add troubleshooting section
  - [ ] Document configuration options
  
- [ ] Create `MIGRATION_GUIDE.md`:
  - [ ] Step-by-step migration instructions
  - [ ] Server setup procedure
  - [ ] Model configuration
  - [ ] Expected response structure
  - [ ] Common issues and solutions
  - [ ] Cost comparison (old vs new)
  
- [ ] Update `.adw.yaml`:
  - [ ] Add OpenCode configuration examples
  - [ ] Document all options
  - [ ] Add comments explaining model choices
  
- [ ] Update code comments:
  - [ ] Document HTTP client strategy
  - [ ] Document Part extraction logic
  - [ ] Document model routing decisions

**Files to Create/Modify**:
- Tests: Comprehensive test suite (~600 lines total)
- `AGENTS.md` - Add OpenCode HTTP section
- `ai_docs/specs/MIGRATION_GUIDE.md` - New guide
- `.adw.yaml` - Add OpenCode config examples
- `README.md` - Update setup instructions

---

## 6. Known Risks & Mitigation

### 6.1 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| OpenCode server not running | Medium | High | Check at startup, guide user to start it |
| Authentication failures | Medium | High | Pre-check auth, suggest `opencode auth login` |
| Connection timeouts | Medium | Medium | Implement retry logic, increase timeout |
| HTTP API changes | Low | Medium | Pin OpenCode version, add compatibility checks |
| Server stability | Low | Medium | Implement reconnection logic, proper error handling |
| Port conflicts (4096 in use) | Low | Low | Document alternative port setup |

### 6.2 Mitigation Strategies

1. **Health Check**: Call `/global/health` on startup to verify server
2. **Graceful Failures**: Clear error messages with recovery steps
3. **Retry Logic**: Automatic reconnection with exponential backoff
4. **Version Pinning**: Specify minimum OpenCode version requirements
5. **Extensive Testing**: Unit + integration tests for all scenarios
6. **Clear Documentation**: Setup guide, troubleshooting section
7. **Rollback Plan**: Keep Copilot code available if needed

---

## 7. Testing Strategy

### 7.1 Unit Tests

**File**: `scripts/adw_tests/test_http_client.py`

- [ ] `test_check_server_available()` - Health check
- [ ] `test_create_session()` - Session creation
- [ ] `test_send_prompt_success()` - Successful prompt
- [ ] `test_send_prompt_timeout()` - Timeout handling
- [ ] `test_send_prompt_server_error()` - Server error handling
- [ ] `test_parse_response_parts()` - Part parsing
- [ ] `test_connection_retry()` - Retry logic
- [ ] `test_malformed_response()` - Error handling

**File**: `scripts/adw_tests/test_output_parser.py`

- [ ] `test_extract_text_response()` - Text extraction
- [ ] `test_extract_tool_uses()` - Tool use counting
- [ ] `test_estimate_metrics()` - Metric estimation
- [ ] `test_convert_to_agent_response()` - Response conversion
- [ ] `test_edge_cases()` - Empty/minimal responses
- [ ] `test_complex_responses()` - Multiple tool uses

### 7.2 Integration Tests

**File**: `scripts/adw_tests/test_integration_opencode.py`

- [ ] `test_implement_plan_complete()` - Full plan execution
- [ ] `test_implement_plan_with_errors()` - Plan with errors
- [ ] `test_resolve_failed_tests()` - Test failure fixing
- [ ] `test_e2e_test_execution()` - E2E test running
- [ ] `test_code_review()` - Code review execution
- [ ] `test_git_fallback_validation()` - Git verification

### 7.3 Regression Tests

- [ ] Ensure existing test suite still passes
- [ ] Verify all adw_* scripts run without errors
- [ ] Check console output consistency

---

## 8. Configuration & Setup

### 8.1 Installation

Users must have OpenCode installed and running:

```bash
# Install OpenCode CLI
brew install opencode
# OR: npm install -g opencode-ai
```

### 8.2 Start HTTP Server

**Terminal 1** - Start server:
```bash
opencode serve --port 4096
# Output: Server running at http://localhost:4096
```

**Terminal 2** - Authenticate (one-time):
```bash
opencode auth login
# Select provider and paste API key
```

### 8.3 Configuration in ADWS

Update `.adw.yaml`:

```yaml
opencode:
  server_url: "http://localhost:4096"
  model: "anthropic/claude-3-5-sonnet-20241022"
  timeout: 600
  max_retries: 3
  reuse_sessions: false
```

### 8.4 Verification

```bash
# Check server is responding
curl http://localhost:4096/global/health

# Expected: {"healthy":true,"version":"..."}
```

---

## 8. Timeline Estimate (5 Epics = 43 Stories)

**Reference**: See JIRA_EPICS_AND_STORIES.md for all detailed story definitions with acceptance criteria

| Epic | Phase | Duration | Start | End | Critical Path | Stories |
|------|-------|----------|-------|-----|----------------|---------|
| Epic 1 | Phase 1: HTTP Client Infrastructure | **6-8 hours** | Day 1 | Day 1 | **YES** | 10 stories |
| Epic 2 | Phase 2: Planning/Classification Operations | **6-8 hours** | Day 2 | Day 2-3 | **YES** | 9 stories |
| Epic 3 | Phase 3: Code Execution Operations | **8-10 hours** | Day 2-3 | Day 4-5 | **YES** | 8 stories |
| Epic 4 | Phase 4: Cleanup & Deprecated Code | **2-3 hours** | Day 5 | Day 5 | NO | 5 stories |
| Epic 5 | Phase 5: Testing & Documentation | **10-12 hours** | Day 5-6 | Day 7-8 | **YES** | 11 stories |
| **Total** | | **40-50 hours** | **Day 1** | **Day 8** | **All sequential** | **43 stories** |

**Key Dependencies**:
1. **Epic 1 MUST complete first** (provides HTTP client infrastructure for all other epics)
2. **Epic 2 and Epic 3 can run in parallel** (both depend on Epic 1, saves 6-8 hours)
3. **Epic 4 depends on Epics 2 & 3** (cleanup only after new systems are stable)
4. **Epic 5 must run last** (validates all changes)

**Recommended Approach**: 
- 1-2 weeks of focused development
- Epic 1 is critical path - get this right first
- Epic 2 and 3 can proceed in parallel after Epic 1 completes
- Epic 5 is thorough - don't skip testing
- **With parallelization: 28-32 hours minimum**

---

## 9. Success Criteria

- [ ] **All 9 LLM operations** successfully use OpenCode HTTP API
  - [ ] 6 planning/classification operations use lightweight model (GPT-4o mini)
  - [ ] 3 code execution operations use heavy model (Claude Sonnet 4.5)
- [ ] **Structured Part parsing** is more reliable than regex-based parsing
- [ ] **Model routing** correctly selects appropriate models per task
- [ ] **No regressions** in existing functionality
- [ ] **All tests pass** (unit + integration + regression)
- [ ] **Documentation** updated and clear
- [ ] **Performance** is comparable or better than old system
- [ ] **Cost efficiency** improved (uses cheaper models for lightweight tasks)
- [ ] **Error messages** are helpful and actionable
- [ ] **Migration** can be completed without downtime

---

## 10. Rollback Plan

If issues arise during migration:

1. **Keep Old Code**: Don't delete `agent.py`, `bedrock_agent.py`, or `copilot_output_parser.py`
2. **Feature Flag**: Add `use_opencode: true/false` in `.adw.yaml` to switch implementations
3. **Version Tagging**: Tag current version before migration
4. **Git Branches**: Create `migrate/opencode-complete` branch for development

---

## 11. Post-Migration

### 11.1 Documentation Updates

- [ ] Update `README.md` with OpenCode HTTP setup
- [ ] Update `AGENTS.md` with OpenCode specifics
- [ ] Create `MIGRATION_GUIDE.md` for users
- [ ] Add troubleshooting guide
- [ ] Document configuration options
- [ ] Document model selection strategy

### 11.2 Monitoring & Observability

- [ ] Add execution metrics logging (track model usage per task)
- [ ] Track success/failure rates by task type
- [ ] Monitor timeout frequency
- [ ] Log cost metrics (lightweight vs heavy tasks)
- [ ] Alert on connection failures
- [ ] Compare performance with old system

### 11.3 Future Improvements

- [ ] Session reuse optimization for faster execution
- [ ] Connection pooling for multiple concurrent requests
- [ ] Cost optimization (use smaller models where appropriate)
- [ ] Integration with OpenCode GitHub agent
- [ ] Custom agent development with OpenCode
- [ ] Performance optimization (caching, batching)
- [ ] Support for additional models as they become available

---

## 12. Architecture Comparison: Old vs New

| Aspect | Old System | New System |
|--------|-----------|-----------|
| **Planning/Classification** | Custom proxy + Bedrock | OpenCode HTTP + GPT-4o mini |
| **Code Execution** | Copilot CLI | OpenCode HTTP + Claude Sonnet 4.5 |
| **Code Implementation** | Copilot CLI | OpenCode HTTP + Claude Sonnet 4.5 |
| **Test Fixing** | Copilot CLI | OpenCode HTTP + Claude Sonnet 4.5 |
| **Code Review** | Copilot CLI | OpenCode HTTP + Claude Sonnet 4.5 |
| **Output Parsing** | Regex on text | Structured Part types |
| **Model Selection** | Hardcoded | Dynamic per task type |
| **API Type** | Multiple (proxy, CLI, Bedrock) | Single HTTP API |
| **Setup Complexity** | High (proxy + CLI + Bedrock) | Medium (single server) |
| **Cost** | Fixed per model | Variable (lightweight + heavy) |
| **Maintainability** | Low (regex brittle) | High (structured data) |
| **Testability** | Difficult (CLI mocking) | Easy (HTTP mocking) |

---

## Appendix A: File Checklist

### Files to Create

**Core Infrastructure**:
- [ ] `scripts/adw_modules/opencode_http_client.py` (~300 lines) - HTTP client with model routing
- [ ] `scripts/adw_modules/opencode_output_parser.py` (~250 lines) - Part parsing and conversion

**Tests**:
- [ ] `scripts/adw_tests/test_http_client.py` (~250 lines)
- [ ] `scripts/adw_tests/test_output_parser.py` (~200 lines)
- [ ] `scripts/adw_tests/test_integration_opencode.py` (~150 lines)

**Documentation**:
- [ ] `ai_docs/specs/MIGRATION_GUIDE.md` (user-facing guide)

### Files to Modify

**Core Application Logic**:
- [ ] `scripts/adw_modules/data_types.py` (add OpenCode types)
- [ ] `scripts/adw_modules/config.py` (add OpenCode config + model mapping)
- [ ] `scripts/adw_modules/agent.py` (refactor execute_template for OpenCode)
- [ ] `scripts/adw_modules/workflow_ops.py` (update all 6 LLM calls)
- [ ] `scripts/adw_test.py` (update 3 functions for code execution)
- [ ] `scripts/adw_review.py` (update run_review function)

**Documentation**:
- [ ] `AGENTS.md` (add OpenCode HTTP server section + model selection strategy)
- [ ] `.adw.yaml` (add OpenCode configuration examples)
- [ ] `README.md` (update setup instructions)

### Files to Deprecate (Keep for Reference)

- [ ] `scripts/adw_modules/bedrock_agent.py` (legacy, not currently used)
- [ ] `scripts/adw_modules/copilot_output_parser.py` (replaced by opencode_output_parser)

---

## Appendix B: Model Configuration Reference

### Claude Sonnet 4.5

**When to use**: Heavy code lifting
- Code implementation (creating new files, refactoring)
- Test failure resolution (debugging, fixing)
- Code review (analyzing logic, security, performance)
- Context window: 200K tokens (can handle large codebases)
- Speed: 2-5 seconds typical
- Cost: ~$3/M input, ~$15/M output tokens

**Model ID**: `anthropic/claude-3-5-sonnet-20241022` (or `anthropic/claude-sonnet-4.5` if available)

### GPT-4o mini

**When to use**: Lightweight tasks
- Issue classification
- Implementation planning
- Branch name generation
- Commit message creation
- PR title/description
- ADW classification
- Context window: 128K tokens (sufficient for task context)
- Speed: 1-2 seconds typical
- Cost: ~$0.15/M input, ~$0.60/M output tokens

**Model ID**: `openai/gpt-4o-mini`

### Cost Estimation Example

**Monthly usage** (assuming 100 workflows):
- 100 lightweight tasks (GPT-4o mini):
  - ~1,000,000 input tokens × $0.15 = **$150**
  - ~500,000 output tokens × $0.60 = **$300**
  - Subtotal: **$450**

- 100 code implementation tasks (Claude Sonnet 4.5):
  - ~10,000,000 input tokens × $3 = **$30,000** (large codebases)
  - ~5,000,000 output tokens × $15 = **$75,000** (extensive implementations)
  - Subtotal: **$105,000**

**Total estimated monthly**: **$105,450** (heavily dependent on codebase size and complexity)

**Compared to old system**:
- Old: All operations on fixed cost model (Bedrock/proxy)
- New: Tiered approach (cheap for planning, expensive for code)
- Net: Could be cheaper if planning tasks dominate, or more expensive if code tasks dominate

---

## Appendix C: Integration Point Details

### 1. extract_adw_info() - ADW Classification
- **Location**: `workflow_ops.py:51-88`
- **Task Type**: "extract_adw"
- **Model**: lightweight (GPT-4o mini)
- **Input**: Natural language text
- **Output**: ADW workflow command + ID
- **Parsing**: JSON response with `adw_slash_command` and `adw_id` fields

### 2. classify_issue() - Issue Classification
- **Location**: `workflow_ops.py:91-138`
- **Task Type**: "classify"
- **Model**: lightweight (GPT-4o mini)
- **Input**: GitHub issue (number, title, body)
- **Output**: Slash command (/chore, /bug, /feature, /new)
- **Parsing**: Regex match on response text

### 3. build_plan() - Implementation Planning
- **Location**: `workflow_ops.py:141-196`
- **Task Type**: "plan"
- **Model**: lightweight (GPT-4o mini)
- **Input**: Full issue context with description, labels, state
- **Output**: Step-by-step implementation plan
- **Parsing**: Markdown plan structure

### 4. generate_branch_name() - Branch Generation
- **Location**: `workflow_ops.py:349-397`
- **Task Type**: "branch_gen"
- **Model**: lightweight (GPT-4o mini)
- **Input**: Issue type, ADW ID, issue JSON
- **Output**: Git branch name (format: `{type}-issue-{number}-adw-{id}-{name}`)
- **Parsing**: Regex pattern matching

### 5. create_commit() - Commit Message
- **Location**: `workflow_ops.py:400-438`
- **Task Type**: "commit_msg"
- **Model**: lightweight (GPT-4o mini)
- **Input**: Agent name, issue type, issue JSON
- **Output**: Commit message text
- **Parsing**: First line is commit message

### 6. create_pull_request() - PR Creation
- **Location**: `workflow_ops.py:441-540`
- **Task Type**: "pr_creation"
- **Model**: lightweight (GPT-4o mini)
- **Input**: Branch name, issue number, plan file, ADW ID
- **Output**: JSON with `title` and `description` fields
- **Parsing**: JSON parsing for PR metadata

### 7. implement_plan() - Code Implementation
- **Location**: `workflow_ops.py:200-346`
- **Task Type**: "implement"
- **Model**: heavy (Claude Sonnet 4.5)
- **Input**: Plan content + instructions
- **Output**: Code implementation (files created/modified)
- **Parsing**: OpenCode Part types (text, tool_use, tool_result)
- **Fallback**: Git verification

### 8. resolve_failed_tests() - Test Fixing
- **Location**: `adw_test.py:402-440`
- **Task Type**: "test_fix"
- **Model**: heavy (Claude Sonnet 4.5)
- **Input**: Test failures, error messages
- **Output**: Fixed code
- **Parsing**: OpenCode Part types
- **Metrics**: Files changed, errors

### 9. run_review() - Code Review
- **Location**: `adw_review.py:110-150`
- **Task Type**: "review"
- **Model**: heavy (Claude Sonnet 4.5)
- **Input**: Changed files, diff context
- **Output**: Review findings and comments
- **Parsing**: OpenCode Part types for issues found

---

## Appendix D: Environment Variable Changes

### Removed Environment Variables

These should be **removed from `.env` and documentation**:

- `AWS_ENDPOINT_URL` - Custom proxy endpoint (not needed with OpenCode)
- `AWS_MODEL_KEY` - Custom proxy auth key (not needed with OpenCode)
- `AWS_MODEL` - Model override for custom system (not needed)
- `AWS_ACCESS_KEY_ID` - AWS credentials (not needed, was for Bedrock)
- `AWS_SECRET_ACCESS_KEY` - AWS credentials (not needed, was for Bedrock)

### New Environment Variables

These are **automatically managed by OpenCode CLI**:

- `OPENCODE_API_KEY` - Optional (OpenCode reads from config file first)
- API keys for specific providers:
  - Anthropic: No env var needed (stored in `~/.local/share/opencode/`)
  - OpenAI: No env var needed (stored in `~/.local/share/opencode/`)

### Kept Environment Variables

These remain **unchanged**:

- `JIRA_SERVER` - Jira server URL
- `JIRA_USERNAME` - Jira username
- `JIRA_API_TOKEN` - Jira API token
- `BITBUCKET_WORKSPACE` - Bitbucket workspace
- `BITBUCKET_REPO_NAME` - Bitbucket repository
- `BITBUCKET_API_TOKEN` - Bitbucket API token

---

**End of Plan**
