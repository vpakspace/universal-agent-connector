# Universal Agent Connector JavaScript/TypeScript SDK

Official JavaScript/TypeScript SDK for the Universal Agent Connector API. Easily integrate AI agent management, database connections, and query execution into your Node.js, browser, or TypeScript applications.

## Features

- ✅ **Full TypeScript Support** - Complete type definitions included
- ✅ **Async/Await** - Modern async/await API
- ✅ **Full API Coverage** - All REST API endpoints wrapped
- ✅ **Error Handling** - Comprehensive exception handling
- ✅ **Tree-shakeable** - ES modules support
- ✅ **Zero Dependencies** - Uses native fetch API

## Installation

```bash
npm install universal-agent-connector
```

or

```bash
yarn add universal-agent-connector
```

or

```bash
pnpm add universal-agent-connector
```

## Quick Start

```typescript
import { UniversalAgentConnector } from 'universal-agent-connector';

// Initialize the client
const client = new UniversalAgentConnector({
  baseUrl: 'http://localhost:5000',
  apiKey: 'your-api-key' // Optional
});

// Register an agent
const agent = await client.registerAgent({
  agent_id: 'my-agent',
  agent_credentials: {
    api_key: 'agent-key',
    api_secret: 'agent-secret'
  },
  database: {
    host: 'localhost',
    port: 5432,
    user: 'dbuser',
    password: 'dbpass',
    database: 'mydb'
  }
});

console.log(`Agent registered with API key: ${agent.api_key}`);
```

## Usage Examples

### Agent Management

```typescript
import { UniversalAgentConnector } from 'universal-agent-connector';

const client = new UniversalAgentConnector({
  baseUrl: 'http://localhost:5000'
});

// Register an agent
const agent = await client.registerAgent({
  agent_id: 'analytics-agent',
  agent_credentials: { api_key: 'key', api_secret: 'secret' },
  database: {
    host: 'db.example.com',
    database: 'analytics',
    user: 'analytics_user',
    password: 'secure_password'
  }
});

// Get agent information
const agentInfo = await client.getAgent('analytics-agent');

// List all agents
const agents = await client.listAgents();
```

### Query Execution

```typescript
// Execute SQL query
const result = await client.executeQuery(
  'analytics-agent',
  'SELECT * FROM users LIMIT 10'
);
console.log(result.data);

// Natural language query
const nlResult = await client.executeNaturalLanguageQuery(
  'analytics-agent',
  'Show me the top 10 customers by revenue'
);
console.log(nlResult.data);
console.log(`Generated SQL: ${nlResult.sql}`);

// Get query suggestions
const suggestions = await client.getQuerySuggestions(
  'analytics-agent',
  'show me sales',
  3
);
suggestions.forEach(suggestion => {
  console.log(`SQL: ${suggestion.sql}`);
  console.log(`Confidence: ${suggestion.confidence}`);
});
```

### AI Agent Management

```typescript
// Register an AI agent (OpenAI)
const aiAgent = await client.registerAIAgent({
  agent_id: 'gpt-agent',
  provider: 'openai',
  model: 'gpt-4o-mini',
  api_key: 'sk-...'
});

// Execute AI query
const response = await client.executeAIQuery(
  'gpt-agent',
  'What is machine learning?'
);
console.log(response.response);

// Set rate limits
await client.setRateLimit('gpt-agent', {
  queries_per_minute: 60,
  queries_per_hour: 1000
});
```

### Provider Failover

```typescript
// Configure failover
await client.configureFailover({
  agent_id: 'my-agent',
  primary_provider_id: 'openai-agent',
  backup_provider_ids: ['claude-agent'],
  health_check_enabled: true,
  auto_failover_enabled: true
});

// Get failover stats
const stats = await client.getFailoverStats('my-agent');
console.log(`Active provider: ${stats.active_provider}`);
console.log(`Provider health: ${stats.provider_health}`);

// Manually switch provider
await client.switchProvider('my-agent', 'claude-agent');
```

### Cost Tracking

```typescript
// Get cost dashboard
const dashboard = await client.getCostDashboard({ periodDays: 30 });
console.log(`Total cost: $${dashboard.total_cost.toFixed(4)}`);
console.log(`Total calls: ${dashboard.total_calls}`);

// Export cost report
const report = await client.exportCostReport({
  format: 'csv',
  periodDays: 30
});
// Save to file or process...

// Create budget alert
const alert = await client.createBudgetAlert({
  name: 'Monthly Budget',
  thresholdUsd: 1000.0,
  period: 'monthly',
  notificationEmails: ['admin@example.com']
});
```

### Query Templates

```typescript
// Create a template
const template = await client.createQueryTemplate(
  'analytics-agent',
  'Top Customers',
  'SELECT * FROM customers ORDER BY revenue DESC LIMIT {{limit}}',
  { tags: ['customers', 'revenue'] }
);

// Use template
const result = await client.executeNaturalLanguageQuery(
  'analytics-agent',
  'Get top customers',
  {
    useTemplate: template.template_id,
    templateParams: { limit: 10 }
  }
);
```

### Permissions

```typescript
// Set permissions
await client.setPermissions('analytics-agent', [
  {
    resource_type: 'table',
    resource_id: 'users',
    permissions: ['read']
  },
  {
    resource_type: 'table',
    resource_id: 'orders',
    permissions: ['read']
  }
]);

// Get permissions
const permissions = await client.getPermissions('analytics-agent');
```

## Error Handling

The SDK provides comprehensive error handling:

```typescript
import {
  UniversalAgentConnector,
  NotFoundError,
  AuthenticationError,
  APIError
} from 'universal-agent-connector';

const client = new UniversalAgentConnector({
  baseUrl: 'http://localhost:5000'
});

try {
  const agent = await client.getAgent('nonexistent');
} catch (error) {
  if (error instanceof NotFoundError) {
    console.error('Agent not found:', error.message);
  } else if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
  } else if (error instanceof APIError) {
    console.error(`API error (${error.statusCode}):`, error.message);
    console.error('Response:', error.response);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

## TypeScript Support

The SDK is written in TypeScript and includes full type definitions:

```typescript
import {
  UniversalAgentConnector,
  Agent,
  QueryResult,
  CostDashboard
} from 'universal-agent-connector';

const client = new UniversalAgentConnector();

// All methods are fully typed
const agent: Agent = await client.getAgent('my-agent');
const result: QueryResult = await client.executeQuery('my-agent', 'SELECT 1');
const dashboard: CostDashboard = await client.getCostDashboard();
```

## Browser Support

The SDK works in both Node.js and browsers (using native fetch):

```typescript
// Node.js (18+)
import { UniversalAgentConnector } from 'universal-agent-connector';

// Browser
import { UniversalAgentConnector } from 'universal-agent-connector';
// Works with native fetch API
```

For older Node.js versions (< 18), you may need a fetch polyfill:

```bash
npm install node-fetch
```

## Configuration

### Environment Variables

```typescript
import { UniversalAgentConnector } from 'universal-agent-connector';

const client = new UniversalAgentConnector({
  baseUrl: process.env.UAC_BASE_URL || 'http://localhost:5000',
  apiKey: process.env.UAC_API_KEY,
  timeout: 30000 // 30 seconds
});
```

## API Reference

### Client Methods

#### Agents
- `registerAgent()` - Register a new agent
- `getAgent()` - Get agent information
- `listAgents()` - List all agents
- `deleteAgent()` - Delete an agent
- `updateAgentDatabase()` - Update database connection

#### Queries
- `executeQuery()` - Execute SQL query
- `executeNaturalLanguageQuery()` - Execute natural language query
- `getQuerySuggestions()` - Get query suggestions

#### Query Templates
- `createQueryTemplate()` - Create template
- `listQueryTemplates()` - List templates
- `getQueryTemplate()` - Get template
- `updateQueryTemplate()` - Update template
- `deleteQueryTemplate()` - Delete template

#### AI Agents
- `registerAIAgent()` - Register AI agent
- `executeAIQuery()` - Execute AI query
- `setRateLimit()` - Set rate limits
- `setRetryPolicy()` - Set retry policy

#### Provider Failover
- `configureFailover()` - Configure provider failover
- `getFailoverStats()` - Get failover statistics
- `switchProvider()` - Manually switch provider

#### Cost Tracking
- `getCostDashboard()` - Get cost dashboard
- `exportCostReport()` - Export cost report
- `createBudgetAlert()` - Create budget alert

#### Permissions
- `setPermissions()` - Set permissions
- `getPermissions()` - Get permissions
- `revokePermission()` - Revoke permission

#### Admin Features
- Database management
- RLS rules
- Column masking
- Query validation
- Query approvals
- Approved patterns
- Query cache
- Audit export
- Alerts
- Query tracing
- Teams
- Query sharing
- Webhooks

## Requirements

- Node.js >= 16.0.0 (or browser with fetch support)
- TypeScript >= 4.0 (optional, for TypeScript projects)

## License

MIT License

## Support

- Documentation: https://docs.universal-agent-connector.com
- Issues: https://github.com/universal-agent-connector/javascript-sdk/issues
- Email: support@universal-agent-connector.com

