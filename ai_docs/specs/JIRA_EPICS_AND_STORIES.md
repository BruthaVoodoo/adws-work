# ADWS OpenCode HTTP API Migration - Jira Epics & Stories

**Created:** January 7, 2026  
**For:** Project Key: DAI  
**Status:** Ready for manual import or API creation

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

## Overview

This document contains all Epics and Stories for the complete migration of ADWS to OpenCode HTTP API as the unified LLM backend. The migration is organized into **5 Epics** with **43 detailed User Stories**.

**Total Scope:** 40-50 hours of work  
**Critical Path:** Epic 1 → Epic 2 & 3 (parallel) → Epic 4 → Epic 5  
**Architecture:** Direct HTTP integration to OpenCode server with intelligent model routing (Claude Haiku 4.5 for lightweight tasks, Claude Sonnet 4 for code execution via GitHub Copilot subscription)

---

## EPICS SUMMARY

### Epic 1: OpenCode HTTP Client Infrastructure Foundation
- **Summary:** Build HTTP client infrastructure and model routing for OpenCode API integration
- **Story Count:** 10 stories
- **Estimated Duration:** 6-8 hours
- **Status:** Critical Path (required before all other epics)

### Epic 2: Planning & Classification Operations Migration  
- **Summary:** Migrate all AI planning and classification tasks to OpenCode HTTP API with Claude Haiku 4.5 (via GitHub Copilot)
- **Story Count:** 9 stories
- **Estimated Duration:** 6-8 hours
- **Status:** Can overlap with Epic 3
- **Dependencies:** Epic 1

### Epic 3: Code Execution Operations Migration
- **Summary:** Migrate code implementation, testing, and review operations to OpenCode HTTP API with Claude Sonnet 4 (via GitHub Copilot)
- **Story Count:** 8 stories
- **Estimated Duration:** 8-10 hours
- **Status:** Can overlap with Epic 2
- **Dependencies:** Epic 1

### Epic 4: Cleanup & Deprecated Code Removal
- **Summary:** Remove deprecated AWS code, environment variables, and update system checks to OpenCode
- **Story Count:** 5 stories
- **Estimated Duration:** 2-3 hours
- **Status:** Sequential (after Epic 2 & 3)
- **Dependencies:** Epic 2, Epic 3

### Epic 5: Comprehensive Testing, Validation & Documentation
- **Summary:** Test all 9 LLM operations, validate end-to-end workflows, and document the migration
- **Story Count:** 11 stories
- **Estimated Duration:** 10-12 hours
- **Status:** Final (must complete last)
- **Dependencies:** Epic 1, 2, 3, 4

---

## EPIC 1: OpenCode HTTP Client Infrastructure Foundation

### Details
- **Type:** Epic
- **Project:** DAI
- **Summary:** OpenCode HTTP Client Infrastructure Foundation
- **Description:** Create the foundational HTTP client layer for communicating with OpenCode HTTP server. This epic establishes the core infrastructure for all subsequent migrations, including connection management, session handling, response parsing, and intelligent model routing based on task type. This is the critical path item that enables all other work.

### Acceptance Criteria
- [ ] HTTP client successfully connects to OpenCode server and manages sessions
- [ ] All Part types (text, tool_use, tool_result, code_block) correctly parsed from responses
- [ ] Model routing selects correct model for each task type (heavy vs lightweight)
- [ ] Configuration loaded from .adw.yaml with sensible defaults
- [ ] Connection health checks pass at startup
- [ ] Comprehensive unit test coverage (50+ tests)

### Stories
1. Create OpenCodeHTTPClient class with session management (4 hours)
2. Implement OpenCode HTTP API communication layer (4 hours)
3. Create OpenCode data types (OpenCodeResponse, OpenCodePart, etc.) (2 hours)
4. Build model routing logic with task-aware selection (2 hours)
5. Develop output parser for structured Part extraction (3 hours)
6. Add response logging and error handling (2 hours)
7. Implement connection retry logic with exponential backoff (2 hours)
8. Write comprehensive unit tests for HTTP client (3 hours)
9. Write comprehensive unit tests for output parser (2 hours)
10. Add OpenCode configuration to .adw.yaml (1 hour)

---

## EPIC 2: Planning & Classification Operations Migration

### Details
- **Type:** Epic
- **Project:** DAI
- **Summary:** Planning & Classification Operations Migration
- **Description:** Refactor all lightweight planning and classification operations to use OpenCode HTTP API with intelligent model selection. These 6 operations currently use custom implementations and will transition to Claude Haiku 4.5 via OpenCode, resulting in better reliability and more maintainable code.

### Acceptance Criteria
- [ ] All 6 planning/classification functions execute via OpenCode HTTP API
- [ ] Correct lightweight model (Claude Haiku 4.5) selected for all tasks
- [ ] No functional regressions in classification/planning output
- [ ] Proper error handling with helpful messages
- [ ] Response logging enabled for all operations
- [ ] Integration tests pass for all 6 operations

### Stories
1. Refactor agent.py execute_template() for OpenCode HTTP (3 hours)
2. Migrate extract_adw_info() to OpenCode lightweight model (2 hours)
3. Migrate classify_issue() to OpenCode lightweight model (2 hours)
4. Migrate build_plan() to OpenCode lightweight model (2 hours)
5. Migrate generate_branch_name() to OpenCode lightweight model (2 hours)
6. Migrate create_commit() to OpenCode lightweight model (2 hours)
7. Migrate create_pull_request() to OpenCode lightweight model (2 hours)
8. Update error handling for planning operations (1 hour)
9. Write integration tests for planning operations (2 hours)

---

## EPIC 3: Code Execution Operations Migration

### Details
- **Type:** Epic
- **Project:** DAI
- **Summary:** Code Execution Operations Migration
- **Description:** Replace Copilot CLI with OpenCode HTTP API for all heavy code lifting operations. These 3 critical operations (implement plan, resolve test failures, code review) will transition to Claude Sonnet 4 via OpenCode, enabling structured response parsing and better error handling.

### Acceptance Criteria
- [ ] All 3 code execution functions use OpenCode HTTP API with Claude Sonnet 4 (GitHub Copilot)
- [ ] Structured Part parsing replaces Copilot text parsing
- [ ] Git fallback validation still works
- [ ] Error messages are helpful and actionable
- [ ] Response logging enabled for all operations
- [ ] Integration tests pass with real code execution scenarios

### Stories
1. Refactor implement_plan() to use OpenCode HTTP API (4 hours)
2. Refactor resolve_failed_tests() to use OpenCode HTTP API (3 hours)
3. Refactor execute_single_e2e_test() to use OpenCode HTTP API (2 hours)
4. Refactor run_review() to use OpenCode HTTP API (3 hours)
5. Update error handling in adw_test.py for OpenCode (1 hour)
6. Update error handling in adw_review.py for OpenCode (1 hour)
7. Write integration tests for code execution operations (3 hours)
8. Test git fallback validation with OpenCode responses (1 hour)

---

## EPIC 4: Cleanup & Deprecated Code Removal

### Details
- **Type:** Epic
- **Project:** DAI
- **Summary:** Cleanup & Deprecated Code Removal
- **Description:** Clean up legacy code paths, remove unused AWS environment variables, and update system health checks. This epic ensures the codebase is maintainable and focused entirely on OpenCode as the LLM backend.

### Acceptance Criteria
- [ ] Deprecated files marked with clear deprecation notices
- [ ] All old environment variable checks removed
- [ ] Health checks updated to verify OpenCode server
- [ ] Copilot CLI checks replaced with OpenCode checks
- [ ] No functional changes to core logic

### Stories
1. Mark bedrock_agent.py as deprecated (30 min)
2. Mark copilot_output_parser.py as deprecated (30 min)
3. Remove AWS environment variable validation from codebase (1 hour)
4. Update health_check.py to verify OpenCode server (1 hour)
5. Remove Copilot CLI checks from adw_test.py and adw_review.py (30 min)

---

## EPIC 5: Comprehensive Testing, Validation & Documentation

### Details
- **Type:** Epic
- **Project:** DAI
- **Summary:** Comprehensive Testing, Validation & Documentation
- **Description:** Execute comprehensive testing across all migrated operations (6 planning + 3 code execution). Validate end-to-end workflows work correctly. Update all documentation including setup guides, troubleshooting, and configuration examples.

### Acceptance Criteria
- [ ] All 9 LLM operations tested and validated
- [ ] 60+ unit tests with >80% code coverage
- [ ] Integration tests pass with real OpenCode server
- [ ] No regressions in existing functionality
- [ ] Documentation complete and reviewed
- [ ] Setup instructions clear and verified
- [ ] Troubleshooting guide covers common issues

### Stories
1. Write unit tests for OpenCode HTTP client (mock server) (4 hours)
2. Write unit tests for output parser (2 hours)
3. Write integration tests for planning operations (2 hours)
4. Write integration tests for code execution operations (3 hours)
5. Write regression tests for all 9 LLM operations (2 hours)
6. Performance test comparison vs old system (2 hours)
7. Update AGENTS.md with OpenCode section (2 hours)
8. Create comprehensive MIGRATION_GUIDE.md (2 hours)
9. Update .adw.yaml with OpenCode configuration examples (1 hour)
10. Update README.md setup instructions (1 hour)
11. Write troubleshooting guide (1 hour)

---

## DETAILED STORY DEFINITIONS

### EPIC 1 STORIES

#### Story 1.1: Create OpenCodeHTTPClient class with session management
**Summary:** Create OpenCodeHTTPClient class with session management  
**Type:** Story  
**Estimation:** 4 hours  
**Dependencies:** None

**Description**
As a developer, I want an HTTP client class that manages OpenCode sessions, so that I can interact with the OpenCode HTTP server reliably.

**Acceptance Criteria**
- Given an OpenCode server is running
  When I instantiate OpenCodeHTTPClient with server URL
  Then it successfully creates a new session with a unique session ID
  
- Given an active session exists
  When I call close_session()
  Then the session is properly closed and cleaned up
  
- Given invalid credentials
  When I attempt to create a session
  Then an authentication error is raised with helpful message

---

#### Story 1.2: Implement OpenCode HTTP API communication layer
**Summary:** Implement OpenCode HTTP API communication layer  
**Type:** Story  
**Estimation:** 4 hours  
**Dependencies:** Story 1.1

**Description**
As a developer, I want to send prompts to OpenCode server and receive structured responses, so that I can execute AI operations.

**Acceptance Criteria**
- Given a valid prompt and model ID
  When I call send_prompt()
  Then a structured OpenCodeResponse is returned with Message + Parts
  
- Given network timeout occurs
  When I call send_prompt()
  Then exponential backoff retry logic activates and retries up to 3 times
  
- Given server returns HTTP error
  When I call send_prompt()
  Then error is caught, logged, and re-raised with context

---

#### Story 1.3: Create OpenCode data types (OpenCodeResponse, OpenCodePart, etc.)
**Summary:** Create OpenCode data types in data_types.py  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** None

**Description**
As a developer, I want strongly-typed data models for OpenCode responses, so that I have type safety and IDE autocomplete.

**Acceptance Criteria**
- Given an OpenCode API response
  When I parse it into OpenCodeResponse, OpenCodeMessageInfo, and OpenCodePart models
  Then all fields are correctly mapped with proper types
  
- Given a Part with type=tool_use
  When I access the tool and input fields
  Then they are correctly typed as Optional[str] and Optional[Dict[str, Any]]
  
- Given a Part with type=tool_result
  When I access the output field
  Then it contains the tool execution output

---

#### Story 1.4: Build model routing logic with task-aware selection
**Summary:** Build model routing logic for task-aware model selection  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Stories 1.1, 1.3

**Description**
As a developer, I want intelligent model routing that selects appropriate models per task type, so that lightweight tasks use cheap models and heavy tasks use powerful models.

**Acceptance Criteria**
- Given task_type = "classify"
   When I call get_model_for_task(task_type)
   Then it returns MODEL_LIGHTWEIGHT ("github-copilot/claude-haiku-4.5")
   
- Given task_type = "implement"
   When I call get_model_for_task(task_type)
   Then it returns MODEL_HEAVY_LIFTING ("github-copilot/claude-sonnet-4")
   
- Given all 9 task types
   When I validate model routing for each
   Then heavy tasks get Claude Sonnet 4 (GitHub Copilot), lightweight tasks get Claude Haiku 4.5 (GitHub Copilot)

---

#### Story 1.5: Develop output parser for structured Part extraction
**Summary:** Develop output parser for Part extraction and metric calculation  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Story 1.3

**Description**
As a developer, I want to extract data from OpenCode response Parts, so that I can process execution results and estimate metrics.

**Acceptance Criteria**
- Given an OpenCodeResponse with multiple Parts
  When I call extract_text_response(parts)
  Then all text parts are concatenated in order
  
- Given Parts with tool_use and tool_result types
  When I call extract_tool_execution_details(parts)
  Then I get a dict with tool counts and execution details
  
- Given tool_result parts with output text
  When I call estimate_metrics_from_parts(parts)
  Then I estimate files_changed, lines_added, lines_removed

---

#### Story 1.6: Add response logging and error handling
**Summary:** Add response logging and comprehensive error handling  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 1.2

**Description**
As a developer, I want detailed logging of all OpenCode interactions, so that I can debug issues and audit operations.

**Acceptance Criteria**
- Given an OpenCodeResponse
  When I call save_response_log(adw_id, agent_name, response)
  Then a JSON file is created at ai_docs/logs/{adw_id}/{agent_name}/response_*.json
  
- Given various error scenarios (timeout, 401, 500, connection error)
  When they occur in send_prompt()
  Then each is caught, logged, and re-raised with context

---

#### Story 1.7: Implement connection retry logic with exponential backoff
**Summary:** Implement connection retry logic with exponential backoff  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 1.2

**Description**
As a developer, I want automatic retry with exponential backoff, so that transient failures are gracefully handled.

**Acceptance Criteria**
- Given a transient connection error
  When send_prompt() is called
  Then it retries automatically with exponential backoff (1s, 2s, 4s)
  
- Given 3 consecutive retries fail
  When all retries are exhausted
  Then TimeoutError is raised with helpful message

---

#### Story 1.8: Write comprehensive unit tests for HTTP client
**Summary:** Write comprehensive unit tests for HTTP client  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Stories 1.1-1.7

**Description**
As a developer, I want unit tests that cover all HTTP client scenarios, so that I have confidence in the implementation.

**Acceptance Criteria**
- Given test_http_client.py file
  When I run pytest on it
  Then minimum 30 tests pass covering session management, prompt sending, timeout handling, retry logic, connection failures, and malformed responses

---

#### Story 1.9: Write comprehensive unit tests for output parser
**Summary:** Write comprehensive unit tests for output parser  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Stories 1.5, 1.6

**Description**
As a developer, I want unit tests for the output parser, so that Part extraction is reliable.

**Acceptance Criteria**
- Given test_output_parser.py file
  When I run pytest on it
  Then minimum 20 tests pass covering text extraction, tool counting, metric estimation, and edge cases

---

#### Story 1.10: Add OpenCode configuration to .adw.yaml
**Summary:** Add OpenCode configuration to .adw.yaml  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Stories 1.1-1.3

**Description**
As a developer, I want OpenCode configuration in .adw.yaml, so that users can customize server URL, models, and timeouts.

**Acceptance Criteria**
- Given .adw.yaml file
  When it's loaded
  Then opencode section is parsed with keys: server_url, models.heavy_lifting, models.lightweight, timeout, lightweight_timeout, max_retries

---

### EPIC 2 STORIES

#### Story 2.1: Refactor agent.py execute_template() for OpenCode HTTP
**Summary:** Refactor agent.py execute_template() for OpenCode HTTP  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Epic 1

**Description**
As a developer, I want execute_template() to use OpenCode HTTP client instead of custom proxy, so that all LLM calls go through unified interface.

**Acceptance Criteria**
- Given execute_template() is called with a prompt and task type
  When it executes
  Then it calls execute_opencode_prompt() with task_type parameter
  
- Given OpenCode server is running
  When execute_template() runs
  Then OpenCodeResponse is converted to AgentPromptResponse for backward compatibility

---

#### Story 2.2: Migrate extract_adw_info() to OpenCode lightweight model
**Summary:** Migrate extract_adw_info() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 2.1

**Description**
As a developer, I want extract_adw_info() to use OpenCode HTTP API, so that ADW classification is more reliable and cheaper.

**Acceptance Criteria**
- Given extract_adw_info() is called with issue text
   When it executes via OpenCode
   Then task_type="extract_adw" is used → Model: Claude Haiku 4.5 (GitHub Copilot)
   
- Given OpenCode response contains ADW slash command and ID
   When response is parsed
   Then values are correctly extracted for downstream use

---

#### Story 2.3: Migrate classify_issue() to OpenCode lightweight model
**Summary:** Migrate classify_issue() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 2.1

**Description**
As a developer, I want classify_issue() to use OpenCode HTTP API, so that issue classification is more reliable.

**Acceptance Criteria**
- Given classify_issue() is called with GitHub issue data
   When it executes via OpenCode
   Then task_type="classify" is used → Model: Claude Haiku 4.5 (GitHub Copilot)
   
- Given OpenCode response contains slash command
   When response is parsed
   Then classification is correctly extracted

---

#### Story 2.4: Migrate build_plan() to OpenCode lightweight model
**Summary:** Migrate build_plan() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 2.1

**Description**
As a developer, I want build_plan() to use OpenCode HTTP API, so that planning is more efficient and maintainable.

**Acceptance Criteria**
- Given build_plan() is called with issue context
   When it executes via OpenCode
   Then task_type="plan" is used → Model: Claude Haiku 4.5 (GitHub Copilot)
   
- Given OpenCode response contains implementation plan
   When response is parsed
   Then markdown plan structure is preserved

---

#### Story 2.5: Migrate generate_branch_name() to OpenCode lightweight model
**Summary:** Migrate generate_branch_name() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 2.1

**Description**
As a developer, I want generate_branch_name() to use OpenCode HTTP API, so that branch naming is consistent and reliable.

**Acceptance Criteria**
- Given generate_branch_name() is called with issue data
   When it executes via OpenCode
   Then task_type="branch_gen" is used → Model: Claude Haiku 4.5 (GitHub Copilot)

---

#### Story 2.6: Migrate create_commit() to OpenCode lightweight model
**Summary:** Migrate create_commit() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 2.1

**Description**
As a developer, I want create_commit() to use OpenCode HTTP API, so that commit messages are generated consistently.

**Acceptance Criteria**
- Given create_commit() is called with issue data
   When it executes via OpenCode
   Then task_type="commit_msg" is used → Model: Claude Haiku 4.5 (GitHub Copilot)

---

#### Story 2.7: Migrate create_pull_request() to OpenCode lightweight model
**Summary:** Migrate create_pull_request() to OpenCode with Claude Haiku 4.5 (GitHub Copilot)  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Story 2.1

**Description**
As a developer, I want create_pull_request() to use OpenCode HTTP API, so that PR metadata generation is reliable.

**Acceptance Criteria**
- Given create_pull_request() is called with plan and context
   When it executes via OpenCode
   Then task_type="pr_creation" is used → Model: Claude Haiku 4.5 (GitHub Copilot)

---

#### Story 2.8: Update error handling for planning operations
**Summary:** Update error handling for planning operations  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Stories 2.2-2.7

**Description**
As a developer, I want comprehensive error handling across all planning operations, so that failures are logged and reported clearly.

**Acceptance Criteria**
- Given any planning operation fails
  When error occurs
  Then it's caught, logged with context, and re-raised with helpful message

---

#### Story 2.9: Write integration tests for planning operations
**Summary:** Write integration tests for planning operations  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Stories 2.1-2.8

**Description**
As a QA engineer, I want integration tests for all planning operations, so that I can validate end-to-end workflows.

**Acceptance Criteria**
- Given integration test suite
  When I run tests
  Then all 6 planning/classification functions execute successfully via real OpenCode server

---

### EPIC 3 STORIES

#### Story 3.1: Refactor implement_plan() to use OpenCode HTTP API
**Summary:** Refactor implement_plan() to use OpenCode HTTP API  
**Type:** Story  
**Estimation:** 4 hours  
**Dependencies:** Epic 1

**Description**
As a developer, I want implement_plan() to use OpenCode HTTP API with Claude Sonnet 4, so that code implementation is more reliable and maintainable.

**Acceptance Criteria**
- Given implement_plan() is called with plan file
   When it executes via OpenCode
   Then task_type="implement" is used → Model: Claude Sonnet 4 (GitHub Copilot)
  
- Given OpenCode response contains implementation
  When Parts are parsed
  Then file changes are extracted from tool_use and tool_result parts

---

#### Story 3.2: Refactor resolve_failed_tests() to use OpenCode HTTP API
**Summary:** Refactor resolve_failed_tests() to use OpenCode HTTP API  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Epic 1

**Description**
As a developer, I want resolve_failed_tests() to use OpenCode HTTP API, so that test failures are fixed more reliably.

**Acceptance Criteria**
- Given resolve_failed_tests() is called with test failures
   When it executes via OpenCode
   Then task_type="test_fix" is used → Model: Claude Sonnet 4 (GitHub Copilot)
  
- Given OpenCode response contains fixes
  When Parts are parsed
  Then error details and fixes are extracted

---

#### Story 3.3: Refactor execute_single_e2e_test() to use OpenCode HTTP API
**Summary:** Refactor execute_single_e2e_test() to use OpenCode HTTP API  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 1

**Description**
As a developer, I want execute_single_e2e_test() to use OpenCode HTTP API, so that E2E test execution is structured and parseable.

**Acceptance Criteria**
- Given execute_single_e2e_test() is called with test name
   When it executes via OpenCode
   Then task_type="test_fix" is used → Model: Claude Sonnet 4 (GitHub Copilot)

---

#### Story 3.4: Refactor run_review() to use OpenCode HTTP API
**Summary:** Refactor run_review() to use OpenCode HTTP API  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Epic 1

**Description**
As a developer, I want run_review() to use OpenCode HTTP API, so that code reviews are more reliable and structured.

**Acceptance Criteria**
- Given run_review() is called with changed files and diff
   When it executes via OpenCode
   Then task_type="review" is used → Model: Claude Sonnet 4 (GitHub Copilot)

---

#### Story 3.5: Update error handling in adw_test.py for OpenCode
**Summary:** Update error handling in adw_test.py for OpenCode  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Stories 3.2, 3.3

**Description**
As a developer, I want adw_test.py to check for OpenCode server instead of Copilot CLI, so that error messages are helpful.

**Acceptance Criteria**
- Given adw_test.py startup
  When it initializes
  Then it calls check_opencode_server_available() instead of shutil.which("copilot")

---

#### Story 3.6: Update error handling in adw_review.py for OpenCode
**Summary:** Update error handling in adw_review.py for OpenCode  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Story 3.4

**Description**
As a developer, I want adw_review.py to check for OpenCode server instead of Copilot CLI, so that error messages are helpful.

**Acceptance Criteria**
- Given adw_review.py startup
  When it initializes
  Then it calls check_opencode_server_available() instead of shutil.which("copilot")

---

#### Story 3.7: Write integration tests for code execution operations
**Summary:** Write integration tests for code execution operations  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Stories 3.1-3.6

**Description**
As a QA engineer, I want integration tests for code execution operations, so that I can validate implementation and review workflows.

**Acceptance Criteria**
- Given integration test suite
  When I run tests with real OpenCode server
  Then all 3 code execution functions execute successfully

---

#### Story 3.8: Test git fallback validation with OpenCode responses
**Summary:** Test git fallback validation with OpenCode responses  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Story 3.1

**Description**
As a developer, I want to verify git fallback validation works correctly with OpenCode responses, so that we have reliable change validation.

**Acceptance Criteria**
- Given implement_plan() generates changes via OpenCode
  When git fallback validation runs
  Then file changes are validated against git log

---

### EPIC 4 STORIES

#### Story 4.1: Mark bedrock_agent.py as deprecated
**Summary:** Mark bedrock_agent.py as deprecated  
**Type:** Story  
**Estimation:** 30 min  
**Dependencies:** Epic 3

**Description**
As a maintainer, I want bedrock_agent.py marked as deprecated, so that developers know it's no longer maintained.

**Acceptance Criteria**
- Given bedrock_agent.py file
  When it's opened
  Then clear deprecation notice is at the top

---

#### Story 4.2: Mark copilot_output_parser.py as deprecated
**Summary:** Mark copilot_output_parser.py as deprecated  
**Type:** Story  
**Estimation:** 30 min  
**Dependencies:** Epic 3

**Description**
As a maintainer, I want copilot_output_parser.py marked as deprecated, so that developers know it's no longer maintained.

**Acceptance Criteria**
- Given copilot_output_parser.py file
  When it's opened
  Then clear deprecation notice is at the top

---

#### Story 4.3: Remove AWS environment variable validation from codebase
**Summary:** Remove AWS environment variable validation  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Epic 3

**Description**
As a developer, I want AWS environment variable checks removed from codebase, so that old config references don't confuse new developers.

**Acceptance Criteria**
- Given AWS_ENDPOINT_URL, AWS_MODEL_KEY, AWS_MODEL usage in codebase
  When I search for them
  Then all occurrences are removed

---

#### Story 4.4: Update health_check.py to verify OpenCode server
**Summary:** Update health_check.py to verify OpenCode server  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Epic 1, Epic 3

**Description**
As a developer, I want health_check.py to verify OpenCode server instead of custom proxy, so that startup verification is correct.

**Acceptance Criteria**
- Given health_check.py runs at startup
  When it executes
  Then it calls check_opencode_server_available()

---

#### Story 4.5: Remove Copilot CLI checks from adw_test.py and adw_review.py
**Summary:** Remove Copilot CLI checks from adw_test.py and adw_review.py  
**Type:** Story  
**Estimation:** 30 min  
**Dependencies:** Epic 3 Stories 5-6

**Description**
As a developer, I want Copilot CLI checks removed from startup code, so that OpenCode is the only LLM backend checked.

**Acceptance Criteria**
- Given adw_test.py and adw_review.py startup code
  When they initialize
  Then references to shutil.which("copilot") are removed

---

### EPIC 5 STORIES

#### Story 5.1: Write unit tests for OpenCode HTTP client
**Summary:** Write comprehensive unit tests for HTTP client  
**Type:** Story  
**Estimation:** 4 hours  
**Dependencies:** Epic 1

**Description**
As a QA engineer, I want unit tests for OpenCode HTTP client, so that connection logic is reliable.

**Acceptance Criteria**
- Given test_http_client.py file with mock HTTP responses
  When pytest runs
  Then minimum 30 tests pass covering connection checks, session management, prompt sending, timeout handling, and error cases

---

#### Story 5.2: Write unit tests for output parser
**Summary:** Write unit tests for output parser  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 1

**Description**
As a QA engineer, I want unit tests for output parser, so that Part extraction is reliable.

**Acceptance Criteria**
- Given test_output_parser.py file
  When pytest runs
  Then minimum 20 tests pass covering text extraction, tool counting, metric estimation, and edge cases

---

#### Story 5.3: Write integration tests for planning operations
**Summary:** Write integration tests for planning operations  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 2

**Description**
As a QA engineer, I want integration tests for all planning operations, so that workflows are validated end-to-end.

**Acceptance Criteria**
- Given integration test suite
  When it runs with real OpenCode server
  Then all 6 planning/classification functions execute successfully

---

#### Story 5.4: Write integration tests for code execution operations
**Summary:** Write integration tests for code execution operations  
**Type:** Story  
**Estimation:** 3 hours  
**Dependencies:** Epic 3

**Description**
As a QA engineer, I want integration tests for code execution operations, so that implementation and review workflows are validated.

**Acceptance Criteria**
- Given integration test suite
  When it runs with real OpenCode server
  Then all 3 code execution functions execute successfully

---

#### Story 5.5: Write regression tests for all 9 LLM operations
**Summary:** Write regression tests for all 9 LLM operations  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 1, 2, 3, 4

**Description**
As a QA engineer, I want regression tests to ensure no functionality is broken, so that migrations don't introduce bugs.

**Acceptance Criteria**
- Given existing test suite
  When new code runs
  Then all existing tests still pass
  
- Given all 9 LLM operations
  When they execute with sample data
  Then output format matches expectations from old system

---

#### Story 5.6: Performance test comparison vs old system
**Summary:** Performance test comparison vs old system  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 1, 2, 3

**Description**
As a developer, I want to compare performance of new system vs old system, so that we understand tradeoffs.

**Acceptance Criteria**
- Given baseline measurements from old system
  When new system runs same operations
  Then execution times are recorded
  
- Given comparison results
  When analyzed
  Then performance is comparable or better (±10%)

---

#### Story 5.7: Update AGENTS.md with OpenCode section
**Summary:** Update AGENTS.md with OpenCode HTTP server section  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 1, 2, 3, 4

**Description**
As a technical writer, I want AGENTS.md updated with OpenCode setup section, so that developers know how to configure the system.

**Acceptance Criteria**
- Given AGENTS.md file
  When it's reviewed
  Then new section "OpenCode HTTP Server Setup" exists with installation, startup, authentication, configuration, verification, and troubleshooting

---

#### Story 5.8: Create comprehensive MIGRATION_GUIDE.md
**Summary:** Create comprehensive MIGRATION_GUIDE.md  
**Type:** Story  
**Estimation:** 2 hours  
**Dependencies:** Epic 1, 2, 3, 4

**Description**
As a technical writer, I want a migration guide for users, so that they understand the transition from old to new system.

**Acceptance Criteria**
- Given new MIGRATION_GUIDE.md file
  When it's reviewed
  Then it contains overview, step-by-step instructions, setup, configuration, response structure, common issues, cost comparison, and FAQ

---

#### Story 5.9: Update .adw.yaml with OpenCode configuration examples
**Summary:** Update .adw.yaml with OpenCode configuration examples  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Epic 1, 2, 3, 4

**Description**
As a technical writer, I want .adw.yaml updated with OpenCode examples, so that users can see all available options.

**Acceptance Criteria**
- Given .adw.yaml file
  When it's reviewed
  Then opencode section contains detailed comments explaining each option with examples

---

#### Story 5.10: Update README.md setup instructions
**Summary:** Update README.md with OpenCode setup instructions  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Epic 1, 2, 3, 4

**Description**
As a technical writer, I want README.md updated with OpenCode setup, so that new users know how to get started.

**Acceptance Criteria**
- Given README.md file
  When it's reviewed
  Then setup section includes OpenCode installation, server startup, configuration, and verification steps

---

#### Story 5.11: Write troubleshooting guide
**Summary:** Write troubleshooting guide for common issues  
**Type:** Story  
**Estimation:** 1 hour  
**Dependencies:** Epic 1, 2, 3, 4

**Description**
As a technical writer, I want a troubleshooting guide, so that users can self-serve common issues.

**Acceptance Criteria**
- Given troubleshooting guide
  When it's reviewed
  Then it covers connection errors, auth failures, model not found, timeouts, stuck requests, and performance issues

---

## IMPORT INSTRUCTIONS

### Option 1: Manual Creation in Jira

1. Create 5 Epics with the Epic details above
2. For each Epic, create the corresponding Stories
3. Link stories to their parent epics
4. Set dependencies between epics

### Option 2: Using Jira API

Use the Python script or REST API to import all issues at once:

```bash
# Example curl command for creating an epic
curl -X POST \
  -H "Content-Type: application/json" \
  -u $JIRA_USERNAME:$JIRA_API_TOKEN \
  -d '{
    "fields": {
      "project": {"key": "DAI"},
      "summary": "OpenCode HTTP Client Infrastructure Foundation",
      "description": "Create the foundational HTTP client layer...",
      "issuetype": {"name": "Epic"}
    }
  }' \
  $JIRA_SERVER/rest/api/3/issues
```

### Option 3: Jira Import via CSV

Export the data to CSV and use Jira's import tool.

---

## CRITICAL PATH ANALYSIS

**Phase 1 (Epic 1):** 6-8 hours
- **Must Complete First:** Establishes all infrastructure

**Phase 2 & 3 (Epics 2 & 3):** 14-18 hours (can overlap)
- Parallel Development: 6-8 hours saved by running in parallel

**Phase 4 (Epic 4):** 2-3 hours
- **Depends on:** Epics 2 & 3

**Phase 5 (Epic 5):** 10-12 hours
- **Depends on:** All previous epics

**Total Sequential:** 40-50 hours  
**Total with Parallelization:** 28-32 hours

---

## SUCCESS METRICS

- [ ] All 5 epics created in Jira
- [ ] All 43 stories created and linked to epics
- [ ] Stories have clear, testable acceptance criteria
- [ ] Dependencies between stories documented
- [ ] Time estimates provided for each story
- [ ] Team knows what to work on next

---

**Document Version:** 2.0  
**Last Updated:** January 9, 2026  
**Status:** Phase 0 Complete - Overview and Epic Summaries Updated
