"""
Advanced usage examples for Universal Agent Connector SDK
"""

from universal_agent_connector import (
    UniversalAgentConnector,
    APIError,
    NotFoundError
)


def example_error_handling():
    """Example: Comprehensive error handling"""
    client = UniversalAgentConnector(base_url="http://localhost:5000")
    
    try:
        agent = client.get_agent("nonexistent-agent")
    except NotFoundError as e:
        print(f"Agent not found: {e}")
    except APIError as e:
        print(f"API error ({e.status_code}): {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def example_query_templates():
    """Example: Using query templates"""
    client = UniversalAgentConnector(base_url="http://localhost:5000")
    
    # Create template
    template = client.create_query_template(
        agent_id="analytics-agent",
        name="Top Customers by Revenue",
        sql="""
            SELECT 
                customer_id,
                customer_name,
                SUM(order_total) as total_revenue
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            WHERE order_date >= '{{start_date}}'
            GROUP BY customer_id, customer_name
            ORDER BY total_revenue DESC
            LIMIT {{limit}}
        """,
        tags=["customers", "revenue", "analytics"]
    )
    
    # Use template
    result = client.execute_natural_language_query(
        agent_id="analytics-agent",
        query="Get top customers",
        use_template=template['template_id'],
        template_params={
            "start_date": "2024-01-01",
            "limit": 10
        }
    )
    
    return result


def example_batch_operations():
    """Example: Batch operations"""
    client = UniversalAgentConnector(base_url="http://localhost:5000")
    
    # Register multiple agents
    agents = [
        {"agent_id": f"agent-{i}", "credentials": {...}, "database": {...}}
        for i in range(5)
    ]
    
    registered = []
    for agent_config in agents:
        try:
            agent = client.register_agent(**agent_config)
            registered.append(agent)
        except APIError as e:
            print(f"Failed to register {agent_config['agent_id']}: {e}")
    
    return registered


def example_cost_optimization():
    """Example: Cost optimization workflow"""
    client = UniversalAgentConnector(base_url="http://localhost:5000")
    
    # Get cost dashboard
    dashboard = client.get_cost_dashboard(period_days=7)
    
    # Check if costs are high
    if dashboard['total_cost'] > 100:
        print("High costs detected, analyzing...")
        
        # Check cost by provider
        for provider, cost in dashboard['cost_by_provider'].items():
            print(f"{provider}: ${cost:.4f}")
        
        # Check cost by operation
        for operation, cost in dashboard['cost_by_operation'].items():
            print(f"{operation}: ${cost:.4f}")
        
        # Export detailed report
        report = client.export_cost_report(
            format="csv",
            period_days=7
        )
        with open("cost_analysis.csv", "w") as f:
            f.write(report)
        
        # Create budget alert if needed
        if dashboard['total_cost'] > 500:
            client.create_budget_alert(
                name="Weekly Budget Alert",
                threshold_usd=500.0,
                period="weekly"
            )


def example_failover_monitoring():
    """Example: Monitor and manage failover"""
    client = UniversalAgentConnector(base_url="http://localhost:5000")
    
    # Get failover stats
    stats = client.get_failover_stats("my-agent")
    
    # Check provider health
    for provider_id, health in stats['provider_health'].items():
        status = health['status']
        failures = health['consecutive_failures']
        
        print(f"{provider_id}: {status} (failures: {failures})")
        
        # Switch if unhealthy
        if status == "unhealthy" and failures >= 3:
            print(f"Switching from {provider_id}...")
            # Find healthy backup
            for backup_id, backup_health in stats['provider_health'].items():
                if backup_health['status'] == "healthy" and backup_id != provider_id:
                    client.switch_provider("my-agent", backup_id)
                    print(f"Switched to {backup_id}")
                    break


def example_audit_trail():
    """Example: Audit trail analysis"""
    client = UniversalAgentConnector(base_url="http://localhost:5000")
    
    # Get recent audit logs
    logs = client.get_audit_logs(limit=100)
    
    # Analyze by action type
    action_counts = {}
    for log in logs:
        action = log.get('action_type', 'unknown')
        action_counts[action] = action_counts.get(action, 0) + 1
    
    print("Action type distribution:")
    for action, count in action_counts.items():
        print(f"  {action}: {count}")
    
    # Get statistics
    stats = client.get_audit_statistics()
    print(f"\nTotal actions: {stats.get('total_actions', 0)}")
    print(f"Unique agents: {stats.get('unique_agents', 0)}")


if __name__ == "__main__":
    print("Advanced Universal Agent Connector SDK Examples")
    print("=" * 50)
    
    # Uncomment to run:
    # example_error_handling()
    # example_query_templates()
    # example_batch_operations()
    # example_cost_optimization()
    # example_failover_monitoring()
    # example_audit_trail()
