#!/usr/bin/env -S uv run
# /// script
# dependencies = ["pydantic"]
# ///

"""
Simple test for review workflow functions.
"""

import sys
import os

# Add the parent directory to the path so we can import adw_modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from adw_modules.data_types import ReviewIssue, ReviewResult
from adw_modules.workflow_ops import create_patch_plan, find_spec_file
from adw_modules.state import ADWState

# Test ReviewIssue and ReviewResult creation
print('=== Testing Review Data Types ===')
try:
    issue = ReviewIssue(
        review_issue_number=1,
        screenshot_path="",
        issue_description="Test issue description",
        issue_resolution="Test resolution",
        issue_severity="blocker"
    )
    
    result = ReviewResult(
        success=False,
        review_issues=[issue],
        screenshots=[],
        screenshot_urls=[]
    )
    
    print('✅ Review data types created successfully')
    print(f'   Issue severity: {issue.issue_severity}')
    print(f'   Result success: {result.success}')
    print(f'   Issues count: {len(result.review_issues)}')
    
except Exception as e:
    print(f'❌ Error creating review data types: {e}')

# Test that the workflow functions exist and are callable
print('\n=== Testing Workflow Function Availability ===')
try:
    # Test that functions exist and are callable
    assert callable(create_patch_plan), "create_patch_plan is not callable"
    assert callable(find_spec_file), "find_spec_file is not callable"
    
    print('✅ Workflow functions are available and callable')
    
except Exception as e:
    print(f'❌ Error testing workflow functions: {e}')

# Test basic find_spec_file with minimal state (should handle gracefully)
print('\n=== Testing find_spec_file with minimal state ===')
try:
    # Create a minimal state
    state = ADWState("test-adw-id")
    
    # This should return None gracefully since no plan_file is set
    spec_file = find_spec_file(state, None)
    
    if spec_file is None:
        print('✅ find_spec_file handled missing plan_file gracefully')
    else:
        print(f'⚠️  find_spec_file returned unexpected result: {spec_file}')
        
except Exception as e:
    print(f'❌ Error in find_spec_file test: {e}')

print('\n=== All Review Workflow Tests Complete ===')