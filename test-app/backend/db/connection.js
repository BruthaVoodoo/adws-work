import mongoose from 'mongoose';

let isConnected = false;

/**
 * Connect to MongoDB using environment variables
 * @returns {Promise<void>}
 */
export async function connectToDatabase() {
  if (isConnected) {
    console.log('MongoDB already connected');
    return;
  }

  try {
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/adws-test-app';
    
    // Set connection options with timeout for faster failure in tests
    const options = {
      serverSelectionTimeoutMS: 5000, // 5 second timeout
      connectTimeoutMS: 5000,
    };
    
    await mongoose.connect(mongoUri, options);
    isConnected = true;
    console.log('MongoDB connected successfully');
  } catch (error) {
    console.error('MongoDB connection error:', error.message);
    throw error;
  }
}

/**
 * Disconnect from MongoDB
 * @returns {Promise<void>}
 */
export async function disconnectFromDatabase() {
  try {
    await mongoose.disconnect();
    isConnected = false;
    console.log('MongoDB disconnected');
  } catch (error) {
    console.error('MongoDB disconnection error:', error.message);
    throw error;
  }
}

/**
 * Check if MongoDB is connected
 * @returns {boolean}
 */
export function isMongoConnected() {
  return isConnected && mongoose.connection.readyState === 1;
}
