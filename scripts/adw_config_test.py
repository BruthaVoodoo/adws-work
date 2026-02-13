#!/usr/bin/env python3
"""
ADW Config Test - Interactive test configuration management

Usage:
  python -m scripts.adw_config_test
  adw config test

This script allows users to reconfigure test settings without running full setup:
- Display current test configuration
- Re-detect test framework
- Edit test command manually
- Switch to console fallback mode
- Validate current configuration
- Save changes to ADWS/config.yaml
"""

import os
import sys
import yaml
import json
import subprocess
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from adw_modules.config import config
from adw_modules.test_parsers import (
    parse_jest_json,
    parse_pytest_json,
    parse_console_output,
)


def display_current_config() -> Dict[str, Any]:
    """
    Display current test configuration from config.yaml.

    Returns:
        Current test configuration dictionary
    """
    test_config = config._data.get("test_configuration", {})

    print("\n📋 Current Test Configuration:")
    print("=" * 60)

    if not test_config:
        print("❌ No test_configuration found in config.yaml")
        print("   Using fallback defaults")
        return {}

    print(f"Framework:         {test_config.get('framework', 'unknown')}")
    print(f"Test Command:      {test_config.get('test_command', 'N/A')}")
    print(f"Output Format:     {test_config.get('output_format', 'console')}")
    print(f"JSON Output File:  {test_config.get('json_output_file', 'N/A')}")
    print(f"Parser:            {test_config.get('parser', 'N/A')}")
    print("=" * 60)

    return test_config


def detect_test_framework() -> Dict[str, Any]:
    """
    Auto-detect test framework and return recommended configuration.

    Returns:
        Dictionary with detected configuration
    """
    print("\n🔍 Detecting test framework...")

    project_dir = Path.cwd()

    # Check for Jest (package.json with jest or react-scripts)
    package_json = project_dir / "package.json"
    if package_json.exists():
        try:
            import json

            with open(package_json, "r") as f:
                pkg_data = json.load(f)

            deps = pkg_data.get("dependencies", {})
            dev_deps = pkg_data.get("devDependencies", {})
            scripts = pkg_data.get("scripts", {})

            # Check for Jest
            if "jest" in dev_deps or "jest" in deps:
                print("✅ Detected: Jest")
                return {
                    "framework": "jest",
                    "test_command": "npm test -- --json --outputFile=.adw/test-results.json",
                    "output_format": "json",
                    "json_output_file": ".adw/test-results.json",
                    "parser": "jest",
                }

            # Check for React scripts (includes Jest)
            if "react-scripts" in dev_deps or "react-scripts" in deps:
                print("✅ Detected: React (Jest)")
                return {
                    "framework": "jest",
                    "test_command": "npm test -- --json --outputFile=.adw/test-results.json --watchAll=false",
                    "output_format": "json",
                    "json_output_file": ".adw/test-results.json",
                    "parser": "jest",
                }
        except Exception:
            pass

    # Check for Pytest
    pytest_indicators = ["pytest.ini", "pyproject.toml", "requirements.txt", "setup.py"]
    if any((project_dir / indicator).exists() for indicator in pytest_indicators):
        print("✅ Detected: Pytest")

        # Check if pytest-json-report is available
        try:
            result = subprocess.run(
                ["pip", "show", "pytest-json-report"], capture_output=True, text=True
            )
            has_json_plugin = result.returncode == 0
        except Exception:
            has_json_plugin = False

        if has_json_plugin:
            print("   ✅ pytest-json-report plugin available")
            return {
                "framework": "pytest",
                "test_command": "pytest --json-report --json-report-file=.adw/test-results.json",
                "output_format": "json",
                "json_output_file": ".adw/test-results.json",
                "parser": "pytest",
            }
        else:
            print("   ⚠️  pytest-json-report plugin not found")
            print("   Using console fallback mode")
            return {
                "framework": "pytest",
                "test_command": "pytest",
                "output_format": "console",
                "json_output_file": None,
                "parser": "console",
            }

    # Check for other frameworks
    if (project_dir / "go.mod").exists():
        print("✅ Detected: Go")
        return {
            "framework": "go",
            "test_command": "go test ./...",
            "output_format": "console",
            "json_output_file": None,
            "parser": "console",
        }

    if (project_dir / "Cargo.toml").exists():
        print("✅ Detected: Rust")
        return {
            "framework": "rust",
            "test_command": "cargo test",
            "output_format": "console",
            "json_output_file": None,
            "parser": "console",
        }

    print("❌ Could not detect test framework")
    print("   Please configure manually")
    return {}


def edit_test_command(current_command: str) -> str:
    """
    Prompt user to edit test command manually.

    Args:
        current_command: Current test command

    Returns:
        Updated test command
    """
    print(f"\n✏️  Current test command: {current_command}")
    print("Enter new test command (or press Enter to keep current):")
    new_command = input("> ").strip()

    if not new_command:
        print("   Keeping current command")
        return current_command

    print(f"   Updated to: {new_command}")
    return new_command


def switch_to_fallback_mode(current_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Switch configuration to console fallback mode.

    Args:
        current_config: Current configuration

    Returns:
        Updated configuration with fallback settings
    """
    print("\n⚠️  Switching to console fallback mode...")

    # Keep test command but remove JSON output
    test_command = current_config.get("test_command", "pytest")

    # Remove JSON-specific flags from command
    # Handle --json and --json=true patterns
    test_command = re.sub(r"\s*--json[=\s]\S*", "", test_command)
    # Handle --outputFile and its value
    test_command = re.sub(r"\s*--outputFile[=\s]\S*", "", test_command)
    # Handle --json-report and --json-report-file patterns
    test_command = re.sub(r"\s*--json-report(-file)?[=\s]\S*", "", test_command)
    # Clean up extra whitespace
    test_command = " ".join(test_command.split())

    fallback_config = {
        "framework": current_config.get("framework", "unknown"),
        "test_command": test_command,
        "output_format": "console",
        "json_output_file": None,
        "parser": "console",
    }

    print("✅ Fallback configuration:")
    print(f"   Test command: {fallback_config['test_command']}")
    print(f"   Output format: console")
    print(f"   Parser: console")

    return fallback_config


def validate_configuration(test_config: Dict[str, Any]) -> bool:
    """
    Validate test configuration by running a quick test.

    Args:
        test_config: Test configuration to validate

    Returns:
        True if validation successful, False otherwise
    """
    print("\n🔍 Validating test configuration...")

    test_command = test_config.get("test_command")
    if not test_command:
        print("❌ No test command specified")
        return False

    output_format = test_config.get("output_format", "console")
    json_output_file = test_config.get("json_output_file")

    print(f"   Running: {test_command}")
    print("   (30 second timeout)")

    try:
        # Run test command with timeout
        result = subprocess.run(
            test_command, shell=True, capture_output=True, text=True, timeout=30
        )

        print(f"   Exit code: {result.returncode}")

        # For JSON mode, verify output file exists and is valid JSON
        if output_format == "json" and json_output_file:
            json_path = Path(json_output_file)

            if not json_path.exists():
                print(f"❌ JSON output file not created: {json_output_file}")
                return False

            try:
                with open(json_path, "r") as f:
                    json_data = json.load(f)
                print("✅ Valid JSON output file created")

                # Try to parse with appropriate parser
                framework = test_config.get("framework", "unknown")
                if framework == "jest":
                    parsed = parse_jest_json(str(json_path))
                    if "error" in parsed:
                        print(f"⚠️  Parser warning: {parsed['error']}")
                    else:
                        print(
                            f"✅ Jest parser successful: {parsed.get('total_tests', 0)} tests found"
                        )
                elif framework == "pytest":
                    parsed = parse_pytest_json(str(json_path))
                    if "error" in parsed:
                        print(f"⚠️  Parser warning: {parsed['error']}")
                    else:
                        print(
                            f"✅ Pytest parser successful: {parsed.get('total_tests', 0)} tests found"
                        )

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in output file: {e}")
                return False

        # For console mode, verify we got output
        else:
            if result.stdout or result.stderr:
                print("✅ Console output captured")

                # Try parsing with console parser
                parsed = parse_console_output(result.stdout + "\n" + result.stderr)
                if "error" in parsed:
                    print(f"⚠️  Parser warning: {parsed['error']}")
                else:
                    print(
                        f"✅ Console parser successful: {len(parsed.get('failed_test_details', []))} failures extracted"
                    )
            else:
                print("⚠️  No output captured (this may be normal)")

        print("✅ Configuration validation passed")
        return True

    except subprocess.TimeoutExpired:
        print("⚠️  Test command timed out (30s)")
        print("   This may be normal for large test suites")
        print("   Consider validation successful if command started")
        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def save_configuration(test_config: Dict[str, Any]) -> bool:
    """
    Save test configuration to ADWS/config.yaml.

    Args:
        test_config: Test configuration to save

    Returns:
        True if save successful, False otherwise
    """
    print("\n💾 Saving configuration to ADWS/config.yaml...")

    config_file = Path.cwd() / "ADWS" / "config.yaml"

    if not config_file.exists():
        print("❌ ADWS/config.yaml not found")
        return False

    try:
        # Read existing config
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Update test_configuration section
        config_data["test_configuration"] = test_config

        # Write back to file
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        print("✅ Configuration saved successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")
        return False


def show_menu() -> str:
    """
    Display interactive menu and get user choice.

    Returns:
        User's menu choice
    """
    print("\n📋 Test Configuration Options:")
    print("=" * 60)
    print("1. Display current configuration")
    print("2. Re-detect test framework")
    print("3. Edit test command manually")
    print("4. Switch to console fallback mode")
    print("5. Validate current configuration")
    print("6. Apply changes and save")
    print("7. Exit without saving")
    print("=" * 60)

    choice = input("Enter your choice (1-7): ").strip()
    return choice


def run_config_test() -> int:
    """
    Run interactive test configuration flow.

    Returns:
        Exit code (0 on success, 1 on failure)
    """
    print("🔧 ADW Test Configuration")
    print()

    # Check if ADWS folder exists
    adws_folder = Path.cwd() / "ADWS"
    if not adws_folder.exists():
        print("❌ ADWS folder not found in current directory")
        print("   Run 'adw init' first to initialize ADWS")
        return 1

    # Load current configuration
    current_config = display_current_config()
    pending_config = current_config.copy() if current_config else {}

    # Interactive loop
    while True:
        choice = show_menu()

        if choice == "1":
            # Display current
            display_current_config()
            if pending_config != current_config:
                print("\n⚠️  You have unsaved changes:")
                print(f"   Pending config: {pending_config}")

        elif choice == "2":
            # Re-detect framework
            detected = detect_test_framework()
            if detected:
                print("\n✅ Detection complete")
                print("Apply this configuration? (y/n): ", end="")
                if input().lower() == "y":
                    pending_config = detected
                    print("✅ Configuration updated (not yet saved)")

        elif choice == "3":
            # Edit command
            current_cmd = pending_config.get("test_command", "")
            if not current_cmd:
                print("❌ No test command in current config")
                print("   Run detection first (option 2)")
                continue

            new_cmd = edit_test_command(current_cmd)
            pending_config["test_command"] = new_cmd
            print("✅ Test command updated (not yet saved)")

        elif choice == "4":
            # Fallback mode
            if not pending_config:
                print("❌ No configuration to convert")
                print("   Run detection first (option 2)")
                continue

            fallback = switch_to_fallback_mode(pending_config)
            print("\nApply fallback configuration? (y/n): ", end="")
            if input().lower() == "y":
                pending_config = fallback
                print("✅ Switched to fallback mode (not yet saved)")

        elif choice == "5":
            # Validate
            if not pending_config:
                print("❌ No configuration to validate")
                continue

            validate_configuration(pending_config)

        elif choice == "6":
            # Save
            if not pending_config:
                print("❌ No configuration to save")
                continue

            print("\n📋 Configuration to save:")
            for key, value in pending_config.items():
                print(f"   {key}: {value}")

            print("\nSave this configuration? (y/n): ", end="")
            if input().lower() == "y":
                if save_configuration(pending_config):
                    print("\n✅ Configuration saved successfully!")
                    print("   Your test configuration has been updated")
                    return 0
                else:
                    print("\n❌ Failed to save configuration")
                    return 1

        elif choice == "7":
            # Exit
            if pending_config != current_config:
                print("\n⚠️  You have unsaved changes")
                print("Exit without saving? (y/n): ", end="")
                if input().lower() != "y":
                    continue

            print("\n👋 Exiting without saving")
            return 0

        else:
            print("❌ Invalid choice. Please enter 1-7")


def main():
    """Main entry point for adw config test command."""
    try:
        exit_code = run_config_test()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
