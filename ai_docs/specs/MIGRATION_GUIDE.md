# ADWS OpenCode Migration Guide

Created: January 9, 2026
Last updated: January 14, 2026

This migration guide explains how to move ADWS from the old Copilot/AWS hybrid approach to the unified OpenCode HTTP API path. It is written for engineers and maintainers responsible for installing, configuring, testing, and validating the migration.

Goals
- Describe the end-to-end migration steps and verification checkpoints.
- Provide clear setup and configuration examples for OpenCode HTTP server usage.
- Explain the OpenCode response structure and how ADWS consumes it.
- List common issues and troubleshooting steps.
- Provide a short cost/efficiency comparison and practical recommendations.

Who should read this
- Platform engineers performing the migration and running the OpenCode service.
- Developers who maintain ADWS scripts and need to update integrations.
- QA engineers writing/maintaining integration tests against OpenCode.

Migration checklist (high level)
1. Ensure Epic 1 (OpenCode HTTP client) is merged and available in the codebase.
2. Replace any remaining Copilot CLI or AWS-specific checks with OpenCode health checks.
3. Add or verify .adw.yaml opencode configuration (server_url, models, timeouts).
4. Install and start OpenCode HTTP server and authenticate (opencode auth login).
5. Run unit tests and integration tests; fix any regressions.
6. Update docs (README, AGENTS.md, MIGRATION_GUIDE.md).  
7. Run end-to-end verification (Plan → Build → Test → Review) against a sample Jira issue.

Step-by-step migration (detailed)

1) Prepare environment
- Update repository to the branch/commit that contains the OpenCode client (opencode_http_client.py) and agent refactor.
- Remove or archive any deprecated modules (bedrock_agent.py, copilot_output_parser.py) if not already done; leave deprecation notices for historical reasons.
- Ensure required environment variables are present in `.env` or CI secrets (Jira credentials, optional Bitbucket tokens). OpenCode itself does not require special env vars in ADWS beyond configuring server_url in `.adw.yaml`.

2) Install OpenCode HTTP server
- Recommended: install OpenCode per project documentation.
  - npm: npm install -g @github/copilot  (or use provided installer)
  - Homebrew (macOS): brew install copilot
- Start server for local development:
  - opencode serve --port 4096
- Authenticate so GitHub Copilot models are accessible:
  - opencode auth login
  - Requires a GitHub account with Copilot access (organization subscription)

3) Configure ADWS (.adw.yaml)
- Example opencode block to add to your `.adw.yaml`:
  opencode:
    server_url: "http://localhost:4096"
    models:
      heavy_lifting: "github-copilot/claude-sonnet-4"
      lightweight: "github-copilot/claude-haiku-4.5"
    timeout: 600
    lightweight_timeout: 60
    max_retries: 3
    retry_backoff: 1.5
    reuse_sessions: false
    connection_timeout: 30
    read_timeout: 600

- Validate you can read these values from the ADWConfig singleton:
  - scripts/adw_modules/config.py exposes properties like `opencode_server_url` and `opencode_model_heavy_lifting`.

4) Verify OpenCode server connectivity
- Quick health check:
  - curl http://localhost:4096/health
  - Or run: python -c "from scripts.adw_modules.opencode_http_client import check_opencode_server_available; print(check_opencode_server_available('http://localhost:4096'))"
- ADWS scripts call `check_opencode_server_available()` during startup and will exit gracefully with instructions if the server is unavailable.

5) Run tests (unit & integration)
- Install dependencies: pip install -r requirements.txt
- Unit tests (mocks): pytest -q
- Integration tests (real server): run targeted integration tests with server running. Examples:
  - uv run pytest tests/test_story_3_7_code_execution_operations_integration.py -v
  - Many integration tests will gracefully skip when the OpenCode server is unavailable; ensure server is up for end-to-end verification.

6) End-to-end verification (recommended)
- Use a local Jira mock or a real Jira issue (if configured): run the sequential workflow with a small test issue.
  - adw plan <ISSUE_KEY>  → check that ADW ID and plan are created
  - adw build <ADW_ID> <ISSUE_KEY> → verify commits/branch created and metrics logged
  - adw test <ADW_ID> <ISSUE_KEY> → run tests and verify resolve_failed_tests flow with OpenCode
  - adw review <ADW_ID> <ISSUE_KEY> → run review and verify ReviewResult parsing
- Inspect ai_docs/logs/{adw_id}/ for saved prompts, response JSON logs, and adw_state.json.

OpenCode response structure (how ADWS consumes it)
ADWS expects structured OpenCode responses made of a message with an ordered list of Parts. Common part types and how ADWS uses them:
- text
  - Purpose: free-form text output (explanations, plan text, etc.)
  - Parser: `extract_text_response(parts)` concatenates text parts in order and returns a single string.
- code_block
  - Purpose: blocks of code the model returns. Used by metric estimators and may be written to files by agent logic.
- tool_use
  - Purpose: indicates the model requested an external tool to perform an action (e.g., run a shell command). ADWS records the tool name and input.
- tool_result
  - Purpose: result output from a tool invocation. ADWS uses tool_result.output to infer file changes and other artifacts.

Key ADWS helpers:
- extract_text_response(parts) → returns concatenated text content
- extract_tool_execution_details(parts) → returns counts and executions for tools used
- estimate_metrics_from_parts(parts) → heuristic to estimate files_changed, lines_added, lines_removed
- save_response_log(adw_id, agent_name, response) → persists full OpenCode response for debugging and audit

Common migration issues & troubleshooting

1) "Cannot connect to OpenCode server"
- Symptoms: requests.exceptions.ConnectionError or health check failing
- Quick fixes:
  - Ensure `opencode serve` is running on the expected port
  - Check `opencode_server_url` in `.adw.yaml` matches the server (include http://)
  - Firewall or port conflicts: ensure port 4096 is free
  - Example troubleshooting steps are printed by ADWS start-up error messages

2) Authentication errors (401 / 403)
- Symptoms: OpenCode client raises authentication error
- Quick fixes:
  - Run `opencode auth login` and follow browser-based authentication
  - Ensure GitHub Copilot subscription is active for your account/organization
  - If using an API key, ensure it is valid and set in the environment if required by your OpenCode deployment

3) Model not found or unexpected model errors
- Symptoms: server returns model not found or modelID errors
- Quick fixes:
  - Validate model IDs used in `.adw.yaml` (e.g., github-copilot/claude-haiku-4.5)
  - Run `opencode models list` to verify available models
  - Ensure your Copilot subscription includes required models

4) Response parsing issues (empty outputs)
- Symptoms: extract_text_response returns empty string while the server returned content
- Causes and fixes:
  - Field naming mismatch: ADWS expects text parts with `content` field for type="text`. Verify the OpenCode server response part keys. If your server returns `text` instead of `content`, either update the server or adjust `extract_text_response` to handle both keys.
  - Verify the response `parts` list actually contains text parts (inspect saved response JSON under ai_docs/logs/{adw_id}/)

5) Timing / Timeout issues
- Symptoms: long-running requests time out
- Mitigation:
  - Increase `timeout` or `read_timeout` in `.adw.yaml` for heavy operations (implement, test_fix, review)
  - Use `lightweight_timeout` for plan/classify operations
  - Tune `max_retries` and `retry_backoff` for your network environment

6) Heuristic metrics are inaccurate
- Notes: `estimate_metrics_from_parts()` uses regex heuristics to estimate files_changed and line counts. It is intentionally conservative and approximate. For exact counts, rely on git diffs produced by ADWS after code is applied.

Cost comparison and recommendations
- Two model classes are used via GitHub Copilot (OpenCode proxy):
  - Claude Haiku 4.5 (lightweight) — used for planning, classification, commit/PR metadata, branch naming. Faster and cheaper; use for high-frequency, small tasks.
  - Claude Sonnet 4 (heavy lifting) — used for code generation, test fixes, and reviews. Slower and more expensive; use only when heavy analysis or code generation is required.

Recommendations:
- Default to Haiku 4.5 for planning/classification operations (6 operations). Reserve Sonnet 4 for implement/test_fix/review operations (3 operations).
- Use caching for repeated planning prompts in CI to reduce calls and cost.
- Monitor usage metrics and tune timeouts and retries to avoid repeated heavy calls on transient failures.

FAQ (short)
Q: Do I still need the Copilot CLI?  
A: No. The Copilot CLI checks and dependencies were removed. ADWS now uses the OpenCode HTTP API. Keep deprecated Copilot-related files for history only.

Q: Where are OpenCode interactions logged?  
A: All OpenCode responses and prompts are saved under `ai_docs/logs/{adw_id}/{agent_name}/` with `response_*.json` and `prompts/` subfolders.

Q: Can I run ADWS without a Copilot subscription?  
A: You can run the OpenCode server, but to access GitHub Copilot models (Haiku/Sonnet) you need an account with Copilot access. For testing, many unit tests mock the OpenCode API.

Q: Are the response parsing heuristics reliable?  
A: They are good for telemetry and quick validation but are heuristic-based. For authoritative change counts use git diffs produced by ADWS after changes are applied.

Q: Where do I change model routing or timeouts?  
A: Update `.adw.yaml` opencode section. ADWConfig reads these values and OpenCodeHTTPClient.from_config() consumes them.

Files to review after migration
- scripts/adw_modules/opencode_http_client.py — client + parsers
- scripts/adw_modules/agent.py — execute_opencode_prompt(), execute_template() refactor
- scripts/adw_modules/config.py — .adw.yaml opencode properties
- scripts/adw_test.py, scripts/adw_review.py — startup checks replaced with OpenCode health check
- ai_docs/logs/ — saved prompts and responses for troubleshooting

If you want, I can:
- Create this MIGRATION_GUIDE.md in the repository (I have written it here).  
- Run a targeted set of tests locally (unit or integration) and report results.  
- Produce a short PR that: (1) standardizes text/content parsing in extract_text_response to accept both `text` and `content`, and (2) removes duplicated TaskType declaration in opencode_http_client.py.

Which of the above would you like me to do next?