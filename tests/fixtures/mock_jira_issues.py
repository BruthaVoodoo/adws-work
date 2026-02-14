"""
Test script to create fake Jira issues for testing plan generation.

This creates mock Jira issues that can be used to test the plan generation
functionality without needing actual Jira connectivity.
"""

import sys
import os
from typing import Dict, Any

# Add the scripts directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

try:
    from adw_modules.data_types import JiraIssue
except ImportError:
    # Fallback if running from different directory
    sys.path.insert(
        0, os.path.join(os.path.dirname(__file__), "..", "scripts", "adw_modules")
    )
    from data_types import JiraIssue


class MockJiraIssueCreator:
    """Creates mock Jira issues for testing plan generation."""

    @staticmethod
    def get_all_test_issues() -> Dict[str, JiraIssue]:
        """Get all test issues in a dictionary keyed by issue number."""
        # Create the actual raw issue data that comes from Jira API
        raw_chore = MockJiraIssueCreator._get_raw_chore_issue()
        raw_feature = MockJiraIssueCreator._get_raw_feature_issue()
        raw_bug = MockJiraIssueCreator._get_raw_bug_issue()

        return {
            "TEST-001": JiraIssue.from_raw_jira_issue(raw_chore),
            "TEST-002": JiraIssue.from_raw_jira_issue(raw_feature),
            "TEST-003": JiraIssue.from_raw_jira_issue(raw_bug),
        }
        return JiraIssue.from_raw_jira_issue(raw_issue)

    @staticmethod
    def create_feature_issue() -> JiraIssue:
        """Create a mock feature issue."""
        raw_issue = {
            "key": "TEST-002",
            "fields": {
                "summary": "Implement user authentication system",
                "description": """Implement a comprehensive user authentication system for the application.

User Stories:
- As a user, I want to create an account with email and password
- As a user, I want to log in securely with my credentials
- As a user, I want to reset my password if I forget it
- As an admin, I want to manage user roles and permissions

Technical Requirements:
- JWT-based authentication
- Password hashing using bcrypt
- Role-based access control (RBAC)
- Password reset functionality via email
- Session management
- Multi-factor authentication support (future)

Security Considerations:
- Input validation and sanitization
- Rate limiting for login attempts
- Secure password storage
- HTTPS enforcement
- Session timeout handling

Integration Points:
- Database for user storage
- Email service for password reset
- Frontend login/register forms
- API endpoints protection""",
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
                "status": {"name": "In Progress"},
                "assignee": {
                    "displayName": "Feature Developer",
                    "emailAddress": "feature.dev@example.com",
                },
                "creator": {
                    "displayName": "Product Manager",
                    "emailAddress": "pm@example.com",
                },
                "created": "2026-01-28T14:30:00.000-0800",
                "updated": "2026-01-29T09:15:00.000-0800",
                "labels": ["authentication", "security", "user-management", "feature"],
            },
        }
        return JiraIssue.from_raw_jira_issue(raw_issue)

    @staticmethod
    def create_bug_issue() -> JiraIssue:
        """Create a mock bug issue."""
        raw_issue = {
            "key": "TEST-003",
            "fields": {
                "summary": "User login redirect fails on mobile devices",
                "description": """Users on mobile devices are experiencing login redirect failures.

Problem Description:
After successfully logging in on mobile devices (iOS Safari, Android Chrome), users are not being redirected to their intended destination page. Instead, they remain on the login page or are redirected to a blank page.

Steps to Reproduce:
1. Open the app on mobile browser (iOS Safari 16+ or Android Chrome 120+)
2. Navigate to any protected page (e.g., /dashboard, /profile)
3. Get redirected to /login with returnUrl parameter
4. Enter valid credentials and submit login form
5. Observe that redirect fails

Expected Behavior:
User should be redirected to the original page they were trying to access (or dashboard if no specific page).

Actual Behavior:
- iOS Safari: Stays on login page, shows success message but no redirect
- Android Chrome: Redirects to blank page with URL showing correct destination
- Desktop browsers: Works correctly

Technical Investigation Needed:
- Check mobile browser session handling
- Verify URL parameter parsing on mobile
- Review JavaScript redirect mechanism
- Test with different mobile browsers/versions

Impact:
- Affects 40% of our mobile users
- Significant UX degradation
- Users have to manually navigate after login
- Potential security concerns with session handling

Severity: High
Priority: Critical""",
                "issuetype": {"name": "Bug"},
                "priority": {"name": "Critical"},
                "status": {"name": "Open"},
                "assignee": {
                    "displayName": "Mobile Developer",
                    "emailAddress": "mobile.dev@example.com",
                },
                "creator": {
                    "displayName": "QA Engineer",
                    "emailAddress": "qa@example.com",
                },
                "created": "2026-01-29T08:45:00.000-0800",
                "updated": "2026-01-29T09:30:00.000-0800",
                "labels": [
                    "mobile",
                    "login",
                    "redirect",
                    "critical-bug",
                    "ios",
                    "android",
                ],
            },
        }
        return JiraIssue.from_raw_jira_issue(raw_issue)

    @staticmethod
    def get_all_test_issues() -> Dict[str, JiraIssue]:
        """Get all test issues in a dictionary keyed by issue number."""
        # Create the actual raw issue data that comes from Jira API
        raw_chore = MockJiraIssueCreator._get_raw_chore_issue()
        raw_feature = MockJiraIssueCreator._get_raw_feature_issue()
        raw_bug = MockJiraIssueCreator._get_raw_bug_issue()

        return {
            "TEST-001": JiraIssue.from_raw_jira_issue(raw_chore),
            "TEST-002": JiraIssue.from_raw_jira_issue(raw_feature),
            "TEST-003": JiraIssue.from_raw_jira_issue(raw_bug),
        }

    @staticmethod
    def _get_raw_chore_issue() -> Any:
        """Get raw chore issue data in Jira API format."""
        return type(
            "MockJiraIssue",
            (),
            {
                "key": "TEST-001",
                "fields": type(
                    "Fields",
                    (),
                    {
                        "summary": "Define TypeScript types in types.ts",
                        "description": """This chore involves defining comprehensive TypeScript types for the Jira testing module.

The types.ts file needs to include:
- NormalizedEpic interface with all required fields
- NormalizedStory interface with proper typing
- Filter types for EpicFilters and story filtering
- Supporting types for assignees, links, and scoring

This is foundational work that will support other development tasks and ensure type safety across the application.

Acceptance Criteria:
- All TypeScript interfaces are properly defined
- Types compile without errors
- Documentation is included for complex types
- Types support both creation and update operations""",
                        "issuetype": type("IssueType", (), {"name": "Task"})(),
                        "priority": type("Priority", (), {"name": "Medium"})(),
                        "status": type("Status", (), {"name": "To Do"})(),
                        "assignee": type(
                            "Assignee",
                            (),
                            {
                                "displayName": "Test User",
                                "emailAddress": "test@example.com",
                            },
                        )(),
                        "creator": type(
                            "Creator",
                            (),
                            {
                                "displayName": "Test Creator",
                                "emailAddress": "creator@example.com",
                            },
                        )(),
                        "created": "2026-01-29T10:00:00.000-0800",
                        "updated": "2026-01-29T10:00:00.000-0800",
                        "labels": ["types", "typescript", "foundation"],
                    },
                )(),
            },
        )()

    @staticmethod
    def _get_raw_feature_issue() -> Any:
        """Get raw feature issue data in Jira API format."""
        return type(
            "MockJiraIssue",
            (),
            {
                "key": "TEST-002",
                "fields": type(
                    "Fields",
                    (),
                    {
                        "summary": "Implement user authentication system",
                        "description": """Implement a comprehensive user authentication system for the application.

User Stories:
- As a user, I want to create an account with email and password
- As a user, I want to log in securely with my credentials
- As a user, I want to reset my password if I forget it
- As an admin, I want to manage user roles and permissions

Technical Requirements:
- JWT-based authentication
- Password hashing using bcrypt
- Role-based access control (RBAC)
- Password reset functionality via email
- Session management
- Multi-factor authentication support (future)

Security Considerations:
- Input validation and sanitization
- Rate limiting for login attempts
- Secure password storage
- HTTPS enforcement
- Session timeout handling

Integration Points:
- Database for user storage
- Email service for password reset
- Frontend login/register forms
- API endpoints protection""",
                        "issuetype": type("IssueType", (), {"name": "Story"})(),
                        "priority": type("Priority", (), {"name": "High"})(),
                        "status": type("Status", (), {"name": "In Progress"})(),
                        "assignee": type(
                            "Assignee",
                            (),
                            {
                                "displayName": "Feature Developer",
                                "emailAddress": "feature.dev@example.com",
                            },
                        )(),
                        "creator": type(
                            "Creator",
                            (),
                            {
                                "displayName": "Product Manager",
                                "emailAddress": "pm@example.com",
                            },
                        )(),
                        "created": "2026-01-28T14:30:00.000-0800",
                        "updated": "2026-01-29T09:15:00.000-0800",
                        "labels": [
                            "authentication",
                            "security",
                            "user-management",
                            "feature",
                        ],
                    },
                )(),
            },
        )()

    @staticmethod
    def _get_raw_bug_issue() -> Any:
        """Get raw bug issue data in Jira API format."""
        return type(
            "MockJiraIssue",
            (),
            {
                "key": "TEST-003",
                "fields": type(
                    "Fields",
                    (),
                    {
                        "summary": "User login redirect fails on mobile devices",
                        "description": """Users on mobile devices are experiencing login redirect failures.

Problem Description:
After successfully logging in on mobile devices (iOS Safari, Android Chrome), users are not being redirected to their intended destination page. Instead, they remain on the login page or are redirected to a blank page.

Steps to Reproduce:
1. Open the app on mobile browser (iOS Safari 16+ or Android Chrome 120+)
2. Navigate to any protected page (e.g., /dashboard, /profile)
3. Get redirected to /login with returnUrl parameter
4. Enter valid credentials and submit login form
5. Observe that redirect fails

Expected Behavior:
User should be redirected to the original page they were trying to access (or dashboard if no specific page).

Actual Behavior:
- iOS Safari: Stays on login page, shows success message but no redirect
- Android Chrome: Redirects to blank page with URL showing correct destination
- Desktop browsers: Works correctly

Technical Investigation Needed:
- Check mobile browser session handling
- Verify URL parameter parsing on mobile
- Review JavaScript redirect mechanism
- Test with different mobile browsers/versions

Impact:
- Affects 40% of our mobile users
- Significant UX degradation
- Users have to manually navigate after login
- Potential security concerns with session handling

Severity: High
Priority: Critical""",
                        "issuetype": type("IssueType", (), {"name": "Bug"})(),
                        "priority": type("Priority", (), {"name": "Critical"})(),
                        "status": type("Status", (), {"name": "Open"})(),
                        "assignee": type(
                            "Assignee",
                            (),
                            {
                                "displayName": "Mobile Developer",
                                "emailAddress": "mobile.dev@example.com",
                            },
                        )(),
                        "creator": type(
                            "Creator",
                            (),
                            {
                                "displayName": "QA Engineer",
                                "emailAddress": "qa@example.com",
                            },
                        )(),
                        "created": "2026-01-29T08:45:00.000-0800",
                        "updated": "2026-01-29T09:30:00.000-0800",
                        "labels": [
                            "mobile",
                            "login",
                            "redirect",
                            "critical-bug",
                            "ios",
                            "android",
                        ],
                    },
                )(),
            },
        )()


def mock_jira_fetch_issue(issue_number: str) -> Dict[str, Any]:
    """Mock version of jira_fetch_issue for testing."""
    test_issues = MockJiraIssueCreator.get_all_test_issues()

    if issue_number in test_issues:
        # Return the raw Jira issue format that jira_fetch_issue would return
        issue = test_issues[issue_number]
        return {
            "key": issue.key,
            "fields": {
                "summary": issue.title,
                "description": issue.description,
                "issuetype": {
                    "name": "Task"
                    if issue_number == "TEST-001"
                    else ("Story" if issue_number == "TEST-002" else "Bug")
                },
                "priority": {"name": issue.priority or "Medium"},
                "status": {"name": issue.status or "To Do"},
                "assignee": {
                    "displayName": "Test User",
                    "emailAddress": "test@example.com",
                },
                "creator": {
                    "displayName": "Test Creator",
                    "emailAddress": "creator@example.com",
                },
                "created": "2026-01-29T10:00:00.000-0800",
                "updated": "2026-01-29T10:00:00.000-0800",
                "labels": issue.labels or [],
            },
        }
    else:
        raise ValueError(
            f"Test issue {issue_number} not found. Available: TEST-001, TEST-002, TEST-003"
        )


if __name__ == "__main__":
    # Print test issues for verification
    print("Available Test Issues:")
    print("=" * 50)

    issues = MockJiraIssueCreator.get_all_test_issues()
    for issue_key, issue in issues.items():
        print(f"\n{issue_key}: {issue.title}")
        print(
            f"Type: {'Chore' if '001' in issue_key else ('Feature' if '002' in issue_key else 'Bug')}"
        )
        print(f"Description length: {len(issue.description)} characters")
        print(f"Labels: {', '.join(issue.labels) if issue.labels else 'None'}")

    print(f"\n\nTo test plan generation, run:")
    print(f"  python3 scripts/adw_plan.py TEST-001  # Chore")
    print(f"  python3 scripts/adw_plan.py TEST-002  # Feature")
    print(f"  python3 scripts/adw_plan.py TEST-003  # Bug")
