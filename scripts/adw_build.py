#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "requests", "jira", "rich", "pyyaml"]
# ///

"""
ADW Build - AI Developer Workflow for agentic building

Usage:
  uv run adw_build.py <issue-number> <adw-id>

Workflow:
1. Find existing plan (from state or by searching)
2. Implement the solution based on plan
3. Commit implementation
4. Push and update PR
"""

import sys
import os
import logging
import json
import subprocess
import argparse
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import (
    commit_changes,
    finalize_git_operations,
    get_current_branch,
)
from adw_modules.jira import (
    jira_fetch_issue,
    jira_make_issue_comment,
    jira_add_attachment,
)
from adw_modules.workflow_ops import (
    implement_plan,
    create_commit,
    format_issue_message,
    AGENT_IMPLEMENTOR,
)
from adw_modules.utils import setup_logger, get_rich_console_instance
from adw_modules.data_types import JiraIssue
from adw_modules.config import config
from adw_modules.opencode_http_client import check_opencode_server_available


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that all required environment variables are set and OpenCode server is available."""
    # Check OpenCode server availability first
    if not check_opencode_server_available():
        error_msg = (
            "❌ OpenCode server is not available or not responding.\n"
            "Please ensure OpenCode is running:\n"
            "  1. Start server: opencode serve --port 4096\n"
            "  2. Authenticate: opencode auth login\n"
            "  3. Verify: curl http://localhost:4096/health\n"
            "  4. Run 'adw setup' to verify your full environment"
        )
        if logger:
            logger.error(error_msg)
        else:
            print(error_msg, file=sys.stderr)
        sys.exit(1)

    # TODO: Enable checks once user provides credentials for the new stack
    required_vars = [
        # "AWS_ACCESS_KEY_ID",
        # "AWS_SECRET_ACCESS_KEY",
        "JIRA_SERVER",
        "JIRA_USERNAME",
        "JIRA_API_TOKEN",
        # "BITBUCKET_SERVER",
        # "BITBUCKET_USERNAME",
        # "BITBUCKET_APP_PASSWORD",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        error_msg = "Error: Missing required environment variables:"
        if logger:
            logger.error(error_msg)
            for var in missing_vars:
                logger.error(f"  - {var}")
        else:
            print(error_msg, file=sys.stderr)
            for var in missing_vars:
                print(f"  - {var}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    # Load environment variables - explicitly load from current working directory
    from pathlib import Path

    project_env = Path.cwd() / ".env"
    if project_env.exists():
        load_dotenv(project_env, override=True)
    else:
        # Fallback to auto-discovery if no .env in current directory
        load_dotenv(override=True)

    # Get rich console instance
    rich_console = get_rich_console_instance()

    # Parse command line args
    parser = argparse.ArgumentParser(
        description="ADW Build - AI Developer Workflow for agentic building"
    )
    parser.add_argument("issue_number", help="The GitHub issue number")
    parser.add_argument("adw_id", help="The ADW ID for the current workflow run")
    parser.add_argument(
        "--target-dir",
        default=str(config.project_root),
        help="The target directory for implementation (defaults to the current directory)",
    )
    args = parser.parse_args()

    issue_number = args.issue_number
    adw_id = args.adw_id
    target_dir = args.target_dir

    # Rich console header
    if rich_console:
        rich_console.rule(f"ADW Build - Issue {issue_number}", style="blue")
        rich_console.info(f"ADW ID: {adw_id}")
        rich_console.info(f"Target Directory: {target_dir}")

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_build")

    # === LOADING STATE PHASE ===
    if rich_console:
        rich_console.rule("Loading State", style="cyan")

    # Fetch issue details from Jira FIRST to determine domain
    logger.info(f"Fetching issue {issue_number} from Jira")
    try:
        if rich_console:
            with rich_console.spinner(f"Fetching issue {issue_number} from Jira..."):
                raw_jira_issue = jira_fetch_issue(issue_number)
                issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
            rich_console.success(f"Successfully fetched issue: {issue.title}")
        else:
            raw_jira_issue = jira_fetch_issue(issue_number)
            issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
    except Exception as e:
        error_msg = f"Failed to fetch issue {issue_number} from Jira: {e}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        sys.exit(1)

    # Try to load existing state
    logger.info(f"Loading state")
    if rich_console:
        with rich_console.spinner(f"Loading ADW state for {adw_id}..."):
            state = ADWState.load(adw_id, logger)
    else:
        state = ADWState.load(adw_id, logger)

    if state:
        # Found existing state
        issue_number = state.get("issue_number", issue_number)
        if rich_console:
            rich_console.success("Found existing ADW state - resuming build")
        jira_make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🔍 Found existing state - resuming build\n```json\n{json.dumps(state.data, indent=2)}\n```",
        )
    else:
        # No existing state found
        error_msg = f"No state found for ADW ID: {adw_id}"
        logger.error(error_msg)
        logger.error("Run adw_plan.py first to create the plan and state")
        if rich_console:
            rich_console.error(error_msg)
            rich_console.error("Run adw_plan.py first to create the plan and state")
        else:
            print(f"\nError: {error_msg}")
            print("Run adw_plan.py first to create the plan and state")
        sys.exit(1)

    logger.info(f"ADW Build starting - ID: {adw_id}, Issue: {issue_number}")
    logger.info(f"Target directory for implementation: {target_dir}")

    # Validate environment
    check_env_vars(logger)

    # Ensure we have required state fields
    if not state.get("branch_name"):
        error_msg = "No branch name in state - run adw_plan.py first"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        jira_make_issue_comment(
            issue_number, format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    if not state.get("plan_file"):
        error_msg = "No plan file in state - run adw_plan.py first"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        jira_make_issue_comment(
            issue_number, format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    # === BRANCH CHECKOUT PHASE ===
    if rich_console:
        rich_console.rule("Preparing Workspace", style="cyan")

    # Checkout the branch from state
    branch_name = state.get("branch_name")
    if rich_console:
        with rich_console.spinner(f"Checking out branch: {branch_name}..."):
            result = subprocess.run(
                ["git", "checkout", branch_name], capture_output=True, text=True
            )
    else:
        result = subprocess.run(
            ["git", "checkout", branch_name], capture_output=True, text=True
        )

    if result.returncode != 0:
        error_msg = f"Failed to checkout branch {branch_name}: {result.stderr}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"❌ Failed to checkout branch {branch_name}"
            ),
        )
        sys.exit(1)

    logger.info(f"Checked out branch: {branch_name}")
    if rich_console:
        rich_console.success(f"Checked out branch: {branch_name}")

    # Get the plan file from state
    plan_file = state.get("plan_file")
    logger.info(f"Using plan file: {plan_file}")
    if rich_console:
        rich_console.info(f"Using plan file: {plan_file}")

    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Starting implementation phase"),
    )

    # === EXECUTING PLAN PHASE ===
    if rich_console:
        rich_console.rule("Executing Implementation Plan", style="cyan")

    # Implement the plan
    logger.info("Implementing solution")
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementing solution"),
    )

    if rich_console:
        with rich_console.spinner("Implementing solution..."):
            implement_response = implement_plan(plan_file, adw_id, logger, target_dir)
    else:
        implement_response = implement_plan(plan_file, adw_id, logger, target_dir)

    # Save implementation output to file regardless of success/failure
    log_dir = config.logs_dir / adw_id / "adw_build"
    os.makedirs(log_dir, exist_ok=True)

    log_file_path = log_dir / "implementation_details.md"
    try:
        with open(log_file_path, "w") as f:
            f.write(implement_response.output)
        logger.info(f"Implementation details saved to {log_file_path}")

        # Attach to Jira
        jira_add_attachment(issue_number, str(log_file_path))
        logger.info(f"Attached implementation details to issue {issue_number}")
    except Exception as e:
        logger.error(f"Failed to save/attach implementation details: {e}")

    if not implement_response.success:
        logger.error(f"Implementation failed. Output saved to {log_file_path}")

        # Post error to Jira
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_IMPLEMENTOR,
                f"❌ Error implementing solution. See attached implementation_details.md for full logs.",
            ),
        )

        if rich_console:
            rich_console.rule("⚠️ Implementation Verification Required", style="yellow")
            rich_console.print(
                "\n[bold yellow]The automated implementation step reported a failure, but the agent may have partially or fully completed the work.[/bold yellow]\n"
            )
            rich_console.print("Please follow these manual recovery steps:\n")

            steps = [
                f"1. [bold]Verify Implementation:[/bold] Check the log file at:\n   [blue]{log_file_path}[/blue]\n   Look for 'Implementation Complete' or similar success messages in the agent's output.",
                f'2. [bold]Commit Changes:[/bold] If the implementation is correct, stage and commit the changes:\n   [green]git add -A[/green]\n   [green]git commit -m "feat: Implementation for {issue_number}"[/green]',
                f"3. [bold]Push and PR:[/bold] Push the branch and create a Pull Request:\n   [green]git push -u origin {branch_name}[/green]\n   (Create PR manually on Bitbucket)",
                "4. [bold]Merge and Switch:[/bold] Merge the PR, then switch back to main:\n   [green]git checkout main[/green]\n   [green]git pull origin main[/green]",
            ]

            for step in steps:
                rich_console.print(step + "\n")

            rich_console.rule(style="yellow")
        else:
            # Fallback for non-rich console
            print("\n⚠️  Implementation Verification Required ⚠️")
            print(f"1. Verify Implementation: Check {log_file_path}")
            print(
                f"2. Commit Changes: git add -A && git commit -m 'feat: Implementation for {issue_number}'"
            )
            print(f"3. Push and PR: git push -u origin {branch_name}")
            print("4. Merge and Switch: git checkout main && git pull origin main\n")

        sys.exit(1)

    logger.debug(f"Implementation response saved to {log_file_path}")
    if rich_console:
        rich_console.success("Solution implemented successfully")

    # Generate E2E test scenario if auto-generation is enabled
    try:
        with open(plan_file, "r") as f:
            plan_content = f.read()

        from adw_modules.workflow_ops import generate_e2e_test_scenario

        # Extract feature name from issue title or plan
        feature_name = (
            issue.title if hasattr(issue, "title") else f"feature-{issue_number}"
        )

        e2e_file = generate_e2e_test_scenario(
            plan_content=plan_content,
            feature_name=feature_name,
            adw_id=adw_id,
            logger=logger,
            target_dir=target_dir,
        )

        if e2e_file:
            logger.info(f"Generated E2E test scenario: {e2e_file}")
            if rich_console:
                rich_console.info(f"Generated E2E test scenario: {e2e_file}")
        else:
            logger.debug("E2E test scenario generation skipped or failed")

    except Exception as e:
        logger.warning(f"Failed to generate E2E test scenario: {e}")
        # Don't fail the build for E2E generation issues

    jira_make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            AGENT_IMPLEMENTOR,
            "✅ Solution implemented. See attached implementation_details.md for execution logs.",
        ),
    )

    # Fetch issue details from Jira
    logger.info(f"Fetching issue {issue_number} from Jira")
    try:
        raw_jira_issue = jira_fetch_issue(issue_number)
        issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
    except Exception as e:
        error_msg = f"Failed to fetch issue {issue_number} from Jira: {e}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        sys.exit(1)

    # Get issue classification from state or classify if needed
    issue_command = state.get("issue_class")
    if not issue_command:
        logger.info("No issue classification in state, running classify_issue")
        from adw_modules.workflow_ops import classify_issue

        issue_command, error = classify_issue(issue, adw_id, logger)
        if error:
            logger.error(f"Error classifying issue: {error}")
            # Default to feature if classification fails
            issue_command = "/feature"
            logger.warning("Defaulting to /feature after classification error")
            if rich_console:
                rich_console.warning(
                    "Defaulting to /feature after classification error"
                )
        else:
            # Save the classification for future use
            state.update(issue_class=issue_command)
            state.save("adw_build")

    # === COMMITTING CHANGES PHASE ===
    if rich_console:
        rich_console.rule("Committing Changes", style="cyan")

    # Create commit message
    logger.info("Creating implementation commit")
    commit_msg, error = create_commit(
        AGENT_IMPLEMENTOR, issue, issue_command, adw_id, logger
    )

    if error:
        error_msg = f"Error creating commit message: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_IMPLEMENTOR, f"❌ Error creating commit message: {error}"
            ),
        )
        sys.exit(1)

    # Commit the implementation
    if rich_console:
        with rich_console.spinner("Committing implementation to git..."):
            success, error = commit_changes(commit_msg)
    else:
        success, error = commit_changes(commit_msg)

    if not success:
        error_msg = f"Error committing implementation: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_IMPLEMENTOR,
                f"❌ Error committing implementation: {error}",
            ),
        )
        sys.exit(1)

    logger.info(f"Committed implementation: {commit_msg}")
    if rich_console:
        rich_console.success("Implementation committed successfully")
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_IMPLEMENTOR, "✅ Implementation committed"),
    )

    # === FINALIZATION PHASE ===
    if rich_console:
        rich_console.rule("Finalizing Git Operations", style="cyan")

    # Finalize git operations (push and PR)
    if rich_console:
        with rich_console.spinner("Pushing changes and updating PR..."):
            finalize_git_operations(state, logger)
        rich_console.success("Git operations completed")
    else:
        finalize_git_operations(state, logger)

    logger.info("Implementation phase completed successfully")
    if rich_console:
        rich_console.rule("✅ Build Complete", style="green")
        rich_console.panel(
            f"Successfully completed implementation for issue {issue_number}\n"
            f"ADW ID: {adw_id}\n"
            f"Branch: {branch_name}\n"
            f"Target Directory: {target_dir}",
            title="Build Summary",
            style="green",
        )
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", "✅ Implementation phase completed"),
    )

    # Save final state
    state.save("adw_build")

    # Create Markdown summary
    summary_md = f"# Build Summary - {adw_id}\n\n"
    summary_md += (
        f"## Final State\n\n```json\n{json.dumps(state.data, indent=2)}\n```\n"
    )

    # Save summary to file
    log_dir = config.logs_dir / adw_id / "adw_build"
    os.makedirs(log_dir, exist_ok=True)
    summary_path = log_dir / "build_summary.md"

    try:
        with open(summary_path, "w") as f:
            f.write(summary_md)
        logger.info(f"Written build summary to {summary_path}")

        # Attach to Jira
        jira_add_attachment(issue_number, str(summary_path))
        logger.info(f"Attached build summary to issue {issue_number}")

        # Post short comment
        jira_make_issue_comment(
            issue_number,
            f"{adw_id}_ops: ✅ Build complete. See attached build_summary.md for details.",
        )
    except Exception as e:
        error_msg = f"Failed to attach build summary: {e}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        # Fallback to comment if attachment fails
        jira_make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 📋 Final implementation state (Fallback):\n```json\n{json.dumps(state.data, indent=2)}\n```",
        )


if __name__ == "__main__":
    main()
