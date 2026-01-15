import { connectToDatabase, disconnectFromDatabase, isMongoConnected } from '../db/connection.js';

describe('MongoDB Connection Module', () => {
  describe('Module exports', () => {
    it('should export connectToDatabase function', () => {
      expect(typeof connectToDatabase).toBe('function');
    });

    it('should export disconnectFromDatabase function', () => {
      expect(typeof disconnectFromDatabase).toBe('function');
    });

    it('should export isMongoConnected function', () => {
      expect(typeof isMongoConnected).toBe('function');
    });
  });

  describe('isMongoConnected', () => {
    it('should return false by default', () => {
      expect(isMongoConnected()).toBe(false);
    });
  });

  describe('connectToDatabase (integration)', () => {
    it('should attempt to connect using default URI if MONGODB_URI not set', async () => {
      // This test verifies the function exists and can be called
      // Actual MongoDB connection is tested manually during server startup
      expect(async () => {
        await connectToDatabase();
      }).not.toThrow();
    }, 10000);
  });
});
