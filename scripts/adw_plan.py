#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "boto3", "requests", "jira", "rich", "pyyaml"]
# ///

"""
ADW Plan - AI Developer Workflow for autonomous planning

Usage:
  uv run adw_plan.py <issue-number> [adw-id]

Workflow:
1. Fetch Jira issue details
2. Classify issue type (/chore, /bug, /feature)
3. Create feature branch
4. Generate implementation plan
5. Commit plan
6. Push and create/update PR
"""

import sys
import os
import logging
import json
from typing import Optional
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import create_branch, commit_changes, finalize_git_operations
from adw_modules import issue_ops
from adw_modules.workflow_ops import (
    classify_issue,
    build_plan,
    generate_branch_name,
    create_commit,
    format_issue_message,
    ensure_adw_id,
    AGENT_PLANNER,
)
from adw_modules.utils import setup_logger, get_rich_console_instance
from adw_modules.data_types import IssueClassSlashCommand, JiraIssue
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
    if len(sys.argv) < 2:
        if rich_console:
            rich_console.error("Usage: uv run adw_plan.py <issue-number> [adw-id]")
        else:
            print("Usage: uv run adw_plan.py <issue-number> [adw-id]")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2] if len(sys.argv) > 2 else None

    # Generate ADW ID if not provided
    if not adw_id:
        from adw_modules.utils import make_adw_id

        adw_id = make_adw_id()
        if rich_console:
            rich_console.success(f"Created new ADW ID: {adw_id}")
        else:
            print(f"Created new ADW ID: {adw_id}")

    # Rich console header
    if rich_console:
        rich_console.rule(f"ADW Plan - Issue {issue_number}", style="blue")
        rich_console.info(f"ADW ID: {adw_id}")

    # Set up logger with ADW ID
    logger = setup_logger(adw_id, "adw_plan")
    logger.info(f"ADW Plan starting - ID: {adw_id}, Issue: {issue_number}")

    # Validate environment
    check_env_vars(logger)

    # === FETCHING ISSUE PHASE ===
    if rich_console:
        rich_console.rule("Fetching Issue Details", style="cyan")

    logger.info(f"Fetching issue {issue_number} from Jira")
    try:
        if rich_console:
            with rich_console.spinner(f"Fetching issue {issue_number} from Jira..."):
                raw_jira_issue = issue_ops.fetch_issue(issue_number)
                # issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
                issue = raw_jira_issue
            rich_console.success(f"Successfully fetched issue: {issue.title}")
        else:
            raw_jira_issue = issue_ops.fetch_issue(issue_number)
            # issue = JiraIssue.from_raw_jira_issue(raw_jira_issue)
            issue = raw_jira_issue
    except Exception as e:
        error_msg = f"Failed to fetch issue {issue_number} from Jira: {e}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        sys.exit(1)

    logger.debug(f"Fetched issue: {issue.model_dump_json(indent=2, by_alias=True)}")

    # NOW create state
    state = ADWState(adw_id)
    state.update(adw_id=adw_id, issue_number=issue_number)
    state.save("adw_plan_init")
    logger.info(f"Initialized state")

    issue_ops.add_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Starting planning phase")
    )

    # === ISSUE CLASSIFICATION PHASE ===
    if rich_console:
        rich_console.rule("Classifying Issue", style="cyan")

    if rich_console:
        with rich_console.spinner("Classifying issue type..."):
            issue_command, error = classify_issue(issue, adw_id, logger)
    else:
        issue_command, error = classify_issue(issue, adw_id, logger)

    if error:
        error_msg = f"Error classifying issue: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        issue_ops.add_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Error classifying issue: {error}"),
        )
        sys.exit(1)

    state.update(issue_class=issue_command)
    state.save("adw_plan")
    logger.info(f"Issue classified as: {issue_command}")
    if rich_console:
        rich_console.success(f"Issue classified as: {issue_command}")
    issue_ops.add_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Issue classified as: {issue_command}"),
    )

    # === BRANCH CREATION PHASE ===
    if rich_console:
        rich_console.rule("Creating Branch", style="cyan")

    # Generate branch name
    branch_name, error = generate_branch_name(issue, issue_command, adw_id, logger)

    if error:
        error_msg = f"Error generating branch name: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        issue_ops.add_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"❌ Error generating branch name: {error}"
            ),
        )
        sys.exit(1)

    # Create git branch
    if rich_console:
        with rich_console.spinner(f"Creating git branch: {branch_name}..."):
            success, error = create_branch(branch_name)
    else:
        success, error = create_branch(branch_name)

    if not success:
        error_msg = f"Error creating branch: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        issue_ops.add_comment(
            issue_number,
            format_issue_message(adw_id, "ops", f"❌ Error creating branch: {error}"),
        )
        sys.exit(1)

    state.update(branch_name=branch_name)
    state.save("adw_plan")
    logger.info(f"Working on branch: {branch_name}")
    if rich_console:
        rich_console.success(f"Working on branch: {branch_name}")
    issue_ops.add_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Working on branch: {branch_name}"),
    )

    # === PLAN BUILDING PHASE ===
    if rich_console:
        rich_console.rule("Building Implementation Plan", style="cyan")

    logger.info("Building implementation plan")
    issue_ops.add_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, "✅ Building implementation plan"),
    )

    if rich_console:
        with rich_console.spinner("Generating implementation plan..."):
            # Force cast to satisfy mypy for now, or update build_plan signature later
            plan_response = build_plan(issue, str(issue_command), adw_id, logger)
    else:
        plan_response = build_plan(issue, str(issue_command), adw_id, logger)

    if not plan_response.success:
        error_msg = f"Error building plan: {plan_response.output}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        else:
            print(f"Error: {error_msg}")
        issue_ops.add_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_PLANNER, f"❌ Error building plan: {plan_response.output}"
            ),
        )
        sys.exit(1)

    logger.debug(f"Plan response: {plan_response.output}")
    if rich_console:
        rich_console.success("Implementation plan created successfully")
    issue_ops.add_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_PLANNER, "✅ Implementation plan created"),
    )

    # The plan file path is now deterministic based on the issue type and IDs
    issue_type = issue_command.strip("/")

    plan_file_path = (
        config.ai_docs_dir / "specs" / issue_type / f"{issue_number}-{adw_id}-plan.md"
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(plan_file_path), exist_ok=True)

    # Extract the actual plan content from the LLM response
    plan_content = plan_response.output.strip()

    if not plan_content:
        error_msg = "Could not extract plan content from the LLM output."
        logger.error(f"{error_msg} Full response:\n{plan_response.output}")
        if rich_console:
            rich_console.error(error_msg)
        sys.exit(1)

    # === PLAN FILE CREATION PHASE ===
    if rich_console:
        rich_console.rule("Creating Plan File", style="cyan")

    # We need to write this content to the plan file
    try:
        with open(plan_file_path, "w") as f:
            f.write(plan_content)
        logger.info(f"Plan content written to {plan_file_path}")
        if rich_console:
            rich_console.success(f"Plan file created: {plan_file_path}")

        # Attach plan to Jira
        try:
            issue_ops.add_attachment(issue_number, str(plan_file_path))
            logger.info(f"Attached plan file to issue {issue_number}")
        except Exception as e:
            logger.error(f"Failed to attach plan file to Jira: {e}")
            if rich_console:
                rich_console.warning(f"Failed to attach plan file to Jira: {e}")

    except IOError as e:
        error_msg = f"Failed to write plan file: {e}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        sys.exit(1)

    state.update(plan_file=str(plan_file_path))
    state.save("adw_plan")
    logger.info(f"Plan file created: {plan_file_path}")
    issue_ops.add_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Plan file created: {plan_file_path}"),
    )

    # === COMMIT PHASE ===
    if rich_console:
        rich_console.rule("Committing Plan", style="cyan")

    logger.info("Creating plan commit")
    commit_msg, error = create_commit(
        AGENT_PLANNER, issue, issue_command, adw_id, logger
    )

    if error:
        error_msg = f"Error creating commit message: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        issue_ops.add_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_PLANNER, f"❌ Error creating commit message: {error}"
            ),
        )
        sys.exit(1)

    # Commit the plan
    if rich_console:
        with rich_console.spinner("Committing plan to git..."):
            success, error = commit_changes(commit_msg)
    else:
        success, error = commit_changes(commit_msg)

    if not success:
        error_msg = f"Error committing plan: {error}"
        logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        issue_ops.add_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_PLANNER, f"❌ Error committing plan: {error}"
            ),
        )
        sys.exit(1)

    logger.info(f"Committed plan: {commit_msg}")
    if rich_console:
        rich_console.success("Plan committed successfully")
    issue_ops.add_comment(
        issue_number, format_issue_message(adw_id, AGENT_PLANNER, "✅ Plan committed")
    )

    # === FINALIZATION PHASE ===
    if rich_console:
        rich_console.rule("Finalizing Git Operations", style="cyan")

    # Finalize git operations (push and PR)
    if rich_console:
        with rich_console.spinner("Pushing changes and creating/updating PR..."):
            finalize_git_operations(state, logger)
        rich_console.success("Git operations completed")
    else:
        finalize_git_operations(state, logger)

    logger.info("Planning phase completed successfully")
    if rich_console:
        rich_console.rule("✅ Planning Complete", style="green")
        rich_console.panel(
            f"Successfully completed planning for issue {issue_number}\n"
            f"ADW ID: {adw_id}\n"
            f"Branch: {branch_name}\n"
            f"Issue Type: {issue_command}",
            title="Planning Summary",
            style="green",
        )
    issue_ops.add_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Planning phase completed")
    )

    # Save final state
    state.save("adw_plan")

    # Post final state summary to issue
    issue_ops.add_comment(
        issue_number,
        f"{adw_id}_ops: 📋 Final planning state:\n```json\n{json.dumps(state.data, indent=2)}\n```",
    )


if __name__ == "__main__":
    main()
