"""
Basic usage examples for Universal Agent Connector SDK
"""

from universal_agent_connector import UniversalAgentConnector

# Initialize client
client = UniversalAgentConnector(
    base_url="http://localhost:5000"
)


def example_register_agent():
    """Example: Register a new agent"""
    agent = client.register_agent(
        agent_id="example-agent",
        agent_credentials={
            "api_key": "example-key",
            "api_secret": "example-secret"
        },
        database={
            "host": "localhost",
            "port": 5432,
            "user": "postgres",
            "password": "postgres",
            "database": "example_db"
        },
        agent_info={
            "name": "Example Agent",
            "description": "Example agent for testing"
        }
    )
    print(f"Agent registered: {agent['agent_id']}")
    print(f"API Key: {agent['api_key']}")
    return agent


def example_execute_query():
    """Example: Execute a SQL query"""
    result = client.execute_query(
        agent_id="example-agent",
        query="SELECT COUNT(*) as total FROM users"
    )
    print(f"Query result: {result['data']}")
    return result


def example_natural_language_query():
    """Example: Execute a natural language query"""
    result = client.execute_natural_language_query(
        agent_id="example-agent",
        query="Show me the top 10 customers by revenue"
    )
    print(f"Generated SQL: {result.get('sql')}")
    print(f"Results: {result.get('data')}")
    return result


def example_ai_agent():
    """Example: Register and use an AI agent"""
    # Register OpenAI agent
    ai_agent = client.register_ai_agent(
        agent_id="gpt-agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-your-key-here"
    )
    print(f"AI Agent registered: {ai_agent['agent_id']}")
    
    # Execute query
    response = client.execute_ai_query(
        agent_id="gpt-agent",
        query="Explain machine learning in simple terms"
    )
    print(f"Response: {response['response']}")
    return response


def example_cost_tracking():
    """Example: Track costs"""
    # Get cost dashboard
    dashboard = client.get_cost_dashboard(period_days=30)
    print(f"Total cost: ${dashboard['total_cost']:.4f}")
    print(f"Total calls: {dashboard['total_calls']}")
    print(f"Cost by provider: {dashboard['cost_by_provider']}")
    
    # Create budget alert
    alert = client.create_budget_alert(
        name="Monthly Budget Alert",
        threshold_usd=1000.0,
        period="monthly",
        notification_emails=["admin@example.com"]
    )
    print(f"Budget alert created: {alert['alert_id']}")
    return dashboard


def example_provider_failover():
    """Example: Configure provider failover"""
    # Register multiple AI agents
    client.register_ai_agent(
        agent_id="openai-agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-openai-key"
    )
    
    client.register_ai_agent(
        agent_id="claude-agent",
        provider="anthropic",
        model="claude-3-haiku-20240307",
        api_key="sk-ant-claude-key"
    )
    
    # Configure failover
    config = client.configure_failover(
        agent_id="my-agent",
        primary_provider_id="openai-agent",
        backup_provider_ids=["claude-agent"],
        health_check_enabled=True,
        auto_failover_enabled=True
    )
    print(f"Failover configured: {config['agent_id']}")
    
    # Get failover stats
    stats = client.get_failover_stats("my-agent")
    print(f"Active provider: {stats['active_provider']}")
    return stats


if __name__ == "__main__":
    print("Universal Agent Connector SDK Examples")
    print("=" * 50)
    
    # Uncomment to run examples:
    # example_register_agent()
    # example_execute_query()
    # example_natural_language_query()
    # example_ai_agent()
    # example_cost_tracking()
    # example_provider_failover()
