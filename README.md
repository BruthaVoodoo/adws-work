# ADW (AI Developer Workflow) - Portable

This is a portable version of the AI Developer Workflow system. It is designed to be dropped into any project to provide autonomous planning, building, testing, and reviewing capabilities.

## Installation

1. Copy the `ADWS` folder (or just the `scripts` and `prompts` directories) to your project.
2. Ensure you have the required dependencies (Python 3.10+, `uv` or `pip`).
   - Dependencies: `pydantic`, `python-dotenv`, `requests`, `jira`, `rich`, `boto3`, `pyyaml`.

## Configuration

ADW looks for a configuration file `.adw.yaml` or `.adw_config.yaml` in your project root. If not found, it defaults to standard paths relative to the current working directory.

### Example `.adw.yaml`

```yaml
# Root directory of the project (default: current directory)
project_root: "."

# Directory where source code lives (default: "src")
source_dir: "src"

# Directory where tests live (default: "tests")
test_dir: "tests"

# Command to run tests (default: "pytest")
test_command: "uv run pytest"

# Directory for ADW logs and plans (default: "ai_docs")
docs_dir: "ai_docs"

# Language of the project (default: "python")
language: "python"
```

## Usage

Run the scripts from your project root.

### 1. Plan
Fetch a Jira ticket and generate an implementation plan.
```bash
uv run path/to/scripts/adw_plan.py <JIRA_ISSUE_KEY>
```

### 2. Build
Implement the plan.
```bash
uv run path/to/scripts/adw_build.py <JIRA_ISSUE_KEY> <ADW_ID>
```

### 3. Test
Run tests and attempt auto-resolution.
```bash
uv run path/to/scripts/adw_test.py <JIRA_ISSUE_KEY> <ADW_ID>
```

### 4. Review
Review the implementation against the plan.
```bash
uv run path/to/scripts/adw_review.py <JIRA_ISSUE_KEY> <ADW_ID>
```

## Environment Variables

Ensure the following environment variables are set (in `.env` or system):
- `JIRA_SERVER`
- `JIRA_USERNAME`
- `JIRA_API_TOKEN`
- `AWS_ENDPOINT_URL` (for AI proxy)
- `AWS_MODEL_KEY` (for AI proxy)
- `AWS_MODEL` (optional, default: sonnet/opus)

Last updated: December 16, 2025








<- Future enhancement suggestions ADW Verification Test: 2025-12-17T10:38:46.588763-05:00 -->
