#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///

from adw_modules.data_types import ADWStateData, IssueClassSlashCommand, ReviewIssue, ReviewResult

# Test /new in IssueClassSlashCommand
print('=== Testing IssueClassSlashCommand ===')
try:
    state = ADWStateData(
        adw_id='test123',
        issue_class='/new',
        domain='ADW_Agent',
        agent_name='DummyAgent'
    )
    print(f'✅ Created state with /new: {state.model_dump()}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test default domain
print('\n=== Testing default domain ===')
try:
    state = ADWStateData(adw_id='test123')
    print(f'✅ Default domain: {state.domain}')
except Exception as e:
    print(f'❌ Error: {e}')

# Test ReviewIssue
print('\n=== Testing ReviewIssue ===')
try:
    review_issue = ReviewIssue(
        review_issue_number=1,
        screenshot_path="/path/to/screenshot.png",
        issue_description="Function is missing error handling",
        issue_resolution="Add try-catch blocks around the function",
        issue_severity="blocker"
    )
    print(f'✅ Created ReviewIssue: {review_issue.model_dump()}')
except Exception as e:
    print(f'❌ Error creating ReviewIssue: {e}')

# Test ReviewResult
print('\n=== Testing ReviewResult ===')
try:
    review_result = ReviewResult(
        success=False,
        review_issues=[
            ReviewIssue(
                review_issue_number=1,
                screenshot_path="",
                issue_description="Missing validation",
                issue_resolution="Add input validation",
                issue_severity="tech_debt"
            ),
            ReviewIssue(
                review_issue_number=2,
                screenshot_path="/screenshots/error.png",
                issue_description="Critical error in main function",
                issue_resolution="Fix the null pointer exception",
                issue_severity="blocker"
            )
        ],
        screenshots=["/screenshots/main.png", "/screenshots/error.png"],
        screenshot_urls=[]
    )
    print(f'✅ Created ReviewResult: {review_result.model_dump()}')
    
    # Test JSON serialization
    json_str = review_result.model_dump_json()
    print(f'✅ JSON serialization successful (length: {len(json_str)})')
    
except Exception as e:
    print(f'❌ Error creating ReviewResult: {e}')

# Test severity validation
print('\n=== Testing severity validation ===')
try:
    invalid_issue = ReviewIssue(
        review_issue_number=1,
        screenshot_path="",
        issue_description="Test issue",
        issue_resolution="Test resolution",
        issue_severity="invalid_severity"
    )
    print(f'❌ Should have failed with invalid severity')
except Exception as e:
    print(f'✅ Correctly rejected invalid severity: {e}')
