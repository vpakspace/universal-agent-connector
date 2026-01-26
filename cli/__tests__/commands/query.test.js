/**
 * Tests for query command
 */

const { queryCommand } = require('../../lib/commands/query');
const { APIClient } = require('../../lib/api/client');

jest.mock('../../lib/api/client');

describe('Query Command', () => {
  let mockClient;
  let consoleLogSpy;
  let consoleErrorSpy;

  beforeEach(() => {
    mockClient = {
      query: jest.fn()
    };
    APIClient.mockImplementation(() => mockClient);
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should execute query successfully', async () => {
    const mockResult = {
      sql: 'SELECT * FROM products LIMIT 10',
      rows: [
        { id: 1, name: 'Product 1', price: 100 },
        { id: 2, name: 'Product 2', price: 200 }
      ],
      columns: ['id', 'name', 'price'],
      execution_time: 45
    };

    mockClient.query.mockResolvedValue(mockResult);

    await queryCommand('What are the top products?', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: false,
      verbose: false
    });

    expect(mockClient.query).toHaveBeenCalledWith('What are the top products?', {
      preview: false,
      useCache: true
    });
    expect(consoleLogSpy).toHaveBeenCalled();
  });

  test('should output JSON format', async () => {
    const mockResult = {
      sql: 'SELECT * FROM products',
      rows: [{ id: 1, name: 'Product 1' }],
      columns: ['id', 'name']
    };

    mockClient.query.mockResolvedValue(mockResult);

    await queryCommand('Get products', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: true
    });

    const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
    expect(jsonOutput.sql).toBe('SELECT * FROM products');
    expect(jsonOutput.rows).toHaveLength(1);
  });

  test('should handle preview mode', async () => {
    const mockResult = {
      sql: 'SELECT * FROM products',
      explanation: 'This query retrieves all products'
    };

    mockClient.query.mockResolvedValue(mockResult);

    await queryCommand('Get products', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      preview: true
    });

    expect(mockClient.query).toHaveBeenCalledWith('Get products', {
      preview: true,
      useCache: true
    });
  });

  test('should handle cache option', async () => {
    mockClient.query.mockResolvedValue({ rows: [] });

    await queryCommand('Get products', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      cache: false
    });

    expect(mockClient.query).toHaveBeenCalledWith('Get products', {
      preview: false,
      useCache: false
    });
  });

  test('should throw error when API key is missing', async () => {
    await expect(
      queryCommand('Get products', {
        url: 'http://localhost:5000',
        agentId: 'test-agent'
      })
    ).rejects.toThrow('API key required');
  });

  test('should throw error when agent ID is missing', async () => {
    await expect(
      queryCommand('Get products', {
        url: 'http://localhost:5000',
        apiKey: 'test-key'
      })
    ).rejects.toThrow('Agent ID required');
  });

  test('should handle API errors', async () => {
    mockClient.query.mockRejectedValue(new Error('API Error (401): Invalid API key'));

    await expect(
      queryCommand('Get products', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        agentId: 'test-agent',
        json: true
      })
    ).rejects.toThrow('API Error (401): Invalid API key');

    const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
    expect(jsonOutput.success).toBe(false);
    expect(jsonOutput.error).toContain('Invalid API key');
  });

  test('should show verbose output', async () => {
    mockClient.query.mockResolvedValue({ rows: [] });

    await queryCommand('Get products', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      verbose: true
    });

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      expect.stringContaining('Querying:')
    );
  });
});

