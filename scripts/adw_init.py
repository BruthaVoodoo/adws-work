#!/usr/bin/env python3
"""
ADWS Init - Initialize ADWS folder in current project.

This command creates an ADWS/ folder with default configuration
and structure, enabling portable ADWS deployment.

Usage:
    adw init [--force]
"""

import os
import sys
import shutil
from pathlib import Path


def get_template_path() -> Path:
    """Get the path to ADWS template directory."""
    current_file = Path(__file__).resolve()
    return current_file.parent / "adw_templates" / "ADWS"


def check_existing_adws_folder(target_dir: Path) -> bool:
    """Check if ADWS folder already exists."""
    adws_dir = target_dir / "ADWS"
    return adws_dir.exists()


def copy_template_with_safety(
    template_dir: Path,
    target_dir: Path,
    force: bool = False,
) -> None:
    """
    Copy ADWS template to target directory with safety checks.

    Args:
        template_dir: Path to template directory
        target_dir: Target project directory
        force: If True, overwrite existing files with confirmation

    Raises:
        SystemExit: On error or cancellation
    """
    adws_target = target_dir / "ADWS"

    # Check for existing ADWS folder
    if adws_target.exists():
        if not force:
            print(
                "Error: ADWS/ directory already exists. "
                "Use --force to overwrite existing files."
            )
            sys.exit(1)

        # Confirm overwrite
        response = input(
            "ADWS/ directory already exists. Overwrite existing files? [y/N]: "
        )
        if response.lower() not in ["y", "yes"]:
            print("Init cancelled.")
            sys.exit(0)

    # Copy template files
    try:
        if adws_target.exists():
            print(f"Updating ADWS/ folder in: {target_dir}")
        else:
            print(f"Creating ADWS/ folder in: {target_dir}")

        shutil.copytree(template_dir, adws_target, dirs_exist_ok=True)
        print("✓ ADWS/ folder created successfully")
        print(f"  Location: {adws_target}")
        print(f"  Config: {adws_target / 'config.yaml'}")
        print()
        print("Next steps:")
        print("  1. Review ADWS/config.yaml for your project")
        print("  2. Run 'adw setup' to verify your environment")
        print("  3. Run 'adw plan <issue-key>' to start working")

    except Exception as e:
        print(f"Error creating ADWS folder: {e}", file=sys.stderr)
        sys.exit(1)


def main(force: bool = False) -> None:
    """
    Main entry point for adw init command.

    Args:
        force: If True, allow overwriting existing files
    """
    # Get paths
    template_dir = get_template_path()
    target_dir = Path.cwd()

    # Verify template exists
    if not template_dir.exists():
        print(f"Error: ADWS template not found at {template_dir}", file=sys.stderr)
        sys.exit(1)

    # Copy template with safety checks
    copy_template_with_safety(template_dir, target_dir, force=force)


if __name__ == "__main__":
    # Parse command-line arguments manually since this is called from adw_cli.py
    force = "--force" in sys.argv or "-f" in sys.argv
    main(force=force)
