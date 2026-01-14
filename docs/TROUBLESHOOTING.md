ADWS Troubleshooting Guide

Purpose
-------
This troubleshooting guide helps developers and operators diagnose and resolve the most common problems when running ADWS: OpenCode connectivity, authentication, LLM model issues, Git operations, test execution, and environment configuration. It also lists where to find logs and how to gather useful debug information for support.

Quick checklist
---------------
- Is the OpenCode server running and authenticated? (opencode serve --port 4096; opencode auth login)
- Are the required environment variables set? (JIRA_SERVER, JIRA_USERNAME, JIRA_API_TOKEN)
- Is your working tree in a clean state for operations that create branches/commits?
- Do the tests run locally with the configured test command (see .adw.yaml test_command)?
- Check ai_docs/logs/{ADW_ID}/ for agent prompts, responses, and adw_state.json

OpenCode HTTP server (local LLM backend)
---------------------------------------
Symptoms
- "Connection refused", timeouts, or operations that hang when calling the LLM.
- Authentication errors (401/403) from OpenCode endpoints.
- Responses saying "Model not found" or unexpected model behavior.

How to verify
1. Health endpoint:
   curl http://localhost:4096/health
   - Expect a 2xx response when server is available.
2. Use the built-in helper from project root:
   python -c "from scripts.adw_modules.opencode_http_client import check_opencode_server_available; print(check_opencode_server_available('http://localhost:4096', 5))"
3. Confirm the correct port and URL in .adw.yaml (opencode.server_url) or OPENCODE_URL env var.
4. If authentication is required, re-run:
   opencode auth login

Common fixes
- Start the server if it is not running: opencode serve --port 4096
- If connection refused, check for process conflicts: lsof -i :4096
- If authentication fails (401/403): re-authenticate (opencode auth login) and ensure GitHub Copilot subscription is active
- If a model ID is incorrect, verify available models: opencode models list and update .adw.yaml accordingly
- Increase opencode read_timeout/opencode.timeout in .adw.yaml for long-running operations

OpenCode request errors and retries
----------------------------------
The OpenCodeHTTPClient implements exponential backoff (1s, 2s, 4s) and retries on timeouts, connection errors, and 5xx server errors. It does not retry on client errors (4xx) including authentication failures.

If you see repeated retries and exhausted attempts:
- Inspect the ai_docs/logs/{adw_id}/{agent_name}/error_response_*.json for detailed error_context and response previews.
- Consider increasing opencode.max_retries and opencode.retry_backoff in .adw.yaml temporarily for flaky networks.

Authentication & Authorization (Jira / OpenCode)
------------------------------------------------
- Jira: Ensure JIRA_SERVER, JIRA_USERNAME, and JIRA_API_TOKEN are set (check with env or .env). Verify you can curl the Jira API endpoint with the credentials.
- OpenCode: opencode auth login must be completed on the machine running the server. A valid Copilot subscription is required to access Copilot models.

Git & repository state issues
-----------------------------
Symptoms
- Branch creation or commits fail, pre-commit hooks block commits, or operations refuse to run on dirty trees.

Checks
- Run git status and ensure the working tree is clean before running plan/build operations that perform commits.
- Verify that the current branch is not main/master if you intend to create feature branches.

Fixes
- Stash uncommitted changes or create a temporary branch to preserve work: git stash push -m "WIP" or git checkout -b wip-save
- If a commit fails due to hooks, inspect the hook logs/output and fix violations before re-running.
- ADWS will never force-push or run destructive git operations; if a push is required, perform it manually or request it explicitly.

Running tests & test failures
----------------------------
- Run the configured test command from .adw.yaml (default: "uv run pytest" or "pytest")
- To see verbose output and prints during tests use: uv run pytest -s -v
- If tests fail that interact with OpenCode, ensure the server is running and tests that require it are not being skipped.

Common test failure causes
- OpenCode server not available → integration tests skipped or failing
- Missing environment variables (JIRA credentials) → tests that call Jira will fail
- Local environment differences (python version, missing deps) → run pip install -r requirements.txt

Logs and where to find them
--------------------------
ADWS writes structured logs for reproducibility and debugging under the configured ai_docs/logs directory (default ai_docs/logs/):
- ai_docs/logs/{adw_id}/adw_state.json — persistent workflow state
- ai_docs/logs/{adw_id}/agent_name/response_*.json — LLM responses (full JSON with parts)
- ai_docs/logs/{adw_id}/agent_name/error_response_*.json — error responses and context

Gathering debug info for support
--------------------------------
When reporting an issue, please collect the following and attach them to the bug report or Jira ticket:
1. Python version and OS (python --version; uname -a)
2. .adw.yaml contents (sanitize secrets) and relevant env vars (JIRA_SERVER, OPENCODE_URL)
3. The exact command that failed (e.g., adw plan PROJ-123 or python -m scripts.adw_cli plan PROJ-123)
4. Output of health checks:
   - curl <opencode_url>/health
   - python -c "from scripts.adw_modules.opencode_http_client import check_opencode_server_available; print(check_opencode_server_available())"
5. Relevant log files from ai_docs/logs/{adw_id}/ (response_*.json or error_response_*.json)
6. git status and recent git log (git status --porcelain; git log -3 --oneline)
7. Reproduction steps and minimal sample input

Troubleshooting specific scenarios
---------------------------------
1) OpenCode returns 401 Unauthorized
   - Cause: API key missing/expired or session expired
   - Action: Re-authenticate (opencode auth login), restart server, verify API key/header usage

2) OpenCode returns 500/502 intermittently
   - Cause: Server overload or model backend failure
   - Action: Retry (client retries automatically). If persistent, check OpenCode server logs and increase timeouts or retry_backoff in .adw.yaml

3) CLI reports "Model not found"
   - Cause: Model name mismatch or Copilot subscription doesn't have access
   - Action: Run opencode models list and check .adw.yaml model IDs. Contact administrator if model access missing.

4) Adw plan/build hangs or takes too long
   - Cause: Large prompt, slow model, insufficient timeouts
   - Action: Increase opencode.timeout/opencode.read_timeout; run with verbose logging to capture timing

5) Tests that require OpenCode are skipped during CI
   - Cause: CI machine has no OpenCode server or credentials
   - Action: Configure CI to run an OpenCode server (if allowed) or mark tests to run conditionally. Use the health check helper to skip gracefully when server unavailable.

Best practices
--------------
- Keep a running OpenCode server during development to speed iteration.
- Use separate ADW IDs for separate runs to avoid log collisions: ADW_ID is provided by adw plan output.
- Sanitize logs before sharing externally (remove secrets, tokens).
- Use the built-in health check and test helpers in scripts/adw_tests for reproducible validation.

When to escalate
----------------
Escalate to the maintainers or open a Jira ticket if:
- You have reproducible server-side errors (5xx) with logs from ai_docs and OpenCode server logs
- Authentication continually fails after re-authentication
- Model access or subscription issues confirmed by opencode models list

Contact & support
-----------------
For help, create a Jira ticket in the DAI project and attach the items under "Gathering debug info". Include ai_docs/logs files, steps to reproduce, and the output of the health checks.

Last updated: January 14, 2026
