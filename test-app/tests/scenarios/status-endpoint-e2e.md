# E2E Test: Status Endpoint Health Check System

<!-- 
This is an End-to-End test scenario that will be executed by AI agents to validate the health check system.
The test covers integration with MongoDB, endpoint response times, edge cases, and system behavior.

Test Focus:
- Integration testing with existing endpoints and MongoDB
- Health endpoint functionality and consistency
- Edge cases and boundary conditions
- System-level behavior under various scenarios
-->

## Test Objective

Verify that the GET `/api/status` endpoint provides accurate health information reflecting the actual system state, integrates properly with existing endpoints, maintains acceptable response times, and behaves correctly under edge cases and concurrent load. This test validates the complete health check system including MongoDB connection status, server uptime, and endpoint consistency.

## Prerequisites

### Environment Setup
- Node.js and npm are installed
- Backend source code is available at `backend/` directory
- MongoDB connection string is configured (or test can run without MongoDB)
- No other services running on port 3000 (or configured `PORT` env var)
- All npm dependencies are installed (`npm install` in backend directory)

### Initial Conditions
- Backend server has not been started (or is stopped)
- MongoDB connection state is known or can be controlled
- System time is synchronized
- Test execution environment has curl or similar HTTP client capability

## Test Steps

### 1. Server Startup and Initial Health Check

**Instructions:**
1. Navigate to the backend directory: `cd backend`
2. Verify dependencies are installed: `npm install`
3. Start the backend server: `npm start`
4. Wait 2 seconds for server to initialize
5. Make a GET request to `http://localhost:3000/api/status`
6. Record the response and note the uptime value

**Expected Result:**
- Server starts successfully without errors
- Server listens on port 3000 (or configured PORT)
- Status endpoint responds with HTTP 200 status
- Response contains: `status: "ok"`
- Response contains: `uptime` field with value close to 0 (0-2 seconds)
- Response contains: `mongodb` field with value `"connected"` or `"disconnected"`
- Response contains: `timestamp` field with valid ISO 8601 format
- Response Content-Type is `application/json`
- Response time is under 100ms

### 2. Verify Existing Endpoints Still Function

**Instructions:**
1. With server running, make GET request to `http://localhost:3000/api/hello`
2. Verify the response
3. Make GET request to `http://localhost:3000/api/messages`
4. Verify the response (should be an array or error if MongoDB unavailable)
5. Verify no errors appear in server console output

**Expected Result:**
- `/api/hello` endpoint returns HTTP 200 with JSON: `{ hello: "world" }`
- `/api/messages` endpoint returns HTTP 200 with `messages` field (array or empty)
- No error messages in server logs related to these endpoints
- All endpoints have response time under 100ms

### 3. MongoDB Connection State Verification

**Instructions:**
1. Record the `mongodb` field value from Step 1
2. Check actual MongoDB connection state:
   - If MongoDB is running: `mongodb` field should be `"connected"`
   - If MongoDB is not running: `mongodb` field should be `"disconnected"`
3. Stop MongoDB (if it was running) or start it (if it wasn't)
4. Make a new GET request to `/api/status` endpoint
5. Verify the `mongodb` field reflects the new connection state
6. Wait 2 seconds and make another request to verify consistency

**Expected Result:**
- When MongoDB is connected: `mongodb: "connected"` in response
- When MongoDB is disconnected: `mongodb: "disconnected"` in response
- Status endpoint always returns HTTP 200 regardless of MongoDB state
- MongoDB state changes are reflected in subsequent requests
- Response remains consistent across multiple requests

### 4. Server Uptime Tracking

**Instructions:**
1. Note the `uptime` value from the first request in Step 1
2. Wait 3 seconds
3. Make a second request to `/api/status`
4. Record the new `uptime` value
5. Calculate the difference: `uptime_2 - uptime_1`
6. Wait another 5 seconds and make a third request
7. Calculate the difference: `uptime_3 - uptime_2`

**Expected Result:**
- First request uptime is 0-2 seconds (shortly after startup)
- Second request uptime has increased by approximately 3 seconds (±1 second tolerance)
- Third request uptime has increased by approximately 5 seconds from second request (±1 second tolerance)
- Uptime values are monotonically increasing
- Uptime is a non-negative integer representing seconds

### 5. Response Time Acceptance Testing

**Instructions:**
1. Make 10 consecutive GET requests to `/api/status`
2. Measure the time taken for each request (from initiation to response received)
3. Record all response times
4. Calculate average, min, and max response times
5. Verify all response times are under the 100ms threshold

**Expected Result:**
- All 10 requests return HTTP 200
- All response times are under 100ms
- Average response time is ideally under 50ms
- No timeouts or connection refused errors
- Server continues functioning normally after rapid requests

### 6. Concurrent Request Handling (Thread-Safe Operation)

**Instructions:**
1. Make 5 concurrent GET requests to `/api/status` simultaneously (or as close as possible)
2. Record all responses
3. Verify all responses are valid
4. Check that responses are identical except for `timestamp` and `uptime` values
5. Verify uptime values are consistent across concurrent responses (should differ by <1 second)
6. Repeat this test 3 times

**Expected Result:**
- All concurrent requests return HTTP 200
- All responses have valid JSON structure
- All responses contain required fields: `status`, `uptime`, `mongodb`, `timestamp`
- Field values are consistent across concurrent requests
- Uptime differences across concurrent responses are negligible (<1 second)
- No errors or data corruption in responses
- Server handles concurrent load without crashing or errors

### 7. Edge Case: MongoDB Disconnection Scenario

**Instructions:**
1. Verify MongoDB is currently disconnected (or disconnect it if connected)
2. Make a GET request to `/api/status`
3. Verify the response
4. Make a GET request to `/api/messages`
5. Verify the response
6. Verify the status endpoint still returns 200 (not 500 or other error)

**Expected Result:**
- Status endpoint returns HTTP 200 with `mongodb: "disconnected"`
- No error state in the status response
- `/api/messages` endpoint may return error (500) due to no MongoDB connection
- Status endpoint resilience is confirmed (doesn't fail when MongoDB is down)
- System remains operational even with MongoDB unavailable

### 8. Edge Case: Immediate Requests After Startup

**Instructions:**
1. Stop the server (Ctrl+C)
2. Wait 5 seconds
3. Start the server again
4. Immediately make a GET request to `/api/status` (within 100ms of server starting)
5. Record the uptime value
6. Make another request 1 second later
7. Verify uptime progression

**Expected Result:**
- First request after startup returns HTTP 200
- Uptime value is 0 or very small (<500ms)
- Subsequent request shows uptime increase
- No startup errors or initialization issues
- Server is immediately responsive to requests

### 9. Timestamp Validation

**Instructions:**
1. Make a GET request to `/api/status`
2. Extract the `timestamp` value
3. Parse the timestamp as ISO 8601 format
4. Verify the timestamp is within ±5 seconds of current system time
5. Make 5 more requests at 1-second intervals
6. Verify each timestamp increases with each request

**Expected Result:**
- Timestamp is in valid ISO 8601 format (e.g., `2024-01-20T15:30:45.123Z`)
- Timestamp is within ±5 seconds of current system time (server time matches system)
- Timestamps from subsequent requests show forward progression (later times)
- No timestamp anomalies (no future dates, no repeated timestamps)

### 10. Response Structure Validation

**Instructions:**
1. Make a GET request to `/api/status`
2. Parse the JSON response
3. Verify the response has exactly 4 top-level fields (no more, no less)
4. Verify field names are: `status`, `uptime`, `mongodb`, `timestamp`
5. Verify field types:
   - `status` is a string
   - `uptime` is a number
   - `mongodb` is a string with value "connected" or "disconnected"
   - `timestamp` is a string in ISO 8601 format
6. Verify no null or undefined values in response

**Expected Result:**
- Response has exactly 4 fields
- All fields are present
- Field names match specification exactly
- Field types match specification
- No extra or unexpected fields
- No null, undefined, or invalid values
- Response structure is consistent across all requests

### 11. Load Testing: Multiple Rapid Requests

**Instructions:**
1. Make 50 GET requests to `/api/status` as rapidly as possible
2. Record the success/failure count
3. Measure total time for all requests
4. Identify any failed or timed-out requests
5. Check server status remains healthy
6. Make a final verification request to `/api/status`
7. Verify server is still responsive

**Expected Result:**
- All 50 requests complete successfully (100% success rate)
- Average response time remains under 100ms even under load
- No timeout errors or connection refused errors
- No server crashes or restarts during load test
- Final verification request succeeds
- Server remains stable and responsive after load testing

### 12. Integration: Health Check with Message Endpoints

**Instructions:**
1. Make a GET request to `/api/status` and record MongoDB connection state
2. If `mongodb: "connected"`:
   - Make a GET request to `/api/messages` (should work)
   - Verify it returns messages or empty array (not error)
3. If `mongodb: "disconnected"`:
   - Make a GET request to `/api/messages` (may error)
   - Status endpoint should still return 200
4. Verify status endpoint accurately reflects MongoDB state that affects `/api/messages`

**Expected Result:**
- Status endpoint accurately indicates MongoDB connection state
- When status shows "connected": `/api/messages` should work (return 200 with messages)
- When status shows "disconnected": `/api/messages` may return 500 error (expected)
- The status information is actionable and reflects actual system state
- Integration between endpoints works correctly

## Acceptance Criteria

- ✅ **Startup Verification**: Server starts successfully and status endpoint is immediately responsive (uptime ~0s)
- ✅ **Health Endpoint Accessibility**: `/api/status` endpoint is reachable at `http://localhost:3000/api/status` and returns HTTP 200
- ✅ **Response Structure**: Response is valid JSON with exactly 4 fields: `status`, `uptime`, `mongodb`, `timestamp`
- ✅ **Status Field**: `status` field always equals `"ok"` regardless of system state
- ✅ **Uptime Tracking**: `uptime` field correctly tracks seconds since server startup, monotonically increasing
- ✅ **MongoDB State Reflection**: `mongodb` field accurately reflects MongoDB connection state (`"connected"` or `"disconnected"`)
- ✅ **Timestamp Accuracy**: `timestamp` field is valid ISO 8601 format and matches system time (±5s tolerance)
- ✅ **Response Time SLA**: All endpoint responses complete in under 100ms
- ✅ **Existing Endpoints**: `/api/hello` and `/api/messages` endpoints continue to function without degradation
- ✅ **MongoDB Disconnection Resilience**: Status endpoint returns 200 even when MongoDB is disconnected (graceful degradation)
- ✅ **Concurrent Request Handling**: Endpoint handles 5+ concurrent requests without errors or data corruption
- ✅ **Rapid Request Handling**: Endpoint handles 50+ rapid sequential requests without timeout or failure
- ✅ **Consistency**: Status endpoint returns consistent data across multiple requests within the same second
- ✅ **Integration**: Status endpoint information accurately reflects the state that affects other endpoints (e.g., `/api/messages`)
- ✅ **No Server Errors**: No error logs or exceptions in server output during all tests

## Test Environment Details

### Backend Service
- **Technology**: Express.js (Node.js)
- **Port**: 3000 (or environment variable `PORT`)
- **Start Command**: `npm start` (from backend directory)
- **Database**: MongoDB (optional for health check endpoint)
- **API Base URL**: `http://localhost:3000`

### Key Endpoints
- **Status Endpoint**: `GET /api/status` - Health check with uptime and MongoDB state
- **Hello Endpoint**: `GET /api/hello` - Simple endpoint returning `{ hello: "world" }`
- **Messages Endpoint**: `GET /api/messages` - Returns messages from MongoDB

### Test Tools Required
- HTTP client capability (curl, Postman, or similar)
- Ability to run commands and capture output
- Ability to measure response times
- Ability to generate concurrent requests
- System clock synchronized for timestamp validation

## Notes

### Troubleshooting

**Issue**: Server fails to start on port 3000
- **Solution**: Check if port 3000 is already in use. Use `lsof -i :3000` (macOS/Linux) or `netstat -ano | findstr :3000` (Windows) to find the process. Either kill the process or set `PORT` environment variable to a different port.

**Issue**: Status endpoint returns `mongodb: "disconnected"` when MongoDB should be running
- **Solution**: Verify MongoDB is actually running. Check MongoDB connection string in environment or code. Verify network connectivity to MongoDB server.

**Issue**: Response times exceed 100ms
- **Solution**: This may indicate system load or network latency. Check system resources (CPU, memory). Verify network connectivity. Run tests during low-load periods.

**Issue**: Timestamp is not current or shows future time
- **Solution**: Verify system clock is synchronized. Check server timezone configuration. Compare with `date` command output.

### Performance Considerations

- The 100ms response time SLA should be achievable on modern hardware even under moderate load
- MongoDB connection checks should be fast (cached connection state) unless explicitly reconnecting
- Uptime calculation is a simple arithmetic operation (current time - start time)
- The endpoint has minimal database queries and can handle hundreds of requests per second

### MongoDB Dependency Notes

- The health check endpoint is designed to work **with or without** MongoDB
- If MongoDB is unavailable, the status endpoint still returns HTTP 200 with `mongodb: "disconnected"`
- Other endpoints like `/api/messages` will fail if MongoDB is unavailable (expected behavior)
- The status endpoint provides visibility into MongoDB state without requiring it to be available

### Long-Running Test Considerations

If running tests over extended periods:
- Verify server uptime calculation remains accurate (does not overflow or restart unexpectedly)
- Check for memory leaks or resource exhaustion after 1000+ requests
- Verify timestamps remain in sync with system time
- Monitor server process for unexpected restarts or crashes

### Concurrent Request Testing Notes

For step 6 (concurrent requests):
- Tools like `curl` can be parallelized with `&` background processes
- Or use load testing tools like `ab` (Apache Bench) or `hey`
- Example with curl: `for i in {1..5}; do curl http://localhost:3000/api/status & done; wait`
- Ensure at least 5 concurrent requests start within 100ms of each other for proper testing

### Regression Testing

This E2E test should be run:
- After any changes to the `/api/status` endpoint
- After upgrading Express.js or Node.js versions
- After any database connection changes
- Before each production deployment
- As part of CI/CD pipeline (automated)
