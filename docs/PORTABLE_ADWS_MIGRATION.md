# Portable ADWS Migration Guide

**Created:** January 15, 2026
**Epic:** Portable ADWS Refactor — Folder-based Zero-Pollution Deployment (Story B5)

This guide helps existing ADWS users migrate from the legacy `.adw.yaml` configuration in project root to the new portable architecture with `ADWS/config.yaml`.

## Table of Contents

- [Overview](#overview)
- [Why the Change?](#why-the-change)
- [What Changed?](#what-changed)
- [Migration Scenarios](#migration-scenarios)
- [Step-by-Step Migration](#step-by-step-migration)
- [Validation & Testing](#validation--testing)
- [Troubleshooting](#troubleshooting)
- [Rollback Plan](#rollback-plan)

---

## Overview

ADWS has been refactored to use a portable, folder-based architecture where configuration lives inside an `ADWS/` folder instead of polluting the project root with `.adw.yaml`.

**Key Benefits:**
- ✅ Zero project pollution - ADWS is self-contained
- ✅ Easy uninstall - just delete the ADWS/ folder
- ✅ Better portability - works in any project without modifying root
- ✅ Cleaner separation - ADWS is an external operator, not integrated into project

---

## Why the Change?

### Problem with Legacy Architecture

Previously, ADWS required a `.adw.yaml` file in the project root:
```
my-project/
├── .adw.yaml          ← Config polluted project root
├── src/
├── tests/
├── package.json
└── README.md
```

**Issues:**
1. Project pollution - extra files in root directory
2. Confusing for new developers - "What's this .adw.yaml file?"
3. Hard to uninstall - need to remember which files to delete
4. Violates single-responsibility principle - config mixed with project files

### New Portable Architecture

ADWS now uses a self-contained folder:
```
my-project/
├── ADWS/               ← Self-contained, can be deleted without affecting project
│   ├── config.yaml
│   ├── logs/
│   └── README.md
├── src/
├── tests/
├── package.json
└── README.md
```

**Benefits:**
1. Zero pollution - project root untouched
2. Clear ownership - ADWS owns the ADWS/ folder exclusively
3. Easy uninstall - `rm -rf ADWS` removes everything
4. Better adoption - no confusing files in project root

---

## What Changed?

### Configuration File Location

| Legacy Location | New Location |
|---------------|--------------|
| `.adw.yaml` (project root) | `ADWS/config.yaml` |

### Configuration Discovery Priority

ADWS now searches for configuration in this order:

1. **Priority 1:** `./ADWS/config.yaml` (current directory)
2. **Priority 2:** Walk up directory tree for `ADWS/config.yaml`
3. **Priority 3:** Fallback to legacy `.adw.yaml` (with deprecation warning)

### New Commands

| Command | Purpose |
|---------|---------|
| `adw init` | Initialize ADWS folder in current project |
| `adw setup` | Configure and validate environment (replaces `adw healthcheck`) |

### Deprecated Commands

| Command | Replacement |
|---------|------------|
| `adw healthcheck` | `adw setup` |

**Note:** `adw healthcheck` is still functional but deprecated and will be removed in a future version.

---

## Migration Scenarios

### Scenario 1: Simple Python Project

**Before:**
```
my-python-project/
├── .adw.yaml
├── src/
├── tests/
└── requirements.txt
```

**After:**
```
my-python-project/
├── ADWS/
│   ├── config.yaml
│   ├── logs/
│   └── README.md
├── src/
├── tests/
└── requirements.txt
```

### Scenario 2: Full-Stack JavaScript Project

**Before:**
```
my-js-project/
├── .adw.yaml
├── frontend/
├── backend/
├── docker-compose.yml
└── package.json
```

**After:**
```
my-js-project/
├── ADWS/
│   ├── config.yaml
│   ├── logs/
│   └── README.md
├── frontend/
├── backend/
├── docker-compose.yml
└── package.json
```

### Scenario 3: Monorepo

**Before:**
```
my-monorepo/
├── .adw.yaml
├── packages/
│   ├── package-a/
│   └── package-b/
└── package.json
```

**After:**
```
my-monorepo/
├── ADWS/
│   ├── config.yaml
│   ├── logs/
│   └── README.md
├── packages/
│   ├── package-a/
│   └── package-b/
└── package.json
```

---

## Step-by-Step Migration

### Prerequisites

1. **Backup your current configuration:**
   ```bash
   cp .adw.yaml .adw.yaml.backup
   ```

2. **Ensure you're in the project root:**
   ```bash
   cd /path/to/your/project
   ```

3. **Verify ADWS is installed:**
   ```bash
   adw --version
   ```

### Migration Steps

#### Step 1: Initialize ADWS Folder

```bash
# Initialize ADWS in your project
adw init
```

**Expected Output:**
```
✓ ADWS/ folder created successfully
  Location: /path/to/your/project/ADWS
  Config: /path/to/your/project/ADWS/config.yaml

Next steps:
  1. Run 'adw setup' to configure and validate your environment
  2. Run 'adw plan <ISSUE_KEY>' to start your first workflow
  3. Run 'adw analyze' to discover your project structure
```

#### Step 2: Migrate Configuration

**Option A: Manual Migration (Recommended for Custom Configs)**

1. Open your backup `.adw.yaml.backup` file
2. Copy relevant settings to `ADWS/config.yaml`
3. Remove `project_root` field (auto-detected by ADWS)
4. Save the file

**Example:**

Legacy `.adw.yaml`:
```yaml
project_root: "."
source_dir: "src"
test_dir: "tests"
test_command: "uv run pytest"
docs_dir: "ai_docs"
language: "python"
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
```

New `ADWS/config.yaml`:
```yaml
# Note: project_root is auto-detected as parent of ADWS folder
source_dir: "src"
test_dir: "tests"
test_command: "uv run pytest"
docs_dir: "ai_docs"
language: "python"
opencode:
  server_url: "http://localhost:4096"
  models:
    heavy_lifting: "github-copilot/claude-sonnet-4"
    lightweight: "github-copilot/claude-haiku-4.5"
```

**Option B: Accept Defaults (For Simple Projects)**

If your `.adw.yaml` used mostly defaults, you can accept the defaults from `adw init`:

```bash
# View current config
cat ADWS/config.yaml

# Edit if needed
vim ADWS/config.yaml
```

#### Step 3: Validate Configuration

```bash
# Configure and validate environment
adw setup
```

**Expected Output:**
```
✓ Configuration validation passed
✓ Environment variables validated
✓ Jira connectivity verified
✓ OpenCode server available
✓ Setup completed successfully

Setup log: ADWS/logs/setup_20260115_143022.txt
```

If any checks fail, `adw setup` will provide actionable error messages.

#### Step 4: Verify Project Analysis

```bash
# Analyze your project structure
adw analyze
```

**Expected Output:**
```
📊 Project Analysis Report

Project: my-project
Root: /path/to/your/project

📁 Directories:
  • src (source code)
  • tests (tests)

📦 Package Managers:
  • pip (requirements.txt)

🔧 Frameworks:
  • None detected

📄 Key Files:
  • README.md
  • .git
  • docker-compose.yml
```

#### Step 5: Clean Up Legacy Files

**After confirming everything works:**

```bash
# Remove legacy config file
rm .adw.yaml

# Optionally remove backup
rm .adw.yaml.backup
```

---

## Validation & Testing

### Pre-Migration Validation

Before migrating, verify your current setup works:

```bash
# Test current configuration
adw healthcheck

# Verify Jira connectivity
curl -H "Authorization: Bearer $JIRA_API_TOKEN" "$JIRA_SERVER/rest/api/2/myself"
```

### Post-Migration Validation

After migrating, verify the new setup works:

```bash
# 1. Verify config is loaded correctly
adw setup

# 2. Verify project analysis works
adw analyze

# 3. Run a test workflow (if you have a test Jira issue)
adw plan TEST-123
```

### Automated Migration Test Script

Save this as `test_migration.sh`:

```bash
#!/bin/bash

echo "Testing ADWS migration..."

# Test 1: Config discovery
echo "Test 1: Config discovery..."
if [ -f "ADWS/config.yaml" ]; then
    echo "✓ ADWS/config.yaml exists"
else
    echo "✗ ADWS/config.yaml not found"
    exit 1
fi

# Test 2: Setup command
echo "Test 2: Setup command..."
if adw setup; then
    echo "✓ Setup command passed"
else
    echo "✗ Setup command failed"
    exit 1
fi

# Test 3: Analyze command
echo "Test 3: Analyze command..."
if adw analyze; then
    echo "✓ Analyze command passed"
else
    echo "✗ Analyze command failed"
    exit 1
fi

echo "All migration tests passed! ✓"
```

Run it:
```bash
chmod +x test_migration.sh
./test_migration.sh
```

---

## Troubleshooting

### Issue 1: "ADWS folder already exists"

**Problem:** You ran `adw init` when an ADWS folder already exists.

**Solution:**
```bash
# Check if ADWS folder has valid config
cat ADWS/config.yaml

# If config is valid, skip init step
# If not, use force to overwrite (with confirmation)
adw init --force
```

### Issue 2: "Configuration not found"

**Problem:** ADWS can't find your configuration file.

**Solution:**
```bash
# Verify config file exists
ls -la ADWS/config.yaml

# Check if you're in the right directory
pwd

# Verify config syntax
cat ADWS/config.yaml
```

### Issue 3: "Legacy config detected" warning

**Problem:** ADWS is still using `.adw.yaml` with deprecation warning.

**Solution:**
```bash
# Check for legacy config
ls -la .adw.yaml

# Remove after migrating
rm .adw.yaml

# Verify warning is gone
adw setup
```

### Issue 4: Setup fails on environment variables

**Problem:** `adw setup` reports missing environment variables.

**Solution:**
```bash
# Check which env vars are set
env | grep -E "JIRA_|BITBUCKET_|OPENCODE_"

# Set missing vars in .env file or shell
export JIRA_SERVER="https://your-jira.atlassian.net"
export JIRA_USERNAME="your-username"
export JIRA_API_TOKEN="your-api-token"

# Re-run setup
adw setup
```

### Issue 5: OpenCode server unavailable

**Problem:** `adw setup` can't reach OpenCode server.

**Solution:**
```bash
# Start OpenCode server (in separate terminal)
opencode serve --port 4096

# Verify server is running
curl http://localhost:4096/health

# Re-run setup
adw setup
```

### Issue 6: Migration breaks existing workflows

**Problem:** Your existing ADW workflows stop working after migration.

**Solution:**
```bash
# Check ADW state files
ls -la ai_docs/logs/

# Verify state file references ADWS/config.yaml
grep -r "config" ai_docs/logs/*/adw_state.json

# If workflows fail, try running from project root
cd /path/to/your/project
adw plan ISSUE-KEY
```

---

## Rollback Plan

If you need to rollback to the legacy configuration:

### Quick Rollback

```bash
# Restore legacy config
cp .adw.yaml.backup .adw.yaml

# Remove ADWS folder
rm -rf ADWS/

# Verify legacy setup works
adw healthcheck
```

### Complete Rollback

```bash
# 1. Restore all backup files
cp .adw.yaml.backup .adw.yaml

# 2. Remove ADWS folder
rm -rf ADWS/

# 3. Verify everything works
adw healthcheck
adw analyze
```

### Rollback Verification

After rolling back, verify:

```bash
# Legacy config is detected
adw healthcheck | grep ".adw.yaml"

# Workflows still work
adw plan TEST-123
```

---

## Advanced Topics

### Customizing ADWS Init Template

You can customize the template used by `adw init`:

```bash
# Edit the template
vim scripts/adw_templates/ADWS/config.yaml

# Reinstall ADWS to pick up changes
pip install -e . --force-reinstall

# Test new template
cd /tmp/test-project
adw init
```

### Using Multiple Configs in a Monorepo

For monorepos with multiple packages, you can place ADWS at different levels:

```bash
# Option 1: Root-level ADWS (operates on entire monorepo)
my-monorepo/adw init

# Option 2: Package-level ADWS (operates on specific package)
my-monorepo/packages/package-a/adw init
```

### CI/CD Integration

Update your CI/CD pipeline to use the new architecture:

```yaml
# Example GitHub Actions
- name: Setup ADWS
  run: |
    adw init
    adw setup

- name: Analyze Project
  run: adw analyze

- name: Run Workflow
  env:
    JIRA_SERVER: ${{ secrets.JIRA_SERVER }}
    JIRA_USERNAME: ${{ secrets.JIRA_USERNAME }}
    JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
  run: |
    adw plan ${{ env.ISSUE_KEY }}
```

---

## FAQ

### Q: Do I have to migrate immediately?

**A:** No. The legacy `.adw.yaml` is still supported with a deprecation warning. However, we recommend migrating soon as the legacy config will be removed in a future version.

### Q: Will my existing ADW workflows still work after migration?

**A:** Yes. ADW IDs and state files are independent of config location. Your workflows will continue to work seamlessly.

### Q: Can I use both `.adw.yaml` and `ADWS/config.yaml`?

**A:** No. ADWS will only use `ADWS/config.yaml` if it exists. The legacy `.adw.yaml` is only used as a fallback if `ADWS/config.yaml` is not found.

### Q: What happens to my logs and state files?

**A:** They remain in `ai_docs/logs/` as before. The migration only affects configuration, not execution artifacts.

### Q: Can I migrate multiple projects at once?

**A:** Yes. Use a script to iterate through your projects:

```bash
#!/bin/bash

projects=(
  "/path/to/project1"
  "/path/to/project2"
  "/path/to/project3"
)

for project in "${projects[@]}"; do
  echo "Migrating $project..."
  cd "$project"
  adw init
  adw setup
done
```

### Q: Who should I contact if I have migration issues?

**A:** Please file an issue in the ADWS repository with:
1. Your project structure (directory listing)
2. Your legacy `.adw.yaml` content (redact secrets)
3. Error messages from `adw setup`
4. Steps you've already tried

---

## Conclusion

Migrating to the portable ADWS architecture is straightforward and provides significant benefits:

- ✅ Cleaner project structure
- ✅ Easier maintenance
- ✅ Better developer experience
- ✅ Zero pollution uninstall

For most users, the migration takes less than 5 minutes. If you encounter issues, refer to the troubleshooting section or file an issue.

**Ready to migrate?** Start with the [Step-by-Step Migration](#step-by-step-migration) section.

---

**Last Updated:** January 15, 2026
**Epic:** Portable ADWS Refactor — Folder-based Zero-Pollution Deployment
**Story:** B5 — Docs, migration notes, and acceptance tests
