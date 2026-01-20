# E2E Test: Status Endpoint Health Check

## Test Objective
Verify that the GET /api/status endpoint returns proper health information and is accessible from the frontend.

## Test Steps

1. **Start the Backend Server**
   - Navigate to the backend directory
   - Run `npm start` to start the Express server
   - Verify server starts on port 5000

2. **Test API Endpoint Directly**
   - Make a GET request to `http://localhost:5000/api/status`
   - Verify response status is 200
   - Verify response contains:
     - `status: "ok"`
     - `timestamp` field with valid ISO date
     - `service: "test-app-backend"`
     - `version` field with semantic version

3. **Test Frontend Integration** 
   - Start the frontend development server (`npm start` in frontend directory)
   - Navigate to the application in browser
   - Trigger any API call that might use the status endpoint
   - Verify no CORS errors or connectivity issues

## Expected Results

- ✅ Backend server starts successfully
- ✅ Status endpoint returns 200 OK
- ✅ Response JSON contains all required fields
- ✅ Frontend can communicate with backend without CORS issues
- ✅ Timestamp is properly formatted and current

## Test Environment

- **Backend**: Express.js server on localhost:5000
- **Frontend**: React development server
- **Test Tool**: Manual verification or automated API testing

## Acceptance Criteria

This test passes when:
1. The status endpoint is reachable and returns proper JSON
2. All required fields are present in the response
3. The response indicates the service is healthy
4. No errors occur during the full request-response cycle