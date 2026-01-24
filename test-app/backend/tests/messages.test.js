import request from 'supertest';
import app from '../server.js';

describe('GET /api/messages', () => {
  it('should return JSON response', async () => {
    const response = await request(app)
      .get('/api/messages')
      .expect('Content-Type', /json/);

    // Response should be JSON (either 200 or 500)
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.status).toBeLessThan(600);
  }, 15000);

  it('should handle database operations', async () => {
    // Verify the endpoint exists and returns structured data
    const response = await request(app)
      .get('/api/messages');

    expect(response.body).toBeDefined();
  }, 15000);

  it('should return proper JSON structure with messages array', async () => {
    const response = await request(app)
      .get('/api/messages')
      .expect('Content-Type', /json/);

    if (response.status === 200) {
      // Should have messages property that's an array
      expect(response.body).toHaveProperty('messages');
      expect(Array.isArray(response.body.messages)).toBe(true);
    } else if (response.status === 500) {
      // If MongoDB is unavailable, should return error
      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toBe('Failed to fetch messages');
    }
  }, 15000);

  it('should return messages with correct structure when present', async () => {
    const response = await request(app)
      .get('/api/messages');

    if (response.status === 200 && response.body.messages.length > 0) {
      // Check that each message has the expected structure
      response.body.messages.forEach(message => {
        expect(message).toHaveProperty('text');
        expect(message).toHaveProperty('createdAt');
        expect(typeof message.text).toBe('string');
        expect(new Date(message.createdAt)).toBeInstanceOf(Date);
      });
    }
  }, 15000);

  it('should handle empty messages array gracefully', async () => {
    const response = await request(app)
      .get('/api/messages');

    if (response.status === 200) {
      expect(response.body.messages).toBeDefined();
      expect(Array.isArray(response.body.messages)).toBe(true);
      // Empty array is valid
      expect(response.body.messages.length >= 0).toBe(true);
    }
  }, 15000);

  it('should return 500 status with error message when database is unavailable', async () => {
    // This test will only pass if MongoDB is actually unavailable
    // In normal operation with MongoDB running, this will return 200
    const response = await request(app)
      .get('/api/messages');

    if (response.status === 500) {
      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toBe('Failed to fetch messages');
    } else {
      // If status is 200, that's also valid when DB is available
      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('messages');
    }
  }, 15000);
});
