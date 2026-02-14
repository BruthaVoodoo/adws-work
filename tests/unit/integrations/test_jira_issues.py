"""
Test data for fake Jira issues for plan generation testing.

Provides mock Jira issue data in the format that the Jira API returns,
allowing us to test plan generation for chore, feature, and bug issues.
"""


def get_test_chore_issue():
    """Get a mock chore issue in Jira API format."""
    return {
        "key": "TEST-001",
        "fields": {
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
            "issuetype": {"name": "Task"},
            "priority": {"name": "Medium"},
            "status": {"name": "To Do"},
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
            "labels": ["types", "typescript", "foundation"],
        },
    }


def get_test_feature_issue():
    """Get a mock feature issue in Jira API format."""
    return {
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


def get_test_bug_issue():
    """Get a mock bug issue in Jira API format."""
    return {
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
            "creator": {"displayName": "QA Engineer", "emailAddress": "qa@example.com"},
            "created": "2026-01-29T08:45:00.000-0800",
            "updated": "2026-01-29T09:30:00.000-0800",
            "labels": ["mobile", "login", "redirect", "critical-bug", "ios", "android"],
        },
    }


def get_all_test_issues():
    """Get all test issues keyed by issue number."""
    return {
        "TEST-001": get_test_chore_issue(),
        "TEST-002": get_test_feature_issue(),
        "TEST-003": get_test_bug_issue(),
    }


def mock_jira_fetch_issue(issue_number):
    """Mock version of jira_fetch_issue for testing."""
    test_issues = get_all_test_issues()

    if issue_number in test_issues:
        return test_issues[issue_number]
    else:
        raise ValueError(
            f"Test issue {issue_number} not found. Available: TEST-001, TEST-002, TEST-003"
        )


if __name__ == "__main__":
    # Print test issues for verification
    print("Available Test Issues:")
    print("=" * 50)

    issues = get_all_test_issues()
    for issue_key, issue_data in issues.items():
        print(f"\n{issue_key}: {issue_data['fields']['summary']}")
        issue_type = issue_data["fields"]["issuetype"]["name"]
        description_len = len(issue_data["fields"]["description"])
        labels = (
            ", ".join(issue_data["fields"]["labels"])
            if issue_data["fields"]["labels"]
            else "None"
        )

        # Map issue type to our slash commands
        if issue_type == "Task":
            slash_command = "/chore"
        elif issue_type == "Story":
            slash_command = "/feature"
        elif issue_type == "Bug":
            slash_command = "/bug"
        else:
            slash_command = "/unknown"

        print(f"Type: {issue_type} ({slash_command})")
        print(f"Priority: {issue_data['fields']['priority']['name']}")
        print(f"Status: {issue_data['fields']['status']['name']}")
        print(f"Description length: {description_len} characters")
        print(f"Labels: {labels}")

    print(f"\n\nTo test plan generation with these issues:")
    print(f"1. Replace jira_fetch_issue() calls with mock_jira_fetch_issue()")
    print(f"2. Run plan generation:")
    print(f"   python3 scripts/adw_plan.py TEST-001  # Chore")
    print(f"   python3 scripts/adw_plan.py TEST-002  # Feature")
    print(f"   python3 scripts/adw_plan.py TEST-003  # Bug")
