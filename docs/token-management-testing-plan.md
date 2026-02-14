# Token Management System - Quality Testing Plan

## Executive Summary

This document outlines a comprehensive, quality-focused testing strategy for the ADWS Token Management System implemented to solve the 184K→128K token overflow problem. The system includes 10 interconnected features that must work together seamlessly to compress test output while preserving critical failure information.

**Testing Philosophy:** Hybrid approach combining automated regression testing (70% coverage) with manual quality validation (30% coverage) to ensure the system not only works correctly but produces high-quality, useful output for LLM-based test fixing.

---

## System Components to Test

### Core Features Implemented
1. **Token Counting Utility** (`token_utils.py`) - tiktoken integration with 95% safety margin
2. **Model Limits Registry** (`model_limits.py`) - Token limits for Claude models
3. **Jest JSON Parser** - Structured test output parsing
4. **Generic JSON Parser** - Fallback for unknown test frameworks
5. **Console Output Parser** - Intelligent truncation with deduplication and compression
6. **Pre-flight Token Validation** - Checks before LLM API calls
7. **User Notification System** - Clear error messages and recovery options
8. **Config-Driven Test Execution** - Routes to appropriate parser based on config
9. **Test Reconfiguration Command** - `adw config test` for setup changes
10. **Documentation** - User guides and troubleshooting

### Test Environment
- **Test Application:** `test-app/` - Node.js monorepo (Express backend + React frontend)
- **Test Framework:** Jest (backend tests)
- **Test Files:** 3 files in `backend/tests/` (~15 tests total)
- **ADWS Config:** Already configured at `test-app/ADWS/config.yaml`

---

## Testing Strategy: Hybrid Approach

### Phase 1: Automated Foundation Tests
**Purpose:** Fast feedback on logic correctness and regression prevention  
**Coverage:** ~70% of functionality  
**Execution Time:** Minutes  
**Frequency:** Every commit / CI/CD

#### Components:
- Unit tests for utilities (token counting, model limits)
- Parser tests with fixtures (known inputs/outputs)
- Integration tests (config loading, command execution)
- Smoke tests (end-to-end workflow completion)

### Phase 2: Quality Validation Protocol
**Purpose:** Verify output quality, information preservation, and LLM effectiveness  
**Coverage:** ~30% of quality attributes that require human judgment  
**Execution Time:** 2-3 hours  
**Frequency:** Weekly or before releases

#### Components:
- Information preservation quality checks
- Compression quality spectrum testing
- Edge case handling validation
- User experience flow testing
- Real-world integration testing

### Phase 3: Quality Feedback Loop
**Purpose:** Continuous improvement based on findings  
**Execution:** Ongoing

#### Components:
- Document quality findings
- Create regression fixtures from manual testing
- Tune compression thresholds
- Update automated tests with new scenarios

---

## Detailed Testing Breakdown

### 1. Automated Test Suite

#### 1.1 Token Management Tests
**Location:** `scripts/tests/test_token_management/`

**Test Files:**
- `test_token_utils.py` - Token counting accuracy
- `test_model_limits.py` - Model limit registry
- `test_preflight_validation.py` - Pre-flight checks

**Test Cases:**
- Token counting accuracy for various input types
- Empty string, simple text, unicode, large strings, code, JSON
- Safety margin calculation (95% of limit)
- Model limit lookups (Sonnet 4: 128K, Haiku 4.5: 128K, Opus 4: 200K)
- Unknown model handling
- Pre-flight validation triggers when over limit
- TokenLimitExceeded exception contains correct details
- Prompt logging to file

**Success Criteria:**
- All token counts match tiktoken directly (±1 token tolerance)
- Model limits accurate to documentation
- Pre-flight catches 100% of overflow scenarios

---

#### 1.2 Parser Tests
**Location:** `scripts/tests/test_parsers/`

**Test Files:**
- `test_jest_parser.py` - Jest JSON output parsing
- `test_generic_json_parser.py` - Generic JSON fallback
- `test_console_parser.py` - Console output compression

**Fixtures Location:** `scripts/tests/test_parsers/fixtures/`
- `jest_outputs/` - Sample Jest outputs (passing, failing, mixed)
- `edge_cases/` - Special cases (unicode, ANSI codes, massive output)
- `expected_results/` - Known-good parsed outputs

**Test Cases - Jest Parser:**
- All tests passing → 0 failures extracted
- Single test failing → failure details captured
- Multiple failures → all extracted correctly
- Nested describe blocks → context preserved
- Timeout errors → captured with context
- Assertion failures → message + stack trace
- Hook failures (beforeEach, afterEach) → captured

**Test Cases - Generic JSON Parser:**
- Non-Jest JSON formats → best-effort extraction
- Malformed JSON → graceful degradation
- Missing required fields → no crash
- Deeply nested structures → flattens correctly

**Test Cases - Console Parser:**
- ANSI code removal → clean output
- Repeated log deduplication → "(repeated Nx)" format
- Stack trace compression → preserves error location
- Test name extraction via regex → accurate
- Jest boilerplate filtering → removed
- Token reduction → 80-90% reduction achieved
- Information preservation → critical errors remain

**Success Criteria:**
- 100% of test failures captured
- Token reduction meets 80%+ target
- No crashes on malformed input
- Test names and error context preserved

---

#### 1.3 Integration Tests
**Location:** `scripts/tests/test_integration/`

**Test Files:**
- `test_config_driven_execution.py` - Config loading and routing
- `test_error_handling.py` - User notification flow
- `test_end_to_end_smoke.py` - Full workflow

**Test Cases:**
- Config.yaml loading and validation
- test_command execution from config
- Parser routing (JSON vs console based on output_format)
- Missing config → graceful fallback
- Invalid config → clear error message
- Token overflow → user notified with options
- User choice capture (aggressive truncation vs abort)
- Retry after truncation succeeds
- Files written to correct locations
- Logs generated appropriately

**Success Criteria:**
- Config-driven execution works 100%
- All error paths handled gracefully
- User sees clear messages and options
- Recovery workflows complete successfully

---

### 2. Quality Validation Protocol

#### 2.1 Information Preservation Quality
**Location:** Manual testing in `test-app/`

**Procedure:**
1. Create 3 intentional failures in `test-app/backend/tests/`:
   - Assertion failure (expected vs actual)
   - Timeout error
   - Unhandled exception with stack trace

2. Capture raw output:
   ```bash
   cd test-app
   npm test --workspace=backend > raw_output.txt
   ```

3. Run through ADWS parsers:
   - Execute with JSON parser
   - Execute with console parser
   - Compare compressed outputs

4. Human quality assessment:
   - Can you understand what failed?
   - Is error message clear?
   - Is enough stack trace preserved?
   - Are test names/paths clear?
   - Would this help you fix the bug?

5. LLM effectiveness test:
   - Feed compressed output to Claude
   - Ask: "What's wrong and how to fix?"
   - Evaluate if fixes are relevant and useful

**Success Criteria:**
- ✓ 100% of failures identified
- ✓ Error context sufficient to understand issue
- ✓ LLM can suggest relevant fixes
- ✓ Token reduction 80-90%

**Deliverable:** Quality assessment report documenting findings

---

#### 2.2 Compression Quality Spectrum
**Location:** Manual testing in `test-app/`

**Procedure:**
Create graduated test scenarios:

**Level 1: Simple (1 test, 1 failure)**
- Should be nearly lossless
- Verify 100% context preserved

**Level 2: Moderate (5 tests, mixed failures)**
- Should preserve all critical info
- Verify each failure has sufficient context

**Level 3: Complex (15 tests, nested describes, hooks)**
- Test context preservation
- Verify nesting/hierarchy clear

**Level 4: Extreme (50+ tests, massive stack traces)**
- Where aggressive compression kicks in
- Verify most critical info preserved
- Document what gets lost

**For Each Level:**
- Run through parser
- Human review compressed output
- Rate information quality (1-10 scale)
- Identify what was lost (if anything)
- Document threshold where quality degrades

**Success Criteria:**
- Levels 1-3: 9-10/10 quality rating
- Level 4: 7-8/10 quality rating (acceptable trade-off)
- Clear documentation of compression boundaries

**Deliverable:** Compression quality matrix with ratings and findings

---

#### 2.3 Edge Case Quality
**Location:** Manual testing with crafted scenarios

**Test Scenarios:**

**Edge Case 1: Repeated Identical Failures**
- 10 tests fail with same error
- Verify deduplication works correctly
- Check context still clear

**Edge Case 2: Multi-line Error Messages**
- Error spans 20+ lines
- Verify compression preserves key parts
- Check readability maintained

**Edge Case 3: Special Characters / Unicode**
- Error contains emoji, special chars, ANSI codes
- Verify clean removal
- Check no corruption

**Edge Case 4: Timeout with No Stack**
- Test times out with minimal info
- Verify parser handles gracefully
- Check what context is provided

**Edge Case 5: Interleaved Output**
- Test output mixed with logs
- Verify test extraction works
- Check noise filtered correctly

**For Each Edge Case:**
- Create scenario in test-app
- Run through parser
- Assess: Does parser handle gracefully?
- Assess: Is output still useful?
- Document any critical failures

**Success Criteria:**
- All edge cases handled without crashes
- Output remains useful in all scenarios
- Documented workarounds for known limitations

**Deliverable:** Edge case handling report

---

#### 2.4 User Experience Quality
**Location:** Manual testing of interactive flows

**Scenario A: Token Overflow Handling**
1. Trigger token overflow deliberately (create massive test output)
2. Observe error message displayed
3. Evaluate: Is it clear what happened?
4. Evaluate: Are options obvious?
5. Test: Choose aggressive truncation
6. Evaluate: Does recovery feel smooth?
7. Test: Choose abort
8. Evaluate: Clean exit?

**Scenario B: Test Configuration Flow**
1. Run: `adw config test`
2. Evaluate: Is current config clear?
3. Test each menu option
4. Evaluate: Do changes persist correctly?
5. Evaluate: Is validation helpful?

**Scenario C: Error Recovery**
1. Break config.yaml (invalid syntax)
2. Evaluate: Error message helpful?
3. Fix config
4. Evaluate: Can user recover easily?

**UX Quality Checklist:**
- [ ] Error messages in plain English
- [ ] User knows what to do next
- [ ] No confusing technical jargon
- [ ] Recovery paths clear
- [ ] Feedback confirms actions

**Success Criteria:**
- All UX flows intuitive
- Error messages actionable
- Recovery paths clear and functional

**Deliverable:** UX evaluation report with recommendations

---

#### 2.5 Real-World Integration Quality
**Location:** Full ADWS workflow in `test-app/`

**Procedure:**

**Setup:** test-app with 3-5 real failing tests

**Step 1: Run Full ADWS Test Cycle**
```bash
cd test-app
adw test
```
- Let it run complete workflow
- Observe token handling
- Check if overflows occur

**Step 2: Evaluate LLM Fix Quality**
- Did LLM receive good context?
- Are fixes relevant?
- Can fixes actually resolve failures?
- Compare: Would full output help more?

**Step 3: Success Rate Measurement**
- Track: How many tests fixed automatically?
- Track: How many needed human intervention?
- Track: Were any failures missed?

**Step 4: Performance Validation**
- Check: Token usage per test
- Check: Is it consistently under limits?
- Check: Response times acceptable?

**Quality Metrics:**
- ✓ 80%+ of failures auto-fixed or given good guidance
- ✓ 0 failures missed/ignored
- ✓ Token usage stays under limit consistently
- ✓ LLM produces relevant fixes

**Success Criteria:**
- System handles real-world scenarios effectively
- Token management works in practice
- LLM receives useful information
- Overall workflow smooth and functional

**Deliverable:** Integration testing report with metrics

---

### 3. Quality Feedback Loop

#### After Manual Testing
1. **Document Quality Findings**
   - What worked well?
   - What information was lost?
   - Where did compression hurt quality?
   - Were any edge cases problematic?

2. **Create Regression Fixtures**
   - Convert failing cases to automated tests
   - Build library of real-world scenarios
   - Add to fixtures directory

3. **Tune Compression Thresholds**
   - If too aggressive → increase preserved info
   - If still overflowing → increase compression
   - Find optimal balance

4. **Update Automated Tests**
   - Add new fixtures from manual testing
   - Codify quality thresholds discovered
   - Prevent regression of fixes

5. **Iterate**
   - Run automated suite (fast)
   - Spot check manual protocol (weekly)
   - Maintain quality over time

---

## Deliverables

### 1. Automated Test Suite
```
scripts/tests/
├── test_token_management/
│   ├── test_token_utils.py
│   ├── test_model_limits.py
│   └── test_preflight_validation.py
├── test_parsers/
│   ├── test_jest_parser.py
│   ├── test_generic_json_parser.py
│   ├── test_console_parser.py
│   └── fixtures/
│       ├── jest_outputs/
│       ├── pytest_outputs/
│       └── edge_cases/
├── test_integration/
│   ├── test_config_driven_execution.py
│   ├── test_error_handling.py
│   └── test_end_to_end_smoke.py
├── run_tests.py
└── README.md
```

### 2. Quality Validation Protocol
```
test-app/ADWS/testing/
├── QUALITY_PROTOCOL.md
├── quality_checklist.md
├── test_scenarios/
│   ├── failing_tests/
│   ├── edge_cases/
│   └── real_world_scenarios/
└── reports/
    ├── quality_report_template.md
    └── [date]_quality_assessment.md
```

### 3. Documentation
- Test suite README with usage instructions
- Quality protocol step-by-step guide
- Report templates for documenting findings
- Integration guide for CI/CD

---

## Implementation Timeline

### Phase 1: Automated Suite (Days 1-2)
- Day 1 Morning: Token management tests
- Day 1 Afternoon: Parser unit tests
- Day 2 Morning: Integration tests
- Day 2 Afternoon: Test runner and documentation

### Phase 2: Quality Protocol (Day 3)
- Morning: Create manual testing procedures
- Afternoon: Set up test scenarios in test-app
- Evening: Create checklists and templates

### Phase 3: Execute Quality Validation (Day 4)
- Morning: Run manual protocol (2.1, 2.2)
- Afternoon: Run manual protocol (2.3, 2.4, 2.5)
- Evening: Document findings

### Phase 4: Refinement (Day 5)
- Morning: Address quality issues found
- Afternoon: Add regression tests from findings
- Evening: Final validation and documentation

**Total Effort:** 5 days (can be compressed to 3 days intensive work)

---

## Success Metrics

### Automated Tests
- [ ] 100% of core logic tests passing
- [ ] 95%+ parser accuracy on fixtures
- [ ] 80%+ token reduction achieved
- [ ] 0 crashes on malformed input
- [ ] All integration tests green

### Quality Validation
- [ ] Information preservation rated 8+/10
- [ ] LLM can fix 80%+ of failures from compressed output
- [ ] All edge cases handled gracefully
- [ ] UX flows intuitive and clear
- [ ] Real-world integration successful

### Overall System
- [ ] Token usage consistently under model limits
- [ ] No critical information lost in compression
- [ ] Error handling robust and user-friendly
- [ ] Documentation complete and accurate
- [ ] Feedback loop established for continuous improvement

---

## Next Steps

1. **Create Archon Project** - "Token Management Testing Implementation"
2. **Create Archon Tasks** - Break down each deliverable into tasks
3. **Execute Phase 1** - Build automated test suite
4. **Execute Phase 2** - Create quality protocol
5. **Execute Phase 3** - Run quality validation
6. **Execute Phase 4** - Iterate based on findings

---

## Notes for Archon Task Creation

### Task Granularity
Each task should represent 2-4 hours of work and produce a specific deliverable.

### Task Dependencies
- Phase 1 tasks can largely run in parallel
- Phase 2 depends on Phase 1 completion (need working system to validate)
- Phase 3 depends on Phase 2 (need protocol to execute)
- Phase 4 depends on Phase 3 (need findings to address)

### Assignee Recommendations
- Automated testing tasks → Developer with Python/pytest experience
- Quality validation → QA or developer familiar with ADWS workflow
- Documentation → Technical writer or developer
- Integration → DevOps for CI/CD setup

### Priority Levels
- **High:** Core automated tests (1.1, 1.2, 1.3)
- **High:** Information preservation quality (2.1)
- **Medium:** Edge cases and UX testing (2.3, 2.4)
- **Medium:** Real-world integration (2.5)
- **Low:** Documentation and polish

---

## Appendix: Test Fixture Examples

### Example Jest Output (Passing)
```json
{
  "numFailedTests": 0,
  "numPassedTests": 3,
  "testResults": [
    {
      "name": "api.test.js",
      "status": "passed"
    }
  ]
}
```

### Example Jest Output (Failing)
```json
{
  "numFailedTests": 1,
  "numPassedTests": 2,
  "testResults": [
    {
      "name": "api.test.js",
      "assertionResults": [
        {
          "status": "failed",
          "title": "should return 200",
          "failureMessages": ["Expected 200 but got 404"]
        }
      ]
    }
  ]
}
```

### Example Console Output
```
FAIL backend/tests/api.test.js
  ● API Tests › GET /users › should return 200

    expect(received).toBe(expected)

    Expected: 200
    Received: 404

      12 |   it('should return 200', async () => {
      13 |     const response = await request(app).get('/users');
    > 14 |     expect(response.status).toBe(200);
         |                              ^
      15 |   });
```
