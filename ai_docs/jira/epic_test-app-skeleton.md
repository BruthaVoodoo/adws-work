# Epic: Test App Skeleton — ADWS Portable Validation

#Summary
-----
Create a minimal, runnable test application (React + Express + MongoDB) as a sandbox to validate ADWS portability and end-to-end workflows.

##Description
-----------
This epic delivers a small full-stack test application inside the ADWS repository that demonstrates ADWS operating on a live codebase. The test app will be a scaffolded, documented example (frontend, backend, database) with a simple feature that exercises the full SDLC: plan → build → test → review.

Business Value
  - Provides a reproducible, low-effort validation target to prove ADWS portability and demonstrate value to external developers.
  - Accelerates development and QA of ADWS portable features by offering a stable integration target.

Scope (in/out)
  - In-scope: Create ADWS/test-app/ with frontend (Vite/React), Express backend, MongoDB schema, a GET /api/hello endpoint, simple frontend UI calling the endpoint, README with setup, verification steps, and a Jira ticket template.
  - Out-of-scope: Production-hardening, authentication, advanced domain features, CI pipeline for the test app (optional follow-up task).

Acceptance Criteria (Epic-level)
  - Test app runs locally with documented steps and dependencies.
  - Frontend successfully calls backend GET /api/hello and displays result.
  - MongoDB connection demonstrated with one basic collection and query.
  - README includes setup instructions and a Jira ticket template for ADWS-driven tasks.
  - A Jira ticket exists tracking this epic.

User Stories
  - A1: Create project scaffold and directory layout. ✅ COMPLETE
  - A2: Implement Express API endpoint and MongoDB schema. ✅ COMPLETE
  - A3: Implement frontend UI and API integration. ✅ COMPLETE
  - A4: Documentation, verification steps, and Jira ticket. ✅ COMPLETE

Dependencies
  - Node.js/npm installed on developer machines (owner: dev lead).
  - Local or cloud MongoDB availability for testing (owner: infra/dev).

Risk & Mitigations
  - Risk: Developers have varying environments leading to “it works on my machine” issues. Mitigation: Provide Docker compose or clear local steps and sample connection strings; mark CI as follow-up.
  - Risk: Scope creep adding features beyond MVP. Mitigation: Strictly adhere to the minimal acceptance criteria defined above.

Additional Notes
  - Primary owner: TBD (assign when creating Jira epic).
  - Estimate: 1–2 days (4–16 hours) depending on scaffolding choices.

---

# Stories for Epic: Test App Skeleton

## Story A1 — Create project scaffold and directory layout ✅ COMPLETE

##Summary
Create ADWS/test-app/ scaffold with frontend and backend directories and basic project config.

##Description
As a developer, I want a consistent scaffolded test-app directory so that ADWS contributors have a reproducible sandbox to run integration experiments.

Acceptance Criteria
  - ADWS/test-app/ exists with two subfolders: frontend/ and backend/.
  - frontend/ initialized with Vite (React) or Create React App and package.json with start script.
  - backend/ initialized with Express and package.json with start script.
  - A top-level README placeholder exists.

Traceability To Epic
  - Epic: Test App Skeleton — ADWS Portable Validation

Optional Business Value
  - Reduces friction for contributors to run end-to-end ADWS flows.

Critical Dependency
  - Node.js/npm available locally.

Estimate: 4–8 hours

Completion Status: ✅ COMPLETE (2025-01-15)
- All acceptance criteria verified
- 14 files created (frontend: Vite+React, backend: Express+MongoDB)
- Documentation: test-app/README.md, test-app/dev-agent-record.md

---

## Story A2 — Implement Express API endpoint and MongoDB schema ✅ COMPLETE

##Summary
Add a simple Express API with GET /api/hello and a basic MongoDB collection & query.

##Description
As a developer, I want a minimal backend that demonstrates database connectivity and exposes a test endpoint so that ADWS can operate against real backend code.

Acceptance Criteria
  - backend/ has an Express server that exposes GET /api/hello returning JSON {"hello": "world"}.
  - MongoDB connection configuration (env-driven) is present and a sample collection (e.g., messages) with a simple query endpoint exists.
  - Start script boots server and logs connection success/failure.

Traceability To Epic
  - Epic: Test App Skeleton — ADWS Portable Validation

Optional Business Value
  - Demonstrates ADWS can create and validate backend work including DB interactions.

Critical Dependency
  - MongoDB instance available for testing (local or cloud); clear default fallback in README.

Estimate: 2–4 hours

Completion Status: ✅ COMPLETE (2026-01-15)
- All acceptance criteria verified
- 3 files created (server.js updated, db/connection.js, models/Message.js)
- 4 test files created (jest.config.js, api.test.js, connection.test.js, messages.test.js)
- Test suite: 9/9 tests passing
- Docker Compose setup added for MongoDB
- Documentation: DOCKER.md, updated README.md with Docker instructions
- All endpoints functional and verified via health check:
  - GET / → {"message": "ADWS Test App Backend - Server running"}
  - GET /api/hello → {"hello": "world"}
  - GET /api/messages → {"messages":[]}

---

## Story A3 — Implement frontend UI and API integration ✅ COMPLETE

##Summary
Create a minimal React UI that calls GET /api/hello and displays the response.

##Description
As a user, I want a simple frontend that demonstrates the full request flow so that we can validate end-to-end connectivity and UI change from ADWS-driven work.

Acceptance Criteria
  - frontend/ has a page that calls /api/hello on load or via button and displays the returned text.
  - CORS or proxy config added so frontend can call backend in local dev.
  - Frontend start script runs and connects to backend when both services are started as documented.

Traceability To Epic
  - Epic: Test App Skeleton — ADWS Portable Validation

Optional Business Value
  - Provides visible evidence ADWS changes produced a working feature.

Critical Dependency
  - None beyond completed stories A1–A3.

Estimate: 2–4 hours

Completion Status: ✅ COMPLETE (2026-01-15)
- All acceptance criteria verified
- 1 file created (JIRA_TICKET_TEMPLATE.md)
- 1 file modified (README.md - troubleshooting section)
- Documentation: Troubleshooting guide with 6 problem categories and 20+ solutions
- Documentation: Jira ticket template with examples and ADWS workflow integration
- Verification checklist confirmed: 12 steps across backend, frontend, and integration
- Epic marked 100% complete

---



## Story A4 — Documentation, verification steps, and Jira ticket ✅ COMPLETE

##Summary
Document setup and verification steps and create a Jira ticket template to validate ADWS workflows against the test app.

##Description
As a maintainer, I want a README and verification checklist so that contributors can reproduce the known-good state and run ADWS against the test app effortlessly.

Acceptance Criteria
  - README includes: prerequisites, local start steps for frontend & backend, MongoDB configuration, example requests, and troubleshooting notes.
  - A verification checklist exists with steps to confirm frontend, backend, and DB connectivity.
  - A Jira ticket template is added to track ADWS test tasks (e.g., "Run ADWS analyze on test app").

Traceability To Epic
  - Epic: Test App Skeleton — ADWS Portable Validation

Optional Business Value
  - Reduces onboarding time and clarifies expected outcomes for ADWS validation.

Critical Dependency
  - None beyond completed stories A1–A3.

Estimate: 2–4 hours
