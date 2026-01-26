"""
Locust load testing script for AI Agent Connector
Tests system with up to 1000 concurrent users
"""

from locust import HttpUser, task, between, events
from locust.contrib.fasthttp import FastHttpUser
import json
import random
import time
from typing import Dict, Any


class AgentConnectorUser(HttpUser):
    """Simulates a user interacting with the API"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts"""
        self.agent_id = None
        self.api_key = None
        self.setup_agent()
    
    def setup_agent(self):
        """Register an agent for this user"""
        try:
            # Register agent
            response = self.client.post(
                "/api/agents/register",
                json={
                    "agent_id": f"load_test_agent_{random.randint(10000, 99999)}",
                    "agent_credentials": {
                        "api_key": f"test_key_{random.randint(10000, 99999)}",
                        "api_secret": f"test_secret_{random.randint(10000, 99999)}"
                    },
                    "database": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "test_db",
                        "user": "test_user",
                        "password": "test_pass"
                    }
                },
                name="Register Agent",
                catch_response=True
            )
            
            if response.status_code == 201:
                data = response.json()
                self.agent_id = data.get('agent', {}).get('agent_id')
                self.api_key = data.get('api_key')
                response.success()
            else:
                response.failure(f"Failed to register agent: {response.status_code}")
        except Exception as e:
            pass  # Continue even if registration fails
    
    @task(3)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/api/health", name="Health Check")
    
    @task(5)
    def get_agent(self):
        """Get agent information"""
        if self.agent_id:
            self.client.get(
                f"/api/agents/{self.agent_id}",
                headers={"X-API-Key": self.api_key} if self.api_key else {},
                name="Get Agent"
            )
    
    @task(2)
    def list_agents(self):
        """List all agents"""
        self.client.get("/api/agents", name="List Agents")
    
    @task(10)
    def execute_query(self):
        """Execute SQL query"""
        if self.agent_id and self.api_key:
            queries = [
                "SELECT * FROM users LIMIT 10",
                "SELECT COUNT(*) FROM orders",
                "SELECT * FROM products WHERE stock > 0",
                "SELECT name, email FROM users WHERE status = 'active'",
                "SELECT * FROM orders ORDER BY created_at DESC LIMIT 5"
            ]
            
            self.client.post(
                f"/api/agents/{self.agent_id}/query",
                headers={"X-API-Key": self.api_key},
                json={"query": random.choice(queries)},
                name="Execute Query",
                catch_response=True
            )
    
    @task(8)
    def execute_natural_language_query(self):
        """Execute natural language query"""
        if self.agent_id and self.api_key:
            nl_queries = [
                "Show me all users",
                "Count total orders",
                "List products in stock",
                "Get active users",
                "Show recent orders"
            ]
            
            self.client.post(
                f"/api/agents/{self.agent_id}/query/natural",
                headers={"X-API-Key": self.api_key},
                json={"query": random.choice(nl_queries)},
                name="NL Query",
                catch_response=True
            )
    
    @task(1)
    def get_cost_dashboard(self):
        """Get cost dashboard"""
        if self.agent_id and self.api_key:
            self.client.get(
                f"/api/cost/dashboard?agent_id={self.agent_id}",
                headers={"X-API-Key": self.api_key} if self.api_key else {},
                name="Cost Dashboard"
            )
    
    @task(1)
    def get_failover_stats(self):
        """Get failover statistics"""
        if self.agent_id and self.api_key:
            self.client.get(
                f"/api/agents/{self.agent_id}/failover/stats",
                headers={"X-API-Key": self.api_key} if self.api_key else {},
                name="Failover Stats"
            )
    
    @task(2)
    def graphql_query(self):
        """GraphQL query"""
        query = """
        query {
            health {
                status
            }
        }
        """
        self.client.post(
            "/graphql",
            json={"query": query},
            name="GraphQL Query"
        )


class FastAgentConnectorUser(FastHttpUser):
    """Fast HTTP user for higher concurrency"""
    
    wait_time = between(0.5, 2)
    
    def on_start(self):
        """Called when a user starts"""
        self.agent_id = None
        self.api_key = None
    
    @task(10)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/api/health", name="Health Check")
    
    @task(5)
    def execute_query(self):
        """Execute SQL query"""
        if self.agent_id:
            self.client.post(
                f"/api/agents/{self.agent_id}/query",
                headers={"X-API-Key": self.api_key} if self.api_key else {},
                json={"query": "SELECT * FROM users LIMIT 10"},
                name="Execute Query"
            )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    print("=" * 60)
    print("Load Test Starting")
    print("=" * 60)
    print(f"Target: {environment.host}")
    print(f"Users: {environment.runner.target_user_count if hasattr(environment.runner, 'target_user_count') else 'N/A'}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    print("=" * 60)
    print("Load Test Complete")
    print("=" * 60)
