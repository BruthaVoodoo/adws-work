# JIRA_EPICS_AND_STORIES.md Alignment Plan

**Created**: January 9, 2026  
**Status**: Ready for Implementation  
**Session**: New session required  
**Total Tasks**: 7 phases + final verification  
**Estimated Time**: 1-2 hours  

---

## Executive Summary

This document contains a detailed plan to align `ai_docs/specs/JIRA_EPICS_AND_STORIES.md` with the two authoritative reference documents:
- `ai_docs/specs/plans/MIGRATION_EXECUTION_GUIDE.md` ✅ (source of truth)
- `ai_docs/specs/plans/MIGRATE_TO_OPENCODE_HTTP_API.md` ✅ (source of truth)

**Key Issues Found:**
1. Incorrect model names (GPT-4o mini instead of Claude Haiku 4.5)
2. Wrong model versions (Claude Sonnet 4.5 instead of Claude Sonnet 4)
3. Missing model ID format (should be `github-copilot/` prefix)
4. Missing Phase 0 architectural context
5. GitHub Copilot subscription source not documented

**Result After Implementation:**
- ✅ Perfect alignment with both reference documents
- ✅ Consistent model naming throughout
- ✅ Clear GitHub Copilot subscription context
- ✅ Phase 0 architectural decision documented
- ✅ All 43 stories use correct model references

---

## Critical Alignment Issues

### Issue 1: Model Name Inconsistencies

| Location | Current (WRONG) | Should Be | Impact |
|----------|-----------------|-----------|--------|
| Line 15 (Overview) | "GPT-4o mini" + "Claude Sonnet 4.5" | "Claude Haiku 4.5" + "Claude Sonnet 4" | Foundation statement wrong |
| Line 28 (Epic 2 Summary) | "Claude Haiku 4.5" | "Claude Haiku 4.5 (GitHub Copilot)" | Missing subscription context |
| Line 35 (Epic 3 Summary) | "Claude Sonnet 4.5" | "Claude Sonnet 4 (GitHub Copilot)" | Wrong model version |
| Story 1.4 Line 288 | `"openai/gpt-4o-mini"` | `"github-copilot/claude-haiku-4.5"` | Wrong provider + format |
| Story 1.4 Line 292 | `"anthropic/claude-3-5-sonnet-20241022"` | `"github-copilot/claude-sonnet-4"` | Wrong provider + outdated model |
| Story 1.4 Line 296 | "GPT-4o mini" + "Claude Sonnet 4.5" | "Claude Haiku 4.5" + "Claude Sonnet 4" | Consistency issue |

### Issue 2: Missing Phase 0 Context

JIRA_EPICS_AND_STORIES.md does NOT document:
- Deluxe fallback was removed (Phase 0 decision, January 9, 2026)
- Direct OpenCode HTTP API path only (no hybrid state, no fallback chain)
- All 95 existing tests passing with new architecture
- GitHub Copilot subscription as the model source
- Simplified architecture (no feature flags needed)

**Where it SHOULD be documented**:
- Add context block at top of document (after title, before "## Overview")
- Reference in Epic 2 & 3 summaries
- Referenced in Story 1.4 acceptance criteria

### Issue 3: Model ID Format

**Current Format** (WRONG):
```
"openai/gpt-4o-mini"
"anthropic/claude-3-5-sonnet-20241022"
```

**Correct Format** (per reference documents):
```
github-copilot/claude-haiku-4.5      (lightweight tasks)
github-copilot/claude-sonnet-4       (heavy lifting tasks)
```

**Why the change:**
- Phase 0 decision: Use GitHub Copilot subscription exclusively
- Model IDs use `github-copilot/` prefix format via OpenCode HTTP API
- Old format references providers that are no longer used

---

## Implementation Plan: 7 Phases + Verification

### Phase 1: Add Phase 0 Context Block

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Location**: After line 5 (after metadata), before line 9 (before "## Overview")  
**Action**: INSERT new section

**Content to INSERT**:
```markdown
---

**Phase 0 Status**: ✅ Complete - Direct OpenCode HTTP Path Confirmed

This document reflects the Phase 0 architectural decision (January 9, 2026):

- ✅ **Deluxe LLM fallback permanently removed** (token expired Dec 30, 2025)
- ✅ **All operations route directly to OpenCode HTTP API** (no fallback chain)
- ✅ **GitHub Copilot models verified and accessible**:
  - Claude Sonnet 4 (heavy lifting: code implementation, test fixing, reviews)
  - Claude Haiku 4.5 (lightweight: planning, classification, document generation)
- ✅ **No feature flags needed** - OpenCode is the ONLY execution path forward
- ✅ **All 95 existing tests passing** with new direct-path architecture
- ✅ **Configuration clean and simplified** - no hybrid state, no fallback logic

**Migration Strategy**: 5 Epics → 43 Stories with direct OpenCode HTTP commitment
(no fallback chains, no feature flags, clean architecture)

**Key Decision**: Phase 0 removed Deluxe fallback that was permanently broken.
All LLM operations now use OpenCode HTTP API with GitHub Copilot models exclusively.

---

```

**Verification**: After insertion, the document should have:
- New context block clearly visible after metadata
- "## Overview" section appears after the Phase 0 block
- Phase 0 decision prominently documented upfront

---

### Phase 2: Update Line 15 - Overview Architecture Statement

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Line**: 15  
**Action**: REPLACE entire line

**Current Line 15**:
```markdown
**Architecture:** Direct HTTP integration to OpenCode server with intelligent model routing (GPT-4o mini for lightweight tasks, Claude Sonnet 4.5 for code execution)
```

**Replace With**:
```markdown
**Architecture:** Direct HTTP integration to OpenCode server with intelligent model routing (Claude Haiku 4.5 for lightweight tasks, Claude Sonnet 4 for code execution via GitHub Copilot subscription)
```

**Verification**:
- ✅ "GPT-4o mini" removed
- ✅ "Claude Haiku 4.5" appears
- ✅ "Claude Sonnet 4" appears (not 4.5)
- ✅ "GitHub Copilot subscription" mentioned

---

### Phase 3: Update Epic 2 Summary (Line 28)

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Line**: 28  
**Action**: REPLACE entire line

**Current Line 28**:
```markdown
- **Summary:** Migrate all AI planning and classification tasks to OpenCode HTTP API with Claude Haiku 4.5
```

**Replace With**:
```markdown
- **Summary:** Migrate all AI planning and classification tasks to OpenCode HTTP API with Claude Haiku 4.5 (via GitHub Copilot)
```

**Verification**:
- ✅ GitHub Copilot source documented
- ✅ Model name matches Phase 0 decision

---

### Phase 4: Update Epic 3 Summary (Line 35)

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Line**: 35  
**Action**: REPLACE entire line

**Current Line 35**:
```markdown
- **Summary:** Migrate code implementation, testing, and review operations to OpenCode HTTP API with Claude Sonnet 4.5
```

**Replace With**:
```markdown
- **Summary:** Migrate code implementation, testing, and review operations to OpenCode HTTP API with Claude Sonnet 4 (via GitHub Copilot)
```

**Verification**:
- ✅ "Claude Sonnet 4" (not 4.5)
- ✅ "GitHub Copilot" subscription source documented

---

### Phase 5: Fix Story 1.4 Model References (Lines 288, 292, 296)

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Story**: 1.4 - Build model routing logic with task-aware selection  
**Action**: REPLACE acceptance criteria

**Current Acceptance Criteria** (Lines 285-296):
```markdown
### Acceptance Criteria
- Given task_type = "classify"
   When I call get_model_for_task(task_type)
   Then it returns MODEL_LIGHTWEIGHT ("openai/gpt-4o-mini")
   
- Given task_type = "implement"
   When I call get_model_for_task(task_type)
   Then it returns MODEL_HEAVY_LIFTING ("anthropic/claude-3-5-sonnet-20241022")
   
- Given all 9 task types
   When I validate model routing for each
   Then heavy tasks get Claude Sonnet 4.5, lightweight tasks get GPT-4o mini
```

**Replace With**:
```markdown
### Acceptance Criteria
- Given task_type = "classify"
   When I call get_model_for_task(task_type)
   Then it returns MODEL_LIGHTWEIGHT ("github-copilot/claude-haiku-4.5")
   
- Given task_type = "implement"
   When I call get_model_for_task(task_type)
   Then it returns MODEL_HEAVY_LIFTING ("github-copilot/claude-sonnet-4")
   
- Given all 9 task types
   When I validate model routing for each
   Then heavy tasks get Claude Sonnet 4 (GitHub Copilot), lightweight tasks get Claude Haiku 4.5 (GitHub Copilot)
```

**Verification**:
- ✅ Line 288: "github-copilot/claude-haiku-4.5" (was "openai/gpt-4o-mini")
- ✅ Line 292: "github-copilot/claude-sonnet-4" (was "anthropic/claude-3-5-sonnet-20241022")
- ✅ Line 296: Both models use GitHub Copilot format

---

### Phase 6: Update All Epic 2 Story Descriptions (Stories 2.2-2.7)

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Stories**: 2.2, 2.3, 2.4, 2.5, 2.6, 2.7  
**Action**: REPLACE story summaries and descriptions

**Pattern**: Replace "GPT-4o mini" with "Claude Haiku 4.5 (GitHub Copilot)"

#### Story 2.2 (Line ~434)
**Current**: `Migrate extract_adw_info() to OpenCode with GPT-4o mini`  
**Change to**: `Migrate extract_adw_info() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)`

#### Story 2.3 (Line ~454)
**Current**: `Migrate classify_issue() to OpenCode with GPT-4o mini`  
**Change to**: `Migrate classify_issue() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)`

#### Story 2.4 (Line ~474)
**Current**: `Migrate build_plan() to OpenCode with GPT-4o mini`  
**Change to**: `Migrate build_plan() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)`

#### Story 2.5 (Line ~494)
**Current**: `Migrate generate_branch_name() to OpenCode with GPT-4o mini`  
**Change to**: `Migrate generate_branch_name() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)`

#### Story 2.6 (Line ~510)
**Current**: `Migrate create_commit() to OpenCode with GPT-4o mini`  
**Change to**: `Migrate create_commit() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)`

#### Story 2.7 (Line ~526)
**Current**: `Migrate create_pull_request() to OpenCode with GPT-4o mini`  
**Change to**: `Migrate create_pull_request() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)`

**Also update descriptions** (lines mentioning task_type):
- Change "Model: GPT-4o mini" to "Model: Claude Haiku 4.5 (GitHub Copilot)"
- Change "task_type=\"classify\"" descriptions to reference Claude Haiku 4.5

**Verification**:
- ✅ No "GPT-4o mini" references remain in Epic 2 stories
- ✅ All Epic 2 stories reference "Claude Haiku 4.5 (GitHub Copilot)"

---

### Phase 7: Update All Epic 3 Story Descriptions (Stories 3.1-3.4)

**File**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`  
**Stories**: 3.1, 3.2, 3.3, 3.4  
**Action**: REPLACE story summaries and descriptions

**Pattern**: Replace "Claude Sonnet 4.5" with "Claude Sonnet 4 (GitHub Copilot)"

#### Story 3.1 (Line ~576)
**Current**: `Refactor implement_plan() to use OpenCode HTTP API with Claude Sonnet 4.5`  
**Change to**: `Refactor implement_plan() to use OpenCode HTTP API with Claude Sonnet 4 (GitHub Copilot)`

**Also in description**: Change "Model: Claude Sonnet 4.5" to "Model: Claude Sonnet 4 (GitHub Copilot)"

#### Story 3.2 (Line ~596)
**Current**: `Refactor resolve_failed_tests() to use OpenCode HTTP API`  
**Description**: Change "Model: Claude Sonnet 4.5" to "Model: Claude Sonnet 4 (GitHub Copilot)"

#### Story 3.3 (Line ~616)
**Current**: `Refactor execute_single_e2e_test() to use OpenCode HTTP API`  
**Description**: Change "Model: Claude Sonnet 4.5" to "Model: Claude Sonnet 4 (GitHub Copilot)"

#### Story 3.4 (Line ~632)
**Current**: `Refactor run_review() to use OpenCode HTTP API`  
**Description**: Change "Model: Claude Sonnet 4.5" to "Model: Claude Sonnet 4 (GitHub Copilot)"

**Verification**:
- ✅ No "Claude Sonnet 4.5" references remain in Epic 3 stories
- ✅ All Epic 3 stories reference "Claude Sonnet 4 (GitHub Copilot)"

---

## Final Verification Checklist

### Model Naming Consistency
- [ ] **Phase 1**: Phase 0 context block added at top of document
- [ ] **Phase 2**: Line 15 overview statement updated
- [ ] **Phase 3**: Epic 2 summary (line 28) updated with GitHub Copilot reference
- [ ] **Phase 4**: Epic 3 summary (line 35) updated with correct version + GitHub Copilot
- [ ] **Phase 5**: Story 1.4 acceptance criteria (lines 288, 292, 296) fixed
- [ ] **Phase 6**: All Epic 2 stories (2.2-2.7) describe Claude Haiku 4.5 (GitHub Copilot)
- [ ] **Phase 7**: All Epic 3 stories (3.1-3.4) describe Claude Sonnet 4 (GitHub Copilot)

### No Obsolete References
- [ ] ✅ No "GPT-4o mini" anywhere in document
- [ ] ✅ No "Claude Sonnet 4.5" anywhere in document (should be 4)
- [ ] ✅ No "openai/" model IDs anywhere
- [ ] ✅ No "anthropic/" model IDs anywhere
- [ ] ✅ No bare version numbers without provider

### All Model IDs Use Correct Format
- [ ] ✅ All lightweight models: `github-copilot/claude-haiku-4.5`
- [ ] ✅ All heavy models: `github-copilot/claude-sonnet-4`
- [ ] ✅ GitHub Copilot subscription context documented

### Cross-Document Verification
- [ ] ✅ Every model name matches MIGRATION_EXECUTION_GUIDE.md
- [ ] ✅ Every model name matches MIGRATE_TO_OPENCODE_HTTP_API.md
- [ ] ✅ Phase 0 decision clearly documented
- [ ] ✅ GitHub Copilot subscription source is clear throughout

### Document Structure
- [ ] ✅ Phase 0 context block is visibly at top
- [ ] ✅ Overview section follows Phase 0 block
- [ ] ✅ All Epics and Stories logically structured
- [ ] ✅ No formatting issues introduced

---

## Implementation Notes

### Order of Execution
Execute phases **in order** (1→2→3→4→5→6→7) because:
1. Phase 1 provides context for all other changes
2. Phase 2 sets the foundation architecture statement
3. Phases 3-4 update Epic summaries
4. Phase 5 fixes the detailed acceptance criteria
5. Phases 6-7 cascade the changes through all stories

### How to Implement
For each phase:
1. Read the "Action" section to understand what to do
2. Use the "Current" and "Replace With" sections to find and replace
3. Check the "Verification" checklist to confirm success
4. Move to next phase

### Search Tips
Use Find/Replace in editor:
- **Find**: Current text (provided in each phase)
- **Replace With**: New text (provided in each phase)
- **Verify**: Use verification checklist after each replacement

### Safety
- Make changes one phase at a time
- Verify after each phase before moving to next
- If you make a mistake, you have git history to revert

---

## Expected Results

After completing all 7 phases + verification:

### ✅ Alignment Achieved
- JIRA_EPICS_AND_STORIES.md perfectly aligned with both reference documents
- All model names consistent and correct
- GitHub Copilot subscription context clear
- Phase 0 architectural decision documented

### ✅ Document Quality
- Clear Phase 0 context at top explaining decisions
- Consistent model naming throughout all 43 stories
- Professional documentation for Jira import
- No conflicting or outdated information

### ✅ Ready for Next Steps
- Document can be imported to Jira without corrections
- All 43 stories have correct acceptance criteria
- Clear model routing specification for developers
- Complete alignment with implementation guides

---

## Post-Implementation Commit

After all phases are complete and verified:

**Commit Message**:
```
docs: Align JIRA_EPICS_AND_STORIES.md with Phase 0 decisions and model naming

- Add Phase 0 architectural context (Deluxe fallback removed)
- Update all model references to Phase 0 standard:
  - Lightweight: claude-haiku-4.5 (via GitHub Copilot)
  - Heavy: claude-sonnet-4 (via GitHub Copilot)
- Fix model ID formats (github-copilot/ prefix)
- Update Epic 2 & 3 summaries with correct versions
- Update all 43 stories with consistent naming
- Now perfectly aligned with:
  - MIGRATION_EXECUTION_GUIDE.md
  - MIGRATE_TO_OPENCODE_HTTP_API.md

This ensures Jira import with no corrections needed.
```

---

## Quick Reference: What Changes

### Before (WRONG)
- Overview: "GPT-4o mini" + "Claude Sonnet 4.5"
- Story 1.4: `"openai/gpt-4o-mini"` + `"anthropic/claude-3-5-sonnet-20241022"`
- Epic 2: "Claude Haiku 4.5" (no subscription context)
- Epic 3: "Claude Sonnet 4.5" (wrong version)
- Epic 2 Stories: No "GitHub Copilot" mention
- Epic 3 Stories: No "GitHub Copilot" mention
- No Phase 0 context anywhere

### After (CORRECT)
- Overview: "Claude Haiku 4.5" + "Claude Sonnet 4" (via GitHub Copilot)
- Story 1.4: `"github-copilot/claude-haiku-4.5"` + `"github-copilot/claude-sonnet-4"`
- Epic 2: "Claude Haiku 4.5 (GitHub Copilot)"
- Epic 3: "Claude Sonnet 4 (GitHub Copilot)"
- Epic 2 Stories: All reference "Claude Haiku 4.5 (GitHub Copilot)"
- Epic 3 Stories: All reference "Claude Sonnet 4 (GitHub Copilot)"
- Phase 0 context block clearly documents all decisions

---

**Status**: ✅ Plan Complete and Saved  
**Next Step**: Start new session and execute phases 1-7 in order  
**File**: This plan is saved at `ai_docs/specs/plans/ALIGNMENT_PLAN.md`

