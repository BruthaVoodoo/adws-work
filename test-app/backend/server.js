import express from 'express';
import cors from 'cors';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Placeholder routes - will be expanded in Story A2
app.get('/', (req, res) => {
  res.json({ message: 'ADWS Test App Backend - Server running' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
});
