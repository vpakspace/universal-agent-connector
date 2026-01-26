/**
 * Tests for API client
 */

const axios = require('axios');
const { APIClient } = require('../../lib/api/client');

jest.mock('axios');

describe('APIClient', () => {
  let client;
  let mockAxios;

  beforeEach(() => {
    mockAxios = {
      create: jest.fn(() => ({
        get: jest.fn(),
        post: jest.fn(),
        interceptors: {
          request: { use: jest.fn() },
          response: { use: jest.fn() }
        }
      }))
    };
    axios.create = mockAxios.create;
  });

  test('should create client with correct configuration', () => {
    client = new APIClient('http://localhost:5000', 'test-key', 'test-agent', false);
    
    expect(mockAxios.create).toHaveBeenCalledWith({
      baseURL: 'http://localhost:5000',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'test-key'
      },
      timeout: 30000
    });
  });

  test('should remove trailing slash from URL', () => {
    client = new APIClient('http://localhost:5000/', 'test-key', 'test-agent', false);
    
    expect(mockAxios.create).toHaveBeenCalledWith(
      expect.objectContaining({
        baseURL: 'http://localhost:5000'
      })
    );
  });

  test('should execute query', async () => {
    const mockResponse = {
      data: {
        sql: 'SELECT * FROM products',
        rows: [{ id: 1, name: 'Product 1' }],
        columns: ['id', 'name']
      }
    };

    const mockClient = {
      post: jest.fn().mockResolvedValue(mockResponse),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    };

    mockAxios.create.mockReturnValue(mockClient);
    client = new APIClient('http://localhost:5000', 'test-key', 'test-agent', false);

    const result = await client.query('What are the products?');

    expect(mockClient.post).toHaveBeenCalledWith(
      '/api/agents/test-agent/query/natural',
      {
        query: 'What are the products?',
        preview_only: false,
        use_cache: true,
        cache_ttl: null
      }
    );
    expect(result).toEqual(mockResponse.data);
  });

  test('should execute explain', async () => {
    const mockResponse = {
      data: {
        sql: 'SELECT * FROM products',
        explanation: 'Retrieves all products'
      }
    };

    const mockClient = {
      post: jest.fn().mockResolvedValue(mockResponse),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    };

    mockAxios.create.mockReturnValue(mockClient);
    client = new APIClient('http://localhost:5000', 'test-key', 'test-agent', false);

    const result = await client.explain('What are the products?');

    expect(mockClient.post).toHaveBeenCalledWith(
      '/api/agents/test-agent/query/natural',
      {
        query: 'What are the products?',
        preview_only: true
      }
    );
    expect(result).toEqual(mockResponse.data);
  });

  test('should test connection', async () => {
    const mockHealthResponse = {
      data: { status: 'ok' }
    };

    const mockAgentResponse = {
      data: {
        agent_id: 'test-agent',
        agent_info: { name: 'Test Agent' },
        database: { connection_string: 'postgresql://...' }
      }
    };

    const mockClient = {
      get: jest.fn()
        .mockResolvedValueOnce(mockHealthResponse)
        .mockResolvedValueOnce(mockAgentResponse),
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() }
      }
    };

    mockAxios.create.mockReturnValue(mockClient);
    client = new APIClient('http://localhost:5000', 'test-key', 'test-agent', false);

    const result = await client.test();

    expect(result.success).toBe(true);
    expect(result.health.status).toBe('ok');
    expect(result.agent.agent_id).toBe('test-agent');
  });

  test('should handle API errors', async () => {
    const mockClient = {
      post: jest.fn().mockRejectedValue({
        response: {
          status: 401,
          data: { error: 'Invalid API key' }
        }
      }),
      interceptors: {
        request: { use: jest.fn() },
        response: {
          use: jest.fn((onFulfilled, onRejected) => {
            // Simulate error handler
            const error = {
              response: {
                status: 401,
                data: { error: 'Invalid API key' }
              }
            };
            return onRejected(error);
          })
        }
      }
    };

    mockAxios.create.mockReturnValue(mockClient);
    client = new APIClient('http://localhost:5000', 'test-key', 'test-agent', false);

    await expect(client.query('test')).rejects.toThrow('API Error (401)');
  });

  test('should handle network errors', async () => {
    const mockClient = {
      post: jest.fn().mockRejectedValue({
        request: {},
        message: 'Network Error'
      }),
      interceptors: {
        request: { use: jest.fn() },
        response: {
          use: jest.fn((onFulfilled, onRejected) => {
            const error = {
              request: {},
              message: 'Network Error'
            };
            return onRejected(error);
          })
        }
      }
    };

    mockAxios.create.mockReturnValue(mockClient);
    client = new APIClient('http://localhost:5000', 'test-key', 'test-agent', false);

    await expect(client.query('test')).rejects.toThrow('Network Error');
  });
});

