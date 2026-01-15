# Docker Setup for MongoDB

This document explains how to use Docker Compose to run MongoDB for the ADWS test app.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose installed (included with Docker Desktop)

## Quick Start

1. **Start MongoDB container**:
   ```bash
   cd test-app
   docker-compose up -d
   ```

2. **Verify MongoDB is running**:
   ```bash
   docker-compose ps
   ```
   Status should show `Up (healthy)` for the mongodb service.

3. **Start the backend**:
   ```bash
   cd backend
   npm start
   ```

   The backend will connect to MongoDB at `mongodb://localhost:27017/adws-test-app`

## Environment Configuration

The backend `.env.example` file is already configured for Docker:

```env
MONGODB_URI=mongodb://localhost:27017/adws-test-app
```

Copy `.env.example` to `.env` in the backend directory:

```bash
cd backend
cp .env.example .env
```

## Docker Compose Commands

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start MongoDB in background |
| `docker-compose down` | Stop and remove containers |
| `docker-compose ps` | Show running containers |
| `docker-compose logs -f mongodb` | View MongoDB logs |
| `docker-compose exec mongodb mongosh` | Access MongoDB shell |
| `docker volume rm adws_mongodb_data` | Delete MongoDB data |

## Connecting to MongoDB

### Using MongoDB Shell

```bash
docker-compose exec mongodb mongosh
```

Or connect to the local port:

```bash
mongosh mongodb://localhost:27017/adws-test-app
```

### Using MongoDB Compass

- Connection string: `mongodb://localhost:27017/adws-test-app`
- No authentication required (default configuration)

## Data Persistence

MongoDB data is stored in a Docker volume named `adws_mongodb_data`. This persists across container restarts. To remove all data:

```bash
docker-compose down -v
```

## Stopping MongoDB

When you're done:

```bash
docker-compose down
```

This stops the MongoDB container but preserves data.

## Troubleshooting

### Port 27017 already in use

If you have MongoDB running locally, stop it first:

```bash
# macOS/Linux
brew services stop mongodb-community
# or
sudo systemctl stop mongod

# Or change the port in docker-compose.yml
ports:
  - "27018:27017"
```

Then update backend `.env`:
```env
MONGODB_URI=mongodb://localhost:27018/adws-test-app
```

### Container not starting

Check logs:
```bash
docker-compose logs mongodb
```

### Backend can't connect to MongoDB

1. Verify MongoDB is healthy:
   ```bash
   docker-compose ps
   ```

2. Verify backend `.env` matches port mapping:
   ```env
   MONGODB_URI=mongodb://localhost:27017/adws-test-app
   ```

3. Wait for MongoDB health check (up to 40 seconds on first start):
   ```bash
   docker-compose logs -f mongodb | grep "waiting for connections"
   ```
