# Example E2E Test: [Feature Name]

<!-- 
This is an End-to-End test scenario that will be executed by AI.
The AI will read this file and follow the instructions to test your application.

Guidelines:
- Describe step-by-step test procedures
- Include expected results and acceptance criteria  
- Be specific about URLs, UI elements, API endpoints
- The AI can use tools to make HTTP requests, run commands, etc.
-->

## Test Objective
Describe what this test validates (e.g., "Verify the status endpoint returns proper health information and is accessible")

## Prerequisites
- Application servers are running
- Test data is available (if needed)
- Any required setup steps completed

## Test Steps

### 1. Server Startup Verification
- Start the backend server (if not running)
- Verify server responds on expected port
- **Expected Result**: Server starts successfully without errors

### 2. API Endpoint Testing
- Make GET request to the target endpoint
- Verify HTTP status code is 200
- Verify response Content-Type is `application/json`
- **Expected Result**: Endpoint responds with valid JSON

### 3. Response Validation  
- Check that all required fields are present in response
- Validate data types and value ranges
- Verify response structure matches specification
- **Expected Result**: Response contains all expected fields with correct types

### 4. Integration Testing
- Test endpoint behavior under different conditions
- Verify interaction with other system components  
- Check for proper error handling
- **Expected Result**: System behaves correctly in various scenarios

## Acceptance Criteria
- ✅ Endpoint is reachable and responds quickly
- ✅ Response status is 200 OK
- ✅ Response JSON contains all required fields
- ✅ All field values are within expected ranges/formats
- ✅ No errors occur during the full request-response cycle
- ✅ System integrations work correctly

## Test Environment
- **Backend**: Specify server details (e.g., Express.js on localhost:5000)
- **Frontend**: Specify frontend details if applicable
- **Test Tools**: Manual verification and/or automated API testing

## Notes
- Add any specific considerations for this test
- Include troubleshooting tips or common issues
- Note any dependencies or limitations