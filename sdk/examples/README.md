# Universal Agent Connector SDK Examples

This directory contains example code demonstrating how to use the Universal Agent Connector Python SDK.

## Examples

### Basic Usage (`basic_usage.py`)

Basic examples covering:
- Agent registration
- Query execution (SQL and natural language)
- AI agent management
- Cost tracking
- Provider failover

### Advanced Usage (`advanced_usage.py`)

Advanced examples covering:
- Error handling
- Query templates
- Batch operations
- Cost optimization
- Failover monitoring
- Audit trail analysis

## Running Examples

```bash
# Install the SDK first
cd sdk
pip install -e .

# Run basic examples
python examples/basic_usage.py

# Run advanced examples
python examples/advanced_usage.py
```

## Example: Complete Workflow

```python
from universal_agent_connector import UniversalAgentConnector

# Initialize client
client = UniversalAgentConnector(base_url="http://localhost:5000")

# 1. Register an agent
agent = client.register_agent(
    agent_id="my-agent",
    agent_credentials={"api_key": "key", "api_secret": "secret"},
    database={"host": "localhost", "database": "mydb"}
)

# 2. Set permissions
client.set_permissions(
    agent_id="my-agent",
    permissions=[
        {"resource_type": "table", "resource_id": "users", "permissions": ["read"]}
    ]
)

# 3. Execute queries
result = client.execute_natural_language_query(
    agent_id="my-agent",
    query="Show me all users"
)

# 4. Monitor costs
dashboard = client.get_cost_dashboard(period_days=7)
print(f"Total cost: ${dashboard['total_cost']:.4f}")

# 5. Configure failover
client.configure_failover(
    agent_id="my-agent",
    primary_provider_id="openai-agent",
    backup_provider_ids=["claude-agent"]
)
```
