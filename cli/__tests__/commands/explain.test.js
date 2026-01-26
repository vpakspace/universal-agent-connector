/**
 * Tests for explain command
 */

const { explainCommand } = require('../../lib/commands/explain');
const { APIClient } = require('../../lib/api/client');

jest.mock('../../lib/api/client');

describe('Explain Command', () => {
  let mockClient;
  let consoleLogSpy;
  let consoleErrorSpy;

  beforeEach(() => {
    mockClient = {
      explain: jest.fn()
    };
    APIClient.mockImplementation(() => mockClient);
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should explain query successfully', async () => {
    const mockResult = {
      sql: 'SELECT * FROM products WHERE price > 100',
      explanation: 'This query retrieves products with price greater than 100',
      tables_used: ['products'],
      columns_used: ['id', 'name', 'price']
    };

    mockClient.explain.mockResolvedValue(mockResult);

    await explainCommand('What are expensive products?', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: false
    });

    expect(mockClient.explain).toHaveBeenCalledWith('What are expensive products?');
    expect(consoleLogSpy).toHaveBeenCalled();
  });

  test('should output JSON format', async () => {
    const mockResult = {
      sql: 'SELECT * FROM products',
      explanation: 'Retrieves all products',
      tables_used: ['products'],
      columns_used: ['id', 'name']
    };

    mockClient.explain.mockResolvedValue(mockResult);

    await explainCommand('Get products', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: true
    });

    const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
    expect(jsonOutput.sql).toBe('SELECT * FROM products');
    expect(jsonOutput.explanation).toBe('Retrieves all products');
    expect(jsonOutput.tables).toEqual(['products']);
  });

  test('should handle missing explanation', async () => {
    const mockResult = {
      sql: 'SELECT * FROM products'
    };

    mockClient.explain.mockResolvedValue(mockResult);

    await explainCommand('Get products', {
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: false
    });

    expect(consoleLogSpy).toHaveBeenCalled();
  });

  test('should throw error when API key is missing', async () => {
    await expect(
      explainCommand('Get products', {
        url: 'http://localhost:5000',
        agentId: 'test-agent'
      })
    ).rejects.toThrow('API key required');
  });

  test('should throw error when agent ID is missing', async () => {
    await expect(
      explainCommand('Get products', {
        url: 'http://localhost:5000',
        apiKey: 'test-key'
      })
    ).rejects.toThrow('Agent ID required');
  });

  test('should handle API errors', async () => {
    mockClient.explain.mockRejectedValue(new Error('API Error (404): Agent not found'));

    await expect(
      explainCommand('Get products', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        agentId: 'test-agent',
        json: true
      })
    ).rejects.toThrow('API Error (404): Agent not found');

    const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
    expect(jsonOutput.success).toBe(false);
  });
});

