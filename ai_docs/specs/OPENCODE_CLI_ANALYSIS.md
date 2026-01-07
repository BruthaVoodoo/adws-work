# OpenCode CLI Analysis: Actual Capabilities vs Original Plan

**Date**: January 6, 2026  
**Status**: Analysis Complete - Plan Revision Required

---

## Executive Summary

The original migration plan assumed OpenCode CLI had:
- `--format json` and `--format jsonl` flags for structured output
- Automatic metrics extraction (files_changed, lines_added, lines_removed)
- Session management with direct JSON output

**Reality**: OpenCode CLI's actual capabilities differ significantly:
- `--format` flag only supports `default` or `json` (no JSONL streaming)
- `opencode run` is **non-interactive mode** (no real-time streaming)
- JSON output contains **Message/Part structure** (not direct metrics)
- Metrics must be **extracted from AI's text response** or derived from file operations
- Better approach: Use **OpenCode SDK** for programmatic access or `opencode serve` for backend

---

## Key Findings

### 1. OpenCode CLI `run` Command

**Command**: `opencode run [message]`

**Flags**:
- `--format` - Output format: `default` (formatted text) or `json` (raw JSON events)
- `--model` `-m` - Model selection (provider/model)
- `--agent` - Agent to use
- `--session` `-s` - Session ID to continue
- `--continue` `-c` - Continue last session
- `--file` `-f` - File(s) to attach
- `--title` - Session title
- `--attach` - Attach to running opencode server

**Missing Features**:
- ❌ No JSONL streaming format
- ❌ No automatic metrics reporting
- ❌ No structured output for files_changed, lines_added, lines_removed
- ❌ Output parsing is still **fragile** (extract from AI response text)

### 2. Output Format: `--format json`

When using `--format json`, OpenCode outputs raw JSON events. However:

```bash
opencode run --format json "Implement feature X"
```

Returns: Machine-readable but **still contains AI conversation**, not structured metrics.

**Example output** (conceptual):
```json
{
  "type": "message|tool_use|tool_result|content_block_delta|status",
  "content": "...",
  "messages": [
    { "type": "user|assistant", "content": "..." }
  ]
}
```

**Problem**: Still need to **parse AI's text response** to extract metrics.

### 3. Better Approach: OpenCode SDK

The **SDK is the recommended integration method** for programmatic access:

```python
from opencode_ai_sdk import createOpencode

# Start OpenCode server with SDK
opencode = await createOpencode({
  'port': 4096,
  'config': {'model': 'anthropic/claude-3-5-sonnet-20241022'}
})

# Send message and get structured response
result = await opencode.session.prompt({
  'path': { 'id': session_id },
  'body': {
    'model': {'providerID': 'anthropic', 'modelID': 'claude-3-5-sonnet'},
    'parts': [{'type': 'text', 'text': prompt}]
  }
})

# Response is structured
# result = { 'info': Message, 'parts': Part[] }
```

**Advantages**:
- ✅ Structured response objects (Message, Part)
- ✅ Direct access to session data
- ✅ No regex parsing needed
- ✅ Full API available (not just CLI)

**Problem**: SDK is **JavaScript/TypeScript**, ADWS is **Python**

### 4. Alternative: OpenCode Server + HTTP Client

Use `opencode serve` to run headless server, then interact via HTTP:

```bash
opencode serve --port 4096
```

Then from Python:
```python
import requests

# Create session
session = requests.post('http://localhost:4096/session', 
  json={'title': 'ADWS Implementation'}).json()

# Send prompt
result = requests.post(
  f'http://localhost:4096/session/{session["id"]}/message',
  json={
    'parts': [{'type': 'text', 'text': prompt}]
  }
).json()

# Response structure: { 'info': Message, 'parts': Part[] }
```

**Advantages**:
- ✅ Full structured API from Python
- ✅ Language-agnostic (HTTP)
- ✅ No subprocess parsing issues
- ✅ Better error handling
- ✅ Session reuse possible

**Disadvantages**:
- ⚠️ Requires background server process
- ⚠️ Extra setup/teardown logic

---

## Comparison: Three Integration Strategies

### Strategy A: CLI Subprocess (Original Plan - REVISED)

```bash
opencode run --format json "Your prompt here"
```

**Parsing Approach**:
1. Capture stdout (JSON-formatted)
2. Parse JSON events
3. **Extract metrics from AI's text response** (still requires regex)
4. Verify with git (fallback)

**Pros**:
- Simple: no background process
- Works out of the box

**Cons**:
- Still fragile (regex on AI response)
- No structured metrics
- Difficult to extract execution details
- **Not actually better than Copilot**

**Estimated Time**: 8-10 hours (minimal improvement)

---

### Strategy B: SDK (Python Wrapper) - NOT VIABLE

The OpenCode SDK is JavaScript/TypeScript only. Would need to:
1. Wrap OpenCode Node.js server
2. Call via subprocess (defeats purpose)
3. Parse JSON response anyway

**Not recommended** - adds complexity without benefit.

---

### Strategy C: HTTP Server (RECOMMENDED) ⭐

Run `opencode serve` separately, call via HTTP client.

```python
def execute_opencode_prompt(prompt: str, working_dir: str) -> Dict:
    """Execute prompt via running OpenCode server."""
    response = requests.post(
        'http://localhost:4096/session/..../message',
        json={'parts': [{'type': 'text', 'text': prompt}]}
    )
    return response.json()
```

**Structured Response**:
```python
{
    'info': {
        'id': 'msg-123',
        'sessionID': 'sess-456',
        'createdAt': '2026-01-06T...',
        'role': 'assistant',
        'status': 'done'
    },
    'parts': [
        {
            'type': 'text',
            'text': 'I implemented the feature...'
        },
        {
            'type': 'tool_use',
            'tool': 'bash',
            'input': {'command': 'npm test'}
        },
        {
            'type': 'tool_result',
            'tool': 'bash',
            'output': '...'
        }
    ]
}
```

**Pros**:
- ✅ Structured API (no parsing)
- ✅ Part types clearly labeled (text, tool_use, tool_result)
- ✅ Session management built-in
- ✅ Better error handling
- ✅ Can extract tool execution details
- ✅ Reusable server for all operations

**Cons**:
- ⚠️ Requires running OpenCode server
- ⚠️ Startup cost
- ⚠️ Extra process management

**Time Estimate**: 6-8 hours (simpler than CLI parsing)

---

## Revised Implementation Plan

### Recommended Approach: HTTP Server + Python requests

**Phase 1: Setup & Infrastructure (6-8 hours)**

**New Module**: `opencode_http_client.py`
```python
class OpenCodeHTTPClient:
    """HTTP client for OpenCode server API."""
    
    def __init__(self, base_url: str = "http://localhost:4096"):
        self.base_url = base_url
    
    def create_session(self, title: str) -> Dict:
        """Create OpenCode session."""
        pass
    
    def send_prompt(self, session_id: str, prompt: str) -> Dict:
        """Send prompt to session, get structured response."""
        # Returns: { 'info': Message, 'parts': Part[] }
        pass
    
    def extract_execution_details(self, parts: List[Dict]) -> Dict:
        """Extract metrics from Part array."""
        # Count tool_use/tool_result parts
        # Extract text from assistant responses
        pass

def execute_opencode_prompt(
    prompt: str,
    working_dir: str,
    server_url: str = "http://localhost:4096"
) -> AgentPromptResponse:
    """Execute prompt via OpenCode HTTP API."""
    pass
```

**New Data Types**: `data_types.py`
```python
class OpenCodePart(BaseModel):
    """Individual part of OpenCode message."""
    type: str  # "text", "tool_use", "tool_result", etc.
    text: Optional[str] = None
    tool: Optional[str] = None
    input: Optional[Dict] = None
    output: Optional[str] = None

class OpenCodeMessage(BaseModel):
    """OpenCode message structure."""
    id: str
    sessionID: str
    role: str  # "user" or "assistant"
    createdAt: str
    status: str  # "done", "running", etc.
    parts: List[OpenCodePart]

class OpenCodeResponse(BaseModel):
    """Response from OpenCode HTTP API."""
    info: OpenCodeMessage
    parts: List[OpenCodePart]
    
    def get_text_response(self) -> str:
        """Extract main text response."""
        pass
    
    def count_tools_used(self) -> int:
        """Count tool_use parts."""
        pass
    
    def extract_tool_details(self) -> List[Dict]:
        """Extract tool execution details."""
        pass
```

**New Parser**: `opencode_output_parser.py`
```python
def extract_metrics_from_parts(parts: List[OpenCodePart]) -> Dict:
    """Extract execution metrics from message parts."""
    # Count tool invocations
    # Extract text response
    # Estimate files changed (heuristic from tool outputs)
    pass

def convert_to_agent_response(
    response: OpenCodeResponse
) -> AgentPromptResponse:
    """Convert OpenCode response to AgentPromptResponse."""
    pass
```

**Configuration**: `.adw.yaml`
```yaml
opencode:
  # Server connection
  server_url: "http://localhost:4096"
  
  # Model selection
  model: "anthropic/claude-3-5-sonnet-20241022"
  
  # Execution options
  timeout: 600
  max_retries: 3
  
  # Requires running: opencode serve
  requires_server: true
```

**Setup Instructions**: Add to AGENTS.md
```markdown
## OpenCode Setup

1. Start OpenCode server in background:
   ```bash
   opencode serve --port 4096
   ```

2. Configure in `.adw.yaml`:
   ```yaml
   opencode:
     server_url: "http://localhost:4096"
   ```

3. Authenticate (if needed):
   ```bash
   opencode auth login
   ```
```

---

## What We Lose vs. Original Plan

❌ **JSONL event logging**: OpenCode doesn't provide JSONL stream format
- Solution: Log HTTP request/response pairs instead
- Write to `ai_docs/logs/<adw_id>/<agent_name>/requests.jsonl`

❌ **Automatic metrics**: No built-in files_changed reporting
- Solution: Use git verification as before
- Extract estimate from tool_result outputs

❌ **No structured output formats**: Only default or JSON (same structure)
- Solution: Use structured Message/Part types

---

## What We Gain vs. Original Plan

✅ **Structured API**: Message/Part types (no regex parsing)
✅ **Tool visibility**: Can inspect tool_use and tool_result parts
✅ **Better error handling**: HTTP API with proper error codes
✅ **Session management**: Built-in session reuse
✅ **No subprocess parsing**: Cleaner integration
✅ **Simpler implementation**: Fewer edge cases

---

## Migration Path (REVISED)

### Phase 1: HTTP Client Infrastructure (6-8 hours)
- Create `opencode_http_client.py`
- Create `opencode_output_parser.py` (Part extraction)
- Add data types: `OpenCodeMessage`, `OpenCodePart`, `OpenCodeResponse`
- Create unit tests
- Document setup in AGENTS.md

### Phase 2: Core Implementation (6-8 hours)
- Refactor `implement_plan()` to use HTTP API
- Keep git verification as fallback
- Log HTTP interactions to JSONL
- Test with real OpenCode server

### Phase 3: Test Execution Path (6-8 hours)
- Update `resolve_failed_tests()`
- Update E2E test execution
- Consistent logging across all paths

### Phase 4: Review Path (4-6 hours)
- Update code review execution
- Parse review findings from response

### Phase 5: Cleanup (2-3 hours)
- Deprecate Copilot code
- Remove old parser usage

### Phase 6: Testing & Docs (10-12 hours)
- Comprehensive test suite
- Integration testing
- Documentation updates

**Total: 35-45 hours** (faster than original plan!)

---

## Decision: CLI vs. HTTP

| Aspect | CLI Subprocess | HTTP Server |
|--------|----------------|------------|
| Simplicity | Medium (regex parsing) | High (structured API) |
| Robustness | Low (fragile) | High (JSON) |
| Parsing needed | Yes (text) | No (Parts) |
| Background process | No | Yes |
| Setup complexity | Low | Medium |
| Error handling | Difficult | Easy |
| Session reuse | No | Yes |
| Time to implement | 8-10 hours | 6-8 hours |
| Code quality | Poor (regex) | Good (types) |

**Recommendation**: Use HTTP Server approach
- Better code quality
- Simpler parsing
- Faster implementation
- More maintainable long-term

---

## Next Steps

1. **Confirm Strategy**: HTTP Server vs. CLI?
2. **Environment Setup**: Ensure OpenCode server can run
3. **Create opencode_http_client.py**: Foundation module
4. **Create test data**: Sample OpenCode responses for testing
5. **Update AGENTS.md**: Setup instructions

---

## Appendix A: OpenCode CLI Documentation Summary

### Commands Used
- `opencode run [message]` - Non-interactive execution
  - `--format json` - Machine-readable output
  - `--model provider/model` - Model selection
  - `--attach url` - Connect to existing server
  - `--file path` - Attach files

- `opencode serve` - Start HTTP server
  - `--port N` - Port (default 4096)
  - `--hostname H` - Hostname (default 127.0.0.1)

### APIs Available
- `POST /session` - Create session
- `POST /session/{id}/message` - Send message (returns Message + Parts)
- `GET /session/{id}/message` - List messages
- `GET /session/{id}/diff` - Get file diffs

### Response Structure
```typescript
{
  info: {
    id: string,
    sessionID: string,
    createdAt: string,
    role: "user" | "assistant",
    status: string
  },
  parts: Array<{
    type: "text" | "tool_use" | "tool_result" | "code_block",
    text?: string,
    tool?: string,
    input?: object,
    output?: string,
    language?: string,
    code?: string
  }>
}
```

This is **much more structured** than raw CLI output.
