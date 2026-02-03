# ADWS (AI Developer Workflow System)

ADWS is a portable, AI-powered autonomous development workflow system designed to automate planning, building, testing, and reviewing software. It integrates seamlessly with Jira, Bitbucket/GitHub, and OpenCode (for LLM capabilities) to provide an end-to-end autonomous coding experience.

## 🚀 Overview

ADWS automates the software development lifecycle (SDLC) through four autonomous phases:

1.  **Plan**: Generates a detailed implementation strategy from a Jira issue.
2.  **Build**: Writes code based on the generated plan.
3.  **Test**: Runs tests and automatically resolves failures.
4.  **Review**: Validates the implementation against acceptance criteria.

Each phase is independent but composable, allowing you to run them individually or chain them together.

## 📦 Installation

### Prerequisites
-   **Python**: 3.10+
-   **Git**: Version control system
-   **Node.js**: Required for OpenCode server (LLM integration)

### 1. Install ADWS
Since ADWS is currently distributed as source, you install it by pointing pip to the ADWS directory.

**Option A: Install from Local Source (Recommended)**
If you have cloned the ADWS repository locally:
```bash
pip install -e /path/to/ADWS
```
*Note: The `-e` flag installs it in "editable" mode, allowing you to pull updates without reinstalling.*

**Option B: Using `uv` (Faster Alternative)**
If you use [uv](https://github.com/astral-sh/uv) for package management:
```bash
# In the ADWS directory
uv pip install -e .
# Or sync dependencies defined in pyproject.toml
uv sync
```

### 2. Install Dependencies
ADWS relies on several key Python packages. These are automatically installed when you run the pip install command above, but listed here for reference:

-   `pydantic` (Data validation)
-   `python-dotenv` (Environment management)
-   `requests` (API communication)
-   `jira` (Jira integration)
-   `rich` (Console UI)
-   `boto3` (AWS Bedrock integration, if used)
-   `pyyaml` (Configuration parsing)

### 3. Install OpenCode Server (Critical)
ADWS uses the **OpenCode HTTP Server** as a local gateway to access LLMs.

1.  **Install the Opencode CLI tool via npm**:
    ```bash
    npm install -g opencode-ai
    ```

2.  **Authenticate & Configure**:
    Authenticate with your chosen provider (e.g., GitHub Copilot, or others supported by OpenCode).
    ```bash
    opencode auth login
    ```
    *Note: ADWS defaults to using GitHub Copilot models in `config.yaml`, but you can configure OpenCode to use other LLM backends if desired.*

### 4. Initialize in Your Project
Navigate to the root of the software project you want to develop with ADWS:

```bash
cd /path/to/your/project
adw init
```
This creates a local `ADWS/` folder for configuration and logs. It does **not** modify your source code.

### 5. Configure Environment
Create a `.env` file in your project root to store credentials:

```bash
# Jira Credentials (Required for Jira integration)
JIRA_SERVER=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_jira_api_token

# Optional: Bitbucket Credentials
BITBUCKET_WORKSPACE=workspace
BITBUCKET_REPO_NAME=repo
BITBUCKET_API_TOKEN=token
```

### 6. Start the System
1.  **Start OpenCode Server** (in a separate terminal window):
    **Important:** You must run this command from the **root directory of your project** so the server can access your files.
    ```bash
    cd /path/to/your/project
    opencode serve --port 4096
    ```
2.  **Validate Setup**:
    ```bash
    adw setup
    ```
    This command checks all connections (Jira, Git, OpenCode) and confirms your system is ready. It will also attempt to start the OpenCode server automatically if it's not running.


## 🛠️ Usage

### Quick Start
Run a full workflow for a specific Jira issue:

```bash
# 1. Plan
adw plan PROJ-123

# 2. Build (using the ADW ID generated in the planning phase)
adw build <ADW_ID> PROJ-123

# 3. Test
adw test <ADW_ID> PROJ-123

# 4. Review
adw review <ADW_ID> PROJ-123
```

### Chained Workflow
```bash
adw plan PROJ-123 | xargs -I {} sh -c 'adw build {} PROJ-123 && adw test {} PROJ-123 && adw review {} PROJ-123'
```

## 📚 Documentation

For detailed information on architecture, configuration, components, and advanced usage, please refer to:

-   **[Detailed Documentation](docs/DOCUMENTATION.md)**: Complete system reference.
-   **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Solutions for common issues.

## 🏗️ Architecture

ADWS operates on a **Portable Architecture** model. All configuration and logs are self-contained within the `ADWS/` directory in your project root, ensuring zero pollution of your source code.

-   **State Management**: Workflow state is persisted in `ADWS/logs/{adw_id}/adw_state.json`.
-   **Logs**: Comprehensive execution logs and prompt audit trails are stored in `ADWS/logs/`.
-   **Configuration**: Project-specific settings live in `ADWS/config.yaml`.
-   **AI Integration**: Uses **OpenCode** as an agnostic gateway. By default, it is configured for GitHub Copilot (Claude Sonnet/Haiku), but can be adapted for other providers supported by OpenCode.


## 🤝 Support

For issues, please check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) or open an issue in the repository.
