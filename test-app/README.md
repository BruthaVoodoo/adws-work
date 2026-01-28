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

   Backend will run on http://localhost:5176

3. **Start Frontend**:
    ```bash
    cd frontend
    npm install
    npm start
    ```

    Frontend will run on http://localhost:5175

4. **Verify Integration**:
     - Open http://localhost:5175 in your browser
     - Click "Call /api/hello" button - should see: `{"hello": "world"}`
     - Click "Load Messages" button - should see messages list or "No messages found"

     The frontend uses Vite proxy to forward `/api` requests to the backend at `http://localhost:5176`.

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

Backend will run on http://localhost:5176

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

Frontend will run on http://localhost:5175

## Development

### Running Both Services Simultaneously

**Terminal 1 - Backend:**
```bash
cd backend
npm start
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

The frontend proxies `/api` requests to `http://localhost:5176`, so you don't need to modify API URLs in React code.

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

## API Endpoints

### Backend (http://localhost:5176)

| Endpoint | Method | Response |
|----------|--------|----------|
| `/` | GET | `{"message": "ADWS Test App Backend - Server running"}` |
| `/api/hello` | GET | `{"hello": "world"}` |
| `/api/status` | GET | `{"status": "ok", "uptime": <seconds>, "mongodb": "connected|disconnected", "timestamp": <iso-string>}` |
| `/api/messages` | GET | `{"messages": [{"_id": "...", "text": "message content", "createdAt": "2026-01-23T..."}]}` |

### Frontend (http://localhost:5175)

The frontend includes a UI to test the backend API:

1. Open http://localhost:5175
2. Click "Call /api/hello" button to test basic connectivity
3. Click "Load Messages" button to fetch and display messages from MongoDB
4. View the API responses displayed on the page

**Message Loading Feature**: The frontend now includes a "Load Messages" button that:
- Fetches messages from MongoDB via the `/api/messages` endpoint
- Displays messages in a formatted list with timestamps
- Shows empty state when no messages exist
- Handles error states gracefully
- Messages are sorted by creation date (newest first)

The frontend uses Vite's proxy configuration to forward `/api/*` requests to `http://localhost:5176`.

## Verification Checklist

### Backend Verification

- [ ] MongoDB container running (`docker-compose ps`)
- [ ] Backend server started (`cd backend && npm start`)
- [ ] Backend responds at http://localhost:5176
- [ ] `/api/hello` returns `{"hello": "world"}`
- [ ] `/api/messages` returns `{"messages":[]}`

### Frontend Verification

- [ ] Frontend dev server started (`cd frontend && npm run dev`)
- [ ] Frontend accessible at http://localhost:5175
- [ ] "Call /api/hello" button visible and working
- [ ] "Load Messages" button visible and working
- [ ] Clicking /api/hello button displays `{"hello": "world"}`
- [ ] Clicking Load Messages shows messages list or "No messages found"
- [ ] No CORS errors in browser console

### Integration Verification
- [ ] Both frontend (5175) and backend (5176) running
- [ ] Frontend successfully proxies `/api` requests to backend
- [ ] Messages loading feature works end-to-end
- [ ] No network errors in browser DevTools
- [ ] API responses displayed correctly in UI
- [ ] Message timestamps are properly formatted

## Testing the Message Loading Feature

### Adding Test Messages

You can add test messages directly to MongoDB to see the message loading feature in action:

```bash
# Add a single message
docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertOne({text: "Hello from MongoDB!", createdAt: new Date()})' adws-test-app

# Add multiple messages
docker exec adws-test-app-mongodb mongosh --eval 'db.messages.insertMany([
  {text: "First message", createdAt: new Date()},
  {text: "Second message", createdAt: new Date()},
  {text: "Third message with timestamp", createdAt: new Date()}
])' adws-test-app
```

### Verifying Message Display

1. Add test messages using the commands above
2. Open http://localhost:5175 in your browser
3. Click the "Load Messages" button
4. You should see:
   - A formatted list of messages with text and timestamps
   - Messages sorted by creation date (newest first)
   - Message count in the header (e.g., "Messages (3)")
   - Properly formatted timestamps (e.g., "Jan 23, 2026 at 7:30 PM")

### Testing Edge Cases

- **Empty State**: Clear all messages and verify "No messages found" displays
  ```bash
  docker exec adws-test-app-mongodb mongosh --eval 'db.messages.deleteMany({})' adws-test-app
  ```

- **Error Handling**: Stop MongoDB and verify error message displays
  ```bash
  docker-compose stop mongodb
  ```

- **Loading State**: The button should show "Loading..." during API calls

## Troubleshooting

### Common Issues

#### MongoDB connection errors

**Symptom**: Backend logs "MongoDB connection error" and exits with code 1

**Solutions**:
1. Check MongoDB is running:
   ```bash
   docker-compose ps
   ```
   Status should show `Up (healthy)`

2. Check port 27017 is not in use:
   ```bash
   lsof -i :27017
   ```

3. Verify `.env` file exists in backend directory:
   ```bash
   cd backend
   cat .env
   ```

4. Check MongoDB logs:
   ```bash
   docker-compose logs mongodb
   ```

#### Frontend can't connect to backend

**Symptom**: Browser console shows "Failed to fetch" or network errors

**Solutions**:
1. Verify backend is running:
   ```bash
   curl http://localhost:5176/api/hello
   ```

2. Check Vite proxy configuration in `frontend/vite.config.js`:
   ```javascript
   proxy: {
     '/api': {
       target: 'http://localhost:5176',
       changeOrigin: true,
     },
   }
   ```

3. Try accessing backend directly: http://localhost:5176/api/hello

4. Check browser DevTools Network tab for failed requests

#### Port already in use errors

**Symptom**: Backend or frontend fails to start with "EADDRINUSE" error

**Solutions**:
1. Find process using the port:
   ```bash
   # macOS/Linux
   lsof -i :5176  # backend port
   lsof -i :5175  # frontend port

   # Or use kill:
   pkill -f "node server.js"
   pkill -f "vite"
   ```

2. Change port in `.env` file (backend) or Vite config (frontend)

#### Docker Compose issues

**Symptom**: `docker-compose up` fails with "database is locked" or other errors

**Solutions**:
1. Stop and remove containers:
   ```bash
   docker-compose down
   ```

2. Remove Docker volumes (deletes all MongoDB data):
   ```bash
   docker-compose down -v
   ```

3. Rebuild containers:
   ```bash
   docker-compose up -d --build
   ```

4. Check Docker Desktop is running and has sufficient resources

#### Module not found errors

**Symptom**: `npm start` fails with "Cannot find module" error

**Solutions**:
1. Install dependencies:
   ```bash
   cd backend  # or frontend
   npm install
   ```

2. Clear npm cache and reinstall:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

### Getting Help

1. Check [DOCKER.md](DOCKER.md) for detailed Docker setup
2. Review [dev-agent-record.md](dev-agent-record.md) for implementation notes
3. Check browser console and terminal logs for error details
4. Verify all prerequisites are installed (Node.js, Docker)

## Status

- ✅ **Story A1** — Create project scaffold and directory layout (2025-01-15)
- ✅ **Story A2** — Implement Express API endpoint and MongoDB schema (2026-01-15)
- ✅ **Story A3** — Implement frontend UI and API integration (2026-01-15)
- ✅ **Message Loading Feature** — Display messages list from MongoDB in frontend UI (2026-01-23)

### Completed Stories
- A1: Create project scaffold and directory layout
- A2: Implement Express API endpoint and MongoDB schema
- A3: Implement frontend UI and API integration
- **NEW**: Message Loading Feature - Users can now load and view messages from MongoDB with formatted timestamps

### Completed Features
- ✅ Backend API endpoints for hello and messages
- ✅ MongoDB integration with Message schema
- ✅ Frontend React application with Vite
- ✅ API proxy configuration for development
- ✅ Message list component with proper styling
- ✅ Loading states and error handling
- ✅ Empty state handling
- ✅ Timestamp formatting
- ✅ End-to-end integration testing
- ✅ Comprehensive documentation

### Pending Stories
- A4: Documentation, verification steps, and Jira ticket

---

This test app is part of the **Epic: Test App Skeleton — ADWS Portable Validation**
