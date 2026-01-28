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
import io
import click
from typing import Optional

# Rich formatting for improved --help output
from rich.console import Console
from rich.table import Table
from rich.text import Text


class RichGroup(click.Group):
    """Custom click Group that renders a Rich-styled help message.

    Overrides get_help to return ANSI-colored help text produced by Rich.
    """

    def get_help(self, ctx: click.Context) -> str:
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=True, color_system="truecolor")

        # Title / header
        console.rule("[bold cyan]ADWS - AI Developer Workflow System", style="cyan")
        console.print(f"[bold]Version:[/bold] {__version__}\n")

        # Long help / description
        if self.help:
            console.print(self.help)
            console.print()

        # Usage
        console.print("[bold yellow]Usage[/bold yellow]")
        try:
            # Use Click's context usage to build a reliable usage string
            usage = ctx.get_usage()
        except Exception:
            usage = "adw [COMMAND] [OPTIONS]"
        console.print(Text(usage, style="green"))
        console.print()

        # Commands table
        console.print("[bold magenta]Commands[/bold magenta]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="white")

        for name, cmd in self.commands.items():
            # hide internal/hidden commands
            if getattr(cmd, "hidden", False):
                continue
            desc = cmd.get_short_help_str() or ""
            table.add_row(name, desc)

        console.print(table)
        console.print()

        # Footer with example hint
        console.print(
            "[bold blue]Tip[/bold blue] Type [green]adw COMMAND --help[/green] for command-specific options."
        )
        console.print()

        return buf.getvalue()


# Add scripts directory to path so relative imports work
sys.path.insert(0, os.path.dirname(__file__))

__version__ = "0.1.0"


@click.group(cls=RichGroup)
@click.version_option(version=__version__, prog_name="adw")
def cli():
    """
    ADWS - AI Developer Workflow System

    Autonomous planning, building, testing, and reviewing for software development.

    Commands:
      plan        Generate implementation plan from Jira issue
      build       Implement plan
      test        Run tests and auto-resolve failures
      review      Review implementation against criteria
      analyze     Analyze project structure and generate report
      setup       Configure ADWS and validate environment (combined setup + healthcheck)
      init        Initialize ADWS folder in current project

    Examples:
      adw init
      adw init --force
      adw analyze
      adw plan PROJ-123
      adw build a1b2c3d4 PROJ-123
      adw test a1b2c3d4 PROJ-123
      adw review a1b2c3d4 PROJ-123
      adw setup
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


@cli.command()
def setup() -> None:
    """
    Configure ADWS and validate environment.

    This command combines configuration and validation:
    1. Verifies ADWS folder and config.yaml exist
    2. Checks all required environment variables
    3. Validates OpenCode HTTP server is running
    4. Tests Jira API connectivity
    5. Tests Bitbucket API connectivity (if configured)
    6. Verifies GitHub CLI is installed and authenticated
    7. Writes setup log to ADWS/logs/

    Returns:
        Exit code 0 on success, 1 on failure with actionable messages
    """
    from scripts.adw_setup import main as setup_main

    try:
        setup_main()
    except SystemExit as e:
        if e.code != 0:
            raise


@cli.command()
def healthcheck() -> None:
    """
    Run comprehensive system health check (deprecated: use 'adw setup').

    This command is maintained for backward compatibility.
    New users should use 'adw setup' which combines configuration and validation.

    Returns:
        Exit code 0 if all checks pass, 1 otherwise
    """
    from scripts.adw_tests.health_check import main as health_main

    try:
        health_main()
    except SystemExit as e:
        if e.code != 0:
            raise


@cli.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Force overwrite existing ADWS/ folder (requires confirmation)",
)
def init(force: bool) -> None:
    """
    Initialize ADWS folder in current project.

    Creates an ADWS/ directory with default configuration,
    enabling portable ADWS deployment without project pollution.

    This command:
    1. Creates ADWS/ folder in current working directory
    2. Copies default config.yaml with sensible defaults
    3. Creates logs/ directory for ADWS execution logs
    4. Does not overwrite existing files unless --force is provided

    Returns:
        Exit code 0 on success, 1 on error

    Next steps after init:
    1. Review ADWS/config.yaml for your project settings
    2. Run 'adw setup' to verify your environment
    3. Run 'adw plan <issue-key>' to start working
    """
    from scripts.adw_init import main as init_main

    # Pass force flag via sys.argv
    if force:
        sys.argv.append("--force")

    try:
        init_main()
    except SystemExit as e:
        if e.code != 0:
            raise


@cli.command()
def analyze() -> None:
    """
    Analyze project structure and generate report.

    Inspects the parent repository and returns a structured report
    indicating frontend/backend directories, package managers,
    frameworks, and key files.

    This command:
    1. Scans project directories for frontend/backend structure
    2. Identifies package managers (npm, pip, cargo, etc.)
    3. Detects frameworks (React, Express, Flask, etc.)
    4. Identifies key files (docker-compose.yml, README.md, etc.)
    5. Prints a formatted analysis report

    Returns:
        Exit code 0 on success, 1 on error

    Example output:
      📊 Project Analysis: test-project
      📁 Directories:
        [FRONTEND] frontend (React)
        [BACKEND] backend (Express)
      📦 Package Managers:
        npm: Found in frontend, backend
      ⚙️  Frameworks:
        react (frontend)
        express (backend)
    """
    from scripts.adw_analyze import main as analyze_main

    try:
        analyze_main()
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
