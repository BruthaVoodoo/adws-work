#!/usr/bin/env python3
"""
ADWS CLI - Unified command-line interface for AI Developer Workflow System

Usage:
  adw plan <issue-key>
  adw build <adw-id> <issue-key>
  adw test <adw-id> <issue-key>
  adw review <adw-id> <issue-key>
  adw --help
  adw --version
"""

import sys
import os
import click
from typing import Optional

# Add scripts directory to path so relative imports work
sys.path.insert(0, os.path.dirname(__file__))

__version__ = "0.1.0"


@click.group()
@click.version_option(version=__version__, prog_name="adw")
def cli():
    """
    ADWS - AI Developer Workflow System

    Autonomous planning, building, testing, and reviewing for software development.

    Commands:
      plan      Generate implementation plan from Jira issue
      build     Implement the plan
      test      Run tests and auto-resolve failures
      review    Review implementation against criteria

    Examples:
      adw plan PROJ-123
      adw build a1b2c3d4 PROJ-123
      adw test a1b2c3d4 PROJ-123
      adw review a1b2c3d4 PROJ-123
    """
    pass


@cli.command()
@click.argument("issue_key")
@click.option(
    "--adw-id",
    default=None,
    help="ADW ID to use (generated automatically if not provided)",
)
def plan(issue_key: str, adw_id: Optional[str]) -> None:
    """
    Generate implementation plan from Jira issue.

    Args:
        ISSUE_KEY: Jira issue key (e.g., PROJ-123)
        --adw-id: Optional ADW ID (generated if not provided)

    This phase:
    1. Fetches the Jira issue details
    2. Classifies the issue type (/feature, /bug, /chore)
    3. Creates a feature branch
    4. Generates implementation plan using LLM
    5. Commits the plan
    6. Creates or updates pull request
    """
    from scripts.adw_plan import main as plan_main

    sys.argv = ["adw", issue_key]
    if adw_id:
        sys.argv.append(adw_id)

    try:
        plan_main()
    except SystemExit as e:
        if e.code != 0:
            raise


@cli.command()
@click.argument("adw_id")
@click.argument("issue_key")
def build(adw_id: str, issue_key: str) -> None:
    """
    Implement the plan by writing code.

    Args:
        ADW_ID: ADW ID from plan phase
        ISSUE_KEY: Jira issue key (e.g., PROJ-123)

    This phase:
    1. Loads the plan from previous phase
    2. Implements code changes
    3. Commits changes to git
    4. Verifies git operations
    5. Updates pull request
    """
    from scripts.adw_build import main as build_main

    sys.argv = ["adw", issue_key, adw_id]

    try:
        build_main()
    except SystemExit as e:
        if e.code != 0:
            raise


@cli.command()
@click.argument("adw_id")
@click.argument("issue_key")
def test(adw_id: str, issue_key: str) -> None:
    """
    Run tests and attempt auto-resolution of failures.

    Args:
        ADW_ID: ADW ID from previous phases
        ISSUE_KEY: Jira issue key (e.g., PROJ-123)

    This phase:
    1. Executes configured test suite
    2. Parses test results
    3. Auto-attempts resolution of failures (up to 3 attempts)
    4. Generates test report
    """
    from scripts.adw_test import main as test_main

    sys.argv = ["adw", issue_key, adw_id]

    try:
        test_main()
    except SystemExit as e:
        if e.code != 0:
            raise


@cli.command()
@click.argument("adw_id")
@click.argument("issue_key")
def review(adw_id: str, issue_key: str) -> None:
    """
    Review implementation against criteria.

    Args:
        ADW_ID: ADW ID from previous phases
        ISSUE_KEY: Jira issue key (e.g., PROJ-123)

    This phase:
    1. Fetches implementation details
    2. Compares against original plan
    3. Validates acceptance criteria met
    4. Generates review findings
    5. Plans patches for issues
    """
    from scripts.adw_review import main as review_main

    sys.argv = ["adw", issue_key, adw_id]

    try:
        review_main()
    except SystemExit as e:
        if e.code != 0:
            raise


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n\nInterrupted by user.", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nError: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
