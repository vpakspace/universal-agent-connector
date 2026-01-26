/**
 * Main client class for Universal Agent Connector SDK
 */

import {
  ClientConfig,
  RegisterAgentRequest,
  Agent,
  QueryResult,
  NaturalLanguageQueryResult,
  QuerySuggestion,
  AIAgentConfig,
  RateLimitConfig,
  RetryPolicyConfig,
  FailoverConfig,
  FailoverStats,
  CostDashboard,
  BudgetAlert,
  QueryTemplate,
  Permission,
  AuditLog,
  Notification,
  RLSRule,
  MaskingRule,
  AlertRule,
  Team,
  SharedQuery,
  Webhook,
  QueryTrace,
  CacheStats,
  DashboardMetrics,
  DatabaseConfig
} from './types';

import {
  APIError,
  AuthenticationError,
  NotFoundError,
  ValidationError,
  RateLimitError,
  ConnectionError
} from './exceptions';

/**
 * Universal Agent Connector JavaScript/TypeScript SDK Client
 * 
 * Provides easy access to all API endpoints for managing AI agents,
 * database connections, permissions, queries, and more.
 * 
 * @example
 * ```typescript
 * import { UniversalAgentConnector } from 'universal-agent-connector';
 * 
 * const client = new UniversalAgentConnector({
 *   baseUrl: 'http://localhost:5000',
 *   apiKey: 'your-api-key'
 * });
 * 
 * const agent = await client.registerAgent({
 *   agent_id: 'my-agent',
 *   agent_credentials: { api_key: 'key', api_secret: 'secret' },
 *   database: { host: 'localhost', database: 'mydb' }
 * });
 * ```
 */
export class UniversalAgentConnector {
  private baseUrl: string;
  private apiUrl: string;
  private apiKey?: string;
  private timeout: number;
  private headers: Record<string, string>;

  constructor(config: ClientConfig = {}) {
    this.baseUrl = (config.baseUrl || 'http://localhost:5000').replace(/\/$/, '');
    this.apiUrl = `${this.baseUrl}/api`;
    this.apiKey = config.apiKey;
    this.timeout = config.timeout || 30000;
    
    this.headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.apiKey) {
      this.headers['Authorization'] = `Bearer ${this.apiKey}`;
    }
  }

  /**
   * Make an HTTP request to the API
   */
  private async request<T = any>(
    method: string,
    endpoint: string,
    params?: Record<string, any>,
    body?: any
  ): Promise<T> {
    const url = new URL(endpoint.startsWith('/') ? endpoint : `/${endpoint}`, this.apiUrl);
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const options: RequestInit = {
      method,
      headers: this.headers,
      signal: AbortSignal.timeout(this.timeout)
    };

    if (body && (method === 'POST' || method === 'PUT')) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url.toString(), options);

      // Handle errors
      if (response.status === 401) {
        const errorData = await response.json().catch(() => ({}));
        throw new AuthenticationError(
          'Authentication failed. Check your API key.',
          401,
          errorData
        );
      } else if (response.status === 404) {
        const errorData = await response.json().catch(() => ({}));
        throw new NotFoundError(
          errorData.message || 'Resource not found',
          404,
          errorData
        );
      } else if (response.status === 400) {
        const errorData = await response.json().catch(() => ({}));
        throw new ValidationError(
          errorData.message || 'Validation error',
          400,
          errorData
        );
      } else if (response.status === 429) {
        const errorData = await response.json().catch(() => ({}));
        throw new RateLimitError(
          'Rate limit exceeded',
          429,
          errorData
        );
      } else if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.message || `API error: ${response.status}`,
          response.status,
          errorData
        );
      }

      // Return JSON response
      if (response.headers.get('content-type')?.includes('application/json')) {
        return await response.json();
      }
      
      // For CSV or text responses
      const text = await response.text();
      try {
        return JSON.parse(text) as T;
      } catch {
        return text as any;
      }
    } catch (error) {
      if (error instanceof APIError || error instanceof AuthenticationError ||
          error instanceof NotFoundError || error instanceof ValidationError ||
          error instanceof RateLimitError) {
        throw error;
      }
      
      if (error instanceof Error && error.name === 'AbortError') {
        throw new ConnectionError(`Request timeout after ${this.timeout}ms`);
      }
      
      throw new ConnectionError(`Connection failed: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  // ============================================================================
  // Health & Info
  // ============================================================================

  /**
   * Check API health status
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.request('GET', '/health');
  }

  /**
   * Get API documentation
   */
  async getApiDocs(): Promise<any> {
    return this.request('GET', '/api-docs');
  }

  // ============================================================================
  // Agents
  // ============================================================================

  /**
   * Register a new AI agent
   */
  async registerAgent(request: RegisterAgentRequest): Promise<Agent> {
    return this.request<Agent>('POST', '/agents/register', undefined, request);
  }

  /**
   * Get agent information
   */
  async getAgent(agentId: string): Promise<Agent> {
    return this.request<Agent>('GET', `/agents/${agentId}`);
  }

  /**
   * List all registered agents
   */
  async listAgents(): Promise<Agent[]> {
    const response = await this.request<{ agents: Agent[] }>('GET', '/agents');
    return response.agents || [];
  }

  /**
   * Delete/revoke an agent
   */
  async deleteAgent(agentId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/agents/${agentId}`);
  }

  /**
   * Update agent's database connection
   */
  async updateAgentDatabase(agentId: string, database: DatabaseConfig): Promise<{ message: string }> {
    return this.request('PUT', `/agents/${agentId}/database`, undefined, database);
  }

  // ============================================================================
  // Permissions
  // ============================================================================

  /**
   * Set permissions for an agent
   */
  async setPermissions(agentId: string, permissions: Permission[]): Promise<{ message: string }> {
    return this.request('PUT', `/agents/${agentId}/permissions/resources`, undefined, { permissions });
  }

  /**
   * Get permissions for an agent
   */
  async getPermissions(agentId: string): Promise<Permission[]> {
    const response = await this.request<{ permissions: Permission[] }>('GET', `/agents/${agentId}/permissions/resources`);
    return response.permissions || [];
  }

  /**
   * Revoke a specific permission
   */
  async revokePermission(agentId: string, resourceId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/agents/${agentId}/permissions/resources/${resourceId}`);
  }

  // ============================================================================
  // Database
  // ============================================================================

  /**
   * Test a database connection
   */
  async testDatabaseConnection(database: DatabaseConfig): Promise<{ success: boolean; message?: string }> {
    return this.request('POST', '/databases/test', undefined, database);
  }

  /**
   * Get list of tables accessible to an agent
   */
  async getAgentTables(agentId: string): Promise<string[]> {
    const response = await this.request<{ tables: string[] }>('GET', `/agents/${agentId}/tables`);
    return response.tables || [];
  }

  /**
   * Get access preview for an agent
   */
  async getAccessPreview(agentId: string): Promise<any> {
    return this.request('GET', `/agents/${agentId}/access-preview`);
  }

  // ============================================================================
  // Queries
  // ============================================================================

  /**
   * Execute a SQL query
   */
  async executeQuery(
    agentId: string,
    query: string,
    params?: Record<string, any>,
    fetch: boolean = true
  ): Promise<QueryResult> {
    return this.request<QueryResult>('POST', `/agents/${agentId}/query`, undefined, {
      query,
      params,
      fetch
    });
  }

  /**
   * Execute a natural language query (converts to SQL)
   */
  async executeNaturalLanguageQuery(
    agentId: string,
    query: string,
    options?: {
      previewOnly?: boolean;
      useCache?: boolean;
      useTemplate?: string;
      templateParams?: Record<string, any>;
    }
  ): Promise<NaturalLanguageQueryResult> {
    return this.request<NaturalLanguageQueryResult>(
      'POST',
      `/agents/${agentId}/query/natural`,
      undefined,
      {
        query,
        preview_only: options?.previewOnly,
        use_cache: options?.useCache,
        use_template: options?.useTemplate,
        template_params: options?.templateParams
      }
    );
  }

  /**
   * Get SQL query suggestions for ambiguous natural language input
   */
  async getQuerySuggestions(
    agentId: string,
    query: string,
    numSuggestions: number = 3
  ): Promise<QuerySuggestion[]> {
    const response = await this.request<{ suggestions: QuerySuggestion[] }>(
      'POST',
      `/agents/${agentId}/query/suggestions`,
      undefined,
      { query, num_suggestions: numSuggestions }
    );
    return response.suggestions || [];
  }

  // ============================================================================
  // Query Templates
  // ============================================================================

  /**
   * Create a query template
   */
  async createQueryTemplate(
    agentId: string,
    name: string,
    sql: string,
    options?: {
      tags?: string[];
      isPublic?: boolean;
    }
  ): Promise<QueryTemplate> {
    return this.request<QueryTemplate>(
      'POST',
      `/agents/${agentId}/query/templates`,
      undefined,
      {
        name,
        sql,
        tags: options?.tags,
        is_public: options?.isPublic
      }
    );
  }

  /**
   * List query templates
   */
  async listQueryTemplates(agentId: string, tags?: string[]): Promise<QueryTemplate[]> {
    const params: Record<string, any> = {};
    if (tags && tags.length > 0) {
      params.tags = tags.join(',');
    }
    
    const response = await this.request<{ templates: QueryTemplate[] }>(
      'GET',
      `/agents/${agentId}/query/templates`,
      params
    );
    return response.templates || [];
  }

  /**
   * Get a specific query template
   */
  async getQueryTemplate(agentId: string, templateId: string): Promise<QueryTemplate> {
    return this.request<QueryTemplate>('GET', `/agents/${agentId}/query/templates/${templateId}`);
  }

  /**
   * Update a query template
   */
  async updateQueryTemplate(
    agentId: string,
    templateId: string,
    updates: Partial<QueryTemplate>
  ): Promise<QueryTemplate> {
    return this.request<QueryTemplate>(
      'PUT',
      `/agents/${agentId}/query/templates/${templateId}`,
      undefined,
      updates
    );
  }

  /**
   * Delete a query template
   */
  async deleteQueryTemplate(agentId: string, templateId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/agents/${agentId}/query/templates/${templateId}`);
  }

  // ============================================================================
  // AI Agents (Admin)
  // ============================================================================

  /**
   * Register an AI agent (OpenAI, Anthropic, or custom)
   */
  async registerAIAgent(config: AIAgentConfig): Promise<Agent> {
    return this.request<Agent>('POST', '/admin/ai-agents/register', undefined, config);
  }

  /**
   * List all registered AI agents
   */
  async listAIAgents(): Promise<Agent[]> {
    const response = await this.request<{ agents: Agent[] }>('GET', '/admin/ai-agents');
    return response.agents || [];
  }

  /**
   * Get AI agent information
   */
  async getAIAgent(agentId: string): Promise<Agent> {
    return this.request<Agent>('GET', `/admin/ai-agents/${agentId}`);
  }

  /**
   * Execute a query using an AI agent
   */
  async executeAIQuery(
    agentId: string,
    query: string,
    context?: Record<string, any>
  ): Promise<{ response: string; model?: string; [key: string]: any }> {
    return this.request('POST', `/admin/ai-agents/${agentId}/query`, undefined, {
      query,
      context
    });
  }

  /**
   * Set rate limit for an AI agent
   */
  async setRateLimit(agentId: string, rateLimit: RateLimitConfig): Promise<{ message: string }> {
    return this.request('POST', `/admin/ai-agents/${agentId}/rate-limit`, undefined, rateLimit);
  }

  /**
   * Get rate limit configuration for an AI agent
   */
  async getRateLimit(agentId: string): Promise<RateLimitConfig> {
    return this.request<RateLimitConfig>('GET', `/admin/ai-agents/${agentId}/rate-limit`);
  }

  /**
   * Set retry policy for an AI agent
   */
  async setRetryPolicy(agentId: string, policy: RetryPolicyConfig): Promise<{ message: string }> {
    return this.request('POST', `/admin/ai-agents/${agentId}/retry-policy`, undefined, policy);
  }

  /**
   * Get retry policy for an AI agent
   */
  async getRetryPolicy(agentId: string): Promise<RetryPolicyConfig> {
    return this.request<RetryPolicyConfig>('GET', `/admin/ai-agents/${agentId}/retry-policy`);
  }

  /**
   * Delete an AI agent
   */
  async deleteAIAgent(agentId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/admin/ai-agents/${agentId}`);
  }

  // ============================================================================
  // Provider Failover
  // ============================================================================

  /**
   * Configure provider failover for an agent
   */
  async configureFailover(config: FailoverConfig): Promise<FailoverConfig> {
    return this.request<FailoverConfig>('POST', `/agents/${config.agent_id}/failover`, undefined, config);
  }

  /**
   * Get failover configuration for an agent
   */
  async getFailoverConfig(agentId: string): Promise<FailoverConfig> {
    return this.request<FailoverConfig>('GET', `/agents/${agentId}/failover`);
  }

  /**
   * Get failover statistics for an agent
   */
  async getFailoverStats(agentId: string): Promise<FailoverStats> {
    return this.request<FailoverStats>('GET', `/agents/${agentId}/failover/stats`);
  }

  /**
   * Check provider health for an agent
   */
  async checkProviderHealth(agentId: string): Promise<Record<string, any>> {
    return this.request('GET', `/agents/${agentId}/failover/health`);
  }

  /**
   * Get health status of all providers
   */
  async getAllProviderHealth(): Promise<Record<string, any>> {
    return this.request('GET', '/providers/health');
  }

  /**
   * Manually switch to a different provider
   */
  async switchProvider(agentId: string, providerId: string): Promise<{ message: string; new_provider: string }> {
    return this.request('POST', `/agents/${agentId}/failover/switch`, undefined, { provider_id: providerId });
  }

  // ============================================================================
  // Cost Tracking
  // ============================================================================

  /**
   * Get cost dashboard data
   */
  async getCostDashboard(options?: {
    agentId?: string;
    provider?: string;
    periodDays?: number;
  }): Promise<CostDashboard> {
    const params: Record<string, any> = {
      period_days: options?.periodDays || 30
    };
    if (options?.agentId) params.agent_id = options.agentId;
    if (options?.provider) params.provider = options.provider;
    
    return this.request<CostDashboard>('GET', '/cost/dashboard', params);
  }

  /**
   * Export cost report
   */
  async exportCostReport(options?: {
    format?: 'json' | 'csv';
    agentId?: string;
    provider?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<any> {
    const params: Record<string, any> = {
      format: options?.format || 'json'
    };
    if (options?.agentId) params.agent_id = options.agentId;
    if (options?.provider) params.provider = options.provider;
    if (options?.startDate) params.start_date = options.startDate;
    if (options?.endDate) params.end_date = options.endDate;
    
    return this.request('GET', '/cost/export', params);
  }

  /**
   * Get cost statistics
   */
  async getCostStats(options?: {
    agentId?: string;
    provider?: string;
    periodDays?: number;
  }): Promise<any> {
    const params: Record<string, any> = {
      period_days: options?.periodDays || 30
    };
    if (options?.agentId) params.agent_id = options.agentId;
    if (options?.provider) params.provider = options.provider;
    
    return this.request('GET', '/cost/stats', params);
  }

  /**
   * Create a budget alert
   */
  async createBudgetAlert(alert: {
    name: string;
    thresholdUsd: number;
    period: 'daily' | 'weekly' | 'monthly';
    notificationEmails?: string[];
    webhookUrl?: string;
  }): Promise<BudgetAlert> {
    return this.request<BudgetAlert>('POST', '/cost/budget-alerts', undefined, {
      name: alert.name,
      threshold_usd: alert.thresholdUsd,
      period: alert.period,
      notification_emails: alert.notificationEmails,
      webhook_url: alert.webhookUrl
    });
  }

  /**
   * List all budget alerts
   */
  async listBudgetAlerts(): Promise<BudgetAlert[]> {
    const response = await this.request<{ alerts: BudgetAlert[] }>('GET', '/cost/budget-alerts');
    return response.alerts || [];
  }

  /**
   * Update a budget alert
   */
  async updateBudgetAlert(alertId: string, updates: Partial<BudgetAlert>): Promise<BudgetAlert> {
    return this.request<BudgetAlert>('PUT', `/cost/budget-alerts/${alertId}`, undefined, updates);
  }

  /**
   * Delete a budget alert
   */
  async deleteBudgetAlert(alertId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/cost/budget-alerts/${alertId}`);
  }

  /**
   * Set custom pricing for a provider/model
   */
  async setCustomPricing(config: {
    provider: string;
    model: string;
    promptPer1M: number;
    completionPer1M: number;
  }): Promise<{ message: string }> {
    return this.request('POST', '/cost/custom-pricing', undefined, {
      provider: config.provider,
      model: config.model,
      prompt_per_1m: config.promptPer1M,
      completion_per_1m: config.completionPer1M
    });
  }

  // ============================================================================
  // Audit & Notifications
  // ============================================================================

  /**
   * Get audit logs
   */
  async getAuditLogs(options?: {
    agentId?: string;
    actionType?: string;
    limit?: number;
  }): Promise<AuditLog[]> {
    const params: Record<string, any> = {
      limit: options?.limit || 100
    };
    if (options?.agentId) params.agent_id = options.agentId;
    if (options?.actionType) params.action_type = options.actionType;
    
    const response = await this.request<{ logs: AuditLog[] }>('GET', '/audit/logs', params);
    return response.logs || [];
  }

  /**
   * Get a specific audit log
   */
  async getAuditLog(logId: number): Promise<AuditLog> {
    return this.request<AuditLog>('GET', `/audit/logs/${logId}`);
  }

  /**
   * Get audit statistics
   */
  async getAuditStatistics(): Promise<any> {
    return this.request('GET', '/audit/statistics');
  }

  /**
   * Get notifications
   */
  async getNotifications(options?: {
    unreadOnly?: boolean;
    limit?: number;
  }): Promise<Notification[]> {
    const params: Record<string, any> = {
      limit: options?.limit || 100
    };
    if (options?.unreadOnly) params.unread_only = 'true';
    
    const response = await this.request<{ notifications: Notification[] }>('GET', '/notifications', params);
    return response.notifications || [];
  }

  /**
   * Mark a notification as read
   */
  async markNotificationRead(notificationId: number): Promise<{ message: string }> {
    return this.request('PUT', `/notifications/${notificationId}/read`);
  }

  /**
   * Mark all notifications as read
   */
  async markAllNotificationsRead(): Promise<{ message: string }> {
    return this.request('PUT', '/notifications/read-all');
  }

  /**
   * Get notification statistics
   */
  async getNotificationStats(): Promise<any> {
    return this.request('GET', '/notifications/stats');
  }

  // ============================================================================
  // Admin: Database Management
  // ============================================================================

  /**
   * List all databases (admin)
   */
  async listDatabases(): Promise<any[]> {
    const response = await this.request<{ databases: any[] }>('GET', '/admin/databases');
    return response.databases || [];
  }

  /**
   * Test database connection (admin)
   */
  async testAdminDatabaseConnection(database: DatabaseConfig): Promise<any> {
    return this.request('POST', '/admin/databases/test', undefined, database);
  }

  /**
   * Get all database connections (admin)
   */
  async getDatabaseConnections(): Promise<any[]> {
    const response = await this.request<{ connections: any[] }>('GET', '/admin/databases/connections');
    return response.connections || [];
  }

  /**
   * Rotate database credentials for an agent
   */
  async rotateDatabaseCredentials(agentId: string, newCredentials: DatabaseConfig): Promise<any> {
    return this.request('POST', `/admin/agents/${agentId}/database/rotate`, undefined, newCredentials);
  }

  /**
   * Activate rotated database credentials
   */
  async activateDatabaseCredentials(agentId: string): Promise<any> {
    return this.request('POST', `/admin/agents/${agentId}/database/activate`);
  }

  /**
   * Rollback database credentials to previous version
   */
  async rollbackDatabaseCredentials(agentId: string): Promise<any> {
    return this.request('POST', `/admin/agents/${agentId}/database/rollback`);
  }

  /**
   * Get database credential rotation status
   */
  async getDatabaseRotationStatus(agentId: string): Promise<any> {
    return this.request('GET', `/admin/agents/${agentId}/database/rotation-status`);
  }

  // ============================================================================
  // Admin: AI Agent Version Control
  // ============================================================================

  /**
   * List configuration versions for an AI agent
   */
  async listAIAgentVersions(agentId: string, limit?: number): Promise<any[]> {
    const params: Record<string, any> = {};
    if (limit) params.limit = limit;
    
    const response = await this.request<{ versions: any[] }>('GET', `/admin/ai-agents/${agentId}/versions`, params);
    return response.versions || [];
  }

  /**
   * Get a specific version of AI agent configuration
   */
  async getAIAgentVersion(agentId: string, version: number): Promise<any> {
    return this.request('GET', `/admin/ai-agents/${agentId}/versions/${version}`);
  }

  /**
   * Rollback AI agent configuration to a previous version
   */
  async rollbackAIAgentConfig(agentId: string, version: number, description?: string): Promise<any> {
    return this.request('POST', `/admin/ai-agents/${agentId}/rollback`, undefined, {
      version,
      description
    });
  }

  // ============================================================================
  // Admin: Webhooks
  // ============================================================================

  /**
   * Register a webhook for an AI agent
   */
  async registerWebhook(config: {
    agentId: string;
    url: string;
    events: string[];
    secret?: string;
  }): Promise<Webhook> {
    return this.request<Webhook>('POST', `/admin/ai-agents/${config.agentId}/webhooks`, undefined, {
      url: config.url,
      events: config.events,
      secret: config.secret
    });
  }

  /**
   * List webhooks for an AI agent
   */
  async listWebhooks(agentId: string): Promise<Webhook[]> {
    const response = await this.request<{ webhooks: Webhook[] }>('GET', `/admin/ai-agents/${agentId}/webhooks`);
    return response.webhooks || [];
  }

  /**
   * Delete a webhook
   */
  async deleteWebhook(agentId: string, webhookUrl: string): Promise<{ message: string }> {
    return this.request('DELETE', `/admin/ai-agents/${agentId}/webhooks`, { url: webhookUrl });
  }

  /**
   * Get webhook delivery history
   */
  async getWebhookHistory(agentId: string, limit: number = 100): Promise<any[]> {
    const response = await this.request<{ history: any[] }>('GET', `/admin/ai-agents/${agentId}/webhooks/history`, { limit });
    return response.history || [];
  }

  // ============================================================================
  // Admin: Row-Level Security (RLS)
  // ============================================================================

  /**
   * Create a row-level security rule
   */
  async createRLSRule(rule: {
    agentId: string;
    tableName: string;
    ruleType: string;
    condition: string;
    description?: string;
  }): Promise<RLSRule> {
    return this.request<RLSRule>('POST', '/admin/rls/rules', undefined, {
      agent_id: rule.agentId,
      table_name: rule.tableName,
      rule_type: rule.ruleType,
      condition: rule.condition,
      description: rule.description
    });
  }

  /**
   * List RLS rules
   */
  async listRLSRules(agentId?: string): Promise<RLSRule[]> {
    const params: Record<string, any> = {};
    if (agentId) params.agent_id = agentId;
    
    const response = await this.request<{ rules: RLSRule[] }>('GET', '/admin/rls/rules', params);
    return response.rules || [];
  }

  /**
   * Delete an RLS rule
   */
  async deleteRLSRule(ruleId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/admin/rls/rules/${ruleId}`);
  }

  // ============================================================================
  // Admin: Column Masking
  // ============================================================================

  /**
   * Create a column masking rule
   */
  async createMaskingRule(rule: {
    agentId: string;
    tableName: string;
    columnName: string;
    maskingType: string;
    config?: Record<string, any>;
  }): Promise<MaskingRule> {
    return this.request<MaskingRule>('POST', '/admin/masking/rules', undefined, {
      agent_id: rule.agentId,
      table_name: rule.tableName,
      column_name: rule.columnName,
      masking_type: rule.maskingType,
      ...rule.config
    });
  }

  /**
   * List masking rules
   */
  async listMaskingRules(agentId?: string): Promise<MaskingRule[]> {
    const params: Record<string, any> = {};
    if (agentId) params.agent_id = agentId;
    
    const response = await this.request<{ rules: MaskingRule[] }>('GET', '/admin/masking/rules', params);
    return response.rules || [];
  }

  /**
   * Delete a masking rule
   */
  async deleteMaskingRule(ruleId: string): Promise<{ message: string }> {
    return this.request('DELETE', '/admin/masking/rules', { rule_id: ruleId });
  }

  // ============================================================================
  // Admin: Query Management
  // ============================================================================

  /**
   * Set query execution limits for an agent
   */
  async setQueryLimits(agentId: string, limits: {
    maxRows?: number;
    maxExecutionTime?: number;
    maxQuerySize?: number;
  }): Promise<any> {
    return this.request('POST', `/admin/agents/${agentId}/query-limits`, undefined, {
      max_rows: limits.maxRows,
      max_execution_time: limits.maxExecutionTime,
      max_query_size: limits.maxQuerySize
    });
  }

  /**
   * Get query execution limits for an agent
   */
  async getQueryLimits(agentId: string): Promise<any> {
    return this.request('GET', `/admin/agents/${agentId}/query-limits`);
  }

  /**
   * Validate a query before execution
   */
  async validateQuery(agentId: string, query: string): Promise<any> {
    return this.request('POST', `/admin/agents/${agentId}/validate-query`, undefined, { query });
  }

  /**
   * List pending query approvals
   */
  async listQueryApprovals(options?: {
    status?: string;
    limit?: number;
  }): Promise<any[]> {
    const params: Record<string, any> = {
      limit: options?.limit || 100
    };
    if (options?.status) params.status = options.status;
    
    const response = await this.request<{ approvals: any[] }>('GET', '/admin/query-approvals', params);
    return response.approvals || [];
  }

  /**
   * Approve a pending query
   */
  async approveQuery(approvalId: string): Promise<any> {
    return this.request('POST', `/admin/query-approvals/${approvalId}/approve`);
  }

  /**
   * Reject a pending query
   */
  async rejectQuery(approvalId: string, reason?: string): Promise<any> {
    return this.request('POST', `/admin/query-approvals/${approvalId}/reject`, undefined, { reason });
  }

  /**
   * Get a specific query approval
   */
  async getQueryApproval(approvalId: string): Promise<any> {
    return this.request('GET', `/admin/query-approvals/${approvalId}`);
  }

  // ============================================================================
  // Admin: Approved Patterns
  // ============================================================================

  /**
   * Create an approved query pattern
   */
  async createApprovedPattern(pattern: {
    name: string;
    sqlTemplate: string;
    naturalLanguageKeywords: string[];
    description?: string;
    [key: string]: any;
  }): Promise<any> {
    return this.request('POST', '/admin/query-patterns', undefined, {
      name: pattern.name,
      sql_template: pattern.sqlTemplate,
      natural_language_keywords: pattern.naturalLanguageKeywords,
      description: pattern.description,
      ...pattern
    });
  }

  /**
   * List all approved query patterns
   */
  async listApprovedPatterns(): Promise<any[]> {
    const response = await this.request<{ patterns: any[] }>('GET', '/admin/query-patterns');
    return response.patterns || [];
  }

  /**
   * Get a specific approved pattern
   */
  async getApprovedPattern(patternId: string): Promise<any> {
    return this.request('GET', `/admin/query-patterns/${patternId}`);
  }

  /**
   * Update an approved pattern
   */
  async updateApprovedPattern(patternId: string, updates: Record<string, any>): Promise<any> {
    return this.request('PUT', `/admin/query-patterns/${patternId}`, undefined, updates);
  }

  /**
   * Delete an approved pattern
   */
  async deleteApprovedPattern(patternId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/admin/query-patterns/${patternId}`);
  }

  // ============================================================================
  // Admin: Query Cache
  // ============================================================================

  /**
   * Set cache TTL for an agent
   */
  async setCacheTTL(agentId: string, ttlSeconds: number): Promise<any> {
    return this.request('POST', `/admin/agents/${agentId}/cache/ttl`, undefined, { ttl_seconds: ttlSeconds });
  }

  /**
   * Get cache TTL for an agent
   */
  async getCacheTTL(agentId: string): Promise<any> {
    return this.request('GET', `/admin/agents/${agentId}/cache/ttl`);
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<CacheStats> {
    return this.request<CacheStats>('GET', '/admin/cache/stats');
  }

  /**
   * Invalidate cache entries
   */
  async invalidateCache(options?: {
    agentId?: string;
    pattern?: string;
  }): Promise<any> {
    return this.request('POST', '/admin/cache/invalidate', undefined, {
      agent_id: options?.agentId,
      pattern: options?.pattern
    });
  }

  /**
   * Clear expired cache entries
   */
  async clearExpiredCache(): Promise<any> {
    return this.request('POST', '/admin/cache/clear-expired');
  }

  /**
   * List cache entries
   */
  async listCacheEntries(options?: {
    agentId?: string;
    limit?: number;
  }): Promise<any[]> {
    const params: Record<string, any> = {
      limit: options?.limit || 100
    };
    if (options?.agentId) params.agent_id = options.agentId;
    
    const response = await this.request<{ entries: any[] }>('GET', '/admin/cache/entries', params);
    return response.entries || [];
  }

  // ============================================================================
  // Admin: Audit Export
  // ============================================================================

  /**
   * Export audit logs
   */
  async exportAuditLogs(options?: {
    format?: 'json' | 'csv';
    agentId?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<any> {
    const params: Record<string, any> = {
      format: options?.format || 'json'
    };
    if (options?.agentId) params.agent_id = options.agentId;
    if (options?.startDate) params.start_date = options.startDate;
    if (options?.endDate) params.end_date = options.endDate;
    
    return this.request('GET', '/admin/audit/export', params);
  }

  /**
   * Get audit export summary
   */
  async getAuditExportSummary(options?: {
    agentId?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<any> {
    const params: Record<string, any> = {};
    if (options?.agentId) params.agent_id = options.agentId;
    if (options?.startDate) params.start_date = options.startDate;
    if (options?.endDate) params.end_date = options.endDate;
    
    return this.request('GET', '/admin/audit/export/summary', params);
  }

  // ============================================================================
  // Admin: Alerts
  // ============================================================================

  /**
   * Create an alert rule
   */
  async createAlertRule(rule: {
    name: string;
    condition: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    [key: string]: any;
  }): Promise<AlertRule> {
    return this.request<AlertRule>('POST', '/admin/alerts/rules', undefined, rule);
  }

  /**
   * List alert rules
   */
  async listAlertRules(): Promise<AlertRule[]> {
    const response = await this.request<{ rules: AlertRule[] }>('GET', '/admin/alerts/rules');
    return response.rules || [];
  }

  /**
   * Get a specific alert rule
   */
  async getAlertRule(ruleId: string): Promise<AlertRule> {
    return this.request<AlertRule>('GET', `/admin/alerts/rules/${ruleId}`);
  }

  /**
   * Update an alert rule
   */
  async updateAlertRule(ruleId: string, updates: Partial<AlertRule>): Promise<AlertRule> {
    return this.request<AlertRule>('PUT', `/admin/alerts/rules/${ruleId}`, undefined, updates);
  }

  /**
   * Delete an alert rule
   */
  async deleteAlertRule(ruleId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/admin/alerts/rules/${ruleId}`);
  }

  /**
   * List alerts
   */
  async listAlerts(options?: {
    severity?: string;
    acknowledged?: boolean;
    limit?: number;
  }): Promise<any[]> {
    const params: Record<string, any> = {
      limit: options?.limit || 100
    };
    if (options?.severity) params.severity = options.severity;
    if (options?.acknowledged !== undefined) params.acknowledged = options.acknowledged ? 'true' : 'false';
    
    const response = await this.request<{ alerts: any[] }>('GET', '/admin/alerts', params);
    return response.alerts || [];
  }

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(alertId: string): Promise<any> {
    return this.request('POST', `/admin/alerts/${alertId}/acknowledge`);
  }

  // ============================================================================
  // Admin: Query Tracing
  // ============================================================================

  /**
   * List query traces
   */
  async listQueryTraces(options?: {
    agentId?: string;
    limit?: number;
  }): Promise<QueryTrace[]> {
    const params: Record<string, any> = {
      limit: options?.limit || 100
    };
    if (options?.agentId) params.agent_id = options.agentId;
    
    const response = await this.request<{ traces: QueryTrace[] }>('GET', '/admin/traces', params);
    return response.traces || [];
  }

  /**
   * Get a specific query trace
   */
  async getQueryTrace(traceId: string): Promise<QueryTrace> {
    return this.request<QueryTrace>('GET', `/admin/traces/${traceId}`);
  }

  /**
   * Get observability configuration
   */
  async getObservabilityConfig(): Promise<any> {
    return this.request('GET', '/admin/observability/config');
  }

  // ============================================================================
  // Admin: Teams
  // ============================================================================

  /**
   * Create a team
   */
  async createTeam(team: {
    name: string;
    description?: string;
  }): Promise<Team> {
    return this.request<Team>('POST', '/admin/teams', undefined, team);
  }

  /**
   * List all teams
   */
  async listTeams(): Promise<Team[]> {
    const response = await this.request<{ teams: Team[] }>('GET', '/admin/teams');
    return response.teams || [];
  }

  /**
   * Get team information
   */
  async getTeam(teamId: string): Promise<Team> {
    return this.request<Team>('GET', `/admin/teams/${teamId}`);
  }

  /**
   * Update a team
   */
  async updateTeam(teamId: string, updates: Partial<Team>): Promise<Team> {
    return this.request<Team>('PUT', `/admin/teams/${teamId}`, undefined, updates);
  }

  /**
   * Delete a team
   */
  async deleteTeam(teamId: string): Promise<{ message: string }> {
    return this.request('DELETE', `/admin/teams/${teamId}`);
  }

  /**
   * Add a member to a team
   */
  async addTeamMember(teamId: string, userId: string, role: string): Promise<any> {
    return this.request('POST', `/admin/teams/${teamId}/members`, undefined, { user_id: userId, role });
  }

  /**
   * Remove a member from a team
   */
  async removeTeamMember(teamId: string, userId: string): Promise<any> {
    return this.request('DELETE', `/admin/teams/${teamId}/members/${userId}`);
  }

  /**
   * Update a team member's role
   */
  async updateTeamMemberRole(teamId: string, userId: string, role: string): Promise<any> {
    return this.request('PUT', `/admin/teams/${teamId}/members/${userId}/role`, undefined, { role });
  }

  /**
   * Assign an agent to a team
   */
  async assignAgentToTeam(teamId: string, agentId: string): Promise<any> {
    return this.request('POST', `/admin/teams/${teamId}/agents/${agentId}`);
  }

  // ============================================================================
  // Query Sharing
  // ============================================================================

  /**
   * Share a query with a shareable link
   */
  async shareQuery(config: {
    agentId: string;
    query: string;
    expiresAt?: string;
    accessLevel?: 'read' | 'write';
  }): Promise<SharedQuery> {
    return this.request<SharedQuery>('POST', `/agents/${config.agentId}/queries/share`, undefined, {
      query: config.query,
      expires_at: config.expiresAt,
      access_level: config.accessLevel || 'read'
    });
  }

  /**
   * Get a shared query by share ID
   */
  async getSharedQuery(shareId: string): Promise<SharedQuery> {
    return this.request<SharedQuery>('GET', `/shared/${shareId}`);
  }

  /**
   * List shared queries for an agent
   */
  async listSharedQueries(agentId: string, limit: number = 100): Promise<SharedQuery[]> {
    const response = await this.request<{ shares: SharedQuery[] }>('GET', `/agents/${agentId}/queries/shares`, { limit });
    return response.shares || [];
  }

  // ============================================================================
  // Admin: Dashboard
  // ============================================================================

  /**
   * Get dashboard metrics (admin)
   */
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    return this.request<DashboardMetrics>('GET', '/admin/dashboard/metrics');
  }
}

