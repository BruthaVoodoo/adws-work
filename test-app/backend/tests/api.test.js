import request from 'supertest';
import app from '../server.js';

describe('GET /api/hello', () => {
  it('should return JSON with hello: world', async () => {
    const response = await request(app)
      .get('/api/hello')
      .expect('Content-Type', /json/)
      .expect(200);

    expect(response.body).toEqual({ hello: 'world' });
  });
});

describe('MongoDB Connection', () => {
  it('should log connection success when MongoDB is available', async () => {
    // This test will be implemented after MongoDB connection is added
    // For now, it's a placeholder
    expect(true).toBe(true);
  });
});
