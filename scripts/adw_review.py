#!/usr/bin/env -S uv run
# /// script
# dependencies = ["python-dotenv", "pydantic", "boto3>=1.26.0", "requests", "jira", "rich", "pyyaml"]
# ///

"""
ADW Review - AI Developer Workflow for agentic review

Usage:
  uv run adw_review.py <issue-number> <adw-id> [--skip-resolution]

Workflow:
1. Find spec file from current branch
2. Review implementation against specification
3. Capture screenshots of critical functionality
4. If issues found and --skip-resolution not set:
   - Create patch plans for issues
   - Implement resolutions
5. Post results as commit message
6. Commit review results
7. Push and update PR
"""

import sys
import os
import logging
import json
import subprocess
import shutil
from typing import Optional, List, Tuple
from dotenv import load_dotenv

from adw_modules.state import ADWState
from adw_modules.git_ops import commit_changes, finalize_git_operations
from adw_modules.jira import (
    jira_fetch_issue,
    jira_make_issue_comment,
    jira_add_attachment,
)
from adw_modules.workflow_ops import (
    create_commit,
    format_issue_message,
    ensure_adw_id,
    implement_plan,
    create_patch_plan,
    find_spec_file,
    AGENT_IMPLEMENTOR,
)
from adw_modules.utils import setup_logger, parse_json, get_rich_console_instance, load_prompt
from adw_modules.data_types import (
    GitHubIssue,
    JiraIssue,
    AgentTemplateRequest,
    ReviewResult,
    ReviewIssue,
    AgentPromptResponse,
)
from adw_modules.agent import save_prompt
from adw_modules.config import config

# Agent name constants
AGENT_REVIEWER = "reviewer"
AGENT_REVIEW_PATCH_PLANNER = "review_patch_planner"
AGENT_REVIEW_PATCH_IMPLEMENTOR = "review_patch_implementor"

# Maximum number of review retry attempts after resolution
MAX_REVIEW_RETRY_ATTEMPTS = 3


def check_env_vars(logger: Optional[logging.Logger] = None) -> None:
    """Check that required tools are available."""
    if not shutil.which("copilot"):
        error_msg = "Error: 'copilot' CLI not found in PATH."
        if logger:
            logger.error(error_msg)
        else:
            console = get_rich_console_instance()
            if console:
                console.error(error_msg)
            else:
                print(error_msg, file=sys.stderr)
        sys.exit(1)


def run_review(
    spec_file: str,
    adw_id: str,
    logger: logging.Logger,
) -> ReviewResult:
    """Run the review using GitHub Copilot CLI."""
    
    # Load the review prompt template
    prompt_template = load_prompt("review")
    
    # Format the prompt with the required parameters
    prompt = prompt_template.replace("{adw_id}", adw_id)
    prompt = prompt.replace("{spec_file}", spec_file)
    prompt = prompt.replace("{agent_name}", AGENT_REVIEWER)
    
    # Save prompt for audit
    save_prompt(
        prompt, 
        adw_id, 
        AGENT_REVIEWER
    )

    logger.debug(f"Running review via Copilot CLI...")

    try:
        command = [
            "copilot",
            "-p",
            prompt,
            "--allow-all-tools",
            "--allow-all-paths",
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        
        output = result.stdout
        logger.debug(f"Copilot output preview: {output[:500]}...")
        
        if result.returncode != 0:
            error_msg = f"Copilot execution failed: {result.stderr}"
            logger.error(error_msg)
            return ReviewResult(
                success=False,
                review_issues=[
                    ReviewIssue(
                        review_issue_number=1,
                        screenshot_path="",
                        issue_description=f"Copilot execution error: {error_msg}",
                        issue_resolution="Fix Copilot CLI execution environment",
                        issue_severity="blocker",
                    )
                ],
            )

        # Parse the review result
        result = parse_json(output, ReviewResult)
        return result

    except Exception as e:
        logger.error(f"Error running review: {e}")
        return ReviewResult(
            success=False,
            review_issues=[
                ReviewIssue(
                    review_issue_number=1,
                    screenshot_path="",
                    issue_description=f"Review execution exception: {str(e)}",
                    issue_resolution="Fix the review script error",
                    issue_severity="blocker",
                )
            ],
        )


def resolve_review_issues(
    review_issues: List[ReviewIssue],
    spec_file: str,
    state: ADWState,
    logger: logging.Logger,
    issue_number: str,
    iteration: int = 1,
) -> Tuple[int, int]:
    """Resolve review issues by creating and implementing patch plans.
    Returns (resolved_count, failed_count)."""

    resolved_count = 0
    failed_count = 0
    adw_id = state.get("adw_id")

    # Filter to only handle blocker issues
    blocker_issues = [i for i in review_issues if i.issue_severity == "blocker"]

    if not blocker_issues:
        logger.info("No blocker issues to resolve")
        return 0, 0

    logger.info(f"Found {len(blocker_issues)} blocker issues to resolve")
    jira_make_issue_comment(
        issue_number,
        format_issue_message(
            adw_id,
            "ops",
            f"🔧 Attempting to resolve {len(blocker_issues)} blocker issues",
        ),
    )

    for idx, issue in enumerate(blocker_issues):
        # Use rich_console step to mark issue resolution steps if available
        if get_rich_console_instance():
            get_rich_console_instance().step(f"Resolving blocker issue {idx + 1}/{len(blocker_issues)}: Issue #{issue.review_issue_number}")
        else:
            logger.info(
                f"\n=== Resolving blocker issue {idx + 1}/{len(blocker_issues)}: Issue #{issue.review_issue_number} ==="
            )

        # Create and implement patch
        # Prepare unique agent names with iteration and issue number for tracking
        agent_name_planner = f"{AGENT_REVIEW_PATCH_PLANNER}_{iteration}_{issue.review_issue_number}"
        agent_name_implementor = f"{AGENT_REVIEW_PATCH_IMPLEMENTOR}_{iteration}_{issue.review_issue_number}"
        
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                agent_name_planner,
                f"📝 Creating patch plan for issue #{issue.review_issue_number}: {issue.issue_description}",
            ),
        )

        # Create patch plan using the new workflow operation
        if rich_console:
            with rich_console.spinner(f"Creating patch plan for issue #{issue.review_issue_number}..."):
                patch_file = create_patch_plan(
                    issue=issue,
                    spec_path=spec_file,
                    adw_id=adw_id,
                    logger=logger
                )
        else:
            patch_file = create_patch_plan(
                issue=issue,
                spec_path=spec_file,
                adw_id=adw_id,
                logger=logger
            )

        if not patch_file:
            failed_count += 1
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name_planner,
                    f"❌ Failed to create patch plan for issue #{issue.review_issue_number}",
                ),
            )
            continue

        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, agent_name_planner, f"✅ Created patch plan: {patch_file}"
            ),
        )

        # Implement the patch plan using the existing implement_plan function
        target_dir = str(config.project_root)
        
        if rich_console:
            with rich_console.spinner(f"Implementing patch for issue #{issue.review_issue_number}..."):
                implement_response = implement_plan(patch_file, adw_id, logger, target_dir)
        else:
            implement_response = implement_plan(patch_file, adw_id, logger, target_dir)

        # Check implementation result
        if implement_response.success:
            resolved_count += 1
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name_implementor,
                    f"✅ Successfully resolved issue #{issue.review_issue_number}",
                ),
            )
            logger.info(f"Successfully resolved issue #{issue.review_issue_number}")
        else:
            failed_count += 1
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    agent_name_implementor,
                    f"❌ Failed to implement patch for issue #{issue.review_issue_number}: {implement_response.output}",
                ),
            )
            logger.error(
                f"Failed to implement patch for issue #{issue.review_issue_number}"
            )

    return resolved_count, failed_count


def process_screenshots(
    review_result: ReviewResult,
    adw_id: str,
    state: ADWState,
    logger: logging.Logger,
) -> None:
    """
    Process screenshots and populate URL fields in the review result.
    
    Note: R2 upload functionality has been removed as legacy dependency.
    Screenshots will be referenced by their local paths only.
    
    Args:
        review_result: The review result containing screenshots to process
        adw_id: ADW workflow ID
        state: ADWState instance for saving screenshot paths
        logger: Logger instance
    """
    # Process screenshots if available
    if review_result.screenshots or any(
        issue.screenshot_path for issue in review_result.review_issues
    ):
        logger.info("Processing review screenshots")

        # For now, we'll use the local paths as the URLs (legacy R2 upload removed)
        # This maintains compatibility while removing the dependency
        review_result.screenshot_urls = list(review_result.screenshots)
        
        # Set screenshot_url for each ReviewIssue to the local path
        for review_issue in review_result.review_issues:
            if review_issue.screenshot_path:
                review_issue.screenshot_url = review_issue.screenshot_path

        logger.info(f"Screenshot processing complete - {len(review_result.screenshots)} files processed")

    # Save screenshot paths to state for documentation workflow
    if review_result.screenshot_urls:
        state.update(review_screenshots=review_result.screenshot_urls)
        state.save("adw_review")
        logger.info(
            f"Saved {len(review_result.screenshot_urls)} screenshot paths to state for documentation"
        )


def format_review_comment(review_result: ReviewResult) -> str:
    """Format review result for GitHub issue comment."""
    parts = []

    if review_result.success:
        parts.append("## ✅ Review Passed")
        parts.append("")
        parts.append("The implementation matches the specification.")
        parts.append("")

        if review_result.screenshot_urls:
            parts.append("### Screenshots")
            parts.append("")
            for i, screenshot_url in enumerate(review_result.screenshot_urls):
                if screenshot_url:  # Only show if URL was successfully generated
                    filename = screenshot_url.split("/")[-1]
                    parts.append(f"![{filename}]({screenshot_url})")
            parts.append("")
    else:
        parts.append("## ❌ Review Issues Found")
        parts.append("")
        parts.append(f"Found {len(review_result.review_issues)} issues during review:")
        parts.append("")

        # Group by severity
        blockers = [
            i for i in review_result.review_issues if i.issue_severity == "blocker"
        ]
        tech_debts = [
            i for i in review_result.review_issues if i.issue_severity == "tech_debt"
        ]
        skippables = [
            i for i in review_result.review_issues if i.issue_severity == "skippable"
        ]

        if blockers:
            parts.append("### 🚨 Blockers")
            parts.append("")
            for issue in blockers:
                parts.append(
                    f"**Issue #{issue.review_issue_number}**: {issue.issue_description}"
                )
                parts.append(f"- **Resolution**: {issue.issue_resolution}")
                if issue.screenshot_url:
                    filename = issue.screenshot_url.split("/")[-1]
                    parts.append(f"- **Screenshot**:")
                    parts.append(f"  ![{filename}]({issue.screenshot_url})")
                parts.append("")

        if tech_debts:
            parts.append("### ⚠️ Tech Debt")
            parts.append("")
            for issue in tech_debts:
                parts.append(
                    f"**Issue #{issue.review_issue_number}**: {issue.issue_description}"
                )
                parts.append(f"- **Resolution**: {issue.issue_resolution}")
                if issue.screenshot_url:
                    filename = issue.screenshot_url.split("/")[-1]
                    parts.append(f"- **Screenshot**:")
                    parts.append(f"  ![{filename}]({issue.screenshot_url})")
                parts.append("")

        if skippables:
            parts.append("### ℹ️ Skippable")
            parts.append("")
            for issue in skippables:
                parts.append(
                    f"**Issue #{issue.review_issue_number}**: {issue.issue_description}"
                )
                parts.append(f"- **Resolution**: {issue.issue_resolution}")
                if issue.screenshot_url:
                    filename = issue.screenshot_url.split("/")[-1]
                    parts.append(f"- **Screenshot**:")
                    parts.append(f"  ![{filename}]({issue.screenshot_url})")
                parts.append("")

    # Add JSON payload
    parts.append("### Review Data")
    parts.append("")
    parts.append("```json")
    parts.append(review_result.model_dump_json(indent=2))
    parts.append("```")

    return "\n".join(parts)


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Get rich console instance early for error output
    rich_console = get_rich_console_instance()

    # Check for --skip-resolution flag
    skip_resolution = "--skip-resolution" in sys.argv
    if skip_resolution:
        sys.argv.remove("--skip-resolution")

    # Parse command line args
    # adw-id is REQUIRED for review to find the correct state and spec
    if len(sys.argv) < 3:
        if rich_console:
            rich_console.error("Usage: uv run adw_review.py <issue-number> <adw-id> [--skip-resolution]")
            rich_console.error("adw-id is required to locate the spec file and state")
        else:
            print("Usage: uv run adw_review.py <issue-number> <adw-id> [--skip-resolution]")
            print("\nadw-id is required to locate the spec file and state")
        sys.exit(1)

    issue_number = sys.argv[1]
    adw_id = sys.argv[2]

    # Get rich console instance
    rich_console = get_rich_console_instance()
    if rich_console:
        rich_console.rule(f"ADW Review - Issue {issue_number}", style="blue")
        rich_console.info(f"ADW ID: {adw_id}")

    # Set up temp logger for initialization (console only)
    temp_logger = setup_logger(adw_id, "adw_review", enable_file_logging=False)
    temp_logger.info(f"ADW Review initializing - ID: {adw_id}, Issue: {issue_number}")

    # === LOADING ISSUE DATA PHASE ===
    if rich_console:
        rich_console.rule("Loading Issue Data", style="cyan")

    # Fetch issue details from Jira
    temp_logger.info(f"Fetching issue {issue_number} from Jira")
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
        temp_logger.error(error_msg)
        if rich_console:
            rich_console.error(error_msg)
        sys.exit(1)
    
    # Set up actual logger with valid ADW ID
    logger = setup_logger(adw_id, "adw_review")
    logger.info(f"ADW Review starting - ID: {adw_id}, Issue: {issue_number}")

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
            rich_console.success("Found existing ADW state - resuming review")
        jira_make_issue_comment(
            issue_number,
            f"{adw_id}_ops: 🔍 Found existing state - starting review\n```json\n{json.dumps(state.data, indent=2)}\n```",
        )
    else:
        # No existing state found
        error_msg = f"No state found for ADW ID: {adw_id}"
        logger.error(error_msg)
        logger.error("Run adw_plan.py first to create the state")
        if rich_console:
            rich_console.error(error_msg)
            rich_console.error("Run adw_plan.py first to create the state")
        sys.exit(1)

    # Validate environment
    check_env_vars(logger)

    # Ensure we have required state fields
    if not state.get("branch_name"):
        error_msg = "No branch name in state - run adw_plan.py first"
        logger.error(error_msg)
        jira_make_issue_comment(
            issue_number, format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    # Checkout the branch from state
    branch_name = state.get("branch_name")
    result = subprocess.run(
        ["git", "checkout", branch_name], capture_output=True, text=True
    )
    if result.returncode != 0:
        logger.error(f"Failed to checkout branch {branch_name}: {result.stderr}")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, "ops", f"❌ Failed to checkout branch {branch_name}"
            ),
        )
        sys.exit(1)
    logger.info(f"Checked out branch: {branch_name}")

    jira_make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Starting review phase")
    )

    # Find the spec file
    spec_file = find_spec_file(state, logger)
    if not spec_file:
        error_msg = "Could not find spec file for review"
        logger.error(error_msg)
        jira_make_issue_comment(
            issue_number, format_issue_message(adw_id, "ops", f"❌ {error_msg}")
        )
        sys.exit(1)

    logger.info(f"Using spec file: {spec_file}")
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, "ops", f"✅ Found spec file: {spec_file}"),
    )

    # Run review with resolution retry loop
    attempt = 0
    max_attempts = MAX_REVIEW_RETRY_ATTEMPTS if not skip_resolution else 1

    while attempt < max_attempts:
        attempt += 1
        logger.info(f"\n=== Review Attempt {attempt}/{max_attempts} ===")

        # === REVIEWING IMPLEMENTATION PHASE ===
        if rich_console:
            rich_console.rule("Reviewing Implementation", style="cyan")

        # Run the review
        logger.info("Running review against specification")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id,
                AGENT_REVIEWER,
                f"\u2705 Reviewing implementation against specification (attempt {attempt}/{max_attempts})",
            ),
        )

        if rich_console:
            with rich_console.spinner("Running AI review analysis..."):
                review_result = run_review(spec_file, adw_id, logger)
        else:
            review_result = run_review(spec_file, adw_id, logger)

        # Process screenshots (legacy R2 upload removed)
        process_screenshots(review_result, adw_id, state, logger)

        # Format and post review results
        review_comment = format_review_comment(review_result)
        jira_make_issue_comment(
            issue_number, format_issue_message(adw_id, AGENT_REVIEWER, review_comment)
        )

        # Save review summary to file and attach to Jira
        try:
            log_dir = config.logs_dir / adw_id
            os.makedirs(log_dir, exist_ok=True)
            
            summary_file_path = log_dir / f"review_results_{adw_id}_attempt_{attempt}.md"
            with open(summary_file_path, "w") as f:
                f.write(f"# Review Results (Attempt {attempt})\n\n{review_comment}")
                
            logger.info(f"Saved review summary to {summary_file_path}")
            
            jira_add_attachment(issue_number, str(summary_file_path))
            logger.info(f"Attached review summary to issue #{issue_number}")
            
        except Exception as e:
            logger.error(f"Failed to attach review summary: {e}")

        # Log summary
        if review_result.success:
            logger.info(
                "Review passed - implementation matches specification (no blocking issues)"
            )
            break
        else:
            blocker_count = sum(
                1 for i in review_result.review_issues if i.issue_severity == "blocker"
            )
            logger.warning(
                f"Review found {len(review_result.review_issues)} issues ({blocker_count} blockers)"
            )

            # If this is the last attempt or no blockers or resolution is skipped, stop
            if attempt == max_attempts or blocker_count == 0 or skip_resolution:
                if skip_resolution and blocker_count > 0:
                    logger.info(
                        f"Skipping resolution workflow for {blocker_count} blocker issues (--skip-resolution flag set)"
                    )
                    jira_make_issue_comment(
                        issue_number,
                        format_issue_message(
                            adw_id,
                            "ops",
                            f"⚠️ Skipping resolution for {blocker_count} blocker issues",
                        ),
                    )
                break

            # === RESOLVING ISSUES PHASE ===
            if rich_console:
                rich_console.rule("Resolving Issues", style="cyan")

            logger.info("\n=== Starting resolution workflow ===")
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"🔧 Starting resolution workflow for {blocker_count} blocker issues",
                ),
            )

            # Resolve the issues
            resolved_count, failed_count = resolve_review_issues(
                review_result.review_issues,
                spec_file,
                state,
                logger,
                issue_number,
                iteration=attempt,
            )

            # Report resolution results
            if resolved_count > 0:
                jira_make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        f"✅ Resolution complete: {resolved_count} issues resolved, {failed_count} failed",
                    ),
                )

                # === COMMITTING RESULTS PHASE ===
                if rich_console:
                    rich_console.rule("Committing Results", style="cyan")

                # Commit the resolution changes
                logger.info("Committing resolution changes")
                raw_review_issue = jira_fetch_issue(issue_number)
                review_issue_pydantic = JiraIssue.from_raw_jira_issue(raw_review_issue)
                issue_command = state.get("issue_class", "/chore")

                # Use a generic review patch implementor name for the commit
                commit_msg, error = create_commit(
                    AGENT_REVIEW_PATCH_IMPLEMENTOR, review_issue_pydantic, issue_command, adw_id, logger
                )

                if not error:
                    if rich_console:
                        with rich_console.spinner("Committing resolution to git..."):
                            success, error = commit_changes(commit_msg)
                    else:
                        success, error = commit_changes(commit_msg)

                    if success:
                        logger.info(f"Committed resolution: {commit_msg}")
                        jira_make_issue_comment(
                            issue_number,
                            format_issue_message(
                                adw_id,
                                AGENT_REVIEW_PATCH_IMPLEMENTOR,
                                "✅ Resolution changes committed",
                            ),
                        )
                    else:
                        logger.error(f"Error committing resolution: {error}")
                        jira_make_issue_comment(
                            issue_number,
                            format_issue_message(
                                adw_id,
                                AGENT_REVIEW_PATCH_IMPLEMENTOR,
                                f"❌ Error committing resolution: {error}",
                            ),
                        )

                # Continue to next iteration to re-review
                logger.info(
                    f"\n=== Preparing for re-review after resolving {resolved_count} issues ==="
                )
                jira_make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        AGENT_REVIEWER,
                        f"🔄 Re-running review (attempt {attempt + 1}/{max_attempts})...",
                    ),
                )
            else:
                # No issues were resolved, no point in retrying
                logger.info("No issues were resolved, stopping retry attempts")
                jira_make_issue_comment(
                    issue_number,
                    format_issue_message(
                        adw_id,
                        "ops",
                        f"❌ Resolution failed: Could not resolve any of the {blocker_count} blocker issues",
                    ),
                )
                break

    # Log final attempt status
    if attempt == max_attempts and not review_result.success:
        blocker_count = sum(
            1 for i in review_result.review_issues if i.issue_severity == "blocker"
        )
        if blocker_count > 0:
            logger.warning(
                f"Reached maximum retry attempts ({max_attempts}) with {blocker_count} blocking issues remaining"
            )
            jira_make_issue_comment(
                issue_number,
                format_issue_message(
                    adw_id,
                    "ops",
                    f"⚠️ Reached maximum retry attempts ({max_attempts}) with {blocker_count} blocking issues",
                ),
            )

    logger.info("Fetching issue data for commit message")
    raw_review_issue = jira_fetch_issue(issue_number)
    review_issue_pydantic = JiraIssue.from_raw_jira_issue(raw_review_issue)

    # Get issue classification from state
    issue_command = state.get("issue_class", "/chore")

    # Create commit message
    logger.info("Creating review commit")
    commit_msg, error = create_commit(
        AGENT_REVIEWER, review_issue_pydantic, issue_command, adw_id, logger
    )

    if error:
        logger.error(f"Error creating commit message: {error}")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_REVIEWER, f"❌ Error creating commit message: {error}"
            ),
        )
        sys.exit(1)

    # Commit the review results
    success, error = commit_changes(commit_msg)

    if not success:
        logger.error(f"Error committing review: {error}")
        jira_make_issue_comment(
            issue_number,
            format_issue_message(
                adw_id, AGENT_REVIEWER, f"❌ Error committing review: {error}"
            ),
        )
        sys.exit(1)

    logger.info(f"Committed review: {commit_msg}")
    jira_make_issue_comment(
        issue_number,
        format_issue_message(adw_id, AGENT_REVIEWER, "✅ Review committed"),
    )

    # Finalize git operations (push and PR)
    finalize_git_operations(state, logger)

    logger.info("Review phase completed successfully")
    jira_make_issue_comment(
        issue_number, format_issue_message(adw_id, "ops", "✅ Review phase completed")
    )

    # Save final state
    state.save("adw_review")

    # Output state for chaining
    state.to_stdout()

    # Display a formatted summary panel
    try:
        blockers = sum(1 for i in review_result.review_issues if i.issue_severity == "blocker")
        total_issues = len(review_result.review_issues)
        status = "PASSED" if review_result.success else "FAILED"
        panel_text = (
            f"Status: {status}\n"
            f"Total Issues: {total_issues}\n"
            f"Blocking Issues: {blockers}\n"
            f"ADW ID: {adw_id}\n"
        )
        if rich_console:
            rich_console.rule("Review Summary", style="cyan")
            # Match Build/Test styling: green for pass, red for fail
            rich_console.panel(panel_text, title="Review Summary", style=("green" if review_result.success else "red"))
        else:
            print(f"Review Summary - Status: {status}, Total Issues: {total_issues}, Blocking: {blockers}")
    except Exception:
        # If summary rendering fails, continue without blocking
        pass

    # Exit with appropriate code based on review result
    if not review_result.success:
        blocker_count = sum(
            1 for i in review_result.review_issues if i.issue_severity == "blocker"
        )
        if blocker_count > 0:
            logger.error(f"Review failed with {blocker_count} blocking issues")
            sys.exit(1)
        else:
            logger.warning("Review found non-blocking issues")
            # Exit successfully since no blockers


if __name__ == "__main__":
    main()