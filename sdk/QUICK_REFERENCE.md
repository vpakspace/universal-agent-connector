# Universal Agent Connector SDK - Quick Reference

## Installation

```bash
pip install universal-agent-connector
```

## Initialization

```python
from universal_agent_connector import UniversalAgentConnector

client = UniversalAgentConnector(
    base_url="http://localhost:5000",
    api_key="your-api-key"  # Optional
)
```

## Common Operations

### Agent Management

```python
# Register agent
agent = client.register_agent(
    agent_id="my-agent",
    agent_credentials={"api_key": "key", "api_secret": "secret"},
    database={"host": "localhost", "database": "mydb"}
)

# Get agent
agent = client.get_agent("my-agent")

# List agents
agents = client.list_agents()

# Delete agent
client.delete_agent("my-agent")
```

### Query Execution

```python
# SQL query
result = client.execute_query("my-agent", "SELECT * FROM users LIMIT 10")

# Natural language
result = client.execute_natural_language_query(
    "my-agent",
    "Show me all users"
)

# Query suggestions
suggestions = client.get_query_suggestions(
    "my-agent",
    "show me sales",
    num_suggestions=3
)
```

### AI Agents

```python
# Register AI agent
ai_agent = client.register_ai_agent(
    agent_id="gpt-agent",
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-..."
)

# Execute AI query
response = client.execute_ai_query("gpt-agent", "What is AI?")

# Set rate limit
client.set_rate_limit("gpt-agent", queries_per_minute=60)
```

### Provider Failover

```python
# Configure failover
client.configure_failover(
    agent_id="my-agent",
    primary_provider_id="openai-agent",
    backup_provider_ids=["claude-agent"]
)

# Get stats
stats = client.get_failover_stats("my-agent")

# Switch provider
client.switch_provider("my-agent", "claude-agent")
```

### Cost Tracking

```python
# Get dashboard
dashboard = client.get_cost_dashboard(period_days=30)

# Export report
report = client.export_cost_report(format="csv", period_days=30)

# Create budget alert
alert = client.create_budget_alert(
    name="Monthly Budget",
    threshold_usd=1000.0,
    period="monthly"
)
```

### Query Templates

```python
# Create template
template = client.create_query_template(
    agent_id="my-agent",
    name="Top Users",
    sql="SELECT * FROM users ORDER BY score DESC LIMIT {{limit}}"
)

# Use template
result = client.execute_natural_language_query(
    "my-agent",
    "Get top users",
    use_template=template['template_id'],
    template_params={"limit": 10}
)
```

### Permissions

```python
# Set permissions
client.set_permissions(
    "my-agent",
    permissions=[
        {"resource_type": "table", "resource_id": "users", "permissions": ["read"]}
    ]
)

# Get permissions
permissions = client.get_permissions("my-agent")
```

## Error Handling

```python
from universal_agent_connector import (
    NotFoundError,
    AuthenticationError,
    APIError
)

try:
    agent = client.get_agent("nonexistent")
except NotFoundError:
    print("Agent not found")
except AuthenticationError:
    print("Authentication failed")
except APIError as e:
    print(f"API error: {e.status_code}")
```

## Method Categories

### Agents (5 methods)
- `register_agent()`, `get_agent()`, `list_agents()`, `delete_agent()`, `update_agent_database()`

### Queries (3 methods)
- `execute_query()`, `execute_natural_language_query()`, `get_query_suggestions()`

### Query Templates (5 methods)
- `create_query_template()`, `list_query_templates()`, `get_query_template()`, `update_query_template()`, `delete_query_template()`

### AI Agents (10+ methods)
- `register_ai_agent()`, `execute_ai_query()`, `set_rate_limit()`, `set_retry_policy()`, etc.

### Provider Failover (6 methods)
- `configure_failover()`, `get_failover_stats()`, `switch_provider()`, etc.

### Cost Tracking (8 methods)
- `get_cost_dashboard()`, `export_cost_report()`, `create_budget_alert()`, etc.

### Permissions (3 methods)
- `set_permissions()`, `get_permissions()`, `revoke_permission()`

### Admin (50+ methods)
- Database, RLS, masking, validation, approvals, cache, audit, alerts, teams, etc.

## Full API Reference

See `README.md` for complete API documentation.
