/**
 * Basic usage examples for Universal Agent Connector SDK
 */

import { UniversalAgentConnector } from '../src';

// Initialize client
const client = new UniversalAgentConnector({
  baseUrl: 'http://localhost:5000'
});

async function exampleRegisterAgent() {
  /** Example: Register a new agent */
  const agent = await client.registerAgent({
    agent_id: 'example-agent',
    agent_credentials: {
      api_key: 'example-key',
      api_secret: 'example-secret'
    },
    database: {
      host: 'localhost',
      port: 5432,
      user: 'postgres',
      password: 'postgres',
      database: 'example_db'
    },
    agent_info: {
      name: 'Example Agent',
      description: 'Example agent for testing'
    }
  });
  
  console.log(`Agent registered: ${agent.agent_id}`);
  console.log(`API Key: ${agent.api_key}`);
  return agent;
}

async function exampleExecuteQuery() {
  /** Example: Execute a SQL query */
  const result = await client.executeQuery(
    'example-agent',
    'SELECT COUNT(*) as total FROM users'
  );
  console.log('Query result:', result.data);
  return result;
}

async function exampleNaturalLanguageQuery() {
  /** Example: Execute a natural language query */
  const result = await client.executeNaturalLanguageQuery(
    'example-agent',
    'Show me the top 10 customers by revenue'
  );
  console.log(`Generated SQL: ${result.sql}`);
  console.log('Results:', result.data);
  return result;
}

async function exampleAIAgent() {
  /** Example: Register and use an AI agent */
  // Register OpenAI agent
  const aiAgent = await client.registerAIAgent({
    agent_id: 'gpt-agent',
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key: 'sk-your-key-here'
  });
  console.log(`AI Agent registered: ${aiAgent.agent_id}`);
  
  // Execute query
  const response = await client.executeAIQuery(
    'gpt-agent',
    'Explain machine learning in simple terms'
  );
  console.log('Response:', response.response);
  return response;
}

async function exampleCostTracking() {
  /** Example: Track costs */
  // Get cost dashboard
  const dashboard = await client.getCostDashboard({ periodDays: 30 });
  console.log(`Total cost: $${dashboard.total_cost.toFixed(4)}`);
  console.log(`Total calls: ${dashboard.total_calls}`);
  console.log('Cost by provider:', dashboard.cost_by_provider);
  
  // Create budget alert
  const alert = await client.createBudgetAlert({
    name: 'Monthly Budget Alert',
    thresholdUsd: 1000.0,
    period: 'monthly',
    notificationEmails: ['admin@example.com']
  });
  console.log(`Budget alert created: ${alert.alert_id}`);
  return dashboard;
}

async function exampleProviderFailover() {
  /** Example: Configure provider failover */
  // Register multiple AI agents
  await client.registerAIAgent({
    agent_id: 'openai-agent',
    provider: 'openai',
    model: 'gpt-4o-mini',
    api_key: 'sk-openai-key'
  });
  
  await client.registerAIAgent({
    agent_id: 'claude-agent',
    provider: 'anthropic',
    model: 'claude-3-haiku-20240307',
    api_key: 'sk-ant-claude-key'
  });
  
  // Configure failover
  const config = await client.configureFailover({
    agent_id: 'my-agent',
    primary_provider_id: 'openai-agent',
    backup_provider_ids: ['claude-agent'],
    health_check_enabled: true,
    auto_failover_enabled: true
  });
  console.log(`Failover configured: ${config.agent_id}`);
  
  // Get failover stats
  const stats = await client.getFailoverStats('my-agent');
  console.log(`Active provider: ${stats.active_provider}`);
  return stats;
}

// Run examples
async function main() {
  console.log('Universal Agent Connector SDK Examples');
  console.log('='.repeat(50));
  
  // Uncomment to run examples:
  // await exampleRegisterAgent();
  // await exampleExecuteQuery();
  // await exampleNaturalLanguageQuery();
  // await exampleAIAgent();
  // await exampleCostTracking();
  // await exampleProviderFailover();
}

if (require.main === module) {
  main().catch(console.error);
}

export {
  exampleRegisterAgent,
  exampleExecuteQuery,
  exampleNaturalLanguageQuery,
  exampleAIAgent,
  exampleCostTracking,
  exampleProviderFailover
};

