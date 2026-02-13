# Token Limit Handling - Brainstorming Session

**Date:** 2026-02-13  
**Status:** Ready for brainstorming  
**Archon Task:** a65457dd-b34c-4f66-9454-db0f8d204c50  
**Project:** d52cf80f-d1ec-411d-a6a2-c40c8592609a (ADWS)

---

## Problem Statement

Hit token limit error during ADWS test phase:
```
OpenCode Server Error: APIError - prompt token count of 184573 exceeds the limit of 128000
```

**Context:**
- Using Claude Sonnet 4 via OpenCode (128K input limit)
- Error occurred in `adw_test.py` when resolving failed tests
- Test output being inserted into prompt without validation: `prompt = prompt_template.replace("$ARGUMENTS", test_output)`
- 184,573 tokens sent (44% over limit)

---

## Current State

### What We Have
✅ Global prompt logging implemented (can inspect saved prompts)  
✅ Task type routing to different models (Haiku for light, Sonnet for heavy)  
✅ OpenCode HTTP client with error handling  
✅ Comprehensive test suite

### What We Need
❌ Token counting before API calls  
❌ Model token limit awareness  
❌ Pre-flight validation  
❌ User notification when limit exceeded  
❌ Resolution strategies when prompt too large  
❌ No fallback model mechanism

---

## Model Token Limits (Per-LLM)

| Model | Input Limit | Notes |
|-------|-------------|-------|
| Claude Sonnet 4 (github-copilot/claude-sonnet-4) | 128,000 tokens | Current default for heavy tasks |
| Claude Haiku 4.5 (github-copilot/claude-haiku-4.5) | 128,000 tokens | Current default for light tasks |
| Claude Opus 4 (github-copilot/claude-opus-4) | 200,000 tokens | Higher limit, but availability? |

**Note:** These are **input** limits. Output limits are typically separate (4K-8K for Claude models).

---

## Proposed Solution Architecture

### Phase 1: Detection & Prevention
1. **Add tiktoken library** for accurate token counting
2. **Create model limits registry** - map model IDs to limits
3. **Pre-flight validation** in `execute_opencode_prompt()`:
   - Count tokens before API call
   - Check against target model's limit
   - Raise exception if exceeded

### Phase 2: User Notification
When limit exceeded, display:
```
❌ Token Limit Exceeded
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prompt: 184,573 tokens
Model: Claude Sonnet 4 (limit: 128,000 tokens)
Exceeded by: 56,573 tokens (44% over limit)

The prompt being sent is too large for the selected model.
Saved prompt: logs/{adw_id}/test_resolver/prompts/test_fix_{timestamp}.txt

Options:
1. Truncate test output intelligently and retry
2. Use aggressive summarization
3. Abort workflow (manual intervention required)

Enter choice [1-3]:
```

### Phase 3: Resolution Strategies
**This is where we need to brainstorm!** 🧠

---

## Brainstorming: Resolution Strategies

### Strategy 1: Intelligent Test Output Truncation
**Concept:** Keep only essential information, truncate verbose details

**Approaches:**
- [ ] **Failed tests only** - Remove passing test output entirely
- [ ] **Stack trace compression** - Keep first 10 + last 10 lines of each stack trace
- [ ] **Deduplicate errors** - If 50 tests fail with same error, show once + count
- [ ] **File diff truncation** - Summarize changed files instead of full diffs
- [ ] **Context window** - Show only N lines around failure point

**Questions:**
- What's the minimum information needed to fix a test?
- How much context is required for the LLM to understand the failure?
- Can we preserve test names + error messages but truncate stack traces?

---

### Strategy 2: Summarization / Compression
**Concept:** Use AI to summarize test output before sending to main LLM

**Approaches:**
- [ ] **Pre-summarization** - Use lightweight model (Haiku) to summarize failures
- [ ] **Extract key info** - Parse test output, extract only: test name, assertion, error type
- [ ] **Group similar failures** - "15 tests failed with ImportError: module 'foo' not found"
- [ ] **Natural language summary** - "The tests failed because X component is missing Y dependency"

**Questions:**
- Does this add too much complexity/latency?
- Would a two-stage process (summarize → fix) be effective?
- Can we use regex/parsing instead of another LLM call?

---

### Strategy 3: Chunked Processing
**Concept:** Split failures into chunks, process separately

**Approaches:**
- [ ] **Process N failures at a time** - If 100 tests failed, process 20 at a time
- [ ] **Iterative fixing** - Fix batch 1, re-run tests, fix batch 2, etc.
- [ ] **Priority-based** - Fix critical/blocking failures first
- [ ] **File-based chunking** - Group failures by affected file

**Questions:**
- How to maintain context across chunks?
- Could this lead to conflicting fixes?
- How to handle cascading failures?

---

### Strategy 4: Dynamic Model Selection
**Concept:** Switch to higher-capacity model when needed

**Approaches:**
- [ ] **Automatic fallback** - If Sonnet 4 limit exceeded, try Opus 4 (200K)
- [ ] **Hybrid approach** - Use Opus only for test_fix, keep Sonnet for other tasks
- [ ] **User choice** - Prompt user to select higher-tier model
- [ ] **Cost awareness** - Warn about pricing differences

**Questions:**
- Is Opus 4 available via OpenCode/GitHub Copilot?
- What's the cost difference?
- Should this be automatic or user-controlled?

---

### Strategy 5: Prompt Engineering
**Concept:** Redesign prompt to be more token-efficient

**Approaches:**
- [ ] **Structured format** - Use JSON/YAML instead of prose
- [ ] **Reference files** - "See test_output.txt" instead of embedding full output
- [ ] **Symbolic references** - Use tokens/IDs to reference repeated content
- [ ] **Compressed encoding** - Base64 or other compression schemes

**Questions:**
- Can the LLM work with external file references?
- Does structured format actually save tokens?
- Would compression hurt LLM comprehension?

---

### Strategy 6: Test Output Pre-processing
**Concept:** Clean/filter test output before insertion

**Approaches:**
- [ ] **Remove ANSI codes** - Strip color/formatting codes
- [ ] **Remove duplicate lines** - Deduplicate repeated log messages
- [ ] **Filter noise** - Remove debug logs, warnings (keep only errors)
- [ ] **Compress whitespace** - Replace multiple newlines with single
- [ ] **Extract essential regex** - Parse pytest/unittest output format

**Questions:**
- How much can we save with basic filtering?
- What patterns are safe to remove?
- Can we preserve enough context?

---

## Recommended Approach (For Discussion)

### Tiered Strategy:
1. **Tier 1: Pre-processing** (automatic, always on)
   - Remove ANSI codes
   - Deduplicate identical errors
   - Compress stack traces (first 5 + last 5 lines)
   - Filter passing tests

2. **Tier 2: Validation** (automatic check)
   - Count tokens after pre-processing
   - If still over limit → notify user

3. **Tier 3: User Choice** (interactive prompt)
   ```
   1. Aggressive truncation (keep only test names + error types)
   2. Process failures in batches (20 at a time)
   3. Abort workflow - manual intervention required
   ```

4. **Future: Fallback Model** (if available)
   - Check if Opus 4 available in environment
   - Offer as option if token count < 200K

---

## Implementation Checklist

### Must Have (MVP)
- [ ] Add tiktoken to dependencies
- [ ] Create `token_utils.py` with counting function
- [ ] Create `model_limits.py` with registry
- [ ] Add validation to `execute_opencode_prompt()`
- [ ] Add user notification to `adw_test.py`
- [ ] Implement basic truncation (Tier 1 pre-processing)
- [ ] Write tests for token counting
- [ ] Update documentation

### Nice to Have (Future)
- [ ] Summarization via Haiku pre-processing
- [ ] Chunked processing with batching
- [ ] Fallback to Opus 4 if available
- [ ] Advanced prompt engineering
- [ ] User preferences (save truncation choice)

---

## Questions to Answer

1. **Token counting accuracy:**
   - Is `tiktoken` with `cl100k_base` accurate for Claude models?
   - Should we add safety margin (e.g., 95% of limit)?

2. **User experience:**
   - Should we pause workflow automatically or let it fail?
   - How much information to show in error message?
   - Should truncation be automatic or require user confirmation?

3. **Test output characteristics:**
   - What's typical size of test output in your workflow?
   - What percentage is stack traces vs. test names vs. other?
   - Are there common patterns we can exploit?

4. **Model availability:**
   - Is Claude Opus 4 available via GitHub Copilot/OpenCode?
   - What's the cost difference between Sonnet 4 and Opus 4?
   - Are there other high-context models available?

5. **Technical constraints:**
   - Can we pass file references to LLM instead of content?
   - Is there a way to stream prompts incrementally?
   - Can we use OpenCode's context caching?

---

## Next Steps

1. **Brainstorm session** - Discuss strategies above
2. **Decide on approach** - Select Tier 1 + 2 + 3 strategies
3. **Spike: Token counting** - Test tiktoken accuracy
4. **Spike: Truncation** - Test basic pre-processing on real test output
5. **Implementation** - Follow task checklist
6. **Testing** - Verify with actual large test outputs
7. **Documentation** - Update user guide with troubleshooting

---

## Reference Files

- **Task:** `adw_test.py` line 438 - where test_output inserted
- **Prompt template:** `prompts/resolve_failed_tests.md`
- **Saved prompts:** `ADWS/logs/{adw_id}/test_resolver/prompts/test_fix_*.txt`
- **Agent module:** `scripts/adw_modules/agent.py` - where validation should go
- **OpenCode client:** `scripts/adw_modules/opencode_http_client.py`

---

## Notes

- The error happened specifically during test failure resolution, not during initial test execution
- Test output can include: test names, status, stack traces, assertion failures, file diffs, environment info
- Current implementation has no awareness of prompt size until API rejects it
- Global prompt logging was added specifically to debug this issue (can now inspect saved prompts)
- No fallback mechanism exists - workflow fails completely when limit exceeded

---

**Status:** Ready for brainstorming session  
**Next Session:** Decide on resolution strategies and create implementation plan
