#!/usr/bin/env python3
"""
Jira Importer Script

Parses JIRA_EPICS_AND_STORIES.md and creates all epics and stories in Jira.
Supports dry-run mode to preview changes without actually creating them.

Usage:
    python jira_importer.py --file ai_docs/specs/JIRA_EPICS_AND_STORIES.md --project DAI [--dry-run]
"""

import sys
import os
import re
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Load .env file
env_path = Path.cwd() / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from adw_modules.issue_ops import (
    jira_create_epic,
    jira_create_story,
    jira_get_project_issues,
    check_connectivity,
)


class JiraImporter:
    """Parses markdown file and imports epics and stories to Jira."""

    def __init__(
        self, md_file: str, project_key: str, dry_run: bool = False, force: bool = False
    ):
        """Initialize the importer.

        Args:
            md_file: Path to the JIRA_EPICS_AND_STORIES.md file
            project_key: Jira project key (e.g., 'DAI')
            dry_run: If True, only show what would be created without creating
            force: If True, skip confirmation prompt for existing issues
        """
        self.md_file = md_file
        self.project_key = project_key
        self.dry_run = dry_run
        self.force = force
        self.epics: Dict[str, Dict[str, Any]] = {}
        self.stories: Dict[str, Dict[str, Any]] = {}
        self.created_epics: Dict[str, str] = {}  # Maps epic name to key
        self.created_stories: List[str] = []

    def read_file(self) -> str:
        """Read the markdown file."""
        if not os.path.exists(self.md_file):
            raise FileNotFoundError(f"File not found: {self.md_file}")

        with open(self.md_file, "r") as f:
            return f.read()

    def parse_epics(self, content: str) -> None:
        """Parse epic definitions from markdown."""
        # Find all Epic sections: ## EPIC N:
        epic_pattern = (
            r"## EPIC (\d+): ([^\n]+)\n\n### Details\n(.*?)\n### Acceptance Criteria"
        )

        for match in re.finditer(epic_pattern, content, re.DOTALL):
            epic_num = match.group(1)
            epic_title = match.group(2)
            epic_details = match.group(3)

            # Parse details
            details_dict = self._parse_details_section(epic_details)

            epic_name = f"Epic {epic_num}"
            self.epics[epic_name] = {
                "number": epic_num,
                "title": epic_title,
                "summary": details_dict.get("Summary", epic_title),
                "description": details_dict.get("Description", ""),
                "project": details_dict.get("Project", self.project_key),
                "type": details_dict.get("Type", "Epic"),
                "story_count": len(
                    [s for s in self.stories.values() if s.get("epic_num") == epic_num]
                ),
            }

    def parse_stories(self, content: str) -> None:
        """Parse story definitions from markdown."""
        # Find all Story sections: #### Story N.M:
        story_pattern = r"#### Story (\d+)\.(\d+): ([^\n]+)\n\*\*Summary:\*\* ([^\n]+)\n\*\*Type:\*\* ([^\n]+)\n\*\*Estimation:\*\* ([^\n]+)\n\*\*Dependencies:\*\* ([^\n]+)\n\n\*\*Description\*\*\n(.*?)\n\n\*\*Acceptance Criteria\*\*\n(.*?)\n\n---"

        for match in re.finditer(story_pattern, content, re.DOTALL):
            epic_num = match.group(1)
            story_num = match.group(2)
            story_title = match.group(3)
            summary = match.group(4)
            story_type = match.group(5)
            estimation = match.group(6)
            dependencies = match.group(7)
            description = match.group(8)
            acceptance_criteria = match.group(9)

            story_name = f"Story {epic_num}.{story_num}"
            full_description = (
                f"{description}\n\n**Acceptance Criteria**\n{acceptance_criteria}"
            )

            # Parse estimation hours
            hours = self._parse_estimation(estimation)

            self.stories[story_name] = {
                "epic_num": epic_num,
                "story_num": story_num,
                "summary": summary,
                "description": full_description,
                "type": story_type,
                "estimation_hours": hours,
                "dependencies": dependencies,
                "labels": [f"epic-{epic_num}", "opencode-migration"],
            }

    def _parse_details_section(self, details: str) -> Dict[str, str]:
        """Parse the Details section of an epic."""
        result = {}
        for line in details.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().replace("**", "").replace("- ", "")
                value = value.strip()
                result[key] = value
        return result

    def _parse_estimation(self, estimation_str: str) -> Optional[int]:
        """Extract hours from estimation string."""
        match = re.search(r"(\d+)", estimation_str)
        return int(match.group(1)) if match else None

    def check_existing_issues(self) -> Dict[str, Any]:
        """Check if epics/stories already exist in Jira."""
        if self.dry_run:
            return {"epics": [], "stories": []}

        try:
            existing_epics = jira_get_project_issues(self.project_key, "Epic")
            existing_stories = jira_get_project_issues(self.project_key, "Story")

            return {
                "epics": [e.key for e in existing_epics],
                "stories": [s.key for s in existing_stories],
            }
        except Exception as e:
            print(f"⚠️  Warning: Could not check existing issues: {e}")
            return {"epics": [], "stories": []}

    def create_epics(self) -> None:
        """Create all epics in Jira."""
        if not self.epics:
            print("❌ No epics found in markdown file!")
            return

        print(f"\n📚 Creating {len(self.epics)} Epics...")
        print("=" * 60)

        for epic_name, epic_data in sorted(self.epics.items()):
            summary = epic_data["summary"]
            description = epic_data["description"]

            print(f"\n📝 {epic_name}: {summary}")
            print(f"   Description: {description[:80]}...")

            if self.dry_run:
                print(f"   [DRY RUN] Would create epic in project {self.project_key}")
                self.created_epics[epic_name] = (
                    f"{self.project_key}-{100 + int(epic_data['number'])}"
                )
            else:
                try:
                    epic_key = jira_create_epic(self.project_key, summary, description)
                    self.created_epics[epic_name] = epic_key
                    print(f"   ✅ Created: {epic_key}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

    def create_stories(self) -> None:
        """Create all stories in Jira and link to epics."""
        if not self.stories:
            print("❌ No stories found in markdown file!")
            return

        print(f"\n📖 Creating {len(self.stories)} Stories...")
        print("=" * 60)

        for story_name, story_data in sorted(self.stories.items()):
            epic_num = story_data["epic_num"]
            epic_name = f"Epic {epic_num}"
            epic_key = self.created_epics.get(
                epic_name, f"{self.project_key}-{100 + int(epic_num)}"
            )

            summary = story_data["summary"]
            description = story_data["description"]
            labels = story_data["labels"]

            print(f"\n📄 {story_name}: {summary}")
            print(f"   Epic: {epic_key}")
            print(
                f"   Estimation: {story_data['estimation_hours']} hours"
                if story_data["estimation_hours"]
                else "   Estimation: Not specified"
            )

            if self.dry_run:
                print(f"   [DRY RUN] Would create story in project {self.project_key}")
                self.created_stories.append(
                    f"{self.project_key}-{200 + len(self.created_stories)}"
                )
            else:
                try:
                    story_key = jira_create_story(
                        self.project_key,
                        summary,
                        description,
                        parent_key=epic_key,
                        estimation_hours=story_data["estimation_hours"],
                        labels=labels,
                    )
                    self.created_stories.append(story_key)
                    print(f"   ✅ Created: {story_key}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")

    def generate_report(self) -> None:
        """Generate a summary report."""
        print("\n" + "=" * 60)
        print("📊 IMPORT REPORT")
        print("=" * 60)

        print(f"\n✅ Epics Created: {len(self.created_epics)}")
        for name, key in sorted(self.created_epics.items()):
            print(f"   - {key}: {name}")

        print(f"\n✅ Stories Created: {len(self.created_stories)}")
        if len(self.created_stories) <= 10:
            for key in self.created_stories:
                print(f"   - {key}")
        else:
            for key in self.created_stories[:5]:
                print(f"   - {key}")
            print(f"   ... and {len(self.created_stories) - 5} more")

        total_hours = sum(
            s.get("estimation_hours", 0) or 0 for s in self.stories.values()
        )
        print(f"\n⏱️  Total Estimated Hours: {total_hours}")

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No actual changes were made to Jira!")

        print("\n" + "=" * 60)

    def run(self) -> int:
        """Run the importer."""
        try:
            print(f"📂 Reading {self.md_file}...")
            content = self.read_file()

            print("🔍 Parsing epics...")
            self.parse_epics(content)
            print(f"   Found {len(self.epics)} epics")

            print("🔍 Parsing stories...")
            self.parse_stories(content)
            print(f"   Found {len(self.stories)} stories")

            print("\n🔐 Verifying Jira connection...")
            if not self.dry_run:
                try:
                    result = check_connectivity()
                    if result.get("success"):
                        print("   ✅ Jira connection successful")
                    else:
                        raise Exception(
                            result.get("error", "Unknown connectivity error")
                        )
                except Exception as e:
                    print(f"   ❌ Jira connection failed: {e}")
                    return 1
            else:
                print("   ⏭️  Skipped (dry-run mode)")

            if not self.dry_run:
                print("\n📋 Checking for existing issues...")
                existing = self.check_existing_issues()
                if existing["epics"] or existing["stories"]:
                    print(
                        f"   ⚠️  Found {len(existing['epics'])} existing epics and {len(existing['stories'])} existing stories"
                    )
                    if not self.force:
                        response = (
                            input("   Continue anyway? (yes/no): ").strip().lower()
                        )
                        if response != "yes":
                            print("   Cancelled.")
                            return 0
                    else:
                        print("   ✅ Proceeding (--force flag set)")

            self.create_epics()
            self.create_stories()
            self.generate_report()

            return 0

        except Exception as e:
            print(f"\n❌ Error: {e}", file=sys.stderr)
            import traceback

            traceback.print_exc()
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Import Jira epics and stories from markdown file"
    )
    parser.add_argument(
        "--file", "-f", required=True, help="Path to JIRA_EPICS_AND_STORIES.md file"
    )
    parser.add_argument(
        "--project", "-p", default="DAI", help="Jira project key (default: DAI)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without actually creating",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt for existing issues",
    )

    args = parser.parse_args()

    importer = JiraImporter(args.file, args.project, args.dry_run, args.force)
    return importer.run()


if __name__ == "__main__":
    sys.exit(main())
