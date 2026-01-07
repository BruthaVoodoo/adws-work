# ADWS OpenCode HTTP API Migration - Execution Guide

**Created:** January 7, 2026  
**Status:** Ready for Development  
**Total Scope:** 43 Jira Stories across 5 Epics  
**Estimated Duration:** 40-50 hours (28-32 hours with parallelization)  
**Critical Safety Mechanism:** Feature Flags + Old Code Fallback

---

## Executive Summary

This document provides the working execution guide for migrating ADWS from AWS Bedrock + Custom Proxy + Copilot CLI to **OpenCode HTTP API with intelligent model routing**.

**Key Feature**: Feature flags allow instant rollback if anything breaks - no code changes needed, just config toggle.

**Structure**: 5 Epics → 43 Stories in strict dependency order:
1. ✅ **Epic 1**: HTTP Client Infrastructure (foundation)
2. ✅ **Epic 2**: Planning/Classification Operations (6 functions → GPT-4o mini)
3. ✅ **Epic 3**: Code Execution Operations (3 functions → Claude Sonnet 4.5)
4. ✅ **Epic 4**: Cleanup & Deprecated Code
5. ✅ **Epic 5**: Comprehensive Testing & Documentation

---

## Part 1: Safety First - Feature Flags

### Why Feature Flags Matter

**Problem**: During migration, we could reach a state where the system breaks and we can't use ADWS to fix ADWS.

**Solution**: Two-level feature flag system allows instant rollback.

### Feature Flag Configuration

**File**: `.adw.yaml`

```yaml
# Migration safety flags - allows instant rollback to old system
migration:
  # Enable OpenCode HTTP for lightweight tasks (planning, classification)
  # All 6 operations: extract_adw_info, classify_issue, build_plan, 
  # generate_branch_name, create_commit, create_pull_request
  use_opencode_for_lightweight: false
  
  # Enable OpenCode HTTP for heavy lifting (code execution, testing, review)
  # All 3 operations: implement_plan, resolve_failed_tests, run_review
  use_opencode_for_heavy_lifting: false
  
  # Emergency kill switch - disables ALL OpenCode features
  # Set to true if system breaks - immediately reverts to old backends
  disable_opencode: false

# OpenCode HTTP Server configuration (only used if enabled above)
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "anthropic/claude-3-5-sonnet-20241022"
    lightweight: "openai/gpt-4o-mini"
  timeout: 600
  lightweight_timeout: 60
  max_retries: 3
```

### How to Use Feature Flags During Development

**Phase 1** (Epic 1 - Build Infrastructure):
- Flags remain `false` - no changes to existing code
- Build new HTTP client in isolation
- Create all unit tests
- NO BREAKING CHANGES

**Phase 2** (Epic 2 - Planning Operations):
- Set `use_opencode_for_lightweight: true`
- Run test suite
- If broken, flip back to `false` → system uses old code
- Once stable, keep `true`

**Phase 3** (Epic 3 - Code Execution):
- Set `use_opencode_for_heavy_lifting: true`
- Run full test suite
- If broken, flip back to `false` → system uses Copilot
- Once stable, keep `true`

**Emergency Procedure**:
```bash
# If system completely breaks:
# 1. Edit .adw.yaml
# 2. Change: disable_opencode: true
# 3. Restart system
# 4. System reverts to old backends (custom proxy + Copilot)
# 5. Investigate and fix issue
```

---

## Part 2: Epic Breakdown (43 Stories)

### Epic 1: HTTP Client Infrastructure (6-8 hours) ⭐ CRITICAL PATH

**Stories**: 10  
**Dependencies**: None  
**Feature Flag Impact**: NONE (isolated new code)

Creates the foundational HTTP client layer. This is the critical path item that enables all other work.

**Stories**:
1. Create OpenCodeHTTPClient class with session management (4h)
2. Implement OpenCode HTTP API communication layer (4h)
3. Create OpenCode data types (OpenCodeResponse, OpenCodePart, etc.) (2h)
4. Build model routing logic with task-aware selection (2h)
5. Develop output parser for structured Part extraction (3h)
6. Add response logging and error handling (2h)
7. Implement connection retry logic with exponential backoff (2h)
8. Write comprehensive unit tests for HTTP client (3h)
9. Write comprehensive unit tests for output parser (2h)
10. Add OpenCode configuration to .adw.yaml (1h)

**Success Criteria**:
- [ ] HTTP client successfully connects and manages sessions
- [ ] All Part types (text, tool_use, tool_result) correctly parsed
- [ ] Model routing selects correct model for each task type
- [ ] Configuration loads from .adw.yaml
- [ ] 50+ unit tests pass
- [ ] All error scenarios handled

**Output Artifacts**:
- `scripts/adw_modules/opencode_http_client.py` (~300 lines)
- `scripts/adw_modules/opencode_output_parser.py` (~250 lines)
- `scripts/adw_modules/data_types.py` (additions for OpenCode types)
- `tests/test_http_client.py` (~250 lines, 30+ tests)
- `tests/test_output_parser.py` (~200 lines, 20+ tests)

---

### Epic 2: Planning & Classification Operations (6-8 hours)

**Stories**: 9  
**Dependencies**: Epic 1  
**Feature Flag**: `use_opencode_for_lightweight`  
**Can Overlap**: With Epic 3 (after Epic 1 complete)

Refactor all lightweight planning/classification operations to use OpenCode HTTP with GPT-4o mini.

**Operations Migrated**:
- `extract_adw_info()` - ADW workflow classification
- `classify_issue()` - Issue classification (/chore, /bug, /feature)
- `build_plan()` - Implementation planning
- `generate_branch_name()` - Branch name generation
- `create_commit()` - Commit message creation
- `create_pull_request()` - PR title/description generation

**Stories**:
1. Refactor agent.py execute_template() for OpenCode HTTP (3h)
2. Migrate extract_adw_info() to OpenCode lightweight (2h)
3. Migrate classify_issue() to OpenCode lightweight (2h)
4. Migrate build_plan() to OpenCode lightweight (2h)
5. Migrate generate_branch_name() to OpenCode lightweight (2h)
6. Migrate create_commit() to OpenCode lightweight (2h)
7. Migrate create_pull_request() to OpenCode lightweight (2h)
8. Update error handling for planning operations (1h)
9. Write integration tests for planning operations (2h)

**Success Criteria**:
- [ ] All 6 operations execute via OpenCode HTTP
- [ ] Correct lightweight model (GPT-4o mini) selected
- [ ] No functional regressions in output
- [ ] Proper error handling with helpful messages
- [ ] Response logging enabled
- [ ] Integration tests pass

**Feature Flag Usage**:
```python
def extract_adw_info(text: str) -> dict:
    if config.migration.use_opencode_for_lightweight:
        # NEW: OpenCode HTTP with GPT-4o mini
        response = execute_opencode_prompt(
            prompt=text,
            task_type="extract_adw"
        )
        return parse_adw_response(response)
    else:
        # OLD: Custom proxy (still works)
        return invoke_model(text, agent_prompt_template)
```

---

### Epic 3: Code Execution Operations (8-10 hours)

**Stories**: 8  
**Dependencies**: Epic 1  
**Feature Flag**: `use_opencode_for_heavy_lifting`  
**Can Overlap**: With Epic 2 (after Epic 1 complete)

Replace Copilot CLI with OpenCode HTTP API for all heavy code lifting operations.

**Operations Migrated**:
- `implement_plan()` - Code implementation
- `resolve_failed_tests()` - Test failure fixing
- `execute_single_e2e_test()` - E2E test execution
- `run_review()` - Code review

**Stories**:
1. Refactor implement_plan() to use OpenCode HTTP API (4h)
2. Refactor resolve_failed_tests() to use OpenCode HTTP API (3h)
3. Refactor execute_single_e2e_test() to use OpenCode HTTP API (2h)
4. Refactor run_review() to use OpenCode HTTP API (3h)
5. Update error handling in adw_test.py for OpenCode (1h)
6. Update error handling in adw_review.py for OpenCode (1h)
7. Write integration tests for code execution operations (3h)
8. Test git fallback validation with OpenCode responses (1h)

**Success Criteria**:
- [ ] All 3 code execution functions use OpenCode with Claude Sonnet 4.5
- [ ] Structured Part parsing replaces Copilot text parsing
- [ ] Git fallback validation still works
- [ ] Error messages are helpful and actionable
- [ ] Response logging enabled
- [ ] Integration tests pass with real code execution scenarios

**Feature Flag Usage**:
```python
def implement_plan(plan_file: str, ...) -> AgentPromptResponse:
    if config.migration.use_opencode_for_heavy_lifting:
        # NEW: OpenCode HTTP with Claude Sonnet 4.5
        response = execute_opencode_prompt(
            prompt=load_plan(plan_file),
            task_type="implement"
        )
        return convert_to_agent_response(response)
    else:
        # OLD: Copilot CLI (still works)
        return subprocess.run(["copilot", "-p", prompt])
```

---

### Epic 4: Cleanup & Deprecated Code (2-3 hours)

**Stories**: 5  
**Dependencies**: Epics 2 & 3  
**Prerequisite**: Both lightweight and heavy lifting must be stable and passing tests

Remove deprecated code paths and old environment variables.

**Stories**:
1. Mark bedrock_agent.py as deprecated (30m)
2. Mark copilot_output_parser.py as deprecated (30m)
3. Remove AWS environment variable validation (1h)
4. Update health_check.py to verify OpenCode server (1h)
5. Remove Copilot CLI checks from adw_test.py and adw_review.py (30m)

**Success Criteria**:
- [ ] Deprecated files clearly marked with notices
- [ ] All AWS environment variable checks removed
- [ ] Health checks updated to verify OpenCode server
- [ ] Copilot CLI checks replaced with OpenCode checks
- [ ] No functional changes to core logic

**⚠️ Important**: Only do cleanup after both lightweight AND heavy lifting are 100% stable with all tests passing. This is not on critical path.

---

### Epic 5: Testing, Validation & Documentation (10-12 hours) ⭐ FINAL

**Stories**: 11  
**Dependencies**: All previous epics  
**Must Complete Last**: Validates entire migration

Comprehensive testing across all 9 migrated LLM operations and complete documentation.

**Stories**:
1. Write unit tests for OpenCode HTTP client (4h) - 30+ tests
2. Write unit tests for output parser (2h) - 20+ tests
3. Write integration tests for planning operations (2h)
4. Write integration tests for code execution operations (3h)
5. Write regression tests for all 9 LLM operations (2h)
6. Performance test comparison vs old system (2h)
7. Update AGENTS.md with OpenCode section (2h)
8. Create comprehensive MIGRATION_GUIDE.md (2h)
9. Update .adw.yaml with OpenCode configuration examples (1h)
10. Update README.md setup instructions (1h)
11. Write troubleshooting guide (1h)

**Success Criteria**:
- [ ] All 9 LLM operations tested and validated
- [ ] 60+ unit tests with >80% code coverage
- [ ] Integration tests pass with real OpenCode server
- [ ] No regressions in existing functionality
- [ ] Documentation complete and reviewed
- [ ] Setup instructions clear and verified
- [ ] Troubleshooting guide covers common issues

**Test Coverage Targets**:
- HTTP Client: 30+ unit tests (connection, session, timeout, retry, error handling)
- Output Parser: 20+ unit tests (text extraction, tool counting, metrics)
- Planning Operations: Integration tests for all 6 functions
- Code Execution: Integration tests for all 3 functions
- Regression: All existing tests must pass

---

## Part 3: Execution Roadmap

### Week 1: Foundation (Epic 1)

**Days 1-2**: HTTP Client Infrastructure (6-8 hours)
- [ ] Create OpenCodeHTTPClient class (Story 1.1)
- [ ] Implement HTTP communication (Story 1.2)
- [ ] Add data types (Story 1.3)
- [ ] Build model routing (Story 1.4)
- [ ] Develop output parser (Story 1.5)
- [ ] Add response logging (Story 1.6)
- [ ] Implement retry logic (Story 1.7)
- [ ] Write HTTP client tests (Story 1.8)
- [ ] Write output parser tests (Story 1.9)
- [ ] Add configuration (Story 1.10)

**Checkpoint**: 50+ unit tests passing, HTTP client fully functional

---

### Week 1-2: Parallel Development (Epics 2 & 3)

**Days 3-4**: Planning Operations (Epic 2, 6-8 hours)
- [ ] Refactor agent.py execute_template() (Story 2.1)
- [ ] Migrate extract_adw_info() (Story 2.2)
- [ ] Migrate classify_issue() (Story 2.3)
- [ ] Migrate build_plan() (Story 2.4)
- [ ] Migrate generate_branch_name() (Story 2.5)
- [ ] Migrate create_commit() (Story 2.6)
- [ ] Migrate create_pull_request() (Story 2.7)
- [ ] Update error handling (Story 2.8)
- [ ] Write integration tests (Story 2.9)

**Checkpoint**: All 6 planning operations working with feature flag OFF, then ON

**Days 4-5**: Code Execution Operations (Epic 3, 8-10 hours)
- [ ] Refactor implement_plan() (Story 3.1)
- [ ] Refactor resolve_failed_tests() (Story 3.2)
- [ ] Refactor execute_single_e2e_test() (Story 3.3)
- [ ] Refactor run_review() (Story 3.4)
- [ ] Update error handling in adw_test.py (Story 3.5)
- [ ] Update error handling in adw_review.py (Story 3.6)
- [ ] Write integration tests (Story 3.7)
- [ ] Test git fallback (Story 3.8)

**Checkpoint**: All 3 code execution operations working with feature flag OFF, then ON

**Days 3-5 (Parallel)**: Can run Epic 2 and Epic 3 simultaneously
- Different developers/agents work on planning vs. code execution
- Both depend only on Epic 1
- Saves 6-8 hours vs. sequential

---

### Week 2: Cleanup (Epic 4)

**Day 6**: Cleanup & Deprecation (2-3 hours)
- [ ] Mark bedrock_agent.py deprecated (Story 4.1)
- [ ] Mark copilot_output_parser.py deprecated (Story 4.2)
- [ ] Remove AWS environment variables (Story 4.3)
- [ ] Update health_check.py (Story 4.4)
- [ ] Remove Copilot CLI checks (Story 4.5)

**Prerequisite**: Epics 2 & 3 must be 100% complete and tests passing

**Checkpoint**: All deprecated code marked, old config removed, health checks updated

---

### Week 2-3: Testing & Documentation (Epic 5)

**Days 6-8**: Comprehensive Testing (10-12 hours)
- [ ] Write HTTP client unit tests (Story 5.1)
- [ ] Write output parser unit tests (Story 5.2)
- [ ] Write planning integration tests (Story 5.3)
- [ ] Write code execution integration tests (Story 5.4)
- [ ] Write regression tests (Story 5.5)
- [ ] Performance comparison (Story 5.6)

**Checkpoint**: 60+ tests passing, no regressions

**Days 8-9**: Documentation (4 hours)
- [ ] Update AGENTS.md (Story 5.7)
- [ ] Create MIGRATION_GUIDE.md (Story 5.8)
- [ ] Update .adw.yaml examples (Story 5.9)
- [ ] Update README.md (Story 5.10)
- [ ] Write troubleshooting guide (Story 5.11)

**Final Checkpoint**: All tests passing, documentation complete, system ready for production

---

## Part 4: Safe Execution Checklist

### Before Starting (Prerequisites)

- [ ] OpenCode installed and working: `opencode serve --port 4096`
- [ ] API keys configured: `opencode auth login`
- [ ] All existing tests passing: `uv run pytest`
- [ ] `.adw.yaml` has migration section with feature flags
- [ ] Old code still works (no breaking changes yet)

### After Each Epic

**Epic 1 Completion**:
- [ ] 50+ HTTP client unit tests passing
- [ ] HTTP client can connect to OpenCode server
- [ ] Model routing correctly selects models
- [ ] No changes to existing code

**Epic 2 Completion**:
- [ ] All 6 planning operations working with feature flag OFF
- [ ] All 6 planning operations working with feature flag ON
- [ ] All integration tests passing
- [ ] Original tests still passing
- [ ] Feature flag `use_opencode_for_lightweight: true`

**Epic 3 Completion**:
- [ ] All 3 code execution operations working with feature flag OFF
- [ ] All 3 code execution operations working with feature flag ON
- [ ] All integration tests passing
- [ ] Original tests still passing
- [ ] Feature flag `use_opencode_for_heavy_lifting: true`

**Epic 4 Completion**:
- [ ] Both feature flags stable and on
- [ ] Deprecated code marked
- [ ] Old environment variables removed
- [ ] Health checks updated
- [ ] All tests still passing

**Epic 5 Completion**:
- [ ] 60+ unit + integration tests passing
- [ ] No regressions
- [ ] Documentation complete
- [ ] Ready for production

### Emergency Procedures

**If anything breaks**:
1. Set `disable_opencode: true` in `.adw.yaml`
2. Restart the application
3. System reverts to old backends (no code changes needed)
4. Investigate and fix the issue

**If OpenCode server crashes**:
1. Restart: `opencode serve --port 4096`
2. Verify: `curl http://localhost:4096/global/health`
3. Re-authenticate if needed: `opencode auth login`

---

## Part 5: File Manifest

### Files to Create

**Core Infrastructure**:
- `scripts/adw_modules/opencode_http_client.py` (~300 lines)
- `scripts/adw_modules/opencode_output_parser.py` (~250 lines)

**Tests**:
- `tests/test_http_client.py` (~250 lines, 30+ tests)
- `tests/test_output_parser.py` (~200 lines, 20+ tests)
- `tests/test_integration_planning.py` (planning operations)
- `tests/test_integration_code_execution.py` (code execution operations)

**Documentation**:
- `ai_docs/specs/MIGRATION_GUIDE.md` (user guide)

### Files to Modify

**Core Application Logic**:
- `scripts/adw_modules/data_types.py` (add OpenCode types)
- `scripts/adw_modules/config.py` (add OpenCode config + feature flags)
- `scripts/adw_modules/agent.py` (add feature flag to execute_template)
- `scripts/adw_modules/workflow_ops.py` (6 functions, add feature flags)
- `scripts/adw_test.py` (3 functions, add feature flags)
- `scripts/adw_review.py` (1 function, add feature flag)

**System Files**:
- `scripts/adw_modules/bedrock_agent.py` (mark deprecated)
- `scripts/adw_modules/copilot_output_parser.py` (mark deprecated)
- `scripts/adw_modules/health_check.py` (update for OpenCode)
- `.adw.yaml` (add migration section + opencode config)

**Documentation**:
- `AGENTS.md` (add OpenCode HTTP server section)
- `README.md` (update setup instructions)

---

## Part 6: Reference Links

**Supporting Documents**:
- `ai_docs/specs/plans/MIGRATE_TO_OPENCODE_HTTP_API.md` - Detailed technical plan
- `ai_docs/specs/JIRA_EPICS_AND_STORIES.md` - All 43 Jira stories with acceptance criteria
- `.adw.yaml` - Configuration file with feature flags

**Key Implementation Guides**:
- OpenCode HTTP API documentation: https://opencode.ai/docs/
- Model IDs: Claude Sonnet 4.5 (`anthropic/claude-3-5-sonnet-20241022`), GPT-4o mini (`openai/gpt-4o-mini`)
- Structured response format: Message + Parts (text, tool_use, tool_result, code_block)

---

## Summary

**Total Scope**: 43 Jira Stories across 5 Epics  
**Estimated Duration**: 40-50 hours (28-32 with parallelization)  
**Safety Mechanism**: Feature flags allow instant rollback  
**Critical Path**: Epic 1 → (Epic 2 | Epic 3) → Epic 4 → Epic 5  
**Risk Level**: LOW (with feature flags, old code always available)

**Success = All 9 LLM operations using OpenCode HTTP, 60+ tests passing, zero regressions**

---

**Document Version:** 1.0  
**Last Updated:** January 7, 2026  
**Status:** Ready for Development
