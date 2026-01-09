# ADWS Phase 0 Status Report
**Generated**: January 9, 2026  
**Session**: Alignment & Readiness Fixes  
**Status**: ✅ Planning Operations Ready, Code Execution Pending

---

## Executive Summary

The ADWS system has been **partially migrated to OpenCode HTTP API** with successful completion of Epics 1 & 2 (Planning/Classification operations). Code execution operations (Epic 3) still use Copilot CLI and are scheduled for future migration.

**Current State**: 
- ✅ **Planning & Classification**: Fully using OpenCode HTTP API (ACTIVE)
- ⏳ **Code Execution**: Still using Copilot CLI (requires migration in Epic 3)
- ✅ **All tests passing**: 95/95 unit tests pass
- ✅ **Configuration complete**: .adw.yaml and agent.py properly configured

---

## What Was Accomplished Today

### Session 1: JIRA Stories Alignment
- ✅ Aligned `JIRA_EPICS_AND_STORIES.md` with reference documentation
- ✅ Fixed all 43 user stories with correct model names/versions
- ✅ Added Phase 0 architectural context block
- ✅ Verified alignment with:
  - `MIGRATION_EXECUTION_GUIDE.md`
  - `MIGRATE_TO_OPENCODE_HTTP_API.md`

### Session 2: ADWS Code & Configuration Fixes
- ✅ Fixed `workflow_ops.py` (2 lines):
  - `build_plan()` now uses `model="opus"` (Claude Sonnet 4)
  - `create_patch_plan()` now uses `model="opus"` (Claude Sonnet 4)

- ✅ Fixed `agent.py` (1 line):
  - Updated comment: "Claude Sonnet 4.5" → "Claude Sonnet 4"

- ✅ Updated `.adw.yaml` (16 lines):
  - Model IDs: `github-copilot/claude-sonnet-4`, `github-copilot/claude-haiku-4.5`
  - Marked migration flags as deprecated
  - Added Phase 0 status documentation
  - Listed prerequisites (OpenCode, Jira creds)
  - Clarified Copilot CLI still required for Epic 3

- ✅ Updated `pyproject.toml`:
  - Noted boto3 is optional (only used by isolated bedrock_agent.py)

- ✅ Added deprecation notice to `bedrock_agent.py`

---

## Current Architecture

### ✅ What's Using OpenCode HTTP API NOW

**Planning & Classification Operations** (Fully Migrated):
```
Extract ADW Info      → OpenCode HTTP (Haiku 4.5)
Classify Issue        → OpenCode HTTP (Haiku 4.5)
Build Plan            → OpenCode HTTP (Sonnet 4)     [USES HEAVY MODEL]
Generate Branch Name  → OpenCode HTTP (Haiku 4.5)
Create Commit Msg     → OpenCode HTTP (Haiku 4.5)
Create PR Description → OpenCode HTTP (Haiku 4.5)
Create Patch Plan     → OpenCode HTTP (Sonnet 4)     [USES HEAVY MODEL]
```

**Status**: ✅ ACTIVE - These operations are fully functional

---

### ⏳ What Still Uses Copilot CLI (Epic 3)

**Code Execution Operations** (Migration Pending):
```
Implement Plan        → Copilot CLI subprocess
Resolve Failed Tests  → Copilot CLI subprocess
Run Code Review       → Copilot CLI subprocess
```

**Status**: ⏳ IN PROGRESS - Requires Copilot CLI in PATH until migrated

---

## Prerequisites to Run ADWS

### ✅ For Planning Operations (Fully Working)

**REQUIRED:**
1. **OpenCode Server** - Must be running
   ```bash
   opencode serve --port 4096
   ```

2. **OpenCode Authentication** - Must be configured
   ```bash
   opencode auth login
   ```

3. **Jira Credentials** - In `.env` file
   ```env
   JIRA_SERVER=https://your-jira-instance.atlassian.net
   JIRA_USERNAME=your-username
   JIRA_API_TOKEN=your-api-token
   ```

**✅ Ready to Use**: `uv run scripts/adw_cli.py plan --issue <issue-key>`

---

### ⏳ For Code Execution (Still Pending Epic 3)

**ADDITIONALLY REQUIRED:**
4. **Copilot CLI** - For build, test, and review phases
   ```bash
   brew install copilot
   # OR
   npm install -g @github/copilot-cli
   
   # Verify it's in PATH
   which copilot
   ```

**⏳ Not Yet Ready**: `adw_build.py`, `adw_test.py`, `adw_review.py` still require Copilot CLI

---

## Model Selection & Routing

### How Models are Selected

**In `agent.py` (execute_template function):**
```python
if request.model == "opus":
    model_id = OPENCODE_MODEL_HEAVY  # github-copilot/claude-sonnet-4
else:
    model_id = OPENCODE_MODEL_LIGHT  # github-copilot/claude-haiku-4.5
```

### Tasks Using Light Model (Haiku 4.5)
- All planning & classification tasks use "sonnet" → Haiku 4.5
- Lighter tasks, faster, cheaper

### Tasks Using Heavy Model (Sonnet 4)
- `build_plan()` uses "opus" → Sonnet 4
- `create_patch_plan()` uses "opus" → Sonnet 4
- More complex tasks requiring better reasoning

---

## Configuration Files

### `.adw.yaml` - OpenCode Configuration
```yaml
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
  timeout: 600              # 10 minutes
  lightweight_timeout: 60   # 1 minute
```

**Note**: Migration flags (`use_opencode_for_lightweight`, etc.) are marked as deprecated - the code directly uses OpenCode for planning operations.

### `agent.py` - Model Definitions
```python
OPENCODE_MODEL_HEAVY = "github-copilot/claude-sonnet-4"
OPENCODE_MODEL_LIGHT = "github-copilot/claude-haiku-4.5"
```

### `bedrock_agent.py` - Deprecated
- ⚠️ No longer used by active code
- Kept for reference and historical purposes
- Uses AWS Bedrock (not GitHub Copilot)

---

## What's NOT in Phase 0 Yet

### Removed/No Longer Used:
- ❌ AWS Bedrock integration (isolated, not used)
- ❌ GPT-4o mini model
- ❌ Claude Sonnet 4.5 (replaced with 4)
- ❌ `openai/` model ID format
- ❌ `anthropic/` model ID format
- ❌ Feature flag-based migration

### Still Pending:
- ⏳ Epic 3: Code execution migration to OpenCode
- ⏳ Epic 4: Cleanup & deprecated code removal
- ⏳ Epic 5: Comprehensive testing & documentation

---

## Testing & Validation

### Current Test Results
```
✅ 95 tests passing
⚠️  2 warnings (pre-existing, non-blocking)
✅ 0 failures
✅ No breaking changes
```

### Test Categories
- Parsing functions (ANSI codes, keywords, metrics)
- JSON parsing and validation
- Output detection and error handling
- Robustness with edge cases (unicode, special chars, large data)

---

## Quick Start Guide

### 1. Start OpenCode Server
```bash
# Terminal 1
opencode serve --port 4096
```

### 2. Authenticate with OpenCode
```bash
opencode auth login
# Follow prompts to select provider and paste API key
```

### 3. Verify Jira Credentials
```bash
# Check .env file has:
# JIRA_SERVER=...
# JIRA_USERNAME=...
# JIRA_API_TOKEN=...
```

### 4. Run ADWS Planning
```bash
# Terminal 2
adw plan <issue-key>
```

### 5. View Results
```bash
# Check logs
cat ai_docs/logs/[adw_id]/issue_classifier/prompts/
```

---

## Known Limitations

### Current (Phase 0)
1. **Code Execution Still Uses Copilot CLI**
   - Requires Copilot CLI in PATH
   - Planned migration in Epic 3

2. **No Feature Flags**
   - Code directly uses OpenCode (no gradual rollout)
   - Faster path but less flexibility

3. **No Fallback Chain**
   - If OpenCode is down, planning operations fail
   - Designed this way (Deluxe fallback was permanently broken)

### After Epic 3
1. Copilot CLI will no longer be required
2. All LLM operations will use OpenCode HTTP API
3. Three execution models will be fully migrated

---

## Next Steps: Epic 3 Migration

When ready to complete the migration:

### Step 1: Refactor Code Execution Functions
- `implement_plan()` → Use OpenCode HTTP API
- `resolve_failed_tests()` → Use OpenCode HTTP API
- `run_review()` → Use OpenCode HTTP API

### Step 2: Update Error Handling
- Remove Copilot CLI availability checks
- Add OpenCode server availability checks

### Step 3: Response Parsing
- Parse OpenCode JSON responses for:
  - File changes (implement_plan)
  - Test fixes (resolve_failed_tests)
  - Review feedback (run_review)

### Step 4: Testing & Validation
- E2E tests with real code operations
- Verify file changes are applied correctly
- Test error handling and edge cases

### Step 5: Cleanup (Epic 4)
- Remove Copilot output parser (if not used elsewhere)
- Remove any AWS Bedrock references
- Update documentation

---

## Support & Troubleshooting

### OpenCode Not Responding
```bash
# Check if server is running
curl http://localhost:4096/global/health

# Restart server
opencode serve --port 4096
```

### Jira Connection Failed
```bash
# Verify credentials in .env
# Check Jira server is accessible
curl https://your-jira-instance.atlassian.net
```

### Tests Failing
```bash
# Run tests locally
uv run pytest -v tests/

# Check logs for details
cat ai_docs/logs/*/*/prompts/
```

---

## Summary Table

| Component | Status | Used By | Location |
|-----------|--------|---------|----------|
| OpenCode HTTP Client | ✅ Complete | Planning ops | `agent.py` |
| Planning Operations | ✅ Complete | adw_plan.py | `workflow_ops.py` |
| Classification Ops | ✅ Complete | adw_plan.py | `workflow_ops.py` |
| Code Execution | ⏳ In Progress | adw_build.py | `workflow_ops.py` |
| Test Fixing | ⏳ In Progress | adw_test.py | `adw_test.py` |
| Code Review | ⏳ In Progress | adw_review.py | `adw_review.py` |
| Bedrock Agent | ⚠️ Deprecated | None | `bedrock_agent.py` |
| Copilot CLI | ⏳ Needed for Epic 3 | Code execution | External tool |
| AWS Bedrock | ❌ Removed | None | Isolated module |

---

**Document Version**: 1.0  
**Last Updated**: January 9, 2026  
**Next Review**: After Epic 3 completion
