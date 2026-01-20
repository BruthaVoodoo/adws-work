import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { connectToDatabase, isMongoConnected } from './db/connection.js';
import Message from './models/Message.js';

// Load environment variables
dotenv.config();

// Track server startup time for uptime calculation
const SERVER_START_TIME = Date.now();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Placeholder routes - will be expanded in Story A2
app.get('/', (req, res) => {
  res.json({ message: 'ADWS Test App Backend - Server running' });
});

// Task 1: GET /api/hello endpoint
app.get('/api/hello', (req, res) => {
  res.json({ hello: 'world' });
});

// Health check endpoint
app.get('/api/status', (req, res) => {
  const uptime = Math.floor((Date.now() - SERVER_START_TIME) / 1000);
  const mongoConnected = isMongoConnected();
  
  const response = {
    status: 'ok',
    uptime: uptime,
    mongodb: mongoConnected ? 'connected' : 'disconnected',
    timestamp: new Date().toISOString()
  };
  
  res.status(200).json(response);
});

// Task 3: GET /api/messages endpoint
app.get('/api/messages', async (req, res) => {
  try {
    const messages = await Message.find().sort({ createdAt: -1 });
    res.json({ messages });
  } catch (error) {
    console.error('Error fetching messages:', error);
    res.status(500).json({ error: 'Failed to fetch messages' });
  }
});

// Start server (only if this file is run directly)
if (import.meta.url === `file://${process.argv[1]}`) {
  // Try to connect to MongoDB but start server regardless
  connectToDatabase()
    .catch((error) => {
      console.warn('MongoDB connection failed, but starting server anyway:', error.message);
    });
  
  // Always start the server
  app.listen(PORT, () => {
    console.log(`Backend server running on http://localhost:${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
  });
}

export default app;
