# ADWS Troubleshooting Guide

## Purpose
This guide helps diagnose and resolve common issues with ADWS, including OpenCode connectivity, authentication, environment configuration, and workflow failures.

## Quick Checklist
1.  **OpenCode Server**: Is it running (`opencode serve --port 4096`) and authenticated (`opencode auth login`)?
2.  **Environment**: Are all required variables set in `.env` (Jira, Bitbucket/GitHub)?
3.  **Git**: Is your working tree clean?
4.  **Tests**: Can you run `uv run pytest` successfully?

## Common Issues & Solutions

### OpenCode Server (LLM Backend)

**Symptoms**:
-   "Connection refused" or timeouts.
-   "Model not found" errors.
-   Authentication failures (401/403).

**Diagnostics**:
```bash
# Check health
curl http://localhost:4096/health

# Check process
lsof -i :4096
```

**Solutions**:
1.  **Start Server**: `opencode serve --port 4096`
2.  **Authenticate**: `opencode auth login` (Requires GitHub Copilot subscription)
3.  **Check Models**: `opencode models list` to verify access to `claude-sonnet-4` and `claude-haiku-4.5`.
4.  **Restart**: Kill existing process (`pkill -f "opencode serve"`) and restart.

### Environment & Configuration

**Symptoms**:
-   `adw setup` fails.
-   "Missing required environment variables" error.

**Solutions**:
1.  **Verify `.env`**: Ensure it exists in the project root and contains `JIRA_SERVER`, `JIRA_USERNAME`, `JIRA_API_TOKEN`.
2.  **Check Syntax**: No spaces around `=` (e.g., `KEY=value`, not `KEY = value`).
3.  **Load Env**: Run `source .env` or ensure your shell loads it.

### Git & Repository

**Symptoms**:
-   Branch creation fails.
-   "Working tree not clean" errors.

**Solutions**:
1.  **Clean State**: Commit or stash changes before running `adw plan` or `adw build`.
2.  **Branch Name**: Ensure the target branch doesn't already exist locally or remotely if you intend to create a new one.

### Workflow Failures

**Symptoms**:
-   Plan generation hangs or returns empty.
-   Implementation fails to write files.

**Solutions**:
1.  **Check Logs**: Inspect `ADWS/logs/{adw_id}/{phase}/execution.log`.
2.  **Timeout**: Increase `timeout` in `ADWS/config.yaml` if operations are taking too long.
3.  **Permissions**: Ensure the process has write access to the source directory.

## Gathering Debug Info

When reporting issues, please provide:
1.  **Version**: `adw --version`
2.  **Health Check**: Output of `adw setup`
3.  **Logs**: Relevant files from `ADWS/logs/` (sanitize secrets!)
4.  **Config**: Contents of `ADWS/config.yaml`
