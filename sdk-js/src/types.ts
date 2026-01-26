/**
 * TypeScript type definitions for Universal Agent Connector SDK
 */

export interface ClientConfig {
  baseUrl?: string;
  apiKey?: string;
  timeout?: number;
}

export interface AgentCredentials {
  api_key: string;
  api_secret: string;
}

export interface DatabaseConfig {
  host?: string;
  port?: number;
  user?: string;
  password?: string;
  database?: string;
  connection_string?: string;
  connection_name?: string;
  type?: string;
  pooling?: Record<string, any>;
  timeouts?: Record<string, any>;
}

export interface AgentInfo {
  name?: string;
  description?: string;
  [key: string]: any;
}

export interface RegisterAgentRequest {
  agent_id: string;
  agent_credentials: AgentCredentials;
  database: DatabaseConfig;
  agent_info?: AgentInfo;
}

export interface Agent {
  agent_id: string;
  status?: string;
  api_key?: string;
  [key: string]: any;
}

export interface QueryResult {
  data: any[];
  rows?: number;
  columns?: string[];
  [key: string]: any;
}

export interface NaturalLanguageQueryResult extends QueryResult {
  sql?: string;
  confidence?: number;
}

export interface QuerySuggestion {
  sql: string;
  confidence: number;
  explanation?: string;
}

export interface AIAgentConfig {
  agent_id: string;
  provider: 'openai' | 'anthropic' | 'custom';
  model: string;
  api_key?: string;
  api_base?: string;
  temperature?: number;
  max_tokens?: number;
  timeout?: number;
  rate_limit?: RateLimitConfig;
  retry_policy?: RetryPolicyConfig;
}

export interface RateLimitConfig {
  queries_per_minute?: number;
  queries_per_hour?: number;
  queries_per_day?: number;
}

export interface RetryPolicyConfig {
  enabled?: boolean;
  max_retries?: number;
  strategy?: 'fixed' | 'exponential' | 'linear';
  initial_delay?: number;
  max_delay?: number;
}

export interface FailoverConfig {
  agent_id: string;
  primary_provider_id: string;
  backup_provider_ids: string[];
  health_check_enabled?: boolean;
  auto_failover_enabled?: boolean;
  health_check_interval?: number;
  consecutive_failures_threshold?: number;
}

export interface FailoverStats {
  active_provider: string;
  total_switches: number;
  provider_health: Record<string, ProviderHealth>;
}

export interface ProviderHealth {
  status: 'healthy' | 'unhealthy' | 'unknown';
  last_check?: string;
  response_time?: number;
  consecutive_failures?: number;
}

export interface CostDashboard {
  total_cost: number;
  total_calls: number;
  cost_by_provider: Record<string, number>;
  cost_by_operation: Record<string, number>;
  cost_by_agent: Record<string, number>;
  daily_costs: Array<{ date: string; cost: number }>;
}

export interface BudgetAlert {
  alert_id: string;
  name: string;
  threshold_usd: number;
  period: 'daily' | 'weekly' | 'monthly';
  notification_emails?: string[];
  webhook_url?: string;
  triggered?: boolean;
}

export interface QueryTemplate {
  template_id: string;
  name: string;
  sql: string;
  tags?: string[];
  is_public?: boolean;
  created_at?: string;
}

export interface Permission {
  resource_type: string;
  resource_id: string;
  permissions: string[];
}

export interface AuditLog {
  log_id: number;
  agent_id?: string;
  action_type: string;
  timestamp: string;
  details?: Record<string, any>;
}

export interface Notification {
  notification_id: number;
  type: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface RLSRule {
  rule_id: string;
  agent_id: string;
  table_name: string;
  rule_type: string;
  condition: string;
  description?: string;
}

export interface MaskingRule {
  rule_id: string;
  agent_id: string;
  table_name: string;
  column_name: string;
  masking_type: string;
  config?: Record<string, any>;
}

export interface AlertRule {
  rule_id: string;
  name: string;
  condition: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  enabled?: boolean;
}

export interface Team {
  team_id: string;
  name: string;
  description?: string;
  members?: TeamMember[];
}

export interface TeamMember {
  user_id: string;
  role: string;
}

export interface SharedQuery {
  share_id: string;
  agent_id: string;
  query: string;
  access_level: 'read' | 'write';
  expires_at?: string;
  created_at: string;
}

export interface Webhook {
  webhook_id: string;
  url: string;
  events: string[];
  secret?: string;
  active?: boolean;
}

export interface QueryTrace {
  trace_id: string;
  agent_id: string;
  query: string;
  stages: TraceStage[];
  duration_ms: number;
}

export interface TraceStage {
  stage: string;
  duration_ms: number;
  details?: Record<string, any>;
}

export interface CacheStats {
  total_entries: number;
  hit_rate: number;
  memory_usage_mb: number;
}

export interface DashboardMetrics {
  total_agents: number;
  total_queries: number;
  total_cost: number;
  active_alerts: number;
}

