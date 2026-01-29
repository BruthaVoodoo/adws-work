# ADWS (AI Developer Workflow System)

AI-powered autonomous development workflow that automates planning, building, testing, and reviewing. Designed to be portable and installable into any Python project.

## Overview

ADWS takes Jira issues and autonomously:
1. **Plan** - Generate implementation strategy
2. **Build** - Write code based on plan
3. **Test** - Run tests and auto-resolve failures
4. **Review** - Validate against acceptance criteria

Each phase is independent but composable, enabling flexible workflows.

## Project Integration Guide

### Step-by-Step Setup for Existing Projects

#### Step 1: Install ADWS System

```bash
# Option 1: Install from local repository
pip install -e /path/to/ADWS

# Option 2: If you have the ADWS source code locally
cd /path/to/ADWS
pip install -e .
```

Verify installation:
```bash
adw --version
adw --help
```

#### Step 2: Navigate to Your Project and Initialize

```bash
# Go to YOUR project directory (not the ADWS directory)
cd /path/to/your/project

# Initialize ADWS in your project
adw init
```

**What `adw init` creates:**
```
your-project/
├── ADWS/                   # ← New folder created
│   ├── config.yaml         # ← ADWS configuration  
│   ├── logs/               # ← Log files directory
│   └── README.md           # ← ADWS folder documentation
├── src/                    # ← Your existing code (unchanged)
├── tests/                  # ← Your existing tests (unchanged)  
└── package.json            # ← Your existing files (unchanged)
```

#### Step 3: Create Environment Configuration

Create `.env` file in your project root (same level as the ADWS folder):

```bash
# In your project root directory
touch .env
```

Add your environment variables to `.env` (see Environment Variables section above for details):

```bash
# Required
JIRA_SERVER=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_jira_token

# Required if using Bitbucket
BITBUCKET_WORKSPACE=your-workspace  
BITBUCKET_REPO_NAME=your-repo-name
BITBUCKET_API_TOKEN=your_bitbucket_token
```

#### Step 4: Configure Project-Specific Settings

Edit `ADWS/config.yaml` to match your project structure:

```yaml
# Customize these for your project
source_dir: "src"                    # Your source code directory  
test_dir: "tests"                    # Your tests directory
test_command: "pytest"               # How to run your tests
language: "python"                  # Your primary language

# OpenCode configuration (usually defaults are fine)
opencode:
  server_url: "http://localhost:4096"
  # ... other settings
```

#### Step 5: Setup and Validate Environment

```bash
# Run comprehensive setup and validation
adw setup
```

This command will:
- ✅ Validate ADWS folder and configuration
- ✅ Check required environment variables  
- ✅ Test Jira API connectivity
- ✅ Test OpenCode server availability
- ✅ Test optional integrations (Bitbucket, GitHub CLI)
- ✅ Provide clear error messages for any issues

#### Step 6: Start OpenCode Server

In a separate terminal, start the OpenCode HTTP server:

```bash
# Start OpenCode server (keep this running)
opencode serve --port 4096

# Authenticate if needed (opens browser)
opencode auth login
```

#### Step 7: Run Your First Workflow

```bash
# Test with a real Jira issue from your project
adw plan YOUR-ISSUE-123
```

### Troubleshooting Integration Issues

**Common Issues During Setup:**

**1. `.env` file not found or not working:**
- Ensure `.env` is in your project root (same directory where you ran `adw init`)
- Check file permissions: `ls -la .env`
- Verify no syntax errors in `.env` (no spaces around `=`)

**2. "ADWS folder not found" errors:**
- Run `adw init` in your project directory first
- Ensure you're running `adw` commands from your project root

**3. Jira connectivity issues:**
- Verify JIRA_SERVER URL is correct (include `https://`)  
- Test API token: `curl -u "email:token" "$JIRA_SERVER/rest/api/2/myself"`
- Ensure API token has proper permissions

**4. Bitbucket API errors:**
- Verify workspace and repository names match your Bitbucket URL
- Check API token permissions include Repositories and Pull requests
- Test with: `adw setup` for detailed connectivity validation

**5. OpenCode server not responding:**
- Ensure server is running: `curl http://localhost:4096/health`
- Verify authentication: `opencode auth login`
- Check port conflicts: `lsof -i :4096`

### Project Structure After Integration

After successful setup, your project structure should look like:

```
your-project/
├── .env                    # Environment variables (YOUR PROJECT ROOT)
├── .git/                   # Your git repository
├── ADWS/                   # ADWS system folder
│   ├── config.yaml         # ADWS configuration
│   ├── logs/               # Workflow logs (created during usage)
│   └── README.md           # ADWS documentation
├── src/                    # Your application source code
├── tests/                  # Your test suite  
├── ai_docs/                # Generated plans and docs (created during usage)
└── [your project files]    # package.json, requirements.txt, etc.
```

**Key Points:**
- ✅ ADWS does not modify your existing code or project structure
- ✅ All ADWS files are contained in the `ADWS/` folder
- ✅ Generated documentation goes in `ai_docs/` (configurable)
- ✅ Your `.env` file is in the project root (NOT in the ADWS folder)

## Configuration

ADWS configuration lives in `ADWS/config.yaml` (created by `adw init`). You can customize it for your project:

```yaml
# Source code directory (default: "src")
source_dir: "src"

# Tests directory (default: "tests")
test_dir: "tests"

# Test command (default: "pytest")
test_command: "uv run pytest"

# Logs/documentation directory (default: "ai_docs")
docs_dir: "ai_docs"

# Project language (default: "python")
language: "python"

# OpenCode configuration
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
```

**Portable Architecture Note:** ADWS configuration is now self-contained in the `ADWS/` folder. There's no need for `.adw.yaml` in your project root (though it's still supported with a deprecation warning for legacy users).

### Environment Variables

⚠️ **IMPORTANT: Environment File Location**

Create your `.env` file in the **root of YOUR project** (not inside the ADWS folder):

```
your-project/
├── .env                    # ← CREATE THIS FILE HERE
├── ADWS/                   # ← ADWS system folder  
│   └── config.yaml         # ← ADWS configuration
├── src/                    # ← Your application code
└── package.json            # ← Your project files
```

**Required Environment Variables:**

Create `.env` file in your project root with these variables:

```bash
# Jira Integration (Required)
JIRA_SERVER=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com  
JIRA_API_TOKEN=your_jira_api_token

# Bitbucket Integration (Required if using Bitbucket)
BITBUCKET_WORKSPACE=your-workspace-name
BITBUCKET_REPO_NAME=your-repository-name
BITBUCKET_API_TOKEN=your_bitbucket_api_token
```

**Optional Environment Variables:**

```bash
# GitHub Integration (Alternative to Bitbucket)
GITHUB_TOKEN=your_github_token

# OpenCode Server Override (if not using default)
OPENCODE_URL=http://localhost:4096
```

#### How to Obtain API Tokens

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Enter a label (e.g., "ADWS Integration")  
4. Copy the generated token
5. Use your email address as JIRA_USERNAME

**Bitbucket API Token:**
1. Go to Bitbucket Settings → Personal Bitbucket settings → App passwords
2. Click "Create app password"
3. Select permissions: Repositories (Read, Write), Pull requests (Read, Write)
4. Copy the generated token

**GitHub Token (if using GitHub instead of Bitbucket):**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: repo, workflow  
4. Copy the generated token

#### Finding Your Workspace and Repository Names

**Bitbucket:**
- Workspace: The part after `bitbucket.org/` in your repository URL
- Repository: The repository name in your URL
- Example URL: `https://bitbucket.org/my-workspace/my-repo`
  - BITBUCKET_WORKSPACE=my-workspace
  - BITBUCKET_REPO_NAME=my-repo

**Validation:**
After creating your `.env` file, validate your configuration:

```bash
adw setup
```

This will test all your API connections and provide clear error messages if anything is misconfigured.

### Start OpenCode before running ADWS
Before running any `adw` commands that call the LLM, ensure the OpenCode server is running and authenticated.

```bash
# Example (start server in a separate terminal)
opencode serve --port 4096
# Authenticate if not already done
opencode auth login
```

## Workflows & Usage Examples

### Complete Development Workflow

Here's how to use ADWS for a typical development task:

#### Scenario: Implementing a new feature from Jira

**1. Start with a Jira Issue**
- Create or assign yourself a Jira issue (e.g., `PROJ-123: Add user authentication`)
- Ensure the issue has clear acceptance criteria

**2. Plan Phase**
```bash
# Generate implementation strategy
adw plan PROJ-123

# Output will include:
# ✅ ADW ID (e.g., a1b2c3d4) - save this!
# ✅ Implementation plan document
# ✅ Feature branch created  
# ✅ Pull request opened
```

**3. Build Phase**
```bash
# Implement the plan (use ADW ID from step 2)
adw build a1b2c3d4 PROJ-123

# Output:
# ✅ Code implementation committed
# ✅ Pull request updated with changes
# ✅ Ready for testing
```

**4. Test Phase**  
```bash
# Run tests and auto-resolve failures
adw test a1b2c3d4 PROJ-123

# Output:
# ✅ Test results
# ✅ Auto-resolved failures (if any)
# ✅ Ready for review
```

**5. Review Phase**
```bash
# Validate implementation
adw review a1b2c3d4 PROJ-123

# Output:
# ✅ Review findings
# ✅ Acceptance criteria validation
# ✅ Ready for merge assessment
```

### Alternative Workflow Patterns

#### Sequential Workflow (Manual Control)
Run each phase individually with manual checkpoints:

```bash
# Phase 1: Plan
ADW_ID=$(adw plan PROJ-123)
echo "Generated ADW ID: $ADW_ID"

# Review the generated plan before proceeding
# Check: ai_docs/logs/$ADW_ID/phase_plan/

# Phase 2: Build  
adw build $ADW_ID PROJ-123

# Review the implementation before testing
# Check the created branch and pull request

# Phase 3: Test
adw test $ADW_ID PROJ-123  

# Review test results before final review
# Check: ai_docs/logs/$ADW_ID/phase_test/

# Phase 4: Review
adw review $ADW_ID PROJ-123
```

#### Automated Workflow (Full Automation)
Chain all phases together with error handling:

```bash
# Get ADW ID from plan phase
ADW_ID=$(adw plan PROJ-123) && \
echo "Plan complete. ADW ID: $ADW_ID" && \
adw build $ADW_ID PROJ-123 && \
echo "Build complete. Running tests..." && \
adw test $ADW_ID PROJ-123 && \
echo "Tests complete. Running review..." && \
adw review $ADW_ID PROJ-123 && \
echo "🎉 Full workflow complete!"
```

#### Partial Workflow (Resume from Any Phase)
If you already have an ADW ID, you can resume from any phase:

```bash
# Resume from build phase
adw build existing-adw-id PROJ-123

# Resume from test phase  
adw test existing-adw-id PROJ-123

# Resume from review phase
adw review existing-adw-id PROJ-123
```

### Real-World Usage Examples

#### Example 1: Bug Fix Workflow
```bash
# Bug report: PROJ-456: Fix login validation error

# 1. Plan the bug fix
adw plan PROJ-456  # Creates branch: bugfix/proj-456-fix-login-validation-error

# 2. Implement the fix
adw build a1b2c3d4 PROJ-456

# 3. Run tests (includes regression testing)
adw test a1b2c3d4 PROJ-456

# 4. Review the fix
adw review a1b2c3d4 PROJ-456
```

#### Example 2: Feature Development Workflow  
```bash
# Feature request: PROJ-789: Add password reset functionality

# 1. Plan the feature
adw plan PROJ-789  # Creates branch: feature/proj-789-add-password-reset-functionality

# 2. Implement feature
adw build a1b2c3d4 PROJ-789

# 3. Test feature (includes unit, integration, e2e tests as needed)
adw test a1b2c3d4 PROJ-789

# 4. Review feature
adw review a1b2c3d4 PROJ-789
```

#### Example 3: Multiple Issues Workflow
```bash
# Working on multiple issues in parallel

# Issue 1: PROJ-100
ADW_ID_1=$(adw plan PROJ-100)
adw build $ADW_ID_1 PROJ-100

# Issue 2: PROJ-101  
ADW_ID_2=$(adw plan PROJ-101)
adw build $ADW_ID_2 PROJ-101

# Continue with testing both
adw test $ADW_ID_1 PROJ-100
adw test $ADW_ID_2 PROJ-101

# Review both
adw review $ADW_ID_1 PROJ-100
adw review $ADW_ID_2 PROJ-101
```

### Understanding ADW Output

#### ADW State Tracking
Each workflow run creates comprehensive logs in `ai_docs/logs/{adw_id}/`:

```
ai_docs/logs/
└── a1b2c3d4/                    # Your ADW ID
    ├── adw_state.json           # Workflow state and progress
    ├── phase_plan/
    │   └── execution.log        # Plan phase logs
    ├── phase_build/
    │   └── execution.log        # Build phase logs  
    ├── phase_test/
    │   └── execution.log        # Test phase logs
    ├── phase_review/
    │   └── execution.log        # Review phase logs
    └── agent_*/prompts/         # LLM prompts used
```

#### Branch and PR Management
- **Branch naming**: Automatic based on issue type and title
  - Features: `feature/proj-123-feature-name`
  - Bugs: `bugfix/proj-123-bug-description`
  - Chores: `chore/proj-123-task-name`
- **PR management**: Automatic creation and updates
- **Commit structure**: Organized commits per phase

#### Integration with Your Git Workflow
ADWS works with your existing Git workflow:
- Respects your main/master branch
- Creates feature branches from latest main
- Handles merge conflicts and provides guidance
- Integrates with Bitbucket/GitHub PR workflows

## Commands Reference

### Init
```bash
adw init [--force]

Arguments:
  --force            Force overwrite existing ADWS folder (with confirmation)
```

Initialize ADWS in your current project directory. Creates an `ADWS/` folder with default configuration.

### Setup
```bash
adw setup

Arguments: (none)
```

Configure and validate your ADWS environment. Checks configuration, environment variables, OpenCode server, Jira, and optional integrations.

### Plan
```bash
adw plan <ISSUE_KEY> [--adw-id ID]

Arguments:
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
  --adw-id ID        Optional: Specify ADW ID instead of generating
```

### Build
```bash
adw build <ADW_ID> <ISSUE_KEY>

Arguments:
  ADW_ID             ADW ID from plan phase
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
```

### Test
```bash
adw test <ADW_ID> <ISSUE_KEY>

Arguments:
  ADW_ID             ADW ID from plan phase
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
```

### Review
```bash
adw review <ADW_ID> <ISSUE_KEY>

Arguments:
  ADW_ID             ADW ID from plan phase
  ISSUE_KEY          Jira issue key (e.g., PROJ-123)
```

### Analyze
```bash
adw analyze

Arguments: (none)
```

Analyze your project structure to identify directories, package managers, frameworks, and key files. Helps ADWS understand your project for better planning and implementation.

**Output:**
- Project name and root directory
- Detected directories (frontend, backend, src, tests, etc.)
- Package managers (npm, pip, cargo, etc.)
- Frameworks (React, Express, Django, etc.)
- Key files (Docker, README, Git, etc.)

### Healthcheck (Deprecated)
```bash
adw healthcheck

⚠️ **Deprecated:** Use `adw setup` instead. This command is maintained for backward compatibility only.

This command performs comprehensive system health checks:
- Validates all required environment variables
- Checks OpenCode HTTP server availability
- Tests Jira API connectivity
- Tests Bitbucket API connectivity (if configured)
- Verifies GitHub CLI installation and authentication

Returns:
  Exit code 0 if all checks pass, 1 otherwise
```

### Help & Version
```bash
adw --help              # Show general help
adw --version           # Show version
adw init --help         # Show init-specific help
adw setup --help        # Show setup-specific help
adw analyze --help      # Show analyze-specific help
adw plan --help         # Show plan-specific help
adw build --help        # Show build-specific help
adw test --help         # Show test-specific help
adw review --help       # Show review-specific help
```

## State Management

ADWS maintains state across phases in `ai_docs/logs/{adw_id}/`:

```
ai_docs/logs/
└── a1b2c3d4/
    ├── adw_state.json          # Workflow state
    ├── phase_plan/
    │   └── execution.log       # Plan phase logs
    ├── phase_build/
    │   └── execution.log       # Build phase logs
    ├── phase_test/
    │   └── execution.log       # Test phase logs
    ├── phase_review/
    │   └── execution.log       # Review phase logs
    └── agent_*/prompts/        # LLM prompts used
```

Each phase reads and updates `adw_state.json`, enabling resumable workflows.

## Troubleshooting

### Environment and Setup Issues

#### Command not found: adw
**Problem:** The `adw` command is not available in your terminal.

**Solutions:**
```bash
# Check if ADWS is installed
pip show adws

# Verify PATH includes pip script directory
which python3
pip show --files adws | grep scripts

# Alternative: Run directly
python3 -m scripts.adw_cli plan PROJ-123

# Reinstall if needed
pip install -e /path/to/ADWS --force-reinstall
```

#### Environment variables not loading
**Problem:** ADWS can't find your environment variables.

**Solutions:**
1. **Verify .env file location:**
   ```bash
   # .env must be in your project root, not in ADWS folder
   ls -la .env  # Should be in same directory as ADWS/
   ```

2. **Check .env file syntax:**
   ```bash
   # Correct format (no spaces around =)
   JIRA_SERVER=https://company.atlassian.net
   
   # Incorrect format  
   JIRA_SERVER = https://company.atlassian.net  # ❌ Spaces around =
   ```

3. **Test environment loading:**
   ```bash
   # Check if variables are loaded
   python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('JIRA_SERVER:', os.getenv('JIRA_SERVER'))"
   ```

4. **Run validation:**
   ```bash
   adw setup  # Will show which env vars are missing
   ```

### API Connection Issues

#### Jira connectivity problems
**Error:** "Failed to connect to Jira" or 401/403 errors.

**Solutions:**
1. **Verify Jira credentials:**
   ```bash
   # Test your Jira connection manually
   curl -u "your-email@company.com:your-api-token" \
        "https://your-company.atlassian.net/rest/api/2/myself"
   ```

2. **Common Jira setup issues:**
   - JIRA_SERVER must include `https://` and end with domain only (no `/rest/api/`)
   - JIRA_USERNAME should be your full email address
   - API token must have proper permissions
   - Two-factor authentication may interfere (use API tokens, not passwords)

3. **Get a new Jira API token:**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Create new token with appropriate permissions
   - Replace old token in `.env` file

#### Bitbucket API errors (400 Bad Request)
**Error:** "Bitbucket API error creating PR: 400 Client Error" (the original problem!)

**Solutions:**
1. **Verify repository configuration:**
   ```bash
   # Check your Bitbucket repository URL
   git remote -v
   
   # Extract workspace and repo from URL:
   # git@bitbucket.org:my-workspace/my-repo.git
   # BITBUCKET_WORKSPACE=my-workspace
   # BITBUCKET_REPO_NAME=my-repo
   ```

2. **Common Bitbucket configuration errors:**
   ```bash
   # ❌ Wrong: Using ADWS repo instead of your project repo
   BITBUCKET_WORKSPACE=deluxe-development
   BITBUCKET_REPO_NAME=adws
   
   # ✅ Correct: Using YOUR project repository  
   BITBUCKET_WORKSPACE=your-company-workspace
   BITBUCKET_REPO_NAME=your-project-repo
   ```

3. **Test Bitbucket API access:**
   ```bash
   # Test repository access
   curl -u "username:api-token" \
        "https://api.bitbucket.org/2.0/repositories/YOUR-WORKSPACE/YOUR-REPO"
   ```

4. **Validate Bitbucket setup:**
   ```bash
   adw setup  # Will test Bitbucket connectivity
   ```

#### OpenCode server issues
**Error:** Connection refused, server not available, or model errors.

**Solutions:**
1. **Check server status:**
   ```bash
   # Test server health
   curl http://localhost:4096/health
   
   # Check if server is running
   ps aux | grep opencode
   lsof -i :4096
   ```

2. **Start/restart OpenCode server:**
   ```bash
   # Start in foreground (recommended for troubleshooting)
   opencode serve --port 4096
   
   # Or start in background
   opencode serve --port 4096 &
   ```

3. **Authentication issues:**
   ```bash
   # Re-authenticate
   opencode auth logout
   opencode auth login
   
   # Verify GitHub Copilot subscription
   # Check: https://github.com/settings/copilot
   ```

4. **Port conflicts:**
   ```bash
   # Check what's using port 4096
   lsof -i :4096
   
   # Use different port if needed
   opencode serve --port 8080
   # Then update ADWS/config.yaml: server_url: "http://localhost:8080"
   ```

### Workflow Execution Issues

#### Git operation failures
**Error:** Branch creation fails, commit errors, or merge conflicts.

**Solutions:**
1. **Check git repository state:**
   ```bash
   git status
   git branch -a
   git remote -v
   ```

2. **Clean working directory:**
   ```bash
   # Ensure clean state before starting
   git status --porcelain  # Should be empty
   
   # Stash uncommitted changes if needed
   git stash
   ```

3. **Update main branch:**
   ```bash
   # Ensure main/master is up to date
   git checkout main
   git pull origin main
   ```

#### Test execution failures
**Error:** Tests fail to run or test command not found.

**Solutions:**
1. **Verify test command configuration:**
   ```yaml
   # In ADWS/config.yaml
   test_command: "pytest"           # Basic pytest
   # or
   test_command: "uv run pytest"    # Using uv package manager
   # or  
   test_command: "python -m pytest" # Using python module
   ```

2. **Test command manually:**
   ```bash
   # Run your configured test command
   cd your-project
   pytest  # or whatever your test_command is set to
   ```

3. **Missing test dependencies:**
   ```bash
   # Install testing dependencies
   pip install pytest pytest-cov
   # or
   uv add pytest pytest-cov
   ```

#### Permissions and access issues
**Error:** Permission denied, access forbidden, or authentication failures.

**Solutions:**
1. **File permissions:**
   ```bash
   # Check ADWS folder permissions
   ls -la ADWS/
   chmod -R 755 ADWS/
   ```

2. **API token permissions:**
   - Jira: Ensure API token has project access
   - Bitbucket: Verify app password has Repository Write and Pull requests permissions  
   - GitHub: Check token has repo and workflow scopes

3. **Repository access:**
   ```bash
   # Test git access
   git remote -v
   git fetch --dry-run
   ```

### Performance and Reliability Issues  

#### Slow response times
**Problem:** Commands take very long to complete.

**Solutions:**
1. **Check OpenCode server performance:**
   ```bash
   # Monitor server logs
   opencode serve --port 4096 --verbose
   ```

2. **Network connectivity:**
   ```bash
   # Test connectivity to GitHub/Jira/Bitbucket
   ping github.com
   ping api.atlassian.net  
   ping api.bitbucket.org
   ```

3. **Reduce timeout for testing:**
   ```yaml
   # In ADWS/config.yaml
   opencode:
     timeout: 300        # Reduce from 600 (10min) to 300 (5min)
     read_timeout: 300
   ```

#### Intermittent failures  
**Problem:** Commands sometimes work, sometimes fail.

**Solutions:**
1. **Enable retry mechanisms:**
   ```yaml
   # In ADWS/config.yaml
   opencode:
     max_retries: 5      # Increase from 3 to 5
     retry_backoff: 2.0  # Increase backoff time
   ```

2. **Check system resources:**
   ```bash
   # Monitor CPU, memory, disk
   top
   df -h
   ```

3. **Review logs for patterns:**
   ```bash
   # Check ADWS logs
   ls -la ADWS/logs/
   tail -f ADWS/logs/setup_*.txt
   ```

### Getting Help

#### Diagnostic Information
When reporting issues, include:

```bash
# System information
adw --version
python3 --version
git --version

# Configuration
cat ADWS/config.yaml
cat .env | sed 's/=.*/=***masked***/'  # Hide sensitive values

# Environment test
adw setup

# Recent logs  
ls -la ADWS/logs/
tail ADWS/logs/setup_*.txt
```

#### Support Resources
1. **Documentation:** Check this README and `ADWS/README.md`
2. **Command help:** `adw --help`, `adw plan --help`, etc.
3. **Logs:** Review `ADWS/logs/` and `ai_docs/logs/{adw_id}/`
4. **Configuration:** Verify `ADWS/config.yaml` settings
5. **Health check:** Run `adw setup` for comprehensive validation

#### Common Resolution Steps
Before reporting issues, try these steps:

1. **Full reset and revalidation:**
   ```bash
   # Stop any running processes
   pkill -f opencode
   
   # Restart OpenCode server
   opencode serve --port 4096
   
   # Re-authenticate
   opencode auth login
   
   # Validate everything
   adw setup
   ```

2. **Clean environment test:**
   ```bash
   # Create fresh .env file with only required variables
   # Run adw setup to identify missing configuration
   # Add variables one by one until working
   ```

3. **Minimal reproduction:**
   ```bash
   # Try with a simple Jira issue
   # Use basic workflow (just adw plan)
   # Check logs for specific error messages
   ```

## How It Works

### ADW ID
A unique 8-character identifier that tracks a workflow run across all phases:
- Generated in Phase 1 (Plan)
- Used in Phases 2, 3, 4
- All logs and state stored under `ai_docs/logs/{adw_id}/`

### LLM Integration
- **Phase 1 (Plan)**: LLM generates implementation strategy
- **Phase 2 (Build)**: LLM implements code
- **Phase 3 (Test)**: LLM attempts auto-resolution of test failures
- **Phase 4 (Review)**: LLM reviews implementation

### Git Workflow
- Creates feature branch based on issue type
- Makes structured commits at each phase
- Creates/updates pull request
- All operations verified before proceeding

### State Flow
```
User Issue (Jira)
       ↓
   Phase 1: Plan
       ↓ (ADW ID + Plan)
   Phase 2: Build
       ↓ (Code + Commits)
   Phase 3: Test
       ↓ (Test Results)
   Phase 4: Review
       ↓
   PR Ready for Merge
```

## Dependencies

### Runtime
- pydantic (≥2.0) - Data validation
- python-dotenv - Environment configuration
- requests - HTTP client
- jira (≥3.0,<4.0) - Jira API
- rich (≥13.0) - CLI formatting
- boto3 - AWS SDK
- pyyaml - YAML parsing
- click (≥8.0) - CLI framework

### Development (Optional)
- pytest - Testing
- pytest-cov - Coverage reporting
- black - Code formatting
- mypy - Type checking

## Development

### Run Tests

```bash
# All tests
pytest

# Specific test
pytest tests/test_console_consistency.py -v

# With coverage
pytest --cov=scripts/adw_modules
```

### Reinstall in Development Mode

```bash
pip install -e . --force-reinstall --no-deps
```

### Check Installation

```bash
pip show adws
which adw
adw --version
```

## Architecture

- **4 Independent Phases**: Plan → Build → Test → Review
- **Composable**: Run individually or chain together
- **Autonomous**: LLM-driven at each phase
- **Stateful**: Persistent state across phases
- **Logging**: Comprehensive audit trail
- **Extensible**: Template-based prompts, pluggable architecture

## License

MIT

## Support

For issues or questions:
1. Check this README
2. Run `adw --help` for command help
3. Review logs in `ai_docs/logs/{adw_id}/`
4. Check `ADWS/config.yaml` configuration
5. Review [Migration Guide](docs/PORTABLE_ADWS_MIGRATION.md) for upgrading from legacy `.adw.yaml`

Last updated: January 15, 2026
