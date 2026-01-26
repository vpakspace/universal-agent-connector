# Multi-Agent Collaboration Guide

Complete guide for using multi-agent collaboration to solve complex queries with multiple specialized agents.

## 🎯 Overview

Multi-agent collaboration allows multiple agents to work together on complex queries, where each agent has a specialized role:

- **Schema Researcher**: Researches database schema and identifies relevant tables/columns
- **SQL Generator**: Generates SQL queries from natural language
- **Query Validator**: Validates SQL queries for safety and correctness
- **Result Analyzer**: Analyzes query results and characteristics

## 🚀 Quick Start

### Create Collaboration Session

```bash
POST /api/agents/collaborate
Headers: X-API-Key: your-api-key
Body: {
  "query": "Find all active users with orders in the last month",
  "agents": [
    {"agent_id": "schema-agent", "role": "schema_researcher"},
    {"agent_id": "sql-agent", "role": "sql_generator"},
    {"agent_id": "validator-agent", "role": "query_validator"}
  ]
}
```

### Execute Collaboration

```bash
POST /api/agents/collaborate/{session_id}/execute
Headers: X-API-Key: your-api-key
```

### View Trace Visualization

```bash
GET /api/agents/collaborate/{session_id}/trace
Headers: X-API-Key: your-api-key
```

Or visit: `/collaboration/trace?session_id={session_id}`

## 🔧 Agent Roles

### Schema Researcher

**Role**: `schema_researcher`

**Responsibilities**:
- Research database schema
- Identify relevant tables and columns
- Provide schema information to other agents

**Input**: Query, database connection
**Output**: Schema information, table/column lists

### SQL Generator

**Role**: `sql_generator`

**Responsibilities**:
- Generate SQL from natural language
- Use schema information from researcher
- Create optimized queries

**Input**: Query, schema information
**Output**: Generated SQL query

### Query Validator

**Role**: `query_validator`

**Responsibilities**:
- Validate SQL syntax
- Check for safety issues (e.g., DELETE without WHERE)
- Verify query correctness

**Input**: SQL query
**Output**: Validation results, validated SQL

### Result Analyzer

**Role**: `result_analyzer`

**Responsibilities**:
- Analyze query characteristics
- Estimate complexity
- Provide insights

**Input**: SQL query
**Output**: Analysis results

## 🔄 Collaboration Workflow

### Default Workflow

1. **Schema Researcher** → Researches schema
2. **SQL Generator** → Generates SQL using schema info
3. **Query Validator** → Validates generated SQL
4. **Result Analyzer** → Analyzes final query

### Custom Workflow

You can specify a custom workflow:

```json
{
  "workflow": ["agent-1", "agent-3", "agent-2"]
}
```

## 📡 Communication Protocol

### Message Types

- **request**: Request information or action
- **response**: Respond to a request
- **error**: Error notification
- **status**: Status update
- **data**: Data sharing

### Sending Messages

```bash
POST /api/agents/collaborate/{session_id}/message
Headers: X-API-Key: your-api-key
Body: {
  "from_agent": "schema-agent",
  "to_agent": "sql-agent",
  "message_type": "data",
  "content": {
    "schema_info": {...}
  }
}
```

### Shared State

Agents share state through the collaboration session. Each agent's output is added to the shared state and available to subsequent agents.

## 📊 Trace Visualization

### Viewing Traces

Access trace visualization via:

1. **API**: `GET /api/agents/collaborate/{session_id}/trace`
2. **Web UI**: `/collaboration/trace?session_id={session_id}`

### Trace Data Includes

- **Timeline**: Chronological order of agent activities
- **Agent Activities**: What each agent did
- **Messages**: Communication between agents
- **State Evolution**: How shared state changed
- **Durations**: Time taken by each agent

### Visualization Features

- Timeline view of all activities
- Agent cards with statistics
- Message flow visualization
- Status indicators (success, error, pending)
- Duration metrics

## 🎯 Use Cases

### Complex Query with Schema Research

**Problem**: Query requires understanding complex schema

**Solution**: Use schema researcher + SQL generator

```json
{
  "query": "Find all customers who purchased products in category 'Electronics' in the last quarter",
  "agents": [
    {"agent_id": "schema-agent", "role": "schema_researcher"},
    {"agent_id": "sql-agent", "role": "sql_generator"}
  ]
}
```

### Query with Validation

**Problem**: Generated queries need validation

**Solution**: Add query validator

```json
{
  "query": "Delete inactive users",
  "agents": [
    {"agent_id": "sql-agent", "role": "sql_generator"},
    {"agent_id": "validator-agent", "role": "query_validator"}
  ]
}
```

### Full Pipeline

**Problem**: End-to-end query generation and analysis

**Solution**: Use all roles

```json
{
  "query": "Analyze sales trends by product category",
  "agents": [
    {"agent_id": "schema-agent", "role": "schema_researcher"},
    {"agent_id": "sql-agent", "role": "sql_generator"},
    {"agent_id": "validator-agent", "role": "query_validator"},
    {"agent_id": "analyzer-agent", "role": "result_analyzer"}
  ]
}
```

## 📚 API Reference

### Create Session

```
POST /api/agents/collaborate
```

**Request:**
```json
{
  "query": "Find all active users",
  "agents": [
    {"agent_id": "agent-1", "role": "schema_researcher"}
  ],
  "initial_state": {}
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "query": "Find all active users",
  "agents": ["agent-1"],
  "roles": {"agent-1": "schema_researcher"},
  "status": "pending",
  "created_at": "2024-01-15T10:00:00Z"
}
```

### Execute Collaboration

```
POST /api/agents/collaborate/{session_id}/execute
```

**Request (optional):**
```json
{
  "workflow": ["agent-1", "agent-2"]
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "status": "completed",
  "traces": [...],
  "messages": [...],
  "state": {...},
  "result": {...}
}
```

### Get Session

```
GET /api/agents/collaborate/{session_id}
```

**Response:** Full session details

### Get Trace Visualization

```
GET /api/agents/collaborate/{session_id}/trace
```

**Response:**
```json
{
  "session_id": "uuid",
  "query": "...",
  "timeline": [...],
  "agents": {...},
  "messages": [...],
  "state_evolution": [...]
}
```

### Send Message

```
POST /api/agents/collaborate/{session_id}/message
```

**Request:**
```json
{
  "from_agent": "agent-1",
  "to_agent": "agent-2",
  "message_type": "data",
  "content": {...}
}
```

## 🔍 Example Workflow

### Step 1: Create Session

```python
import requests

response = requests.post(
    'http://localhost:5000/api/agents/collaborate',
    headers={'X-API-Key': 'your-api-key'},
    json={
        'query': 'Find all active users with orders',
        'agents': [
            {'agent_id': 'schema-agent', 'role': 'schema_researcher'},
            {'agent_id': 'sql-agent', 'role': 'sql_generator'}
        ]
    }
)

session_id = response.json()['session_id']
```

### Step 2: Execute Collaboration

```python
response = requests.post(
    f'http://localhost:5000/api/agents/collaborate/{session_id}/execute',
    headers={'X-API-Key': 'your-api-key'}
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Traces: {len(result['traces'])}")
```

### Step 3: View Results

```python
response = requests.get(
    f'http://localhost:5000/api/agents/collaborate/{session_id}',
    headers={'X-API-Key': 'your-api-key'}
)

session = response.json()
print(f"Final SQL: {session['state'].get('generated_sql')}")
```

### Step 4: View Trace

Visit: `http://localhost:5000/collaboration/trace?session_id={session_id}`

## 🎨 Best Practices

### Agent Selection

1. **Match Roles to Needs**: Use appropriate roles for your use case
2. **Start Simple**: Begin with 2-3 agents
3. **Add Validation**: Include validator for production queries
4. **Use Analyzer**: Add analyzer for complex queries

### Workflow Design

1. **Schema First**: Research schema before generating SQL
2. **Validate Always**: Validate generated SQL
3. **Analyze Complex**: Use analyzer for complex queries
4. **Custom Workflows**: Customize workflow for specific needs

### Error Handling

1. **Check Status**: Always check session status
2. **Review Traces**: Review traces for errors
3. **Handle Failures**: Handle failed agent tasks
4. **Retry Logic**: Implement retry for transient failures

## 🐛 Troubleshooting

### Session Not Found

**Issue**: Session ID not found
**Solution**: Verify session ID, check if session was created

### Agent Not Found

**Issue**: Agent ID doesn't exist
**Solution**: Verify agent IDs, ensure agents are registered

### Invalid Role

**Issue**: Invalid role specified
**Solution**: Use valid roles: schema_researcher, sql_generator, query_validator, result_analyzer

### Workflow Failed

**Issue**: Collaboration execution failed
**Solution**: Check traces for errors, verify agent configurations

## 📈 Performance

### Optimization Tips

1. **Minimize Agents**: Use only necessary agents
2. **Parallel Execution**: Some agents can run in parallel (future feature)
3. **Cache Schema**: Cache schema research results
4. **Reuse Sessions**: Reuse sessions for similar queries

---

**Questions?** Check [GitHub Discussions](https://github.com/your-repo/ai-agent-connector/discussions) or open an issue!


