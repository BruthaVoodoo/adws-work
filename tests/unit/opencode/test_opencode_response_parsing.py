"""
Unit tests for OpenCode response parsing and plan content extraction.

Tests the fixed extract_text_response() function with various OpenCode response structures
to ensure plan content is properly extracted from tool_use parts.
"""

import unittest
import json
from typing import Dict, List, Any

# Import the functions we want to test
from scripts.adw_modules.opencode_http_client import (
    extract_text_response,
    extract_tool_execution_details,
    estimate_metrics_from_parts,
)
from scripts.adw_modules.agent import convert_opencode_to_agent_response


class TestOpenCodeResponseParsing(unittest.TestCase):
    """Test OpenCode response parsing for plan content extraction."""

    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None

    def test_extract_text_response_with_text_only(self):
        """Test extraction from text-only response parts."""
        parts = [
            {"type": "text", "content": "This is a conversational response."},
            {"type": "text", "content": "With multiple text parts."},
        ]

        result = extract_text_response(parts)
        expected = "This is a conversational response.\nWith multiple text parts."
        self.assertEqual(result, expected)

    def test_extract_text_response_with_plan_tool_use(self):
        """Test extraction of plan content from tool_use parts."""
        parts = [
            {"type": "text", "content": "I'm creating a comprehensive plan."},
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "ai_docs/specs/chore/DAI-291-5004c442-plan.md",
                    "content": "# Chore: Define TypeScript types in types.ts\n\n## Description\n\nThis chore involves defining comprehensive TypeScript types...",
                },
            },
            {"type": "tool_result", "output": "File created successfully"},
        ]

        result = extract_text_response(parts)
        expected = "I'm creating a comprehensive plan.\n# Chore: Define TypeScript types in types.ts\n\n## Description\n\nThis chore involves defining comprehensive TypeScript types..."
        self.assertEqual(result, expected)

    def test_extract_text_response_with_multiple_plan_files(self):
        """Test extraction when multiple plan files are created."""
        parts = [
            {"type": "text", "content": "Creating multiple plan files."},
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "specs/feature/PROJ-123-abc123-plan.md",
                    "content": "# Feature: User Authentication\n\n## Overview\nImplement user authentication system...",
                },
            },
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "specs/bug/PROJ-456-def456-plan.md",
                    "content": "# Bug: Fix login redirect\n\n## Issue\nUsers are not redirected after login...",
                },
            },
        ]

        result = extract_text_response(parts)
        expected = "Creating multiple plan files.\n# Feature: User Authentication\n\n## Overview\nImplement user authentication system...\n# Bug: Fix login redirect\n\n## Issue\nUsers are not redirected after login..."
        self.assertEqual(result, expected)

    def test_extract_text_response_ignores_non_plan_tool_use(self):
        """Test that non-plan tool_use parts are ignored."""
        parts = [
            {"type": "text", "content": "Working on the project."},
            {"type": "tool_use", "tool": "read", "input": {"path": "src/utils.py"}},
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "tests/test_feature.py",
                    "content": "import unittest\n# Test code here...",
                },
            },
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "specs/feature/FEAT-789-xyz789-plan.md",
                    "content": "# Feature: New Dashboard\n\n## Requirements\nCreate a new dashboard...",
                },
            },
        ]

        result = extract_text_response(parts)
        expected = "Working on the project.\n# Feature: New Dashboard\n\n## Requirements\nCreate a new dashboard..."
        self.assertEqual(result, expected)

    def test_extract_text_response_handles_malformed_parts(self):
        """Test graceful handling of malformed or missing data."""
        parts = [
            {"type": "text", "content": "Valid text part."},
            {"type": "tool_use"},  # Missing input
            {"type": "tool_use", "input": {}},  # Empty input
            {"type": "tool_use", "input": {"path": "not-a-plan.py"}},  # Non-plan file
            {
                "type": "tool_use",
                "input": {"path": "specs/chore/TEST-plan.md"},
            },  # Missing content
            {
                "type": "tool_use",
                "input": {"path": "specs/bug/BUG-123-plan.md", "content": ""},
            },  # Empty content
            {
                "type": "tool_use",
                "input": {
                    "path": "specs/feature/FEAT-456-plan.md",
                    "content": "# Valid plan content",
                },
            },
            "invalid_part",  # Not a dict
            {"invalid": "structure"},  # Missing type
        ]

        result = extract_text_response(parts)
        expected = "Valid text part.\n# Valid plan content"
        self.assertEqual(result, expected)

    def test_extract_text_response_empty_parts(self):
        """Test handling of empty parts list."""
        parts = []
        result = extract_text_response(parts)
        self.assertEqual(result, "")

    def test_extract_text_response_plan_content_extraction_patterns(self):
        """Test various plan file path patterns are detected."""
        test_cases = [
            "ai_docs/specs/chore/DAI-291-abc123-plan.md",
            "specs/feature/PROJ-123-def456-plan.md",
            "plans/bug/BUG-789-ghi789-plan.md",
            "implementation-plan.md",
            "task-plan.md",
        ]

        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                parts = [
                    {
                        "type": "tool_use",
                        "tool": "write",
                        "input": {
                            "path": file_path,
                            "content": f"# Plan for {file_path}\n\nContent here...",
                        },
                    }
                ]

                result = extract_text_response(parts)
                expected = f"# Plan for {file_path}\n\nContent here..."
                self.assertEqual(result, expected)

    def test_convert_opencode_to_agent_response_with_plan_content(self):
        """Test the complete conversion flow with plan content."""
        # Mock OpenCodeHTTPClient - we only need it for the signature
        mock_client = None

        response_data = {
            "info": {"model": "claude-haiku-4.5", "usage": {"tokens": 150}},
            "parts": [
                {
                    "type": "text",
                    "content": "I have successfully created the comprehensive chore plan.",
                },
                {
                    "type": "tool_use",
                    "tool": "write",
                    "input": {
                        "path": "ai_docs/specs/chore/DAI-291-test123-plan.md",
                        "content": "# Chore: Test Plan\n\n## Description\nThis is a test plan for unit testing.\n\n## Steps\n1. First step\n2. Second step\n\n## Validation\n- Check that types compile\n- Run tests",
                    },
                },
                {"type": "tool_result", "output": "File created successfully"},
            ],
            "session_id": "test_session_123",
            "success": True,
        }

        result = convert_opencode_to_agent_response(response_data, mock_client)

        # Check that the agent response contains both conversational text AND plan content
        expected_output = "I have successfully created the comprehensive chore plan.\n# Chore: Test Plan\n\n## Description\nThis is a test plan for unit testing.\n\n## Steps\n1. First step\n2. Second step\n\n## Validation\n- Check that types compile\n- Run tests"

        self.assertEqual(result.output, expected_output)
        self.assertTrue(result.success)
        self.assertEqual(result.session_id, "test_session_123")


class TestPlanContentExtractionScenarios(unittest.TestCase):
    """Test realistic plan content extraction scenarios for different story types."""

    def test_chore_plan_extraction(self):
        """Test extraction of chore plan content."""
        parts = [
            {
                "type": "text",
                "content": "I have successfully created the comprehensive chore plan for DAI-291.",
            },
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "ai_docs/specs/chore/DAI-291-5004c442-plan.md",
                    "content": """# Chore: Define TypeScript types in types.ts

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

## Validation Commands
- npm run build
- npx tsc --noEmit
- Manual verification of all required types

## Notes
Design decisions, type safety considerations, integration points.""",
                },
            },
            {"type": "tool_result", "output": "Plan file created successfully"},
        ]

        result = extract_text_response(parts)

        # Verify it contains both conversational summary and actual plan
        self.assertIn("I have successfully created", result)
        self.assertIn("# Chore: Define TypeScript types", result)
        self.assertIn("## Step by Step Tasks", result)
        self.assertIn("npm run build", result)

    def test_feature_plan_extraction(self):
        """Test extraction of feature plan content."""
        parts = [
            {
                "type": "text",
                "content": "I've analyzed the feature requirements and created a comprehensive implementation plan.",
            },
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "ai_docs/specs/feature/PROJ-456-abc789-plan.md",
                    "content": """# Feature: User Authentication System

## Description
Implement a secure user authentication system with JWT tokens and role-based access control.

## User Stories
- As a user, I want to log in securely
- As an admin, I want to manage user roles

## Technical Approach
- JWT token implementation
- Password hashing with bcrypt
- Role-based middleware

## Implementation Steps
1. Set up authentication middleware
2. Create user model with password hashing
3. Implement login/logout endpoints
4. Add role-based access control
5. Create frontend login components

## Acceptance Criteria
- Users can log in with email/password
- JWT tokens expire after 24 hours
- Role-based access works correctly

## Testing Strategy
- Unit tests for auth middleware
- Integration tests for login flow
- Security testing for token validation""",
                },
            },
        ]

        result = extract_text_response(parts)

        self.assertIn("I've analyzed the feature requirements", result)
        self.assertIn("# Feature: User Authentication System", result)
        self.assertIn("JWT token implementation", result)
        self.assertIn("## Acceptance Criteria", result)

    def test_bug_plan_extraction(self):
        """Test extraction of bug fix plan content."""
        parts = [
            {
                "type": "text",
                "content": "I've identified the root cause and created a targeted fix plan.",
            },
            {
                "type": "tool_use",
                "tool": "write",
                "input": {
                    "path": "ai_docs/specs/bug/BUG-789-def456-plan.md",
                    "content": """# Bug: Login Redirect Failure

## Issue Description
Users are not being redirected to the intended page after successful login. They remain on the login page.

## Root Cause Analysis
The redirect URL parameter is being lost during the authentication flow due to improper session handling.

## Affected Components
- LoginController.js (lines 45-67)
- AuthMiddleware.js (session handling)
- login.html (redirect parameter)

## Fix Strategy
1. Preserve redirect URL in session storage
2. Update authentication flow to check for stored URL
3. Implement fallback to default dashboard

## Implementation Steps
1. Modify LoginController to store redirect URL
2. Update AuthMiddleware session handling
3. Add redirect logic after successful auth
4. Update frontend to handle redirect parameter
5. Add error handling for invalid redirect URLs

## Testing Plan
- Test redirect with various URL parameters
- Verify security (no external redirects)
- Test fallback behavior
- Cross-browser compatibility testing

## Rollback Plan
If issues arise, revert to previous LoginController version and disable redirect feature temporarily.""",
                },
            },
        ]

        result = extract_text_response(parts)

        self.assertIn("I've identified the root cause", result)
        self.assertIn("# Bug: Login Redirect Failure", result)
        self.assertIn("Root Cause Analysis", result)
        self.assertIn("## Rollback Plan", result)


if __name__ == "__main__":
    unittest.main()
