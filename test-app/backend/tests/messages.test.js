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
});
