/**
 * Comprehensive test suite for Universal Agent Connector SDK
 */

import { UniversalAgentConnector } from '../client';
import {
  APIError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ConnectionError
} from '../exceptions';

// Mock fetch globally
global.fetch = jest.fn();

describe('UniversalAgentConnector', () => {
  let client: UniversalAgentConnector;
  const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

  beforeEach(() => {
    client = new UniversalAgentConnector({
      baseUrl: 'http://localhost:5000'
    });
    mockFetch.mockClear();
  });

  describe('Client Initialization', () => {
    it('should initialize with default parameters', () => {
      const defaultClient = new UniversalAgentConnector();
      expect(defaultClient).toBeInstanceOf(UniversalAgentConnector);
    });

    it('should initialize with custom parameters', () => {
      const customClient = new UniversalAgentConnector({
        baseUrl: 'https://api.example.com',
        apiKey: 'test-key',
        timeout: 60000
      });
      expect(customClient).toBeInstanceOf(UniversalAgentConnector);
    });

    it('should remove trailing slashes from baseUrl', () => {
      const clientWithSlash = new UniversalAgentConnector({
        baseUrl: 'http://localhost:5000/'
      });
      expect(clientWithSlash).toBeInstanceOf(UniversalAgentConnector);
    });
  });

  describe('Request Handling', () => {
    it('should make successful GET request', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ status: 'success', data: { id: '123' } }),
        text: async () => JSON.stringify({ status: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await (client as any).request('GET', '/test');
      expect(result).toEqual({ status: 'success', data: { id: '123' } });
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('should handle authentication error (401)', async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        json: async () => ({ message: 'Unauthorized' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      await expect((client as any).request('GET', '/test')).rejects.toThrow(AuthenticationError);
    });

    it('should handle not found error (404)', async () => {
      const mockResponse = {
        ok: false,
        status: 404,
        json: async () => ({ message: 'Not found' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      await expect((client as any).request('GET', '/test')).rejects.toThrow(NotFoundError);
    });

    it('should handle validation error (400)', async () => {
      const mockResponse = {
        ok: false,
        status: 400,
        json: async () => ({ message: 'Invalid input' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      await expect((client as any).request('POST', '/test', undefined, { invalid: 'data' })).rejects.toThrow(ValidationError);
    });

    it('should handle rate limit error (429)', async () => {
      const mockResponse = {
        ok: false,
        status: 429,
        json: async () => ({ message: 'Rate limit exceeded' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      await expect((client as any).request('GET', '/test')).rejects.toThrow(RateLimitError);
    });

    it('should handle generic API error (500)', async () => {
      const mockResponse = {
        ok: false,
        status: 500,
        json: async () => ({ message: 'Internal server error' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      await expect((client as any).request('GET', '/test')).rejects.toThrow(APIError);
    });

    it('should handle connection errors', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      await expect((client as any).request('GET', '/test')).rejects.toThrow(ConnectionError);
    });

    it('should handle timeout errors', async () => {
      const abortError = new Error('AbortError');
      abortError.name = 'AbortError';
      mockFetch.mockRejectedValueOnce(abortError);

      await expect((client as any).request('GET', '/test')).rejects.toThrow(ConnectionError);
    });
  });

  describe('Health & Info', () => {
    it('should check health status', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ status: 'healthy', service: 'AI Agent Connector' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.healthCheck();
      expect(result.status).toBe('healthy');
    });

    it('should get API documentation', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ openapi: '3.0.0', info: { title: 'API' } }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getApiDocs();
      expect(result.openapi).toBe('3.0.0');
    });
  });

  describe('Agent Management', () => {
    it('should register an agent', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          agent_id: 'test-agent',
          api_key: 'generated-key'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.registerAgent({
        agent_id: 'test-agent',
        agent_credentials: { api_key: 'key', api_secret: 'secret' },
        database: { host: 'localhost', database: 'testdb' }
      });
      expect(result.agent_id).toBe('test-agent');
      expect(result.api_key).toBe('generated-key');
    });

    it('should get an agent', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ agent_id: 'test-agent', status: 'active' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getAgent('test-agent');
      expect(result.agent_id).toBe('test-agent');
    });

    it('should list all agents', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          agents: [
            { agent_id: 'agent1' },
            { agent_id: 'agent2' }
          ]
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.listAgents();
      expect(result).toHaveLength(2);
      expect(result[0].agent_id).toBe('agent1');
    });

    it('should delete an agent', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ message: 'Agent deleted' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.deleteAgent('test-agent');
      expect(result.message).toBe('Agent deleted');
    });

    it('should update agent database', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ message: 'Database updated' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.updateAgentDatabase('test-agent', {
        host: 'newhost',
        database: 'newdb'
      });
      expect(result.message).toBe('Database updated');
    });
  });

  describe('Query Execution', () => {
    it('should execute SQL query', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          data: [{ id: 1, name: 'Test' }],
          rows: 1
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.executeQuery('test-agent', 'SELECT * FROM users');
      expect(result.data).toHaveLength(1);
      expect(result.rows).toBe(1);
    });

    it('should execute natural language query', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          sql: 'SELECT * FROM users',
          data: [{ id: 1 }],
          confidence: 0.95
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.executeNaturalLanguageQuery(
        'test-agent',
        'Show me all users'
      );
      expect(result.sql).toBe('SELECT * FROM users');
      expect(result.confidence).toBe(0.95);
    });

    it('should get query suggestions', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          suggestions: [
            { sql: 'SELECT * FROM users', confidence: 0.9 },
            { sql: 'SELECT * FROM customers', confidence: 0.7 }
          ]
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getQuerySuggestions('test-agent', 'show users');
      expect(result).toHaveLength(2);
      expect(result[0].confidence).toBe(0.9);
    });
  });

  describe('AI Agents', () => {
    it('should register AI agent', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          agent_id: 'gpt-agent',
          provider: 'openai',
          model: 'gpt-4o-mini'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.registerAIAgent({
        agent_id: 'gpt-agent',
        provider: 'openai',
        model: 'gpt-4o-mini',
        api_key: 'sk-...'
      });
      expect(result.agent_id).toBe('gpt-agent');
      expect(result.provider).toBe('openai');
    });

    it('should execute AI query', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          response: 'AI response text',
          model: 'gpt-4o-mini'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.executeAIQuery('gpt-agent', 'What is AI?');
      expect(result.response).toBe('AI response text');
    });

    it('should set rate limit', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ message: 'Rate limit updated' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.setRateLimit('gpt-agent', {
        queries_per_minute: 60,
        queries_per_hour: 1000
      });
      expect(result.message).toBe('Rate limit updated');
    });

    it('should get rate limit', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          queries_per_minute: 60,
          queries_per_hour: 1000
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getRateLimit('gpt-agent');
      expect(result.queries_per_minute).toBe(60);
    });

    it('should set retry policy', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ message: 'Retry policy updated' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.setRetryPolicy('gpt-agent', {
        enabled: true,
        max_retries: 3,
        strategy: 'exponential'
      });
      expect(result.message).toBe('Retry policy updated');
    });
  });

  describe('Provider Failover', () => {
    it('should configure failover', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          agent_id: 'test-agent',
          primary_provider_id: 'openai-agent',
          backup_provider_ids: ['claude-agent']
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.configureFailover({
        agent_id: 'test-agent',
        primary_provider_id: 'openai-agent',
        backup_provider_ids: ['claude-agent']
      });
      expect(result.primary_provider_id).toBe('openai-agent');
    });

    it('should get failover stats', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          active_provider: 'openai-agent',
          total_switches: 2,
          provider_health: {
            'openai-agent': { status: 'healthy' }
          }
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getFailoverStats('test-agent');
      expect(result.active_provider).toBe('openai-agent');
      expect(result.total_switches).toBe(2);
    });

    it('should switch provider', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          message: 'Provider switched',
          new_provider: 'claude-agent'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.switchProvider('test-agent', 'claude-agent');
      expect(result.new_provider).toBe('claude-agent');
    });
  });

  describe('Cost Tracking', () => {
    it('should get cost dashboard', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          total_cost: 123.45,
          total_calls: 1000,
          cost_by_provider: { openai: 100.0, anthropic: 23.45 }
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getCostDashboard({ periodDays: 30 });
      expect(result.total_cost).toBe(123.45);
      expect(result.total_calls).toBe(1000);
    });

    it('should export cost report as JSON', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          records: [{ cost: 10.0, provider: 'openai' }]
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.exportCostReport({ format: 'json' });
      expect(result).toHaveProperty('records');
    });

    it('should export cost report as CSV', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        text: async () => 'timestamp,provider,cost\n2024-01-01,openai,10.0',
        headers: new Headers({ 'content-type': 'text/csv' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.exportCostReport({ format: 'csv' });
      expect(typeof result).toBe('string');
      expect(result).toContain('timestamp');
    });

    it('should create budget alert', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          alert_id: 'alert-123',
          name: 'Monthly Budget',
          threshold_usd: 1000.0
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.createBudgetAlert({
        name: 'Monthly Budget',
        thresholdUsd: 1000.0,
        period: 'monthly'
      });
      expect(result.alert_id).toBe('alert-123');
      expect(result.threshold_usd).toBe(1000.0);
    });
  });

  describe('Permissions', () => {
    it('should set permissions', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ message: 'Permissions updated' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.setPermissions('test-agent', [
        {
          resource_type: 'table',
          resource_id: 'users',
          permissions: ['read']
        }
      ]);
      expect(result.message).toBe('Permissions updated');
    });

    it('should get permissions', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          permissions: [
            { resource_type: 'table', resource_id: 'users', permissions: ['read'] }
          ]
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getPermissions('test-agent');
      expect(result).toHaveLength(1);
      expect(result[0].resource_id).toBe('users');
    });
  });

  describe('Query Templates', () => {
    it('should create query template', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          template_id: 'tpl-123',
          name: 'Top Users',
          sql: 'SELECT * FROM users LIMIT {{limit}}'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.createQueryTemplate(
        'test-agent',
        'Top Users',
        'SELECT * FROM users LIMIT {{limit}}'
      );
      expect(result.template_id).toBe('tpl-123');
    });

    it('should list query templates', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          templates: [
            { template_id: 'tpl-1', name: 'Template 1' },
            { template_id: 'tpl-2', name: 'Template 2' }
          ]
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.listQueryTemplates('test-agent');
      expect(result).toHaveLength(2);
    });
  });

  describe('Admin Methods', () => {
    it('should list databases', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          databases: [
            { name: 'db1', type: 'postgresql' },
            { name: 'db2', type: 'mysql' }
          ]
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.listDatabases();
      expect(result).toHaveLength(2);
    });

    it('should create RLS rule', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          rule_id: 'rls-123',
          table_name: 'users',
          rule_type: 'filter'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.createRLSRule({
        agentId: 'test-agent',
        tableName: 'users',
        ruleType: 'filter',
        condition: 'user_id = current_user_id()'
      });
      expect(result.rule_id).toBe('rls-123');
    });

    it('should create alert rule', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          rule_id: 'alert-rule-123',
          name: 'High Cost Alert',
          severity: 'high'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.createAlertRule({
        name: 'High Cost Alert',
        condition: 'cost > 1000',
        severity: 'high'
      });
      expect(result.rule_id).toBe('alert-rule-123');
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing optional parameters', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ result: 'success' }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.getCostDashboard();
      expect(result.result).toBe('success');
    });

    it('should handle empty list responses', async () => {
      const mockResponse = {
        ok: true,
        status: 200,
        json: async () => ({ agents: [] }),
        headers: new Headers({ 'content-type': 'application/json' })
      };
      mockFetch.mockResolvedValueOnce(mockResponse as Response);

      const result = await client.listAgents();
      expect(result).toEqual([]);
    });
  });

  describe('Integration Scenarios', () => {
    it('should complete workflow: register -> query -> check costs', async () => {
      // Register agent
      const registerResponse = {
        ok: true,
        status: 200,
        json: async () => ({
          agent_id: 'workflow-agent',
          api_key: 'key-123'
        }),
        headers: new Headers({ 'content-type': 'application/json' })
      };

      // Execute query
      const queryResponse = {
        ok: true,
        status: 200,
        json: async () => ({ data: [{ id: 1 }] }),
        headers: new Headers({ 'content-type': 'application/json' })
      };

      // Get costs
      const costResponse = {
        ok: true,
        status: 200,
        json: async () => ({ total_cost: 5.0 }),
        headers: new Headers({ 'content-type': 'application/json' })
      };

      mockFetch
        .mockResolvedValueOnce(registerResponse as Response)
        .mockResolvedValueOnce(queryResponse as Response)
        .mockResolvedValueOnce(costResponse as Response);

      // Register
      const agent = await client.registerAgent({
        agent_id: 'workflow-agent',
        agent_credentials: { api_key: 'key', api_secret: 'secret' },
        database: { host: 'localhost', database: 'testdb' }
      });
      expect(agent.agent_id).toBe('workflow-agent');

      // Query
      const result = await client.executeQuery('workflow-agent', 'SELECT 1');
      expect(result.data).toBeDefined();

      // Costs
      const costs = await client.getCostDashboard();
      expect(costs.total_cost).toBe(5.0);
    });
  });
});

