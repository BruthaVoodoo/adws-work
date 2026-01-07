# OpenCode Migration - Quick Reference Card

**Print this or keep in your editor for quick lookup during development**

---

## Feature Flags (Safety First!)

```yaml
# .adw.yaml
migration:
  use_opencode_for_lightweight: false    # Planning/classification (Epic 2)
  use_opencode_for_heavy_lifting: false  # Code execution (Epic 3)
  disable_opencode: false                # Emergency kill switch
```

**Emergency Override**:
```bash
# System breaking? Edit .adw.yaml:
# Set: disable_opencode: true
# Restart app → System reverts to old backends
```

---

## 5 Epics in Order

| # | Epic | Hours | Stories | Flag | Can Parallel? |
|---|------|-------|---------|------|---------------|
| 1 | HTTP Client Infrastructure | 6-8 | 10 | NONE | — |
| 2 | Planning/Classification Ops | 6-8 | 9 | `use_opencode_for_lightweight` | With Epic 3 |
| 3 | Code Execution Ops | 8-10 | 8 | `use_opencode_for_heavy_lifting` | With Epic 2 |
| 4 | Cleanup & Deprecation | 2-3 | 5 | N/A | After 2+3 |
| 5 | Testing & Documentation | 10-12 | 11 | N/A | Last |
| **TOTAL** | | **40-50** | **43** | | **28-32 parallel** |

---

## 9 Operations Migrated

### Lightweight Tasks (Epic 2) → GPT-4o mini
1. `extract_adw_info()` - ADW classification
2. `classify_issue()` - Issue type classification
3. `build_plan()` - Implementation planning
4. `generate_branch_name()` - Branch naming
5. `create_commit()` - Commit messages
6. `create_pull_request()` - PR generation

### Heavy Lifting (Epic 3) → Claude Sonnet 4.5
7. `implement_plan()` - Code implementation
8. `resolve_failed_tests()` - Test fixing
9. `run_review()` - Code review

---

## Files Created by Epic

### Epic 1 Creates (Infrastructure)
- `scripts/adw_modules/opencode_http_client.py` (~300 lines)
- `scripts/adw_modules/opencode_output_parser.py` (~250 lines)
- `tests/test_http_client.py` (~250 lines, 30+ tests)
- `tests/test_output_parser.py` (~200 lines, 20+ tests)

### Epic 2 Modifies (6 functions)
- `scripts/adw_modules/agent.py` (execute_template)
- `scripts/adw_modules/workflow_ops.py` (6 functions)
- Feature flag: `use_opencode_for_lightweight`

### Epic 3 Modifies (4 functions)
- `scripts/adw_modules/workflow_ops.py` (implement_plan)
- `scripts/adw_test.py` (resolve_failed_tests, execute_single_e2e_test)
- `scripts/adw_review.py` (run_review)
- Feature flag: `use_opencode_for_heavy_lifting`

### Epic 4 Updates (Cleanup)
- Mark `bedrock_agent.py` deprecated
- Mark `copilot_output_parser.py` deprecated
- Remove AWS environment variables
- Update `health_check.py`
- Update `adw_test.py` + `adw_review.py` checks

### Epic 5 Creates (Testing & Docs)
- `tests/test_integration_planning.py`
- `tests/test_integration_code_execution.py`
- `ai_docs/specs/MIGRATION_GUIDE.md`
- Update: `AGENTS.md`, `README.md`, `.adw.yaml`

---

## Typical Feature Flag Pattern

```python
# Example: Any operation
def some_operation(...) -> Result:
    # Check feature flag
    if config.migration.disable_opencode:
        # Emergency override - use old system
        return old_system_call(...)
    
    if is_lightweight and config.migration.use_opencode_for_lightweight:
        # NEW: OpenCode HTTP with GPT-4o mini
        return execute_opencode_prompt(..., task_type="classify")
    
    elif is_heavy and config.migration.use_opencode_for_heavy_lifting:
        # NEW: OpenCode HTTP with Claude Sonnet 4.5
        return execute_opencode_prompt(..., task_type="implement")
    
    else:
        # OLD: Custom proxy or Copilot (still works)
        return old_system_call(...)
```

---

## Test Targets

- **Epic 1**: 50+ unit tests (HTTP client + parser)
- **Epic 2**: Integration tests for 6 planning functions
- **Epic 3**: Integration tests for 3 code execution functions
- **Epic 4**: No new tests (just cleanup)
- **Epic 5**: 60+ total tests + regression suite

**Success Criteria**: All tests pass, zero regressions

---

## Safe Execution Checklist

### Before Each Epic
- [ ] All previous tests passing
- [ ] Feature flags set correctly
- [ ] OpenCode server running: `opencode serve --port 4096`

### After Each Epic
- [ ] Run full test suite: `uv run pytest`
- [ ] Check logs: `ai_docs/logs/`
- [ ] Verify no regressions
- [ ] Feature flags in correct state

### Before Moving to Next Epic
- [ ] Feature flag for current epic: ON or OFF?
- [ ] All acceptance criteria met
- [ ] All tests passing
- [ ] Ready to proceed

---

## Quick Commands

```bash
# Check OpenCode server
curl http://localhost:4096/global/health

# Start OpenCode server
opencode serve --port 4096

# Authenticate OpenCode
opencode auth login

# Run all tests
uv run pytest

# Run specific test
uv run pytest -s tests/test_http_client.py

# Check test coverage
uv run pytest --cov=scripts/adw_modules

# View logs
tail -f ai_docs/logs/*/*/response_*.json
```

---

## Model IDs Reference

**Heavy Lifting** (Code):
- `anthropic/claude-3-5-sonnet-20241022`

**Lightweight** (Planning):
- `openai/gpt-4o-mini`

---

## Jira Story Links

**Full Details**: `ai_docs/specs/JIRA_EPICS_AND_STORIES.md`
- All 43 stories with acceptance criteria
- Estimation for each story
- Dependencies clearly marked

**Technical Details**: `ai_docs/specs/plans/MIGRATE_TO_OPENCODE_HTTP_API.md`
- Architecture diagrams
- Model routing logic
- Output parsing strategies
- Configuration examples

**Execution Guide**: `ai_docs/specs/plans/MIGRATION_EXECUTION_GUIDE.md` ← YOU ARE HERE
- Day-by-day roadmap
- Feature flag patterns
- File manifest
- Emergency procedures

---

## Remember

✅ **You CAN use ADWS to work on itself** with feature flags  
✅ **Old code always available** as fallback  
✅ **No code changes needed to rollback** - just flip config  
✅ **Test early, test often** - especially after each epic  
✅ **Parallelization saves 12-18 hours** - do Epic 2 & 3 in parallel  

---

**Last Updated**: January 7, 2026  
**Status**: Ready for Development
