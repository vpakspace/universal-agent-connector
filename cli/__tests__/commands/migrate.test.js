/**
 * Tests for migrate command
 */

const fs = require('fs');
const path = require('path');
const { migrateCommand } = require('../../lib/commands/migrate');
const { APIClient } = require('../../lib/api/client');

jest.mock('../../lib/api/client');
jest.mock('fs');

describe('Migrate Command', () => {
  let mockClient;
  let consoleLogSpy;
  let consoleErrorSpy;

  beforeEach(() => {
    mockClient = {
      getAgent: jest.fn(),
      listTables: jest.fn()
    };
    APIClient.mockImplementation(() => mockClient);
    consoleLogSpy = jest.spyOn(console, 'log').mockImplementation();
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Export', () => {
    test('should export configuration successfully', async () => {
      const mockAgent = {
        agent_id: 'test-agent',
        agent_info: { name: 'Test Agent', type: 'analytics' },
        database: { type: 'postgresql', connection_name: 'test-db' },
        resource_permissions: {
          'products': { type: 'table', permissions: ['read'] }
        }
      };

      const mockTables = {
        tables: ['products', 'customers']
      };

      mockClient.getAgent.mockResolvedValue(mockAgent);
      mockClient.listTables.mockResolvedValue(mockTables);
      fs.writeFileSync.mockImplementation();

      await migrateCommand('export', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        agentId: 'test-agent',
        output: 'config.json',
        json: false
      });

      expect(mockClient.getAgent).toHaveBeenCalled();
      expect(mockClient.listTables).toHaveBeenCalled();
      expect(fs.writeFileSync).toHaveBeenCalled();
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Configuration exported')
      );
    });

    test('should export to JSON format', async () => {
      const mockAgent = {
        agent_id: 'test-agent',
        agent_info: { name: 'Test Agent' },
        resource_permissions: {}
      };

      mockClient.getAgent.mockResolvedValue(mockAgent);
      mockClient.listTables.mockResolvedValue({ tables: [] });
      fs.writeFileSync.mockImplementation();

      await migrateCommand('export', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        agentId: 'test-agent',
        output: 'config.json',
        json: true
      });

      const writtenContent = fs.writeFileSync.mock.calls[0][1];
      const config = JSON.parse(writtenContent);
      expect(config.agent.agent_id).toBe('test-agent');
      expect(config.version).toBe('1.0.0');
    });

    test('should throw error when API key is missing', async () => {
      await expect(
        migrateCommand('export', {
          url: 'http://localhost:5000',
          agentId: 'test-agent'
        })
      ).rejects.toThrow('API key required');
    });

    test('should throw error when agent ID is missing', async () => {
      await expect(
        migrateCommand('export', {
          url: 'http://localhost:5000',
          apiKey: 'test-key'
        })
      ).rejects.toThrow('Agent ID required');
    });

    test('should handle export errors', async () => {
      mockClient.getAgent.mockRejectedValue(new Error('API Error'));

      await expect(
        migrateCommand('export', {
          url: 'http://localhost:5000',
          apiKey: 'test-key',
          agentId: 'test-agent',
          output: 'config.json',
          json: true
        })
      ).rejects.toThrow('API Error');

      const jsonOutput = JSON.parse(consoleLogSpy.mock.calls[0][0]);
      expect(jsonOutput.success).toBe(false);
    });
  });

  describe('Import', () => {
    const mockConfig = {
      version: '1.0.0',
      exported_at: '2024-01-15T00:00:00Z',
      agent: {
        agent_id: 'test-agent',
        name: 'Test Agent',
        resource_permissions: {
          'products': { type: 'table', permissions: ['read'] }
        }
      },
      tables: ['products']
    };

    beforeEach(() => {
      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));
    });

    test('should import configuration successfully', async () => {
      mockClient.getAgent.mockRejectedValue({
        message: 'API Error (404): Agent not found'
      });

      await migrateCommand('import', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        input: 'config.json',
        json: false
      });

      expect(fs.readFileSync).toHaveBeenCalled();
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Configuration validated')
      );
    });

    test('should validate only when --validate flag is set', async () => {
      await migrateCommand('import', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        input: 'config.json',
        validate: true,
        json: false
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Validation only')
      );
    });

    test('should perform dry run', async () => {
      mockClient.getAgent.mockRejectedValue({
        message: 'API Error (404): Agent not found'
      });

      await migrateCommand('import', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        input: 'config.json',
        dryRun: true,
        json: false
      });

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Dry run mode')
      );
    });

    test('should throw error when input file is missing', async () => {
      await expect(
        migrateCommand('import', {
          url: 'http://localhost:5000',
          apiKey: 'test-key'
        })
      ).rejects.toThrow('Input file required');
    });

    test('should throw error when input file does not exist', async () => {
      fs.existsSync.mockReturnValue(false);

      await expect(
        migrateCommand('import', {
          url: 'http://localhost:5000',
          apiKey: 'test-key',
          input: 'nonexistent.json'
        })
      ).rejects.toThrow('Configuration file not found');
    });

    test('should throw error for invalid JSON', async () => {
      fs.readFileSync.mockReturnValue('invalid json');

      await expect(
        migrateCommand('import', {
          url: 'http://localhost:5000',
          apiKey: 'test-key',
          input: 'config.json'
        })
      ).rejects.toThrow();
    });

    test('should throw error for invalid configuration', async () => {
      const invalidConfig = {
        version: '1.0.0'
        // Missing agent
      };

      fs.readFileSync.mockReturnValue(JSON.stringify(invalidConfig));

      await expect(
        migrateCommand('import', {
          url: 'http://localhost:5000',
          apiKey: 'test-key',
          input: 'config.json'
        })
      ).rejects.toThrow('Configuration validation failed');
    });
  });

  describe('Rollback', () => {
    const mockBackupConfig = {
      version: '1.0.0',
      agent: {
        agent_id: 'test-agent',
        name: 'Test Agent',
        resource_permissions: {}
      }
    };

    beforeEach(() => {
      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockReturnValue(JSON.stringify(mockBackupConfig));
      mockClient.getAgent.mockRejectedValue({
        message: 'API Error (404): Agent not found'
      });
    });

    test('should rollback configuration successfully', async () => {
      await migrateCommand('rollback', {
        url: 'http://localhost:5000',
        apiKey: 'test-key',
        backup: 'backup.json',
        json: false
      });

      expect(fs.readFileSync).toHaveBeenCalled();
      expect(consoleLogSpy).toHaveBeenCalled();
    });

    test('should throw error when backup file is missing', async () => {
      await expect(
        migrateCommand('rollback', {
          url: 'http://localhost:5000',
          apiKey: 'test-key'
        })
      ).rejects.toThrow('Backup file required');
    });

    test('should throw error when backup file does not exist', async () => {
      fs.existsSync.mockReturnValue(false);

      await expect(
        migrateCommand('rollback', {
          url: 'http://localhost:5000',
          apiKey: 'test-key',
          backup: 'nonexistent.json'
        })
      ).rejects.toThrow('Backup file not found');
    });
  });

  describe('Invalid Action', () => {
    test('should throw error for unknown action', async () => {
      await expect(
        migrateCommand('unknown', {
          url: 'http://localhost:5000',
          apiKey: 'test-key'
        })
      ).rejects.toThrow('Unknown action');
    });
  });
});

