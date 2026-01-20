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

describe('GET /api/status', () => {
  it('should respond with 200 status code', async () => {
    await request(app)
      .get('/api/status')
      .expect(200);
  });

  it('should return JSON with required fields', async () => {
    const response = await request(app)
      .get('/api/status')
      .expect('Content-Type', /json/)
      .expect(200);

    expect(response.body).toHaveProperty('status');
    expect(response.body).toHaveProperty('uptime');
    expect(response.body).toHaveProperty('mongodb');
    expect(response.body).toHaveProperty('timestamp');
  });

  it('should return status field with value "ok"', async () => {
    const response = await request(app)
      .get('/api/status')
      .expect(200);

    expect(response.body.status).toBe('ok');
  });

  it('should return mongodb field with value "connected" or "disconnected"', async () => {
    const response = await request(app)
      .get('/api/status')
      .expect(200);

    expect(['connected', 'disconnected']).toContain(response.body.mongodb);
  });

  it('should return uptime as a positive integer', async () => {
    const response = await request(app)
      .get('/api/status')
      .expect(200);

    expect(typeof response.body.uptime).toBe('number');
    expect(response.body.uptime).toBeGreaterThanOrEqual(0);
    expect(Number.isInteger(response.body.uptime)).toBe(true);
  });

  it('should return timestamp as an ISO string', async () => {
    const response = await request(app)
      .get('/api/status')
      .expect(200);

    expect(typeof response.body.timestamp).toBe('string');
    // Verify it's a valid ISO 8601 date string
    const date = new Date(response.body.timestamp);
    expect(date.toISOString()).toBe(response.body.timestamp);
  });
});

describe('MongoDB Connection', () => {
  it('should log connection success when MongoDB is available', async () => {
    // This test will be implemented after MongoDB connection is added
    // For now, it's a placeholder
    expect(true).toBe(true);
  });
});
