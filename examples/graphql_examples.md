# GraphQL API Usage Examples

## Overview

Examples of using the GraphQL API for Universal Agent Connector.

## Accessing the Playground

Navigate to: `http://localhost:5000/graphql/playground`

## Query Examples

### Get Agent Information

```graphql
query {
  agent(agentId: "my-agent") {
    agentId
    status
    databaseType
    databaseName
    permissionsCount
    lastQueryAt
  }
}
```

### List All Agents

```graphql
query {
  agents(limit: 10, offset: 0) {
    agentId
    status
    databaseType
  }
}
```

### Get Cost Dashboard

```graphql
query {
  costDashboard(periodDays: 30, agentId: "my-agent") {
    totalCost
    totalCalls
    costByProvider
    costByOperation
    dailyCosts
  }
}
```

### Get Cost Records

```graphql
query {
  costRecords(agentId: "my-agent", limit: 50) {
    callId
    timestamp
    provider
    model
    costUsd
    totalTokens
    operationType
  }
}
```

### Get Failover Statistics

```graphql
query {
  failoverStats(agentId: "my-agent") {
    agentId
    activeProvider
    totalSwitches
    providerHealth
    consecutiveFailures
  }
}
```

### Get Audit Logs

```graphql
query {
  auditLogs(agentId: "my-agent", limit: 20) {
    logId
    agentId
    actionType
    timestamp
    details
  }
}
```

### Execute SQL Query

```graphql
query {
  executeQuery(input: {
    agentId: "my-agent"
    query: "SELECT * FROM users LIMIT 10"
    fetch: true
  }) {
    data
    rows
    columns
    executionTimeMs
    sql
  }
}
```

### Execute Natural Language Query

```graphql
query {
  executeNaturalLanguageQuery(input: {
    agentId: "my-agent"
    query: "Show me the top 10 customers by revenue"
    previewOnly: false
    useCache: true
  }) {
    data
    rows
    sql
    confidence
  }
}
```

## Mutation Examples

### Register Agent

```graphql
mutation {
  registerAgent(input: {
    agentId: "new-agent"
    agentCredentials: {
      "api_key": "agent-key"
      "api_secret": "agent-secret"
    }
    database: {
      "host": "localhost"
      "port": 5432
      "user": "postgres"
      "password": "postgres"
      "database": "mydb"
    }
    agentInfo: {
      "name": "My Agent"
      "description": "Test agent"
    }
  }) {
    success
    message
    agent {
      agentId
      status
    }
  }
}
```

### Configure Failover

```graphql
mutation {
  configureFailover(input: {
    agentId: "my-agent"
    primaryProviderId: "openai-agent"
    backupProviderIds: ["claude-agent"]
    healthCheckEnabled: true
    autoFailoverEnabled: true
    healthCheckInterval: 60
    consecutiveFailuresThreshold: 3
  }) {
    success
    message
    config
  }
}
```

### Create Budget Alert

```graphql
mutation {
  createBudgetAlert(input: {
    name: "Monthly Budget Alert"
    thresholdUsd: 1000.0
    period: "monthly"
    notificationEmails: ["admin@example.com"]
    webhookUrl: "https://example.com/webhook"
  }) {
    success
    message
    alert {
      alertId
      name
      thresholdUsd
      period
    }
  }
}
```

## Subscription Examples

### Subscribe to Cost Updates

```graphql
subscription {
  costUpdated(agentId: "my-agent") {
    callId
    agentId
    provider
    costUsd
    timestamp
  }
}
```

### Subscribe to Failover Switches

```graphql
subscription {
  failoverSwitched(agentId: "my-agent") {
    agentId
    activeProvider
    totalSwitches
    timestamp
  }
}
```

### Subscribe to Audit Logs

```graphql
subscription {
  auditLogCreated(agentId: "my-agent") {
    logId
    agentId
    actionType
    timestamp
    details
  }
}
```

### Subscribe to Notifications

```graphql
subscription {
  notificationCreated {
    notificationId
    type
    message
    read
    createdAt
    severity
  }
}
```

## Complex Queries

### Get Agent with Costs and Failover Stats

```graphql
query {
  agent(agentId: "my-agent") {
    agentId
    status
    permissionsCount
  }
  
  costDashboard(agentId: "my-agent", periodDays: 7) {
    totalCost
    totalCalls
    costByProvider
  }
  
  failoverStats(agentId: "my-agent") {
    activeProvider
    totalSwitches
    providerHealth
  }
}
```

### Get Multiple Agents with Costs

```graphql
query {
  agents(limit: 5) {
    agentId
    status
  }
  
  costDashboard(periodDays: 30) {
    totalCost
    costByAgent
    dailyCosts
  }
}
```

## Using Variables

```graphql
query GetAgent($agentId: ID!, $periodDays: Int) {
  agent(agentId: $agentId) {
    agentId
    status
  }
  
  costDashboard(agentId: $agentId, periodDays: $periodDays) {
    totalCost
    totalCalls
  }
}
```

Variables:
```json
{
  "agentId": "my-agent",
  "periodDays": 30
}
```

## Error Handling

GraphQL returns errors in the response:

```json
{
  "data": null,
  "errors": [
    {
      "message": "Agent not found",
      "locations": [{"line": 2, "column": 3}],
      "path": ["agent"]
    }
  ]
}
```

## Schema Introspection

Query the schema itself:

```graphql
query {
  __schema {
    queryType {
      name
      fields {
        name
        type {
          name
        }
      }
    }
  }
}
```

## Best Practices

1. **Fetch Only What You Need** - GraphQL allows you to request only the fields you need
2. **Use Variables** - Use variables for dynamic values
3. **Handle Errors** - Always check for errors in the response
4. **Use Subscriptions** - Use subscriptions for real-time updates instead of polling
5. **Batch Queries** - Combine multiple queries in a single request
