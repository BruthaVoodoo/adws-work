# OpenCode Server Integration Guide for ADWS

**Version**: 1.1.39+  
**Last Updated**: January 29, 2026  
**Purpose**: Comprehensive guide for OpenCode HTTP server setup, configuration, and troubleshooting in ADWS environments

---

## Overview

OpenCode Server provides a headless HTTP API that enables programmatic interaction with OpenCode's AI capabilities. ADWS uses this server for all AI operations including planning, implementation, testing, and code review.

### Architecture

```
ADWS Application → OpenCode HTTP Server → AI Models (GitHub Copilot)
                ↳ Port 4096 (default)  ↳ Claude Sonnet 4 / Haiku 4.5
```

**Key Benefits:**
- ✅ **Headless operation** - No GUI required for server environments
- ✅ **HTTP REST API** - Standard integration patterns
- ✅ **Session management** - Persistent context across operations
- ✅ **Tool execution** - File operations, shell commands, etc.
- ✅ **Multi-model support** - Route tasks to appropriate AI models

---

## Installation & Basic Setup

### 1. Installation

OpenCode is part of the GitHub Copilot ecosystem:

```bash
# Using npm (recommended)
npm install -g @github/copilot

# Using Homebrew (macOS)
brew install copilot

# Verify installation
opencode --version  # Should show 1.1.39+
```

### 2. Authentication

**Required**: Active GitHub Copilot subscription

```bash
# Authenticate with GitHub account
opencode auth login
```

This opens a browser window for GitHub authentication and grants access to:
- **Claude Sonnet 4** (`github-copilot/claude-sonnet-4`) - Heavy lifting tasks
- **Claude Haiku 4.5** (`github-copilot/claude-haiku-4.5`) - Lightweight tasks

### 3. Basic Server Startup

```bash
# Standard startup (ADWS default)
opencode serve --port 4096

# Keep running in background
opencode serve --port 4096 &

# With debug logging (troubleshooting)
opencode serve --port 4096 --print-logs --log-level DEBUG
```

---

## Server Configuration Options

### Command Line Flags

| Flag | Description | Default | ADWS Usage |
|------|-------------|---------|------------|
| `--port` | Port to listen on | `4096` | ✅ **4096** (standard) |
| `--hostname` | Hostname to bind | `127.0.0.1` | ✅ **localhost only** |
| `--mdns` | Enable mDNS discovery | `false` | ❌ Not needed |
| `--cors` | Additional CORS origins | `[]` | ❌ Not needed |
| `--print-logs` | Print logs to stderr | `false` | 🔧 **For debugging** |
| `--log-level` | Log verbosity | `INFO` | 🔧 **DEBUG for issues** |

### Environment Variables

| Variable | Purpose | ADWS Requirement |
|----------|---------|------------------|
| `OPENCODE_SERVER_PASSWORD` | HTTP Basic Auth password | ❌ Optional |
| `OPENCODE_SERVER_USERNAME` | HTTP Basic Auth username | ❌ Optional |

**Note**: ADWS does not require authentication by default. Use only in secure environments.

### ADWS Configuration (`.adw.yaml`)

```yaml
opencode:
  # Server connection
  server_url: \"http://localhost:4096\"
  
  # Model routing
  models:
    heavy_lifting: \"github-copilot/claude-sonnet-4\"    # Implementation, testing, review
    lightweight: \"github-copilot/claude-haiku-4.5\"     # Planning, classification
  
  # Timeouts (seconds)
  timeout: 1800                # 30 minutes for heavy operations
  lightweight_timeout: 60      # 1 minute for lightweight operations
  
  # Connection settings
  connection_timeout: 30       # TCP connection timeout
  read_timeout: 1800          # Response read timeout
  
  # Retry configuration
  max_retries: 3              # Retry attempts on failures
  retry_backoff: 1.5          # Exponential backoff multiplier
  
  # Session management
  reuse_sessions: false       # Create fresh session per operation
```

---

## HTTP API Reference

### Core Endpoints Used by ADWS

#### Health Check
```http
GET /global/health
Response: { \"healthy\": true, \"version\": \"1.1.39\" }
```

#### Session Management
```http
# Create session
POST /session
Body: {}
Response: { \"id\": \"session_id\", ... }

# Send message (main ADWS operation)
POST /session/:id/message
Body: {
  \"parts\": [{ \"type\": \"text\", \"text\": \"prompt_content\" }],
  \"model\": {
    \"providerID\": \"github-copilot\",
    \"modelID\": \"claude-sonnet-4\"
  }
}
Response: {
  \"info\": { ... },
  \"parts\": [
    { \"type\": \"text\", \"text\": \"response\" },
    { \"type\": \"tool_use\", \"tool\": \"write\", \"input\": {...} },
    { \"type\": \"tool_result\", \"output\": \"...\" }
  ]
}
```

#### File Operations
```http
# Read file
GET /file/content?path=<filepath>

# List files  
GET /file?path=<directory>

# Search content
GET /find?pattern=<search_term>

# Find files
GET /find/file?query=<filename>
```

### Model Selection Logic

ADWS automatically routes operations based on task type:

| Task Type | Model | Use Cases |
|-----------|-------|-----------|
| `classify` | Haiku 4.5 | Issue classification |
| `extract_adw` | Haiku 4.5 | ADW info extraction |
| `plan` | Haiku 4.5 | Implementation planning |
| `branch_gen` | Haiku 4.5 | Git branch naming |
| `commit_msg` | Haiku 4.5 | Commit message generation |
| `pr_creation` | Haiku 4.5 | Pull request creation |
| `implement` | Sonnet 4 | **Code implementation** |
| `test_fix` | Sonnet 4 | Test failure resolution |
| `review` | Sonnet 4 | Code review |

---

## Tool Execution & File Operations

### Overview

OpenCode Server provides **tool execution capabilities** that allow AI models to:
- ✅ **Read files** from the project directory
- ✅ **Write/create files** in the project
- ✅ **Edit existing files** with precise changes  
- ✅ **Execute shell commands** for builds/tests
- ✅ **Search content** across the codebase
- ✅ **Browse directories** and understand project structure

### Tool Types Available

| Tool | Purpose | ADWS Usage |
|------|---------|------------|
| `read` | Read file contents | ✅ **Analyze existing code** |
| `write` | Create new files | ✅ **Generate new modules** |
| `edit` | Modify existing files | ✅ **Update configurations** |
| `bash` | Execute shell commands | ✅ **Run tests, builds** |
| `find` | Search file contents | ✅ **Understand codebase** |
| `glob` | Find files by pattern | ✅ **Locate project files** |

### Expected Tool Execution Flow

During `implement` task:

1. **Analysis Phase**:
   ```http
   POST /session/:id/message
   Response parts: [
     { \"type\": \"text\", \"text\": \"I'll start by reading the existing files...\" },
     { \"type\": \"tool_use\", \"tool\": \"read\", \"input\": { \"filePath\": \"src/app.ts\" } },
     { \"type\": \"tool_result\", \"output\": \"// file contents...\" }
   ]
   ```

2. **Implementation Phase**:
   ```http
   Response parts: [
     { \"type\": \"text\", \"text\": \"Creating the story normalizer module...\" },
     { \"type\": \"tool_use\", \"tool\": \"write\", \"input\": { \"filePath\": \"src/lib/storyNormalizer.ts\", \"content\": \"...\" } },
     { \"type\": \"tool_result\", \"output\": \"File created successfully\" }
   ]
   ```

3. **Validation Phase**:
   ```http
   Response parts: [
     { \"type\": \"tool_use\", \"tool\": \"bash\", \"input\": { \"command\": \"npm run test\" } },
     { \"type\": \"tool_result\", \"output\": \"Tests passed: 15/15\" }
   ]
   ```

---

## ADWS Integration Points

### 1. Server Health Checking

**Function**: `check_opencode_server_available()`  
**Location**: `scripts/adw_modules/opencode_http_client.py`

```python
def check_opencode_server_available(server_url=None, timeout=5.0):
    \"\"\"Verify OpenCode server is running and responsive\"\"\"
    health_url = f\"{server_url}/global/health\"
    response = requests.get(health_url, timeout=timeout)
    return 200 <= response.status_code < 300
```

**Usage in ADWS**:
- ✅ **adw_build.py** - Startup validation
- ✅ **adw_test.py** - Pre-test checks  
- ✅ **adw_review.py** - Review process validation

### 2. HTTP Client Implementation

**Class**: `OpenCodeHTTPClient`  
**Location**: `scripts/adw_modules/opencode_http_client.py`

**Key Features**:
- ✅ **Session management** with automatic creation
- ✅ **Model routing** based on task type
- ✅ **Retry logic** with exponential backoff
- ✅ **Error handling** for connection/auth issues
- ✅ **Response parsing** for tool execution results

### 3. Agent Integration

**Function**: `execute_opencode_prompt()`  
**Location**: `scripts/adw_modules/agent.py`

```python
def execute_opencode_prompt(prompt, task_type, adw_id, agent_name):
    \"\"\"Execute prompt via OpenCode with task-aware model routing\"\"\"
    client = OpenCodeHTTPClient.from_config()
    response = client.send_prompt(
        prompt=prompt,
        task_type=task_type,  # Auto-selects appropriate model
        adw_id=adw_id,
        agent_name=agent_name
    )
    return convert_opencode_to_agent_response(response)
```

---

## Troubleshooting Guide

### Issue: \"Connection Refused\"

**Symptoms**:
```
ConnectionError: Failed to connect to OpenCode server at http://localhost:4096
```

**Diagnostics**:
```bash
# Check if server is running
curl http://localhost:4096/global/health

# Check process
ps aux | grep \"opencode serve\"

# Check port availability
lsof -i :4096
```

**Solutions**:
1. **Start server**: `opencode serve --port 4096`
2. **Different port**: `opencode serve --port 8080` (update `.adw.yaml`)
3. **Kill conflicting process**: `pkill -f \"opencode serve\"`

### Issue: \"Authentication Failed (401)\"

**Symptoms**:
```
OpenCodeAuthenticationError: Authentication failed (401 Unauthorized)
```

**Diagnostics**:
```bash
# Check auth status
opencode auth status

# Re-authenticate
opencode auth login
```

**Solutions**:
1. **Re-authenticate**: `opencode auth login`
2. **Verify subscription**: Check GitHub Copilot subscription at https://github.com/settings/copilot
3. **Clear auth cache**: `opencode auth logout && opencode auth login`

### Issue: \"Tools Not Executing\"

**Symptoms**:
- AI responds with text but no files are created
- Claims \"File created successfully\" but no actual files exist
- No `tool_use` parts in response JSON

**Diagnostics**:
```bash
# Start server with debug logging
opencode serve --port 4096 --print-logs --log-level DEBUG

# Monitor for tool execution errors in logs

# Test direct tool request
curl -X POST http://localhost:4096/session/:id/message \\
  -H \"Content-Type: application/json\" \\
  -d '{\"parts\":[{\"type\":\"text\",\"text\":\"Use the write tool to create hello.txt\"}]}'
```

**Solutions**:
1. **Check permissions**: Ensure OpenCode can write to project directory
2. **Restart server**: `pkill -f \"opencode serve\" && opencode serve --port 4096`
3. **Update OpenCode**: `npm install -g @github/copilot@latest`
4. **Check working directory**: Ensure server starts from correct project root

### Issue: \"Request Timeouts\"

**Symptoms**:
```
Request timeout (attempt 1/3). Retrying in 1.0s...
TimeoutError: Request timeout after 3 retries
```

**Solutions**:
1. **Increase timeouts** in `.adw.yaml`:
   ```yaml
   opencode:
     timeout: 2400        # 40 minutes
     read_timeout: 2400   # 40 minutes
   ```

2. **Check network connectivity**: `curl -I http://localhost:4096/global/health`
3. **Reduce prompt complexity**: Break large plans into smaller steps

### Issue: \"Model Not Found\"

**Symptoms**:
```
Model github-copilot/claude-sonnet-4 not found
```

**Solutions**:
1. **Verify models**: `opencode models list`
2. **Check authentication**: GitHub Copilot subscription required
3. **Update model IDs** in `.adw.yaml` if they've changed

---

## Performance Optimization

### Session Management

**Default behavior** (ADWS):
```yaml
opencode:
  reuse_sessions: false  # New session per operation
```

**High-throughput environments**:
```yaml
opencode:
  reuse_sessions: true   # Reuse sessions for better performance
```

### Timeout Tuning

**For large codebases**:
```yaml
opencode:
  timeout: 3600          # 1 hour for complex implementations
  lightweight_timeout: 120  # 2 minutes for planning
```

**For development/testing**:
```yaml
opencode:
  timeout: 600           # 10 minutes (faster feedback)
  lightweight_timeout: 30   # 30 seconds
```

### Retry Strategy

**Reliable networks**:
```yaml
opencode:
  max_retries: 2
  retry_backoff: 1.0
```

**Unreliable networks**:
```yaml
opencode:
  max_retries: 5
  retry_backoff: 2.0
```

---

## Security Considerations

### Network Security

**Default configuration** (secure for local development):
- ✅ **Localhost only** (`127.0.0.1`) - Not accessible from network
- ✅ **No authentication** required for local usage
- ✅ **HTTP protocol** acceptable for localhost

**Production/shared environments**:
```bash
# Enable authentication
OPENCODE_SERVER_PASSWORD=secure-password opencode serve --port 4096

# Custom username
OPENCODE_SERVER_USERNAME=adws OPENCODE_SERVER_PASSWORD=secure-password opencode serve
```

### File System Access

**Default behavior**:
- ✅ OpenCode can read/write files in the **project directory**
- ✅ Limited to **current working directory** and subdirectories
- ❌ Cannot access files outside project scope

**Recommendations**:
1. **Start OpenCode from project root** to ensure correct file access scope
2. **Use dedicated service accounts** in production environments
3. **Monitor file system operations** via debug logging if needed

---

## Monitoring & Logging

### Server Health Monitoring

**ADWS built-in checks**:
```python
# Automatic health checking in all ADWS scripts
from adw_modules.opencode_http_client import check_opencode_server_available

if not check_opencode_server_available():
    print(\"❌ OpenCode server not available\")
    sys.exit(1)
```

**External monitoring**:
```bash
# Simple health check
curl -f http://localhost:4096/global/health || exit 1

# Detailed status
curl -s http://localhost:4096/global/health | jq '.'
```

### Debug Logging

**Server-side logging**:
```bash
# Start with debug logging
opencode serve --port 4096 --print-logs --log-level DEBUG
```

**ADWS logging**:
- ✅ **Request/response logs**: `ai_docs/logs/{adw_id}/{agent_name}/`
- ✅ **Error logs**: `error_response_*.json` files
- ✅ **Success logs**: `response_*.json` files

### Performance Metrics

**Key metrics to monitor**:
- ✅ **Response times** per task type (plan vs implement)
- ✅ **Success rates** for tool execution
- ✅ **Retry frequency** and failure patterns
- ✅ **Session lifecycle** duration

---

## Version Compatibility

### OpenCode Version Support

| OpenCode Version | ADWS Compatibility | Status | Notes |
|-----------------|-------------------|--------|-------|
| 1.1.39+ | ✅ **Fully Supported** | Current | Recommended version |
| 1.1.x | ✅ **Supported** | Stable | Minor version updates |
| 1.0.x | ⚠️ **Limited** | Legacy | Missing features |
| <1.0 | ❌ **Not Supported** | EOL | Breaking changes |

### GitHub Copilot Model IDs

**Current stable models**:
```yaml
models:
  heavy_lifting: \"github-copilot/claude-sonnet-4\"
  lightweight: \"github-copilot/claude-haiku-4.5\"
```

**Check for updates**:
```bash
opencode models list | grep github-copilot
```

---

## Quick Reference

### Essential Commands
```bash
# Start server
opencode serve --port 4096

# Debug mode  
opencode serve --port 4096 --print-logs --log-level DEBUG

# Authentication
opencode auth login
opencode auth status

# Health check
curl http://localhost:4096/global/health

# Stop server
pkill -f \"opencode serve\"
```

### ADWS Health Check
```bash
# From ADWS project root
python -c \"
from scripts.adw_modules.opencode_http_client import check_opencode_server_available
print('✅ OpenCode OK' if check_opencode_server_available() else '❌ OpenCode Down')
\"
```

### Common File Paths
```
~/.opencode/           # OpenCode configuration
.adw.yaml              # ADWS OpenCode configuration  
ai_docs/logs/          # ADWS operation logs
scripts/adw_modules/   # ADWS OpenCode integration code
```

---

## Conclusion

OpenCode Server provides the foundation for ADWS's AI-powered development workflows. Proper setup, configuration, and monitoring ensure reliable tool execution and high-quality code generation.

**Key Success Factors**:
1. ✅ **Proper authentication** with GitHub Copilot
2. ✅ **Correct working directory** setup
3. ✅ **Appropriate timeout configuration**
4. ✅ **Regular health monitoring**
5. ✅ **Debug logging** when issues arise

For additional support, consult the [OpenCode Documentation](https://opencode.ai/docs/) or join the [OpenCode Discord](https://opencode.ai/discord).

---

**Document Version**: 1.0  
**Compatible with**: OpenCode 1.1.39+, ADWS 2.0+  
**Last Verified**: January 29, 2026