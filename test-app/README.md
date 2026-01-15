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
- Docker Desktop (for MongoDB) OR a local MongoDB installation

### Option 1: Using Docker (Recommended)

1. **Start MongoDB**:
   ```bash
   cd test-app
   docker-compose up -d
   ```

2. **Start Backend**:
   ```bash
   cd backend
   cp .env.example .env
   npm install
   npm start
   ```

   Backend will run on http://localhost:3000

3. **Start Frontend**:
   ```bash
   cd frontend
   npm install
   npm start
   ```

   Frontend will run on http://localhost:5173

See [DOCKER.md](DOCKER.md) for detailed Docker setup and troubleshooting.

### Option 2: Local MongoDB Installation

If you prefer running MongoDB locally instead of Docker:

1. **Install MongoDB** from [mongodb.com](https://www.mongodb.com/try/download/community)

2. **Start MongoDB**:
   ```bash
   # macOS (with Homebrew)
   brew services start mongodb-community

   # Linux
   sudo systemctl start mongod
   ```

3. **Follow Option 1 steps 2-3** (backend setup is the same)

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

- ✅ **Story A1** — Create project scaffold and directory layout (2025-01-15)
- ✅ **Story A2** — Implement Express API endpoint and MongoDB schema (2026-01-15)

### Completed Stories
- A1: Create project scaffold and directory layout
- A2: Implement Express API endpoint and MongoDB schema

### Pending Stories
- A3: Implement frontend UI and API integration
- A4: Documentation, verification steps, and Jira ticket

---

This test app is part of the **Epic: Test App Skeleton — ADWS Portable Validation**
