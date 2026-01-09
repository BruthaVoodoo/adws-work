# Phase 0 Architecture Decision: Remove Deluxe Fallback

**Date**: January 9, 2026  
**Session**: ADWS OpenCode Migration - Phase 0 Configuration  
**Status**: DECISION MADE - Awaiting Implementation  
**Priority**: High (affects Phase 1+ architecture)

---

## Decision

**Remove the Deluxe LLM fallback chain from `agent.py` and commit fully to OpenCode HTTP API with GitHub Copilot models.**

---

## Rationale

### The Problem with Current Implementation

Current `agent.py` has a fallback chain:
```
Try Deluxe endpoint → Fall back to OpenCode → Error
```

**Why this is wrong**:

1. **Deluxe is dead**
   - Token expired: 2025-12-30
   - Endpoint returns 403 Forbidden
   - Will never be available again
   - No recovery path

2. **Fallback makes no sense**
   - A fallback should be to a working system
   - Deluxe is not working (and won't be)
   - Trying it first wastes 30+ seconds per operation
   - User experiences unnecessary delays

3. **Migration plan assumes old system works**
   - Feature flags were designed for: "Try old, fall back to new"
   - But the old system (Deluxe) is completely unavailable
   - Feature flag strategy doesn't apply to a dead system

4. **Architectural dishonesty**
   - We're treating OpenCode as a "fallback" when it's actually the primary system
   - The real architecture is: OpenCode is it, nothing else
   - Fallback chain misrepresents this reality

### The Reality

- Organization has GitHub Copilot subscription
- Both models work via OpenCode (verified Jan 8, 2026):
  - ✅ `github-copilot/claude-sonnet-4` (heavy lifting)
  - ✅ `github-copilot/claude-haiku-4.5` (lightweight)
- OpenCode is the only available path forward
- Deluxe is the past (and it's dead)

### The Correct Architecture

```
OpenCode HTTP API (GitHub Copilot) → Error (with troubleshooting)
```

Simple, honest, and effective.

---

## Implementation Scope

### File: `scripts/adw_modules/agent.py`

**Delete entirely**:
- `invoke_deluxe_model()` function (currently lines ~69-120)
  - Tries legacy Deluxe endpoint
  - Returns None on failure to trigger fallback
  - Not needed anymore

**Simplify `invoke_model()` function**:
- **Before** (~40 lines):
  ```python
  def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse:
      """Invoke a model with intelligent fallback chain."""
      
      # Try Deluxe first (if configured)
      deluxe_response = invoke_deluxe_model(prompt, model_id)
      if deluxe_response is not None:
          if deluxe_response.success:
              print(f"✅ Using Deluxe endpoint", file=sys.stderr)
              return deluxe_response
          elif ("expired" in deluxe_response.output.lower() 
                or "unauthorized" in deluxe_response.output.lower()):
              print(f"⚠️  Deluxe token invalid/expired. Falling back to OpenCode...", file=sys.stderr)
          else:
              print(f"⚠️  Deluxe error. Trying OpenCode fallback...", file=sys.stderr)
      else:
          print(f"🔄 Deluxe endpoint unavailable. Using OpenCode HTTP API...", file=sys.stderr)
      
      # Fall back to OpenCode with GitHub Copilot models
      opencode_response = invoke_opencode_model(prompt, model_id)
      return opencode_response
  ```

- **After** (~5 lines):
  ```python
  def invoke_model(prompt: str, model_id: str) -> AgentPromptResponse:
      """Invoke a model via OpenCode HTTP API (GitHub Copilot)."""
      return invoke_opencode_model(prompt, model_id)
  ```

**Keep unchanged**:
- `invoke_opencode_model()` function (all ~90 lines)
- `execute_template()` function (all ~20 lines)
- `save_prompt()` function (all ~35 lines)
- All imports and environment variable loading (load_dotenv())
- OPENCODE_MODEL_HEAVY and OPENCODE_MODEL_LIGHT constants

### File: `.env`

**No changes needed**
- Keep all OpenCode configuration as-is:
  ```
  OPENCODE_URL=http://localhost:4096
  OPENCODE_MODEL_HEAVY=github-copilot/claude-sonnet-4
  OPENCODE_MODEL_LIGHT=github-copilot/claude-haiku-4.5
  ```
- Keep legacy AWS variables for reference (even though unused):
  ```
  AWS_ENDPOINT_URL=...
  AWS_MODEL_KEY=...
  AWS_MODEL=...
  ```

---

## Testing

After making changes:

```bash
cd /Users/t449579/Desktop/DEV/ADWS
python3 -m pytest tests/ -v
```

**Expected result**: All 95 tests passing (no regressions)

---

## Git Commit

**After verification passes**, create commit:

```
commit message:
  refactor: Remove dead Deluxe fallback, use OpenCode directly

body:
  - Delete invoke_deluxe_model() function (Deluxe token expired 2025-12-30)
  - Simplify invoke_model() to call invoke_opencode_model() directly
  - Removes 30+ second timeout delays from trying failed Deluxe endpoint
  - Reflects architectural reality: OpenCode is the only path forward
  - Keeps backward-compatible environment variable loading
  - Keeps GitHub Copilot model configuration in .env
  - All 95 tests passing
  - No breaking changes
```

---

## Migration Plan Impact

This decision affects the migration plan documentation:

**What changes in next session** (after code fix is merged):
1. **Delete Section 3.1 (Feature Flags)** - No longer applies
   - Feature flag strategy was designed for: "Switch between old and new"
   - But old system is dead, so no point in feature flags
   - Remove ~25 lines about migration.use_opencode_for_lightweight, etc.

2. **Rewrite Phase 0 description** in migration plan
   - Update status from "In Progress - Phase 0: Configuration"
   - Add note: "Phase 0 now includes architectural decision to remove Deluxe fallback"
   - Clarify: "Full commitment to OpenCode; no hybrid state"

3. **Simplify error handling narrative** in Epics 1-5
   - Remove references to feature flags
   - Focus on: "Make OpenCode rock solid"

4. **Update Appendix D (Environment Variables)**
   - Clarify: AWS_ENDPOINT_URL and AWS_MODEL_KEY are deprecated/unused
   - Kept only for reference

**File to update**: `ai_docs/specs/plans/MIGRATE_TO_OPENCODE_HTTP_API.md`

---

## Context for Next Session

When starting the next session:

1. **Read this file first** to understand the decision
2. **Execute the implementation** described above
3. **Run tests** to verify no regressions
4. **Create the commit** with the message provided
5. **After code fix succeeds**: Schedule documentation update session

---

## Q&A

**Q: Why not keep Deluxe as a fallback "just in case"?**
A: Because it's not just in case—it's permanently broken. The token expired Dec 30, 2025. There's no recovery. Keeping it as a fallback means every operation wastes 30+ seconds trying something that will always fail.

**Q: What if Deluxe comes back?**
A: It won't. The endpoint is dead, the token is expired, and the organization is moving away from it entirely. If somehow it becomes available again in the future, we can add it back. But betting on a resurrection is not a sound strategy.

**Q: Does this break anything?**
A: No. The only change is removing dead code and simplifying the call chain. OpenCode is already the working path. We're just making it the only path, which is what it actually is.

**Q: What about backward compatibility?**
A: Fully maintained. `.env` still accepts all the old variables. Code just doesn't use them anymore. If someone has old config, it doesn't break—it's just ignored.

---

## Sign-Off

**Decision made by**: ADWS OpenCode Migration Session (Jan 9, 2026)  
**Reviewed by**: Architecture analysis and fallback chain evaluation  
**Status**: Ready for implementation in next session  
**No further analysis needed**

---

**Next action**: Start new session, read this file, execute implementation.
