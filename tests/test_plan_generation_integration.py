"""
Integration test script for plan generation with fixed OpenCode response parsing.

This script tests the complete plan generation flow for chore, feature, and bug
issue types using mock Jira issues and validates that the plan content extraction
works correctly with the new tool_use extraction logic.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import json

# Add the scripts and tests directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Import test data
from test_jira_issues import get_all_test_issues, mock_jira_fetch_issue

# Import the modules we want to test
from scripts.adw_modules.data_types import JiraIssue
from scripts.adw_modules.workflow_ops import build_plan, classify_issue
from scripts.adw_modules.opencode_http_client import extract_text_response
from scripts.adw_modules.agent import convert_opencode_to_agent_response


class TestPlanGenerationIntegration(unittest.TestCase):
    """Integration test for plan generation with mock OpenCode responses."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_issues = get_all_test_issues()
        self.maxDiff = None

    def _create_mock_opencode_response_for_plan(
        self, issue_type: str, issue_key: str
    ) -> dict:
        """Create a realistic mock OpenCode response with plan content in tool_use."""

        if issue_type == "chore":
            plan_content = f"""# Chore: Define TypeScript types in types.ts

## Description
Define comprehensive TypeScript type contracts for the Jira Testing Module based on the DPAP specification.

## Relevance to Project
This chore establishes type safety across the monorepo and supports Epic DAI-278.

## Relevant Files
- shared/types/index.ts (main file to be populated)
- package.json files
- ai_docs/jira-dpap-spec.md (specifications)

## Step by Step Tasks
1. Package preparation and configuration
2. Filter type definitions
3. User/Assignee types
4. Story types
5. Scoring types
6. Epic types
7. API request/response types
8. Component props types
9. Type exports and organization
10. Documentation and validation
11. TypeScript compilation validation
12. Build and type-check commands

## Validation Commands
- npm run build - Verify types compile
- npx tsc --noEmit - TypeScript compiler check
- Manual verification of all required types
- Import testing in client and server packages

## Notes
Design decisions, type safety considerations, integration points, and future considerations."""

        elif issue_type == "feature":
            plan_content = f"""# Feature: Implement user authentication system

## Description
Implement a comprehensive user authentication system for the application with JWT tokens and role-based access control.

## User Stories
- As a user, I want to create an account with email and password
- As a user, I want to log in securely with my credentials
- As a user, I want to reset my password if I forget it
- As an admin, I want to manage user roles and permissions

## Technical Approach
- JWT token implementation
- Password hashing with bcrypt
- Role-based middleware
- Session management
- Email integration for password reset

## Implementation Steps
1. Set up authentication middleware
2. Create user model with password hashing
3. Implement login/logout endpoints
4. Add role-based access control
5. Create frontend login components
6. Implement password reset flow
7. Add session timeout handling
8. Create user management admin interface

## Acceptance Criteria
- Users can log in with email/password
- JWT tokens expire after 24 hours
- Role-based access works correctly
- Password reset emails are sent
- Sessions timeout appropriately
- Admin can manage user roles

## Testing Strategy
- Unit tests for auth middleware
- Integration tests for login flow
- Security testing for token validation
- End-to-end tests for complete user journey

## Security Considerations
- Input validation and sanitization
- Rate limiting for login attempts
- Secure password storage
- HTTPS enforcement"""

        else:  # bug
            plan_content = f"""# Bug: User login redirect fails on mobile devices

## Issue Description
Users on mobile devices are experiencing login redirect failures after successful authentication.

## Root Cause Analysis
The redirect URL parameter is being lost during the authentication flow due to mobile browser session handling differences.

## Affected Components
- LoginController.js (authentication flow)
- SessionManager.js (mobile session handling)
- login.html (redirect parameter processing)
- MobileDetection.js (browser-specific logic)

## Fix Strategy
1. Preserve redirect URL in session storage for mobile browsers
2. Update authentication flow to handle mobile-specific session behavior
3. Implement mobile-specific redirect logic
4. Add mobile browser detection and handling

## Implementation Steps
1. Analyze mobile browser session handling differences
2. Modify LoginController to store redirect URL in session storage
3. Update AuthMiddleware session handling for mobile
4. Add mobile browser detection utility
5. Implement mobile-specific redirect logic after successful auth
6. Update frontend to handle mobile redirect parameters
7. Add error handling for invalid redirect URLs
8. Implement fallback to dashboard for failed redirects

## Testing Plan
- Test redirect with various URL parameters on iOS Safari
- Test redirect functionality on Android Chrome
- Verify security (no external redirects allowed)
- Test fallback behavior when redirect fails
- Cross-browser compatibility testing
- Performance testing on mobile devices

## Rollback Plan
If issues arise, revert to previous LoginController version and disable redirect feature temporarily for mobile browsers.

## Monitoring
Add logging for mobile redirect attempts and failures to monitor success rate post-fix."""

        return {
            "info": {"model": "claude-haiku-4.5", "usage": {"tokens": 250}},
            "parts": [
                {
                    "type": "text",
                    "text": f"I have successfully created the comprehensive {issue_type} plan for {issue_key}. The plan includes detailed steps, validation commands, and implementation guidance.",
                },
                {
                    "type": "tool_use",
                    "tool": "write",
                    "input": {
                        "path": f"ai_docs/specs/{issue_type}/{issue_key}-test123-plan.md",
                        "content": plan_content,
                    },
                },
                {
                    "type": "tool_result",
                    "output": f"Plan file created successfully at ai_docs/specs/{issue_type}/{issue_key}-test123-plan.md",
                },
            ],
            "session_id": "test_session_123",
            "success": True,
        }

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    def test_chore_plan_generation(self, mock_execute_opencode):
        """Test plan generation for chore issue type."""
        # Set up mock response
        mock_response = self._create_mock_opencode_response_for_plan(
            "chore", "TEST-001"
        )
        mock_agent_response = convert_opencode_to_agent_response(mock_response, None)
        mock_execute_opencode.return_value = mock_agent_response

        # Get test issue and convert to JiraIssue
        raw_issue = self.test_issues["TEST-001"]
        issue = JiraIssue.from_raw_jira_issue(type("MockIssue", (), raw_issue)())

        # Test plan generation
        result = build_plan(issue, "/chore", "test123", MagicMock())

        # Verify the response contains both conversational text and plan content
        self.assertTrue(result.success)
        self.assertIn(
            "I have successfully created the comprehensive chore plan", result.output
        )
        self.assertIn("# Chore: Define TypeScript types", result.output)
        self.assertIn("## Step by Step Tasks", result.output)
        self.assertIn("npm run build", result.output)
        self.assertIn("TypeScript compilation validation", result.output)

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    def test_feature_plan_generation(self, mock_execute_opencode):
        """Test plan generation for feature issue type."""
        # Set up mock response
        mock_response = self._create_mock_opencode_response_for_plan(
            "feature", "TEST-002"
        )
        mock_agent_response = convert_opencode_to_agent_response(mock_response, None)
        mock_execute_opencode.return_value = mock_agent_response

        # Get test issue and convert to JiraIssue
        raw_issue = self.test_issues["TEST-002"]
        issue = JiraIssue.from_raw_jira_issue(type("MockIssue", (), raw_issue)())

        # Test plan generation
        result = build_plan(issue, "/feature", "test123", MagicMock())

        # Verify the response contains both conversational text and plan content
        self.assertTrue(result.success)
        self.assertIn(
            "I have successfully created the comprehensive feature plan", result.output
        )
        self.assertIn("# Feature: Implement user authentication", result.output)
        self.assertIn("## User Stories", result.output)
        self.assertIn("JWT token implementation", result.output)
        self.assertIn("## Acceptance Criteria", result.output)

    @patch("scripts.adw_modules.workflow_ops.execute_opencode_prompt")
    def test_bug_plan_generation(self, mock_execute_opencode):
        """Test plan generation for bug issue type."""
        # Set up mock response
        mock_response = self._create_mock_opencode_response_for_plan("bug", "TEST-003")
        mock_agent_response = convert_opencode_to_agent_response(mock_response, None)
        mock_execute_opencode.return_value = mock_agent_response

        # Get test issue and convert to JiraIssue
        raw_issue = self.test_issues["TEST-003"]
        issue = JiraIssue.from_raw_jira_issue(type("MockIssue", (), raw_issue)())

        # Test plan generation
        result = build_plan(issue, "/bug", "test123", MagicMock())

        # Verify the response contains both conversational text and plan content
        self.assertTrue(result.success)
        self.assertIn(
            "I have successfully created the comprehensive bug plan", result.output
        )
        self.assertIn("# Bug: User login redirect fails", result.output)
        self.assertIn("## Root Cause Analysis", result.output)
        self.assertIn("mobile browser session handling", result.output)
        self.assertIn("## Rollback Plan", result.output)

    def test_extract_text_response_with_multiple_plan_types(self):
        """Test that extract_text_response correctly extracts plan content for all types."""

        for issue_type in ["chore", "feature", "bug"]:
            with self.subTest(issue_type=issue_type):
                mock_response = self._create_mock_opencode_response_for_plan(
                    issue_type, f"TEST-{issue_type.upper()}"
                )

                # Extract text using our fixed function
                result = extract_text_response(mock_response["parts"])

                # Verify both conversational text and plan content are present
                self.assertIn(f"comprehensive {issue_type} plan", result)
                self.assertIn(f"# {issue_type.title()}:", result)

                # Verify issue-type specific content
                if issue_type == "chore":
                    self.assertIn("TypeScript type", result)
                    self.assertIn("npm run build", result)
                elif issue_type == "feature":
                    self.assertIn("authentication system", result)
                    self.assertIn("JWT token", result)
                elif issue_type == "bug":
                    self.assertIn("mobile devices", result)
                    self.assertIn("Root Cause Analysis", result)

    def test_plan_content_structure_validation(self):
        """Test that generated plan content has the expected structure."""

        for issue_type in ["chore", "feature", "bug"]:
            with self.subTest(issue_type=issue_type):
                mock_response = self._create_mock_opencode_response_for_plan(
                    issue_type, f"TEST-{issue_type.upper()}"
                )

                result = extract_text_response(mock_response["parts"])

                # Check for required plan sections
                self.assertIn("## Description", result)

                if issue_type == "chore":
                    self.assertIn("## Step by Step Tasks", result)
                    self.assertIn("## Validation Commands", result)
                elif issue_type == "feature":
                    self.assertIn("## User Stories", result)
                    self.assertIn("## Acceptance Criteria", result)
                    self.assertIn("## Testing Strategy", result)
                elif issue_type == "bug":
                    self.assertIn("## Root Cause Analysis", result)
                    self.assertIn("## Implementation Steps", result)
                    self.assertIn("## Rollback Plan", result)


if __name__ == "__main__":
    # Run the integration tests
    print("Running Plan Generation Integration Tests")
    print("=" * 50)

    # Test our OpenCode response parsing fix
    unittest.main(verbosity=2)
