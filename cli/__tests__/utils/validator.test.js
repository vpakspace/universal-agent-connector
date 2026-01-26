/**
 * Tests for configuration validator
 */

const fs = require('fs');
const { validateConfig, validateMigrationFile } = require('../../lib/utils/validator');

jest.mock('fs');

describe('Configuration Validator', () => {
  describe('validateConfig', () => {
    test('should validate valid configuration', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent',
          resource_permissions: {
            'products': {
              type: 'table',
              permissions: ['read']
            }
          }
        },
        tables: ['products'],
        metadata: {}
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should reject configuration without version', () => {
      const config = {
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent'
        }
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing version field');
    });

    test('should reject configuration without agent', () => {
      const config = {
        version: '1.0.0'
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing agent configuration');
    });

    test('should reject configuration without agent_id', () => {
      const config = {
        version: '1.0.0',
        agent: {
          name: 'Test Agent'
        }
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing agent.agent_id');
    });

    test('should reject configuration without agent name', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent'
        }
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Missing agent.name');
    });

    test('should validate resource permissions structure', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent',
          resource_permissions: {
            'products': {
              type: 'table',
              permissions: ['read', 'write']
            }
          }
        }
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(true);
    });

    test('should reject invalid resource permissions', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent',
          resource_permissions: {
            'products': {
              // Missing type
              permissions: ['read']
            }
          }
        }
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Missing type'))).toBe(true);
    });

    test('should reject non-array permissions', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent',
          resource_permissions: {
            'products': {
              type: 'table',
              permissions: 'read' // Should be array
            }
          }
        }
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('must be an array'))).toBe(true);
    });

    test('should validate tables array', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent'
        },
        tables: ['products', 'customers']
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(true);
    });

    test('should reject non-array tables', () => {
      const config = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent'
        },
        tables: 'products' // Should be array
      };

      const result = validateConfig(config);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('tables must be an array');
    });
  });

  describe('validateMigrationFile', () => {
    test('should validate existing file', () => {
      const mockConfig = {
        version: '1.0.0',
        agent: {
          agent_id: 'test-agent',
          name: 'Test Agent'
        }
      };

      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockReturnValue(JSON.stringify(mockConfig));

      const result = validateMigrationFile('config.json');
      expect(result.valid).toBe(true);
    });

    test('should reject non-existent file', () => {
      fs.existsSync.mockReturnValue(false);

      const result = validateMigrationFile('nonexistent.json');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('File does not exist');
    });

    test('should reject invalid JSON', () => {
      fs.existsSync.mockReturnValue(true);
      fs.readFileSync.mockReturnValue('invalid json');

      const result = validateMigrationFile('config.json');
      expect(result.valid).toBe(false);
      expect(result.errors.some(e => e.includes('Invalid JSON'))).toBe(true);
    });
  });
});

