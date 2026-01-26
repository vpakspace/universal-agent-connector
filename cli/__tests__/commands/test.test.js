/**
 * Tests for test command
 */

const { testCommand } = require('../../lib/commands/test');
const { APIClient } = require('../../lib/api/client');

jest.mock('../../lib/api/client');

describe('Test Command', () => {
  let mockClient;
  let consoleLogSpy;
  let consoleErrorSpy;
  let processExitSpy;

  beforeEach(() => {
    mockClient = {
      test: jest.fn()
    };
    APIClient.mockImplementation(() => mockClient);
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
    processExitSpy = jest.spyOn(process, 'exit').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('should test connection successfully', async () => {
    const mockResult = {
      success: true,
      health: { status: 'ok' },
      agent: {
        agent_id: 'test-agent',
        name: 'Test Agent',
        has_database: true
      }
    };

    mockClient.test.mockResolvedValue(mockResult);

    await testCommand({
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: false
    });

    expect(mockClient.test).toHaveBeenCalled();
    expect(consoleLogSpy).toHaveBeenCalled();
  });

  test('should output JSON format', async () => {
    const mockResult = {
      success: true,
      health: { status: 'ok' },
      agent: {
        agent_id: 'test-agent',
        name: 'Test Agent',
        has_database: true
      }
    };

    mockClient.test.mockResolvedValue(mockResult);

    await testCommand({
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: true
    });

    const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
    expect(jsonOutput.success).toBe(true);
    expect(jsonOutput.agent.agent_id).toBe('test-agent');
  });

  test('should handle connection failure', async () => {
    const mockResult = {
      success: false,
      error: 'Connection failed'
    };

    mockClient.test.mockResolvedValue(mockResult);

    await testCommand({
      url: 'http://localhost:5000',
      apiKey: 'test-key',
      agentId: 'test-agent',
      json: false
    });

    expect(processExitSpy).toHaveBeenCalledWith(1);
  });

  test('should throw error when API key is missing', async () => {
    await expect(
      testCommand({
        url: 'http://localhost:5000',
        agentId: 'test-agent'
      })
    ).rejects.toThrow('API key required');
  });

  test('should throw error when agent ID is missing', async () => {
    await expect(
      testCommand({
        url: 'http://localhost:5000',
        apiKey: 'test-key'
      })
    ).rejects.toThrow('Agent ID required');
  });

  test('should handle API errors', async () => {
    mockClient.test.mockRejectedValue(new Error('Network Error'));

    await expect(
      testCommand({
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        agentId: 'test-agent',
        json: true
      })
    ).rejects.toThrow('Network Error');

    const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
    expect(jsonOutput.success).toBe(false);
  });
});

