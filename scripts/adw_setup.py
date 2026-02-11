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
import yaml
import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from adw_modules.config import config
from adw_tests.health_check import (
    check_env_vars,
    check_issue_connectivity,
    check_repo_connectivity,
    check_github_cli,
    check_opencode_server,
    HealthCheckResult,
    CheckResult,
)


def detect_or_ask_repo_provider(project_dir: Optional[Path] = None) -> str:
    """Detect repository provider or ask user."""
    if project_dir is None:
        project_dir = Path.cwd()

    # Check for .git directory
    git_dir = project_dir / ".git"
    if git_dir.exists():
        try:
            # Check git config for origin URL
            with open(git_dir / "config", "r") as f:
                content = f.read()
                if "github.com" in content:
                    return "github"
                if "bitbucket.org" in content:
                    return "bitbucket"
        except Exception:
            pass

    # Ask user if we can't detect (Note: in non-interactive mode this defaults to bitbucket)
    # Since we are running in an agent, we can't easily ask interactively via standard input
    # inside this script if it's run via subprocess. But since this is a CLI tool run by user,
    # we'll default to 'bitbucket' for now to match legacy behavior unless we want to prompt.
    # For now, let's default to bitbucket if not detected, but print a message.
    print("   Could not auto-detect repo provider (defaulting to bitbucket)")
    return "bitbucket"


def detect_project_type(
    project_dir: Optional[Path] = None,
) -> Tuple[str, str, str, str, str]:
    """
    Auto-detect project type and recommend appropriate ADWS settings.

    Args:
        project_dir: Directory to analyze (defaults to current directory)

    Returns:
        Tuple of (language, test_command, source_dir, test_dir, repo_provider)
    """
    if project_dir is None:
        project_dir = Path.cwd()

    repo_provider = detect_or_ask_repo_provider(project_dir)

    # Check for Node.js/JavaScript indicators
    if (project_dir / "package.json").exists():
        package_json_path = project_dir / "package.json"
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                package_data = json.load(f)

            # Check for workspaces (monorepo)
            if "workspaces" in package_data:
                return "javascript", "npm test", ".", ".", repo_provider

            # Check for React app
            if "react-scripts" in package_data.get(
                "dependencies", {}
            ) or "react-scripts" in package_data.get("devDependencies", {}):
                return "javascript", "npm test", "src", "__tests__", repo_provider

            # Generic Node.js project
            return "javascript", "npm test", "src", "test", repo_provider

        except (json.JSONDecodeError, FileNotFoundError):
            # Fallback to basic Node.js detection
            return "javascript", "npm test", "src", "test", repo_provider

    # Check for Python indicators
    python_indicators = ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"]
    if any((project_dir / indicator).exists() for indicator in python_indicators):
        # Check for uv usage
        if (project_dir / "uv.lock").exists() or (
            project_dir / "pyproject.toml"
        ).exists():
            return "python", "uv run pytest", "src", "tests", repo_provider
        else:
            return "python", "pytest", "src", "tests", repo_provider

    # Check for Go
    if (project_dir / "go.mod").exists():
        return "go", "go test ./...", ".", ".", repo_provider

    # Check for Rust
    if (project_dir / "Cargo.toml").exists():
        return "rust", "cargo test", "src", "tests", repo_provider

    # Check for Java/Maven
    if (project_dir / "pom.xml").exists():
        return "java", "mvn test", "src/main/java", "src/test/java", repo_provider

    # Check for Java/Gradle
    if (project_dir / "build.gradle").exists() or (
        project_dir / "build.gradle.kts"
    ).exists():
        return "java", "./gradlew test", "src/main/java", "src/test/java", repo_provider

    # Default fallback (assume Python)
    return "python", "pytest", "src", "tests", repo_provider


def detect_pre_commit_hooks(project_dir: Optional[Path] = None) -> bool:
    """
    Detect presence of git pre-commit hooks.

    Checks for:
    1. .husky directory
    2. .pre-commit-config.yaml file
    3. git config core.hooksPath
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Check for husky
    if (project_dir / ".husky").exists():
        return True

    # Check for pre-commit config
    if (project_dir / ".pre-commit-config.yaml").exists():
        return True

    # Check for git hooks path
    try:
        # Check if we are in a git repo
        if (project_dir / ".git").exists():
            result = subprocess.run(
                ["git", "config", "core.hooksPath"],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
    except Exception:
        pass

    return False


def update_project_config(
    language: str,
    test_command: str,
    source_dir: str,
    test_dir: str,
    repo_provider: str,
    issue_provider: str,
    has_pre_commit_hooks: bool = False,
) -> bool:
    """
    Update ADWS/config.yaml with detected settings.
    Preserves existing values if they are already set in the configuration.

    Args:
        language: Programming language
        test_command: Test command to run
        source_dir: Source code directory
        test_dir: Test directory
        repo_provider: Repository provider (bitbucket/github)
        issue_provider: Issue tracker provider (jira/github)
        has_pre_commit_hooks: Whether project has pre-commit hooks

    Returns:
        True if update was successful, False otherwise
    """
    config_file = Path.cwd() / "ADWS" / "config.yaml"

    if not config_file.exists():
        return False

    try:
        # Read existing config
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Define settings to update
        settings = {
            "language": language,
            "test_command": test_command,
            "source_dir": source_dir,
            "test_dir": test_dir,
            "repo_provider": repo_provider,
            "issue_provider": issue_provider,
            "has_pre_commit_hooks": has_pre_commit_hooks,
        }

        updates_made = False

        # Only update keys that are missing from config_data
        for key, value in settings.items():
            if key not in config_data:
                config_data[key] = value
                updates_made = True

        # Write back to file only if changes were made
        if updates_made:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        return True

    except Exception as e:
        print(f"Error updating config: {e}", file=sys.stderr)
        return False

    try:
        # Read existing config
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Update project-specific settings
        config_data["language"] = language
        config_data["test_command"] = test_command
        config_data["source_dir"] = source_dir
        config_data["test_dir"] = test_dir
        config_data["repo_provider"] = repo_provider
        config_data["issue_provider"] = issue_provider
        config_data["has_pre_commit_hooks"] = has_pre_commit_hooks

        # Write back to file
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        return True

    except Exception as e:
        print(f"Error updating config: {e}", file=sys.stderr)
        return False


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


def start_opencode_server(log_dir: Path) -> bool:
    """Attempt to start OpenCode server in background."""
    print("\n   ⚠️  OpenCode server not running. Attempting to auto-start...", end=" ")

    os.makedirs(log_dir, exist_ok=True)
    log_file = log_dir / "opencode_server.log"

    try:
        # Check if opencode command exists first
        if (
            subprocess.call(
                ["which", "opencode"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            != 0
        ):
            print("❌ FAILED (command 'opencode' not found)")
            return False

        with open(log_file, "a") as f:
            f.write(f"\n--- Starting OpenCode Server at {datetime.now()} ---\n")
            # Start detached process
            subprocess.Popen(
                ["opencode", "serve", "--port", "4096"],
                cwd=os.getcwd(),
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        # Wait for server to initialize
        time.sleep(3)
        return True
    except Exception as e:
        print(f"❌ FAILED ({e})")
        return False


def detect_running_opencode_pid(port: int = 4096) -> Optional[int]:
    """Check if opencode is running on the specified port using lsof."""
    try:
        # lsof -i :4096 -t (returns PID only)
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"], capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            # Return the first PID found
            return int(result.stdout.strip().split("\n")[0])
    except Exception:
        pass
    return None


def get_process_cwd(pid: int) -> Optional[str]:
    """Get CWD of a process given its PID."""
    try:
        # Try 'pwdx' on Linux or 'lsof -p PID' on macOS/Linux
        # lsof is more portable for macOS
        result = subprocess.run(
            ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-F", "n"],
            capture_output=True,
            text=True,
        )
        # Output format:
        # p1234
        # n/path/to/cwd
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("n"):
                    return line[1:]  # Strip 'n' prefix
    except Exception:
        pass
    return None


def kill_process(pid: int) -> bool:
    """Kill a process by PID."""
    try:
        os.kill(pid, 9)  # SIGKILL
        return True
    except Exception:
        return False


def check_opencode_server_wrapper() -> "CheckResult":
    """Check if OpenCode server is running and accessible."""
    try:
        # Import CheckResult here to ensure visibility
        from scripts.adw_tests.health_check import CheckResult

        is_available = check_opencode_server()

        # is_available is a CheckResult
        if is_available.success:
            # Extended check: Verify CWD if it's running
            pid = detect_running_opencode_pid(4096)
            if pid:
                cwd = get_process_cwd(pid)
                current_project_root = str(Path.cwd())

                # Check if running from a different directory (allowing for some flexibility, e.g. subdirs)
                if cwd and cwd != current_project_root:
                    print(
                        f"\n      ⚠️  OpenCode server (PID {pid}) is running in: {cwd}"
                    )
                    print(f"      Current project is: {current_project_root}")
                    print(f"      This may cause 'File not found' errors.")

                    print(
                        "      Do you want to restart it in the current directory? [y/N] ",
                        end="",
                    )
                    response = input().lower()
                    if response == "y":
                        print("      Stopping old server...", end=" ")
                        if kill_process(pid):
                            print("Done.")
                            # Returning False triggers the auto-start logic in run_setup
                            time.sleep(1)  # Give port time to free up

                            # Return a CheckResult indicating failure so setup loop retries
                            return CheckResult(
                                success=False,
                                error="Restarting server in correct directory",
                            )
                        else:
                            print("Failed to stop server.")

            # Return original success CheckResult
            return is_available

        return is_available
    except Exception as e:
        # Return CheckResult on exception
        from scripts.adw_tests.health_check import CheckResult

        return CheckResult(success=False, error=str(e))


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

    # Step 2: Auto-detect project type and update config if needed
    print()
    print("🔍 Step 2: Auto-detecting project type...")

    language, test_command, source_dir, test_dir, repo_provider = detect_project_type()
    print(f"   Detected: {language.title()} project")
    print(f"   Test command: {test_command}")
    print(f"   Source directory: {source_dir}")
    print(f"   Test directory: {test_dir}")
    print(f"   Repo provider: {repo_provider}")

    # For now, default issue_provider to 'jira' unless user specifically wants GitHub issues
    # In the future, we could detect this or ask
    issue_provider = "jira"
    print(f"   Issue provider: {issue_provider} (default)")

    # Detect pre-commit hooks
    has_hooks = detect_pre_commit_hooks(cwd)
    if has_hooks:
        print("   Detected: Git pre-commit hooks enabled")
    else:
        print("   Detected: No pre-commit hooks found")

    # Update config with detected settings
    print("   Updating ADWS/config.yaml with detected settings...", end=" ")
    if update_project_config(
        language,
        test_command,
        source_dir,
        test_dir,
        repo_provider,
        issue_provider,
        has_hooks,
    ):
        print("✅ UPDATED")
    else:
        print("❌ FAILED TO UPDATE")
        print("   Warning: Could not update config.yaml with detected settings")

    # Step 3: Get log directory (ADWS/logs/)
    try:
        logs_dir = cwd / "ADWS" / "logs"
    except Exception as e:
        print(f"❌ Error determining log directory: {e}")
        return 1

    # Step 4: Run health checks
    print()
    print("🏥 Step 3: Running health checks...")

    health_checks = {
        "environment": check_env_vars,
        "issue_connectivity": check_issue_connectivity,
        "repo_connectivity": check_repo_connectivity,
        "github_cli": check_github_cli,
        "opencode_server": check_opencode_server_wrapper,
    }

    checks_passed = 0
    checks_failed = 0

    for check_name, check_func in health_checks.items():
        print(f"   Checking {check_name.replace('_', ' ').title()}...", end=" ")
        try:
            result = check_func()

            # Special handling for OpenCode auto-start
            if not result.success and check_name == "opencode_server":
                if start_opencode_server(logs_dir):
                    # Re-run check
                    print(
                        f"   Checking {check_name.replace('_', ' ').title()} (retry)...",
                        end=" ",
                    )
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
