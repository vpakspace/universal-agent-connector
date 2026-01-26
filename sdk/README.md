# Universal Agent Connector Python SDK

Official Python SDK for the Universal Agent Connector API. Easily integrate AI agent management, database connections, and query execution into your Python applications.

## Installation

```bash
pip install universal-agent-connector
```

## Quick Start

```python
from universal_agent_connector import UniversalAgentConnector

# Initialize the client
client = UniversalAgentConnector(
    base_url="http://localhost:5000",
    api_key="your-api-key"  # Optional
)

# Register an agent
agent = client.register_agent(
    agent_id="my-agent",
    agent_credentials={
        "api_key": "agent-key",
        "api_secret": "agent-secret"
    },
    database={
        "host": "localhost",
        "port": 5432,
        "user": "dbuser",
        "password": "dbpass",
        "database": "mydb"
    }
)

print(f"Agent registered with API key: {agent['api_key']}")
```

## Features

- ✅ **Full API Coverage** - All REST API endpoints wrapped
- ✅ **Type-Safe** - Clear method signatures and error handling
- ✅ **Easy to Use** - Simple, intuitive API
- ✅ **Error Handling** - Comprehensive exception handling
- ✅ **Documentation** - Full docstrings and examples

## Examples

### Agent Management

```python
from universal_agent_connector import UniversalAgentConnector

client = UniversalAgentConnector(base_url="http://localhost:5000")

# Register an agent
agent = client.register_agent(
    agent_id="analytics-agent",
    agent_credentials={"api_key": "key", "api_secret": "secret"},
    database={
        "host": "db.example.com",
        "database": "analytics",
        "user": "analytics_user",
        "password": "secure_password"
    }
)

# Get agent information
agent_info = client.get_agent("analytics-agent")

# List all agents
agents = client.list_agents()
```

### Query Execution

```python
# Execute SQL query
result = client.execute_query(
    agent_id="analytics-agent",
    query="SELECT * FROM users LIMIT 10"
)
print(result['data'])

# Natural language query
result = client.execute_natural_language_query(
    agent_id="analytics-agent",
    query="Show me the top 10 customers by revenue"
)
print(result['data'])

# Get query suggestions
suggestions = client.get_query_suggestions(
    agent_id="analytics-agent",
    query="show me sales",
    num_suggestions=3
)
for suggestion in suggestions:
    print(f"SQL: {suggestion['sql']}")
    print(f"Confidence: {suggestion['confidence']}")
```

### AI Agent Management

```python
# Register an AI agent (OpenAI)
ai_agent = client.register_ai_agent(
    agent_id="gpt-agent",
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-..."
)

# Execute AI query
response = client.execute_ai_query(
    agent_id="gpt-agent",
    query="What is machine learning?"
)
print(response['response'])

# Set rate limits
client.set_rate_limit(
    agent_id="gpt-agent",
    queries_per_minute=60,
    queries_per_hour=1000
)
```

### Provider Failover

```python
# Configure failover
client.configure_failover(
    agent_id="my-agent",
    primary_provider_id="openai-agent",
    backup_provider_ids=["claude-agent"],
    health_check_enabled=True,
    auto_failover_enabled=True
)

# Get failover stats
stats = client.get_failover_stats("my-agent")
print(f"Active provider: {stats['active_provider']}")
print(f"Provider health: {stats['provider_health']}")

# Manually switch provider
client.switch_provider("my-agent", "claude-agent")
```

### Cost Tracking

```python
# Get cost dashboard
dashboard = client.get_cost_dashboard(period_days=30)
print(f"Total cost: ${dashboard['total_cost']:.4f}")
print(f"Total calls: {dashboard['total_calls']}")

# Export cost report
report = client.export_cost_report(format="csv", period_days=30)
with open("cost_report.csv", "w") as f:
    f.write(report)

# Create budget alert
alert = client.create_budget_alert(
    name="Monthly Budget",
    threshold_usd=1000.0,
    period="monthly",
    notification_emails=["admin@example.com"]
)
```

### Query Templates

```python
# Create a template
template = client.create_query_template(
    agent_id="analytics-agent",
    name="Top Customers",
    sql="SELECT * FROM customers ORDER BY revenue DESC LIMIT {{limit}}",
    tags=["customers", "revenue"]
)

# Use template
result = client.execute_natural_language_query(
    agent_id="analytics-agent",
    query="Get top customers",
    use_template=template['template_id'],
    template_params={"limit": 10}
)
```

### Permissions

```python
# Set permissions
client.set_permissions(
    agent_id="analytics-agent",
    permissions=[
        {
            "resource_type": "table",
            "resource_id": "users",
            "permissions": ["read"]
        },
        {
            "resource_type": "table",
            "resource_id": "orders",
            "permissions": ["read"]
        }
    ]
)

# Get permissions
permissions = client.get_permissions("analytics-agent")
```

## Error Handling

The SDK provides comprehensive error handling:

```python
from universal_agent_connector import (
    UniversalAgentConnector,
    APIError,
    AuthenticationError,
    NotFoundError,
    ValidationError
)

client = UniversalAgentConnector(base_url="http://localhost:5000")

try:
    agent = client.get_agent("nonexistent")
except NotFoundError as e:
    print(f"Agent not found: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except APIError as e:
    print(f"API error: {e.status_code} - {e}")
```

## Configuration

### Environment Variables

You can configure the SDK using environment variables:

```bash
export UAC_BASE_URL="http://localhost:5000"
export UAC_API_KEY="your-api-key"
```

Then initialize without parameters:

```python
import os
from universal_agent_connector import UniversalAgentConnector

client = UniversalAgentConnector(
    base_url=os.getenv("UAC_BASE_URL", "http://localhost:5000"),
    api_key=os.getenv("UAC_API_KEY")
)
```

## API Reference

### Client Methods

#### Agents
- `register_agent()` - Register a new agent
- `get_agent()` - Get agent information
- `list_agents()` - List all agents
- `delete_agent()` - Delete an agent
- `update_agent_database()` - Update database connection

#### Queries
- `execute_query()` - Execute SQL query
- `execute_natural_language_query()` - Execute natural language query
- `get_query_suggestions()` - Get query suggestions

#### AI Agents
- `register_ai_agent()` - Register AI agent (OpenAI, Anthropic, custom)
- `execute_ai_query()` - Execute AI query
- `set_rate_limit()` - Set rate limits
- `set_retry_policy()` - Set retry policy

#### Provider Failover
- `configure_failover()` - Configure provider failover
- `get_failover_stats()` - Get failover statistics
- `switch_provider()` - Manually switch provider

#### Cost Tracking
- `get_cost_dashboard()` - Get cost dashboard
- `export_cost_report()` - Export cost report
- `create_budget_alert()` - Create budget alert

#### Query Templates
- `create_query_template()` - Create template
- `list_query_templates()` - List templates
- `get_query_template()` - Get template
- `update_query_template()` - Update template
- `delete_query_template()` - Delete template

#### Permissions
- `set_permissions()` - Set permissions
- `get_permissions()` - Get permissions
- `revoke_permission()` - Revoke permission

#### Audit & Notifications
- `get_audit_logs()` - Get audit logs
- `get_notifications()` - Get notifications
- `mark_notification_read()` - Mark notification as read

## Requirements

- Python 3.10+
- requests >= 2.31.0

## License

MIT License

## Support

- Documentation: https://docs.universal-agent-connector.com
- Issues: https://github.com/universal-agent-connector/python-sdk/issues
- Email: support@universal-agent-connector.com
