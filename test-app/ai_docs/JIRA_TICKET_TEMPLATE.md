# Jira Ticket Template for ADWS Test Tasks

## Ticket Template

This template can be used to create Jira tickets for ADWS-driven development tasks against the test app.

---

## Basic Fields

**Summary**: [Brief description of the task]

**Description**:
```
As a [role], I want [feature/capability] so that [benefit/value].

**Context**:
- Task type: [feature | bug | chore | test]
- Epic: Test App Skeleton — ADWS Portable Validation
- Related stories: [A1 | A2 | A3 | A4]
- Test app version: [current version]

**Example Tasks**:
- Add [new feature] to frontend
- Create new backend endpoint for [use case]
- Fix [bug] in [component/module]
- Add tests for [feature]
- Update documentation for [change]
```

**Acceptance Criteria**:
- [ ] AC1: [First acceptance criteria]
- [ ] AC2: [Second acceptance criteria]
- [ ] AC3: [Third acceptance criteria]

**Definition of Done**:
- [ ] Code implemented and follows project standards
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Manual testing completed (verification checklist)
- [ ] Documentation updated (README, API docs, etc.)
- [ ] Dev Agent Record updated with implementation details
- [ ] Code reviewed (if applicable)
- [ ] No console errors in browser or terminal
- [ ] All existing tests still passing

---

## Example Ticket: Add New API Endpoint

**Summary**: Add GET /api/status endpoint returning server health information

**Description**:
```
As a developer, I want a health check endpoint so that I can verify the backend is running without calling other endpoints.

**Context**:
- Task type: feature
- Epic: Test App Skeleton — ADWS Portable Validation
- Related stories: A2 (backend implementation)
- Test app version: 1.0.0

**Implementation Plan**:
1. Create endpoint in backend/server.js
2. Return JSON with status, uptime, and MongoDB connection state
3. Add unit tests in tests/api.test.js
4. Update API documentation in README
5. Run full test suite
```

**Acceptance Criteria**:
- [ ] GET /api/status exists and returns JSON
- [ ] Response includes `status: "ok"` field
- [ ] Response includes `mongodb: "connected" | "disconnected"` field
- [ ] Unit tests added and passing
- [ ] README API endpoints table updated

**Definition of Done**:
- [ ] GET /api/status endpoint implemented in backend/server.js
- [ ] Returns `{"status": "ok", "mongodb": "connected"}`
- [ ] Test added in tests/api.test.js
- [ ] Test suite passes (npm test)
- [ ] README API endpoints table updated with new endpoint
- [ ] Manual verification: curl http://localhost:5176/api/status
- [ ] Dev Agent Record updated

---

## Example Ticket: Add Messages List to Frontend

**Summary**: Display messages list from MongoDB in frontend UI

**Description**:
```
As a user, I want to see all messages from the database so that I can verify data persistence.

**Context**:
- Task type: feature
- Epic: Test App Skeleton — ADWS Portable Validation
- Related stories: A3 (frontend UI), A2 (messages endpoint)
- Test app version: 1.0.0

**Implementation Plan**:
1. Add "Load Messages" button to App.jsx
2. Call GET /api/messages endpoint
3. Display messages in a list format
4. Add error handling for API failures
5. Style the message list component
6. Update README with new feature documentation
```

**Acceptance Criteria**:
- [ ] "Load Messages" button added to UI
- [ ] Clicking button fetches from /api/messages
- [ ] Messages displayed in a list (not JSON)
- [ ] Each message shows text and timestamp
- [ ] Empty state displayed when no messages exist
- [ ] Error state displayed when API fails

**Definition of Done**:
- [ ] Button and list component implemented in App.jsx
- [ ] Styles added for message list in App.css
- [ ] API integration tested with curl
- [ ] Manual verification: add message via MongoDB, reload frontend, verify display
- [ ] README updated with new feature description
- [ ] Dev Agent Record updated
- [ ] All existing tests still passing

---

## Example Ticket: Implement Light/Dark Mode Toggle

**Summary**: Implement Light/Dark mode theme toggle for test app UI

**Description**:
```
As a user, I want to switch between light and dark themes so that I can use the application comfortably in different lighting conditions.

**Context**:
- Task type: feature
- Epic: Test App Skeleton — ADWS Portable Validation
- Related stories: A3 (frontend UI)
- Test app version: 1.0.0

**Implementation Plan**:
1. Create theme context and provider in frontend (React Context API)
2. Add theme toggle button to App.jsx header
3. Implement dark mode CSS styles for all components
4. Persist theme preference in localStorage
5. Add unit tests for theme switching logic
6. Update README with theme feature documentation
7. Ensure all components respect theme colors
```

**Acceptance Criteria**:
- [ ] Theme toggle button displays in UI header
- [ ] Light mode displays light background with dark text
- [ ] Dark mode displays dark background with light text
- [ ] Theme preference persists across page reloads
- [ ] All existing components styled for both themes
- [ ] No console errors when switching themes
- [ ] Unit tests for theme context passing
- [ ] README updated with theme switching instructions

**Definition of Done**:
- [ ] Theme context and provider created in frontend
- [ ] Toggle button implemented in App.jsx header
- [ ] CSS variables or styled-components setup for theme colors
- [ ] Light and dark theme palettes defined and applied
- [ ] localStorage integration for theme persistence
- [ ] Unit tests written and passing (npm test)
- [ ] Manual verification: toggle theme, reload page, verify persistence
- [ ] All components tested in both light and dark modes
- [ ] README updated with theme feature documentation
- [ ] Dev Agent Record updated with implementation details
- [ ] All existing tests still passing
- [ ] No console errors in browser DevTools

---

## ADWS Workflow Integration

### Running ADWS on Test App

When creating tickets to run ADWS workflows against the test app:

**Ticket Summary**: "Run ADWS [workflow] on test app for [feature]"

**Description Template**:
```
Execute ADWS [plan|build|test|review] workflow on the test app to [validate/implement] [feature].

**Workflow Type**: [plan | build | test | review]
**Target**: [test-app/backend | test-app/frontend | entire test-app]
**Jira Issue**: [Link to related Jira issue]
**Branch**: [branch-name]

**Acceptance Criteria**:
- [ ] ADWS workflow completes successfully
- [ ] Generated plan/code/tests meet expectations
- [ ] Verification checklist updated with ADWS results
- [ ] Dev Agent Record updated with ADWS execution details
```

### Example ADWS Workflow Ticket

**Summary**: "Run ADWS build on test app for messages list feature"

**Description**:
```
Execute ADWS build workflow on the test app to implement messages list feature in frontend.

**Workflow Type**: build
**Target**: test-app/frontend
**Jira Issue**: ADD-123 (Add messages list to frontend)
**Branch**: feature/messages-list

**Acceptance Criteria**:
- [ ] ADWS build generates frontend code
- [ ] Messages list component created in App.jsx
- [ ] Styles generated for message display
- [ ] No TypeScript or React errors
- [ ] Manual verification: npm run dev, test feature
- [ ] Dev Agent Record updated with ADWS build results
```

---

## Labels and Components

**Labels** (use as applicable):
- `adw-task` - For ADWS-driven tasks
- `adw-test` - For testing ADWS workflows on test app
- `test-app` - For test app specific tasks
- `frontend` - Frontend changes
- `backend` - Backend changes
- `documentation` - Documentation updates
- `bug` - Bug fixes
- `feature` - New features

**Components**:
- `test-app-frontend` - Frontend component
- `test-app-backend` - Backend component
- `test-app-documentation` - Documentation component

---

## Verification Checklist (Copy into ticket description)

### Backend Verification
- [ ] Code changes committed to branch
- [ ] Backend starts successfully (`npm start`)
- [ ] No console errors on startup
- [ ] All API endpoints responding correctly
- [ ] MongoDB connection successful
- [ ] Unit tests passing (`npm test`)
- [ ] Manual testing completed via curl or Postman

### Frontend Verification
- [ ] Code changes committed to branch
- [ ] Frontend starts successfully (`npm run dev`)
- [ ] UI displays correctly in browser
- [ ] No console errors in browser DevTools
- [ ] API calls successful (check Network tab)
- [ ] Proxy configuration working (if applicable)
- [ ] Manual testing completed via browser

### Integration Verification
- [ ] Both frontend and backend running
- [ ] End-to-end flow tested successfully
- [ ] No CORS errors in browser
- [ ] No network errors in browser DevTools
- [ ] All acceptance criteria met
- [ ] Documentation updated (README, API docs)
- [ ] Dev Agent Record updated

---

## Notes

- Always link to related epic: "Epic: Test App Skeleton — ADWS Portable Validation"
- Include story references (A1, A2, A3, A4) when applicable
- Copy relevant verification checklist items into Definition of Done
- Update Dev Agent Record after implementation
- Reference DOCKER.md if MongoDB-related issues arise
