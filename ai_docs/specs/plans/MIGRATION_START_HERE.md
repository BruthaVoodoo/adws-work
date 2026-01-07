# OpenCode HTTP API Migration - START HERE

**Jason, start with this document. It explains everything you need to know.**

---

## The Question You Asked

> "I have 5 epics and a bunch of stories we need to work through. I'm going to use the ADWS process to work on itself. Will there be an issue with that idea? Could I get to a point where the changes I'm making don't allow me to use the system to make the change?"

### The Answer

**✅ YES, you can use ADWS to work on itself - with proper safeguards.**

**The safeguard: Feature Flags + Old Code Fallback**

If the OpenCode integration breaks, you flip a config setting (not code) and ADWS reverts to the old system (AWS Bedrock + Copilot). This happens instantly - no code changes, no complex rollback.

---

## What You're Building

**Migration Scope**: Replace AWS Bedrock + Copilot CLI with OpenCode HTTP API

**Organized as**: 5 Epics → 43 Jira Stories (all detailed in JIRA_EPICS_AND_STORIES.md)

**Duration**: 40-50 hours (28-32 hours with parallelization)

**Status**: Ready for development right now

---

## 5 Epics (In Order)

### Epic 1: HTTP Client Infrastructure (6-8 hours) ⭐ START HERE
- Creates foundation for everything else
- No breaking changes (isolated new code)
- Output: HTTP client + 50+ unit tests
- **After this, system is still fully functional with old backends**

### Epic 2: Planning Operations (6-8 hours)
- Migrate 6 functions to OpenCode HTTP (GPT-4o mini)
- Feature flag: `use_opencode_for_lightweight`
- Can run in parallel with Epic 3

### Epic 3: Code Execution Operations (8-10 hours)
- Migrate 3 functions to OpenCode HTTP (Claude Sonnet 4.5)
- Feature flag: `use_opencode_for_heavy_lifting`
- Can run in parallel with Epic 2

### Epic 4: Cleanup (2-3 hours)
- Mark deprecated code
- Remove old environment variables
- **Only after Epics 2 & 3 are stable**

### Epic 5: Testing & Documentation (10-12 hours)
- 60+ comprehensive tests
- Update all documentation
- **Must be last to validate everything**

---

## Safety Mechanism: Feature Flags

### How It Works

```yaml
# .adw.yaml
migration:
  use_opencode_for_lightweight: false    # Planning/classification (Epic 2)
  use_opencode_for_heavy_lifting: false  # Code execution (Epic 3)
  disable_opencode: false                # Emergency kill switch
```

**Each operation checks its flag**:
- If `false` → uses old system (works perfectly)
- If `true` → uses new OpenCode HTTP
- If something breaks → set `disable_opencode: true` → instant rollback

### Emergency Procedure (30 seconds)
1. Edit `.adw.yaml`
2. Change: `disable_opencode: true`
3. Restart your app
4. **Done.** System reverts to old backends (no code changes!)

---

## The 9 Operations You're Migrating

### Lightweight Tasks (Epic 2) → GPT-4o mini
1. `extract_adw_info()` - ADW workflow classification
2. `classify_issue()` - Issue classification
3. `build_plan()` - Implementation planning
4. `generate_branch_name()` - Branch naming
5. `create_commit()` - Commit messages
6. `create_pull_request()` - PR generation

### Heavy Lifting Tasks (Epic 3) → Claude Sonnet 4.5
7. `implement_plan()` - Code implementation
8. `resolve_failed_tests()` - Test fixing
9. `run_review()` - Code review

---

## Timeline

```
Week 1 (Days 1-2):
  Epic 1: HTTP Client Infrastructure (6-8h)
  → After this: System still works with old backends

Week 1-2 (Days 3-5) - PARALLEL:
  Epic 2: Planning Operations (6-8h)
  Epic 3: Code Execution Operations (8-10h)
  → Can run simultaneously, saves 6-8 hours!

Week 2 (Day 6):
  Epic 4: Cleanup (2-3h)
  → Only after Epics 2 & 3 are stable

Week 2-3 (Days 6-9):
  Epic 5: Testing & Documentation (10-12h)
  → Last step: validate everything works

Total: 28-32 hours with parallelization ⭐
```

---

## Files to Read (In This Order)

### 1. THIS FILE (you're reading it now)
Quick overview and safety explanation

### 2. MIGRATION_EXECUTION_GUIDE.md (523 lines)
**⭐ READ THIS NEXT**
- Day-by-day roadmap
- Feature flag patterns
- File manifest
- Emergency procedures

### 3. JIRA_EPICS_AND_STORIES.md (1047 lines)
All 43 stories with detailed acceptance criteria
- Use this to create Jira issues
- Reference during development
- Each story has clear "Definition of Done"

### 4. MIGRATE_TO_OPENCODE_HTTP_API.md (1460 lines)
Technical deep dive
- Architecture details
- Model routing logic
- Output parsing strategies
- Configuration examples

### 5. QUICK_REFERENCE.md (217 lines)
Printable reference card
- Keep open during development
- Quick lookup for epic summaries
- Feature flag reminders
- Common commands

---

## How to Use This Plan

### Phase 1: Preparation
1. Read MIGRATION_EXECUTION_GUIDE.md (523 lines)
2. Review JIRA_EPICS_AND_STORIES.md (understand all 43 stories)
3. Keep QUICK_REFERENCE.md open

### Phase 2: Implementation
1. Start Epic 1 (HTTP Client Infrastructure)
2. Run full test suite after Epic 1
3. Enable Epics 2 & 3 in parallel with feature flags
4. Run tests frequently
5. After both are stable, do Epic 4 cleanup
6. Do Epic 5 (testing & docs) last

### Phase 3: Production
1. All 43 stories complete
2. 60+ tests passing
3. Zero regressions
4. Documentation complete
5. Deploy! ✅

---

## Key Decisions Made

### 1. Feature Flags (Not Breaking Changes)
- Each refactored operation checks its flag
- If flag is `false`, uses old system
- If flag is `true`, uses new OpenCode HTTP
- Zero risk of breaking the system

### 2. Parallelization Strategy
- Epic 1 must complete first (foundation)
- Epic 2 and 3 can run in parallel (both depend on Epic 1)
- Saves 6-8 hours vs. sequential

### 3. Keep Old Code
- Mark as deprecated but don't delete
- Fallback if something goes wrong
- Provides audit trail of changes

### 4. Comprehensive Testing
- 50+ tests in Epic 1 (infrastructure)
- Integration tests in Epics 2 & 3
- 60+ tests total in Epic 5
- Regression tests for all 9 operations

---

## Success Criteria

**Epic 1**: ✓ 50+ unit tests passing  
**Epic 2**: ✓ All 6 planning operations working via OpenCode  
**Epic 3**: ✓ All 3 code execution operations working via OpenCode  
**Epic 4**: ✓ Deprecated code marked, old env vars removed  
**Epic 5**: ✓ 60+ tests passing, zero regressions, docs complete  

**Final**: ✓ Production-ready system using OpenCode HTTP for all 9 operations

---

## FAQ

### Q: Can I really use ADWS to work on itself?
**A**: Yes! Feature flags make it safe. If anything breaks, flip a config setting and the system reverts to old backends.

### Q: What if OpenCode breaks in the middle of development?
**A**: Set `disable_opencode: true` in `.adw.yaml` and restart. System immediately reverts to AWS Bedrock + Copilot. No code changes needed.

### Q: How much time will this take?
**A**: 40-50 hours sequentially, or 28-32 hours if you run Epics 2 & 3 in parallel.

### Q: Can I delete the old code?
**A**: Not yet. Keep it as a fallback. Mark as deprecated in Epic 4. Only consider deletion after months of stable production use.

### Q: What if a story takes longer than estimated?
**A**: That's fine. The estimates are conservative. Feature flags let you work incrementally without breaking anything.

### Q: Do I need to refactor all 9 operations at once?
**A**: No! Do Epic 1 first (foundation), then Epics 2 & 3 with feature flags (can be independent). This keeps risk low.

### Q: What if I want to rollback a specific operation?
**A**: Flip its feature flag in `.adw.yaml`. That operation reverts to old backend, others stay on new backend.

### Q: How do I know if my implementation is working?
**A**: Run the integration tests for that operation. They verify all 9 operations work as expected.

---

## Next Steps

1. **Read MIGRATION_EXECUTION_GUIDE.md** (523 lines, comprehensive execution plan)
2. **Review JIRA_EPICS_AND_STORIES.md** (detailed acceptance criteria for all 43 stories)
3. **Keep QUICK_REFERENCE.md open** (during development)
4. **Start with Epic 1** (HTTP Client Infrastructure - isolated, no risk)
5. **Use feature flags** (for Epics 2 & 3 - instant rollback if needed)
6. **Test frequently** (run full suite after each epic)
7. **Go to production** (after Epic 5 - all tests passing, zero regressions)

---

## Documents You Have

```
ai_docs/specs/JIRA_EPICS_AND_STORIES.md
  └─ All 43 stories with acceptance criteria (1047 lines)

ai_docs/specs/plans/MIGRATE_TO_OPENCODE_HTTP_API.md
  └─ Technical architecture and implementation details (1460 lines)

ai_docs/specs/plans/MIGRATION_EXECUTION_GUIDE.md ⭐ READ THIS NEXT
  └─ Day-by-day execution roadmap with feature flags (523 lines)

ai_docs/specs/plans/QUICK_REFERENCE.md
  └─ Printable reference card for development (217 lines)

MIGRATION_START_HERE.md (this file)
  └─ Overview and safety explanation
```

---

## The Risk is ZERO with Feature Flags

| Scenario | Old Approach | New Approach (Feature Flags) |
|----------|--------------|------------------------------|
| OpenCode breaks | System breaks, need to revert code | Flip config, instant rollback ✅ |
| Need to rollback | Git revert (complex, time-consuming) | Change config file (30 seconds) ✅ |
| Partial migration | All-or-nothing (risky) | Each operation independent ✅ |
| Production issues | Requires code push | Change config + restart ✅ |

---

## You're Ready

✅ Complete plan with 43 stories  
✅ Feature flags for safety  
✅ Detailed execution guide  
✅ All documentation prepared  
✅ Zero-risk rollback mechanism  

**Start with MIGRATION_EXECUTION_GUIDE.md (523 lines). Everything else flows from there.**

---

**Status**: Ready for Development ✅  
**Created**: January 7, 2026  
**Version**: 1.0
