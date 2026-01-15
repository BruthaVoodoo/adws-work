# ADWS Test App

A minimal, runnable test application (React + Express + MongoDB) to validate ADWS portability and end-to-end workflows.

## Project Structure

```
test-app/
├── frontend/          # React frontend (Vite)
├── backend/           # Express backend
└── README.md          # This file
```

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- MongoDB (local or cloud instance)

### Backend Setup
```bash
cd backend
cp .env.example .env
# Edit .env with your MongoDB connection string
npm install
npm start
```

Backend will run on http://localhost:3000

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

Frontend will run on http://localhost:5173

## Development

### Backend Development
```bash
cd backend
npm run dev  # Uses --watch flag for hot reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

## Status

**Story A1 — Create project scaffold and directory layout**: ✅ Completed

### Completed Stories
- A1: Create project scaffold and directory layout

### Pending Stories
- A2: Implement Express API endpoint and MongoDB schema
- A3: Implement frontend UI and API integration
- A4: Documentation, verification steps, and Jira ticket

---

This test app is part of the **Epic: Test App Skeleton — ADWS Portable Validation**
