# E2E Test: Display messages list from MongoDB in frontend UI

## Test Objective
Validate that the Display messages list from MongoDB in frontend UI works correctly in end-to-end scenarios, including integration testing, edge case handling, and system behavior validation.

## Prerequisites
- Backend server is available and can be started on port 3000
- Frontend dev server can be started on port 5173
- MongoDB service is available
- Docker and docker-compose are installed
- Test environment is properly configured
- No conflicting services on target ports (3000, 5173, 27017)

## Test Steps

### 1. Infrastructure Setup Verification
**Objective**: Verify all services can be started correctly
- Start MongoDB container: `docker-compose up -d`
- Verify MongoDB is ready by checking container logs
- Start backend server: `cd test-app && npm run dev:backend`
- Verify backend responds on `http://localhost:3000`
- Start frontend dev server: `cd test-app && npm run dev:frontend`
- Verify frontend is accessible at `http://localhost:5173`
- **Expected Result**: All services start without errors and are responsive

### 2. Backend Messages Endpoint Functionality
**Objective**: Verify the `/api/messages` endpoint works correctly
- Make GET request to `http://localhost:3000/api/messages`
- Verify HTTP status code is 200
- Verify response Content-Type is application/json
- Verify response structure: `{messages: []}`
- Verify empty messages array when no data exists
- **Expected Result**: Endpoint responds with valid JSON structure `{messages: []}`

### 3. Frontend Application Loads Successfully
**Objective**: Verify the React application initializes without errors
- Open `http://localhost:5173` in browser
- Verify page loads without console errors
- Verify "Load Messages" button is visible and clickable
- Verify existing "Call /api/hello" button remains functional
- Check browser console for any JavaScript errors or warnings
- **Expected Result**: Application loads cleanly with no errors

### 4. Message Loading Button Functionality - Empty State
**Objective**: Verify the Load Messages button fetches and displays empty state correctly
- Ensure MongoDB is empty (no messages in database)
- Click "Load Messages" button on frontend
- Observe loading state displays (button shows "Loading...")
- Wait for API response
- Verify empty state message displays: "No messages found"
- Verify no error messages appear
- Verify button returns to clickable state after loading completes
- **Expected Result**: Empty state displays correctly when database has no messages

### 5. Message Loading - Adding Test Data
**Objective**: Verify backend correctly stores and retrieves messages
- Add test message to MongoDB: `docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertOne({text: "Test message 1", createdAt: new Date()})' adws-test-app`
- Click "Load Messages" button again
- Verify loading state displays
- Wait for API response
- Verify message list renders (no longer shows "No messages found")
- Verify the test message text displays: "Test message 1"
- Verify timestamp is formatted and displayed
- **Expected Result**: Message displays with properly formatted timestamp

### 6. Message Loading - Multiple Messages
**Objective**: Verify message list handles multiple messages correctly
- Add additional test messages: 
  ```
  docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertMany([{text: "Test message 2", createdAt: new Date()}, {text: "Test message 3", createdAt: new Date()}])' adws-test-app
  ```
- Click "Load Messages" button
- Verify all three messages display in the list
- Verify messages are sorted by creation date (newest first)
- Verify each message has correct text and timestamp
- Verify no duplicate messages appear
- **Expected Result**: All messages display with correct ordering and formatting

### 7. Error State Handling - Database Unavailable
**Objective**: Verify graceful error handling when MongoDB becomes unavailable
- Click "Load Messages" button (verify it works with current data)
- Stop MongoDB service: `docker-compose stop mongodb`
- Click "Load Messages" button again
- Verify loading state displays
- Wait for API response
- Verify error message displays to user (descriptive error message)
- Verify no raw error stack traces appear in UI
- Verify button is clickable for retry
- **Expected Result**: Graceful error handling with user-friendly message

### 8. Error State Recovery
**Objective**: Verify system can recover from error state
- Restart MongoDB service: `docker-compose start mongodb`
- Wait for MongoDB to become ready
- Click "Load Messages" button
- Verify loading state displays
- Verify API successfully retrieves messages after recovery
- Verify message list displays correctly
- **Expected Result**: System recovers and functions normally after MongoDB restart

### 9. Button State During Loading
**Objective**: Verify button state prevents duplicate API requests
- Click "Load Messages" button
- Observe button becomes disabled during loading (should appear grayed out)
- Attempt to click button multiple times during loading
- Verify no duplicate API requests are made
- Wait for loading to complete
- Verify button re-enables and returns to normal state
- **Expected Result**: Button is disabled during loading, preventing concurrent requests

### 10. Timestamp Formatting Accuracy
**Objective**: Verify timestamps display in correct format
- Add message with known timestamp:
  ```
  docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertOne({text: "Timestamp test", createdAt: new Date("2024-01-15T14:30:00Z")})' adws-test-app
  ```
- Click "Load Messages" button
- Verify timestamp displays in readable format (e.g., "Jan 15, 2024 2:30 PM" or similar)
- Verify timestamp is not raw ISO string
- Verify timestamp matches the date inserted
- **Expected Result**: Timestamps format correctly and display readably

### 11. Large Message List Performance
**Objective**: Verify system handles large datasets efficiently
- Add many messages to MongoDB:
  ```
  docker exec adws-test-app-mongodb mongosh --eval 'const msgs = Array.from({length: 100}, (_, i) => ({text: `Message ${i}`, createdAt: new Date(Date.now() - i * 1000)})); db.messages.insertMany(msgs)' adws-test-app
  ```
- Click "Load Messages" button
- Measure response time (should be under 2 seconds)
- Verify all 100+ messages load without crashing
- Verify message list is scrollable
- Verify UI remains responsive while scrolling
- Check browser performance (no significant jank or lag)
- **Expected Result**: System handles 100+ messages efficiently with acceptable performance

### 12. No Regressions in Existing Functionality
**Objective**: Verify new feature doesn't break existing features
- Verify "Call /api/hello" button still works
- Click "Call /api/hello" button
- Verify response displays correctly
- Click "Load Messages" button
- Verify both features work independently
- Alternate between both buttons multiple times
- Verify no state conflicts occur
- **Expected Result**: All existing functionality remains intact

### 13. Frontend Build Without Errors
**Objective**: Verify production build succeeds
- Run: `cd test-app/frontend && npm run build`
- Verify build completes without errors or warnings
- Verify bundle size is reasonable (no unexpected growth)
- Verify generated assets are present in `dist/` directory
- **Expected Result**: Frontend builds successfully for production

### 14. Backend Unit Tests Pass
**Objective**: Verify backend tests for messages endpoint
- Run: `cd test-app/backend && npm test`
- Verify all tests pass
- Verify GET `/api/messages` endpoint test passes
- Verify empty database test passes
- Verify multiple messages test passes
- Verify error handling test passes
- **Expected Result**: All backend tests pass with zero failures

### 15. Frontend Unit Tests Pass
**Objective**: Verify frontend component tests pass
- Run: `cd test-app/frontend && npm test`
- Verify MessageList component tests pass
- Verify empty state test passes
- Verify message list rendering test passes
- Verify timestamp formatting test passes
- Verify all props are correctly handled
- **Expected Result**: All frontend tests pass with zero failures

### 16. Full Test Suite Execution
**Objective**: Verify entire application test suite passes
- Run: `cd test-app && npm test`
- Verify all backend tests pass
- Verify all frontend tests pass
- Verify no test failures or errors
- Verify code coverage is acceptable
- **Expected Result**: All tests pass with zero failures

### 17. API Endpoint Response Format Validation
**Objective**: Verify API response matches expected schema
- Make GET request to `http://localhost:3000/api/messages` using curl:
  ```
  curl -s http://localhost:3000/api/messages | jq .
  ```
- Verify response is valid JSON
- Verify response has top-level `messages` property
- Verify `messages` is an array
- Verify each message has `_id`, `text`, and `createdAt` properties
- Verify no unexpected properties appear in response
- **Expected Result**: Response matches expected schema exactly

### 18. Concurrent Request Handling
**Objective**: Verify system handles multiple simultaneous requests
- Open browser developer tools (Network tab)
- Click "Load Messages" button
- Immediately click it 5 more times before loading completes
- Observe network tab shows only one request completes (or requests are queued)
- Verify no duplicate messages appear in UI
- Verify final result is consistent
- **Expected Result**: Concurrent requests are handled gracefully without duplication

### 19. Empty Database After Message Deletion
**Objective**: Verify system handles transition from messages to empty state
- Clear all messages from MongoDB: `docker exec adws-test-app-mongodb mongosh --eval 'db.messages.deleteMany({})' adws-test-app`
- Click "Load Messages" button
- Verify "No messages found" message displays
- Verify message list container is hidden
- Add a new message again
- Click "Load Messages" button
- Verify new message displays (state transitions correctly)
- **Expected Result**: System handles empty state transitions correctly

### 20. Browser Console Validation
**Objective**: Verify no errors or warnings in browser console
- Open browser developer tools (Console tab)
- Perform all UI interactions (click buttons, wait for API calls)
- Verify no JavaScript errors appear in console
- Verify no warning messages appear
- Verify no unhandled promise rejections appear
- **Expected Result**: Console is clean with no errors or warnings

### 21. Network Request Timing
**Objective**: Verify API response time meets performance requirements
- Open browser developer tools (Network tab)
- Click "Load Messages" button
- Observe response time in Network tab
- Verify response time is under 100ms in normal conditions
- Verify response time under 2 seconds even with 100+ messages
- Verify no timeouts occur
- **Expected Result**: API response times meet performance thresholds

### 22. Message List CSS and Styling
**Objective**: Verify visual presentation is correct
- Verify message list container has proper spacing
- Verify each message item has consistent styling
- Verify timestamps are displayed inline or below text
- Verify "No messages found" text is visually distinct
- Verify loading state provides visual feedback
- Verify error messages are clearly visible
- Verify responsive design works on mobile viewport (resize browser window)
- **Expected Result**: Styling is consistent and visually appealing

### 23. Accessibility - Keyboard Navigation
**Objective**: Verify keyboard accessibility
- Use Tab key to navigate to "Load Messages" button
- Verify button receives focus (visible focus indicator)
- Press Enter or Space to activate button
- Verify API call triggers
- Tab through page to verify all interactive elements are accessible
- **Expected Result**: Full keyboard navigation works without issues

### 24. Accessibility - Screen Reader Compatibility
**Objective**: Verify semantic HTML and ARIA labels
- Inspect HTML source for semantic elements
- Verify buttons have descriptive text or ARIA labels
- Verify message list has proper heading structure
- Verify error messages are associated with appropriate elements
- Test with screen reader (if available) to verify content is readable
- **Expected Result**: Page is navigable and understandable with screen readers

## Edge Case Tests

### Edge Case 1: Empty Messages Array
**Scenario**: Database exists but has no messages
- Ensure MongoDB has messages table but is empty
- Click "Load Messages"
- **Expected Result**: "No messages found" displays, no errors occur

### Edge Case 2: Database Connection Failure
**Scenario**: MongoDB becomes unavailable during operation
- Stop MongoDB while application is running
- Click "Load Messages"
- **Expected Result**: User-friendly error message displays, application remains functional

### Edge Case 3: Network Timeout
**Scenario**: API request takes longer than expected
- Simulate slow network in browser DevTools (throttle to slow 3G)
- Click "Load Messages"
- **Expected Result**: Loading state persists, request eventually completes or times out gracefully

### Edge Case 4: Invalid Response Format
**Scenario**: Backend returns unexpected JSON structure
- Manually modify backend to return malformed response
- Click "Load Messages"
- **Expected Result**: Error is caught and user-friendly message displays

### Edge Case 5: Very Large Message Text
**Scenario**: Message text exceeds normal length
- Add message with 5000+ character text
- Click "Load Messages"
- **Expected Result**: Message displays correctly, UI remains usable (text wraps)

### Edge Case 6: Special Characters in Message Text
**Scenario**: Message contains HTML, emojis, or special Unicode characters
- Add message: `Test with <script>alert('xss')</script> and emoji 🎉`
- Click "Load Messages"
- **Expected Result**: Special characters display safely without rendering HTML or executing scripts

### Edge Case 7: Concurrent Button Clicks
**Scenario**: User rapidly clicks Load Messages multiple times
- Click "Load Messages" 10 times in quick succession
- **Expected Result**: Only one API request completes, no duplicate messages appear

### Edge Case 8: Very Old Timestamps
**Scenario**: Messages have timestamps from far past
- Add message with timestamp from year 1970
- Click "Load Messages"
- **Expected Result**: Timestamp displays correctly without errors

### Edge Case 9: Future Timestamps
**Scenario**: Messages have timestamps in the future
- Add message with timestamp 1 year in future
- Click "Load Messages"
- **Expected Result**: Timestamp displays correctly

### Edge Case 10: Null or Invalid Timestamp
**Scenario**: Message has missing or invalid createdAt field
- Add message with no createdAt property or invalid date
- Click "Load Messages"
- **Expected Result**: Message displays with "Invalid date" or suitable fallback

### Edge Case 11: Very Large Message Count (1000+)
**Scenario**: Database contains 1000+ messages
- Add 1000 messages to MongoDB
- Click "Load Messages"
- **Expected Result**: All messages load and display, performance remains acceptable

### Edge Case 12: Missing Required Fields
**Scenario**: Message document lacks required fields
- Add message with no `text` field
- Click "Load Messages"
- **Expected Result**: Message displays gracefully (empty text or suitable default)

### Edge Case 13: Browser Refresh During Loading
**Scenario**: User refreshes page while API call is in progress
- Click "Load Messages"
- Immediately refresh page (F5) during loading
- **Expected Result**: Page refreshes cleanly, no error state persists

### Edge Case 14: Rapid Connect/Disconnect Cycles
**Scenario**: MongoDB repeatedly becomes available/unavailable
- Start with messages loaded
- Stop MongoDB, click button (error occurs)
- Start MongoDB, click button (messages load)
- Repeat 3-5 times
- **Expected Result**: System handles state transitions correctly each time

### Edge Case 15: Response with No Text Property
**Scenario**: API returns message objects without text field
- Modify backend to omit text field
- Click "Load Messages"
- **Expected Result**: UI handles gracefully (empty message or suitable fallback)

## Validation Commands

### Command 1: Start Full Stack for Manual Testing
```bash
cd test-app && npm run dev:both
```
Starts both backend server and frontend dev server with hot reload enabled.

### Command 2: Run All Tests (Backend + Frontend)
```bash
cd test-app && npm test
```
Executes all tests to validate feature works with zero regressions.

### Command 3: Run Backend Tests Only
```bash
cd test-app/backend && npm test
```
Runs backend-only tests for messages API endpoint.

### Command 4: Run Frontend Tests Only
```bash
cd test-app/frontend && npm test
```
Runs frontend-only tests for MessageList component.

### Command 5: Start Infrastructure Services
```bash
docker-compose up -d
```
Starts MongoDB container in the background. Verify with: `docker-compose ps`

### Command 6: Add Test Message to MongoDB
```bash
docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertOne({text: "Test message", createdAt: new Date()})' adws-test-app
```
Inserts a single test message into MongoDB messages collection.

### Command 7: Add Multiple Test Messages
```bash
docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertMany([{text: "Message 1", createdAt: new Date()}, {text: "Message 2", createdAt: new Date()}, {text: "Message 3", createdAt: new Date()}])' adws-test-app
```
Inserts multiple test messages for list testing.

### Command 8: Add Large Dataset (100 Messages)
```bash
docker exec adws-test-app-mongodb mongosh --eval 'const msgs = Array.from({length: 100}, (_, i) => ({text: `Message ${i}`, createdAt: new Date(Date.now() - i * 1000)})); db.messages.insertMany(msgs)' adws-test-app
```
Inserts 100 messages for performance and load testing.

### Command 9: Clear All Messages
```bash
docker exec adws-test-app-mongodb mongosh --eval 'db.messages.deleteMany({})' adws-test-app
```
Removes all messages from MongoDB for empty state testing.

### Command 10: Verify API Endpoint
```bash
curl http://localhost:3000/api/messages
```
Makes HTTP GET request to backend endpoint and displays response.

### Command 11: Verify API Response Structure
```bash
curl -s http://localhost:3000/api/messages | jq .
```
Makes HTTP GET request and formats response as pretty-printed JSON.

### Command 12: Check MongoDB Connection
```bash
docker exec adws-test-app-mongodb mongosh --eval 'db.runCommand({ping: 1})' adws-test-app
```
Verifies MongoDB is running and responsive.

### Command 13: View MongoDB Messages Collection
```bash
docker exec adws-test-app-mongodb mongosh --eval 'db.messages.find()' adws-test-app
```
Displays all messages currently stored in MongoDB.

### Command 14: Stop MongoDB Service
```bash
docker-compose stop mongodb
```
Stops MongoDB for error state testing.

### Command 15: Start MongoDB Service
```bash
docker-compose start mongodb
```
Starts MongoDB after stopping for recovery testing.

### Command 16: Build Frontend for Production
```bash
cd test-app/frontend && npm run build
```
Creates production build and verifies no errors occur.

### Command 17: Check Frontend Build Output
```bash
ls -la test-app/frontend/dist/
```
Lists build artifacts to verify production bundle was created.

### Command 18: Stop All Services
```bash
docker-compose down
```
Stops all services and cleans up containers.

### Command 19: Check Service Health Status
```bash
docker-compose ps
```
Shows status of all services (running, stopped, etc.).

### Command 20: View Backend Logs
```bash
docker-compose logs -f backend
```
Streams backend service logs in real-time (Ctrl+C to stop).

## Acceptance Criteria
- ✅ Backend `/api/messages` endpoint is reachable and responds with status 200
- ✅ API response structure matches `{messages: [...]}`
- ✅ Frontend button fetches messages successfully
- ✅ Messages display in UI with formatted timestamps
- ✅ Empty state ("No messages found") displays when database is empty
- ✅ Error state displays descriptive messages when API fails
- ✅ Loading state shows during API calls with disabled button
- ✅ Button re-enables after loading completes
- ✅ Multiple messages display correctly with proper sorting (newest first)
- ✅ Large datasets (100+ messages) load without errors or performance degradation
- ✅ System recovers gracefully when MongoDB becomes available again
- ✅ All edge cases handled without crashes or user-facing errors
- ✅ No regressions in existing functionality
- ✅ All backend unit tests pass
- ✅ All frontend component tests pass
- ✅ Production build succeeds without errors
- ✅ Browser console is clean with no errors or warnings
- ✅ Keyboard navigation and accessibility features work correctly
- ✅ API response times meet performance thresholds (<100ms normal, <2s for large datasets)
- ✅ Responsive design works on mobile viewports

## Notes
- This test validates end-to-end functionality including integration between frontend, backend, and MongoDB
- Manual browser testing is essential to verify UI/UX behavior and styling
- All services must be running and accessible for tests to execute successfully
- Edge cases should be tested sequentially to isolate any failures
- Performance testing should use realistic network conditions (throttled in DevTools if needed)
- The AI executing this test can use available tools to make HTTP requests, run commands, and validate responses
