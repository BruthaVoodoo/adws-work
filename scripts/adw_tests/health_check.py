#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "python-dotenv",
#     "pydantic",
#     "jira",
#     "requests",
# ]
# ///

"""
Health Check Script for ADW System

Usage:
uv run adws/health_check.py

This script performs comprehensive health checks:
1. Validates all required environment variables
2. Checks Jira API connectivity
3. Checks Bitbucket API connectivity
4. Checks GitHub CLI functionality
5. Checks OpenCode server availability (Story 4.4)
6. Returns structured results
"""

import os
import sys
import json
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import argparse
import requests
from urllib.parse import urlparse

from dotenv import load_dotenv
from pydantic import BaseModel

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required functions
from adw_modules.opencode_http_client import check_opencode_server_available
from adw_modules import repo_ops
from adw_modules import issue_ops

# Load environment variables
load_dotenv(override=True)


class CheckResult(BaseModel):
    """Individual check result."""

    success: bool
    error: Optional[str] = None
    warning: Optional[str] = None
    details: Dict[str, Any] = {}


class HealthCheckResult(BaseModel):
    """Structure for health check results."""

    success: bool
    timestamp: str
    checks: Dict[str, CheckResult]
    warnings: List[str] = []
    errors: List[str] = []


def check_env_vars() -> CheckResult:
    """Check required environment variables."""
    from adw_modules.config import config

    required_vars = {
        "JIRA_SERVER": "Jira Server URL",
        "JIRA_USERNAME": "Jira Username (email)",
        "JIRA_API_TOKEN": "Jira API Token",
    }

    # Add provider-specific requirements
    if config.repo_provider == "bitbucket":
        required_vars.update(
            {
                "BITBUCKET_API_TOKEN": "Bitbucket API Token (for Bearer auth)",
                "BITBUCKET_WORKSPACE": "Bitbucket Workspace",
                "BITBUCKET_REPO_NAME": "Bitbucket Repository Name",
            }
        )
    # GitHub relies on CLI auth usually, so strict env vars might not be needed
    # unless we enforce GITHUB_TOKEN. For now, we let the connectivity check handle it.

    optional_vars = {
        "GITHUB_PAT": "(Optional) GitHub Personal Access Token - only needed if you want ADW to use a different GitHub account than 'gh auth login'",
    }

    missing_required = []
    missing_optional = []

    # Check required vars
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"{var} ({desc})")

    # Check optional vars
    for var, desc in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var} ({desc})")

    success = len(missing_required) == 0

    return CheckResult(
        success=success,
        error="Missing required environment variables" if not success else None,
        details={
            "missing_required": missing_required,
            "missing_optional": missing_optional,
        },
    )


def check_issue_connectivity() -> CheckResult:
    """Test Issue Tracker connectivity (Jira or GitHub)."""
    try:
        result = issue_ops.check_connectivity()
        if result["success"]:
            return CheckResult(success=True, details=result.get("details", {}))
        else:
            return CheckResult(
                success=False, error=result.get("error", "Unknown error")
            )
    except Exception as e:
        return CheckResult(
            success=False, error=f"Issue tracker connectivity failed: {str(e)}"
        )


def check_repo_connectivity() -> CheckResult:
    """Test Repository Provider connectivity (Bitbucket or GitHub)."""
    try:
        result = repo_ops.check_connectivity()
        if result["success"]:
            return CheckResult(success=True, details=result.get("details", {}))
        else:
            return CheckResult(
                success=False, error=result.get("error", "Unknown error")
            )
    except Exception as e:
        return CheckResult(success=False, error=f"Repo connectivity failed: {str(e)}")


def check_github_cli() -> CheckResult:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "--version"], capture_output=True, text=True, check=True
        )
        auth_result = subprocess.run(
            ["gh", "auth", "status"], capture_output=True, text=True, check=True
        )
        return CheckResult(
            success=True,
            details={
                "version": result.stdout.strip(),
                "auth_status": auth_result.stderr.strip(),
            },
        )
    except FileNotFoundError:
        return CheckResult(
            success=False,
            error="GitHub CLI (gh) is not installed. Install with: brew install gh",
        )
    except subprocess.CalledProcessError as e:
        return CheckResult(
            success=False, error=f"GitHub CLI not authenticated: {e.stderr.strip()}"
        )
    except Exception as e:
        return CheckResult(
            success=False,
            error=f"An unexpected error occurred during GitHub CLI check: {str(e)}",
        )


def check_opencode_server() -> CheckResult:
    """
    Check if OpenCode server is available and responding.

    Story 4.4: Update health_check.py to verify OpenCode server instead of GitHub Copilot CLI.

    This function calls check_opencode_server_available() from opencode_http_client
    to verify the OpenCode HTTP server is accessible.

    Returns:
        CheckResult with success status and details
    """
    try:
        # Import config to get server URL
        from adw_modules.config import config

        server_url = config.opencode_server_url
        is_available = check_opencode_server_available(server_url=server_url)

        if is_available:
            return CheckResult(
                success=True, details={"server_url": server_url, "status": "available"}
            )
        else:
            return CheckResult(
                success=False,
                error=f"OpenCode server at {server_url} is not available. Start it with: opencode serve --port 4096",
            )
    except ImportError as e:
        return CheckResult(
            success=False, error=f"Failed to import OpenCode modules: {str(e)}"
        )
    except Exception as e:
        return CheckResult(
            success=False,
            error=f"An unexpected error occurred during OpenCode server check: {str(e)}",
        )


def run_health_check() -> HealthCheckResult:
    """Run all health checks and return results."""
    result = HealthCheckResult(
        success=True, timestamp=datetime.now().isoformat(), checks={}
    )

    checks_to_run = {
        "environment": check_env_vars,
        "issue_connectivity": check_issue_connectivity,
        "repo_connectivity": check_repo_connectivity,
        "github_cli": check_github_cli,  # Still good to check generally
        "opencode_server": check_opencode_server,
    }

    for name, check_func in checks_to_run.items():
        check_result = check_func()
        result.checks[name] = check_result
        if not check_result.success:
            result.success = False
            if check_result.error:
                result.errors.append(
                    f"[{name.replace('_', ' ').title()}] {check_result.error}"
                )
            if name == "environment":
                missing_required = check_result.details.get("missing_required", [])
                result.errors.extend(
                    [
                        f"[Environment] Missing required env var: {var}"
                        for var in missing_required
                    ]
                )
        if check_result.warning:
            result.warnings.append(
                f"[{name.replace('_', ' ').title()}] {check_result.warning}"
            )

    return result


def main():
    """Main entry point."""
    print("🏥 Running ADW System Health Check...\n")

    result = run_health_check()

    print(
        f"{('✅' if result.success else '❌')} Overall Status: {'HEALTHY' if result.success else 'UNHEALTHY'}"
    )
    print(f"📅 Timestamp: {datetime.now().isoformat()}\n")

    print("📋 Check Results:")
    print("-" * 50)

    for check_name, check_result in result.checks.items():
        status_icon = "✅" if check_result.success else "❌"
        print(f"\n{status_icon} {check_name.replace('_', ' ').title()}:")

        for key, value in check_result.details.items():
            if value and key not in ["missing_required", "missing_optional"]:
                print(f"   - {key.replace('_', ' ').title()}: {value}")

        if check_result.warning:
            print(f"   ⚠️  Warning: {check_result.warning}")
        if check_result.error:
            print(f"   ❌ Error: {check_result.error}")

    if result.warnings:
        print("\n" + "=" * 50)
        print("⚠️  Warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")

    if result.errors:
        print("\n" + "=" * 50)
        print("❌ Errors & Next Steps:")
        for error in result.errors:
            print(f"   - {error}")
        if not result.success:
            print("\n   Please resolve the errors above.")

    print("\n" + "=" * 50)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
