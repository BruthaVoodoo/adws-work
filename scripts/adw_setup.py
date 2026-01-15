#!/usr/bin/env python3
"""
ADW Setup Script - Combines configuration validation and health checks

Usage:
  python -m scripts.adw_setup
  adw setup

This script performs both configuration and validation:
1. Verifies ADWS folder and config.yaml exist
2. Runs comprehensive health checks (environment, Jira, Bitbucket, GitHub CLI, OpenCode)
3. Writes setup log to ADWS/logs/
4. Returns exit code 0 on success, 1 on failure

Story B3: Combine setup + healthcheck into single validation flow
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from adw_modules.config import config
from adw_tests.health_check import (
    check_env_vars,
    check_jira_connectivity,
    check_bitbucket_connectivity,
    check_github_cli,
    check_opencode_server,
    HealthCheckResult,
    CheckResult,
)


def validate_configuration() -> tuple[bool, List[str]]:
    """
    Validate ADWS configuration.

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check if ADWS folder exists
    cwd = Path.cwd()
    adws_folder = cwd / "ADWS"

    if not adws_folder.exists() or not adws_folder.is_dir():
        errors.append(
            "ADWS folder not found in current directory. "
            "Run 'adw init' first to initialize ADWS."
        )
        return False, errors

    # Check if config.yaml exists in ADWS folder
    config_file = adws_folder / "config.yaml"
    if not config_file.exists() or not config_file.is_file():
        errors.append(
            "ADWS/config.yaml not found. "
            "Run 'adw init' to create default configuration."
        )
        return False, errors

    return True, errors


def write_setup_log(
    success: bool,
    config_valid: bool,
    health_result: HealthCheckResult,
    log_dir: Path,
) -> None:
    """
    Write setup log file to ADWS/logs/.

    Args:
        success: Overall setup success status
        config_valid: Configuration validation status
        health_result: Health check results
        log_dir: Directory to write log file
    """
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"setup_{timestamp}.txt"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"ADW Setup Log\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"\n")

        f.write(f"Configuration Status: {'VALID' if config_valid else 'INVALID'}\n")
        f.write(f"\n")

        f.write(f"Health Check Results:\n")
        f.write(f"{'-' * 50}\n")

        for check_name, check_result in health_result.checks.items():
            status = "PASS" if check_result.success else "FAIL"
            f.write(f"\n[{check_name}] {status}\n")

            if check_result.details:
                f.write(f"  Details: {json.dumps(check_result.details, indent=2)}\n")

            if check_result.error:
                f.write(f"  Error: {check_result.error}\n")

            if check_result.warning:
                f.write(f"  Warning: {check_result.warning}\n")

        f.write(f"\n")
        f.write(f"Overall Status: {'SUCCESS' if success else 'FAILURE'}\n")

        if health_result.errors:
            f.write(f"\nErrors:\n")
            for error in health_result.errors:
                f.write(f"  - {error}\n")

        if health_result.warnings:
            f.write(f"\nWarnings:\n")
            for warning in health_result.warnings:
                f.write(f"  - {warning}\n")

    print(f"\n📝 Setup log written to: {log_file}")


def run_setup() -> int:
    """
    Run complete setup flow: configuration validation + health checks.

    Returns:
        Exit code (0 on success, 1 on failure)
    """
    print("🔧 Running ADWS Setup...")
    print()

    cwd = Path.cwd()

    # Step 1: Validate configuration
    print("📋 Step 1: Validating configuration...")
    config_valid, config_errors = validate_configuration()

    if not config_valid:
        print("❌ Configuration validation failed:")
        for error in config_errors:
            print(f"   - {error}")
        print()
        print("Please fix the above errors and run 'adw setup' again.")
        print("💡 Tip: Run 'adw init' to initialize ADWS in this project.")
        return 1

    print("✅ Configuration valid")

    # Step 2: Get log directory (ADWS/logs/)
    try:
        logs_dir = cwd / "ADWS" / "logs"
    except Exception as e:
        print(f"❌ Error determining log directory: {e}")
        return 1

    # Step 3: Run health checks
    print()
    print("🏥 Step 2: Running health checks...")

    health_checks = {
        "environment": check_env_vars,
        "jira_connectivity": check_jira_connectivity,
        "bitbucket_connectivity": check_bitbucket_connectivity,
        "github_cli": check_github_cli,
        "opencode_server": check_opencode_server,
    }

    checks_passed = 0
    checks_failed = 0

    for check_name, check_func in health_checks.items():
        print(f"   Checking {check_name.replace('_', ' ').title()}...", end=" ")
        try:
            result = check_func()
            if result.success:
                print("✅ PASS")
                checks_passed += 1
            else:
                print("❌ FAIL")
                checks_failed += 1
                if result.error:
                    print(f"      Error: {result.error}")
        except Exception as e:
            print("❌ FAIL")
            checks_failed += 1
            print(f"      Error: {str(e)}")

    # Build health result
    health_result = HealthCheckResult(
        success=(checks_failed == 0),
        timestamp=datetime.now().isoformat(),
        checks={},
        errors=[],
        warnings=[],
    )

    # Re-run checks to capture details for log
    for check_name, check_func in health_checks.items():
        try:
            result = check_func()
            health_result.checks[check_name] = result
            if not result.success:
                if result.error:
                    health_result.errors.append(
                        f"[{check_name.replace('_', ' ').title()}] {result.error}"
                    )
                if check_name == "environment" and result.details.get(
                    "missing_required"
                ):
                    for var in result.details["missing_required"]:
                        health_result.errors.append(f"[Environment] Missing: {var}")
            if result.warning:
                health_result.warnings.append(
                    f"[{check_name.replace('_', ' ').title()}] {result.warning}"
                )
        except Exception as e:
            health_result.checks[check_name] = CheckResult(
                success=False, error=f"Check failed: {str(e)}"
            )
            health_result.errors.append(
                f"[{check_name.replace('_', ' ').title()}] {str(e)}"
            )

    # Step 4: Report results
    print()
    if health_result.success:
        print("✅ All health checks passed!")
    else:
        print("❌ Health checks failed:")
        for error in health_result.errors:
            print(f"   - {error}")

    if health_result.warnings:
        print()
        print("⚠️  Warnings:")
        for warning in health_result.warnings:
            print(f"   - {warning}")

    # Step 5: Write setup log
    overall_success = config_valid and health_result.success
    write_setup_log(
        success=overall_success,
        config_valid=config_valid,
        health_result=health_result,
        log_dir=logs_dir,
    )

    # Step 6: Print final status and exit
    print()
    if overall_success:
        print("✅ Setup completed successfully!")
        print()
        print("Your ADWS environment is ready. You can now:")
        print("  - Run 'adw plan <issue-key>' to start a new workflow")
        print("  - Run 'adw setup' again to verify your environment")
        return 0
    else:
        print("❌ Setup failed.")
        print()
        print("Please resolve the errors above and run 'adw setup' again.")
        print("\nCommon fixes:")
        if not config_valid:
            print("  - Run 'adw init' to initialize ADWS")
        if any("environment" in e.lower() for e in health_result.errors):
            print("  - Set missing environment variables in .env or your shell")
        if any("opencode" in e.lower() for e in health_result.errors):
            print("  - Start OpenCode server: opencode serve --port 4096")
        if any("jira" in e.lower() for e in health_result.errors):
            print("  - Verify Jira credentials in environment variables")
        if any("bitbucket" in e.lower() for e in health_result.errors):
            print("  - Verify Bitbucket API token is valid")
        if any("github" in e.lower() for e in health_result.errors):
            print("  - Install GitHub CLI: brew install gh")
            print("  - Authenticate: gh auth login")
        return 1


def main():
    """Main entry point for adw setup command."""
    try:
        exit_code = run_setup()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
