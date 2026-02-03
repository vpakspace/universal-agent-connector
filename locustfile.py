"""
Load Testing for Universal Agent Connector API.

Uses Locust for distributed load testing.

Usage:
    # Web UI mode (recommended for exploration)
    locust -f locustfile.py --host=http://localhost:5000

    # Headless mode (for CI/CD)
    locust -f locustfile.py --host=http://localhost:5000 \
           --headless -u 100 -r 10 -t 60s \
           --csv=results/load_test

    # With specific user class
    locust -f locustfile.py --host=http://localhost:5000 \
           -u 50 -r 5 -t 30s AgentUser

Scenarios:
    - AgentUser: Agent registration, queries, permissions
    - OntoGuardUser: Validation, permissions check, allowed actions
    - CacheUser: Cache operations (stats, invalidate, cleanup)
    - AuditUser: Audit logs, statistics, export
    - AlertUser: Alert channels, send alerts, history
    - MixedUser: Realistic mix of all operations
"""

import json
import random
import string
from locust import HttpUser, task, between, tag, events
from locust.runners import MasterRunner


# Test data
ROLES = ["Doctor", "Nurse", "Admin", "LabTech", "Receptionist"]
ENTITIES = ["PatientRecord", "MedicalRecord", "LabResult", "Appointment", "Billing", "Staff"]
ACTIONS = ["read", "create", "update", "delete"]
TABLES = ["patients", "medical_records", "lab_results", "appointments", "billing", "staff"]

# Queries for testing
TEST_QUERIES = [
    "SELECT * FROM patients LIMIT 10",
    "SELECT * FROM appointments WHERE status = 'scheduled'",
    "SELECT * FROM lab_results ORDER BY test_date DESC LIMIT 5",
    "SELECT COUNT(*) FROM medical_records",
    "SELECT p.*, m.diagnosis FROM patients p JOIN medical_records m ON p.id = m.patient_id LIMIT 5",
]

NL_QUERIES = [
    "Show all patients",
    "List scheduled appointments",
    "Show recent lab results",
    "Count medical records",
    "Show patients with their diagnoses",
]


def generate_agent_id():
    """Generate unique agent ID."""
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"load-test-agent-{suffix}"


class AgentUser(HttpUser):
    """
    Simulates agent operations: registration, queries, permissions.
    """
    wait_time = between(1, 3)
    weight = 3  # Higher weight = more users

    def on_start(self):
        """Register agent on start."""
        self.agent_id = generate_agent_id()
        self.api_key = None
        self.register_agent()

    def on_stop(self):
        """Cleanup agent on stop."""
        if self.agent_id:
            self.client.delete(f"/api/agents/{self.agent_id}")

    def register_agent(self):
        """Register a new agent."""
        response = self.client.post(
            "/api/agents/register",
            json={
                "agent_id": self.agent_id,
                "agent_info": {
                    "name": f"Load Test Agent {self.agent_id}",
                    "role": random.choice(ROLES)
                },
                "rate_limits": {
                    "queries_per_minute": 120,
                    "queries_per_hour": 5000,
                    "queries_per_day": 50000
                }
            },
            name="/api/agents/register"
        )
        if response.status_code == 201:
            data = response.json()
            self.api_key = data.get("api_key")

    @task(5)
    @tag("agents")
    def list_agents(self):
        """List all agents."""
        self.client.get("/api/agents", name="/api/agents")

    @task(3)
    @tag("agents")
    def get_agent(self):
        """Get agent details."""
        self.client.get(f"/api/agents/{self.agent_id}", name="/api/agents/[agent_id]")

    @task(2)
    @tag("agents", "permissions")
    def get_permissions(self):
        """Get agent permissions."""
        self.client.get(
            f"/api/agents/{self.agent_id}/permissions",
            name="/api/agents/[agent_id]/permissions"
        )

    @task(1)
    @tag("agents", "permissions")
    def add_permission(self):
        """Add resource permission."""
        table = random.choice(TABLES)
        permission = random.choice(["READ", "WRITE"])
        self.client.post(
            f"/api/agents/{self.agent_id}/resources/{table}/permissions",
            json={"permission": permission},
            name="/api/agents/[agent_id]/resources/[resource]/permissions"
        )

    @task(3)
    @tag("rate-limits")
    def get_rate_limits(self):
        """Get rate limit status."""
        self.client.get(
            f"/api/rate-limits/{self.agent_id}",
            name="/api/rate-limits/[agent_id]"
        )


class QueryUser(HttpUser):
    """
    Simulates query execution: SQL and natural language queries.
    Requires a pre-registered agent with database connection.
    """
    wait_time = between(0.5, 2)
    weight = 2

    def on_start(self):
        """Register agent with database connection."""
        self.agent_id = generate_agent_id()
        self.api_key = None
        self.role = random.choice(ROLES)

        response = self.client.post(
            "/api/agents/register",
            json={
                "agent_id": self.agent_id,
                "agent_info": {"name": f"Query Agent {self.agent_id}", "role": self.role},
                "database": {
                    "type": "postgresql",
                    "host": "localhost",
                    "port": 5433,
                    "database": "hospital_db",
                    "user": "uac_user",
                    "password": "uac_password"
                },
                "rate_limits": {
                    "queries_per_minute": 200,
                    "queries_per_hour": 10000
                }
            },
            name="/api/agents/register (with DB)"
        )
        if response.status_code == 201:
            data = response.json()
            self.api_key = data.get("api_key")

            # Add permissions for all tables
            for table in TABLES:
                self.client.post(
                    f"/api/agents/{self.agent_id}/resources/{table}/permissions",
                    json={"permission": "READ"}
                )

    def on_stop(self):
        """Cleanup agent."""
        if self.agent_id:
            self.client.delete(f"/api/agents/{self.agent_id}")

    @task(5)
    @tag("queries", "sql")
    def execute_sql_query(self):
        """Execute SQL query."""
        if not self.api_key:
            return

        query = random.choice(TEST_QUERIES)
        self.client.post(
            f"/api/agents/{self.agent_id}/query",
            json={"query": query},
            headers={
                "X-API-Key": self.api_key,
                "X-User-Role": self.role
            },
            name="/api/agents/[agent_id]/query"
        )

    @task(2)
    @tag("queries", "natural-language")
    def execute_nl_query(self):
        """Execute natural language query."""
        if not self.api_key:
            return

        query = random.choice(NL_QUERIES)
        self.client.post(
            f"/api/agents/{self.agent_id}/query/natural",
            json={"query": query},
            headers={
                "X-API-Key": self.api_key,
                "X-User-Role": self.role
            },
            name="/api/agents/[agent_id]/query/natural"
        )


class OntoGuardUser(HttpUser):
    """
    Simulates OntoGuard validation operations.
    """
    wait_time = between(0.5, 1.5)
    weight = 3

    @task(5)
    @tag("ontoguard", "validation")
    def validate_action(self):
        """Validate action against ontology."""
        self.client.post(
            "/api/ontoguard/validate",
            json={
                "action": random.choice(ACTIONS),
                "entity_type": random.choice(ENTITIES),
                "context": {
                    "role": random.choice(ROLES),
                    "domain": "hospital"
                }
            },
            name="/api/ontoguard/validate"
        )

    @task(3)
    @tag("ontoguard")
    def check_permissions(self):
        """Check role permissions."""
        self.client.post(
            "/api/ontoguard/permissions",
            json={
                "role": random.choice(ROLES),
                "action": random.choice(ACTIONS),
                "entity_type": random.choice(ENTITIES)
            },
            name="/api/ontoguard/permissions"
        )

    @task(2)
    @tag("ontoguard")
    def get_allowed_actions(self):
        """Get allowed actions for role."""
        role = random.choice(ROLES)
        entity = random.choice(ENTITIES)
        self.client.get(
            f"/api/ontoguard/allowed-actions?role={role}&entity_type={entity}",
            name="/api/ontoguard/allowed-actions"
        )

    @task(1)
    @tag("ontoguard")
    def get_status(self):
        """Get OntoGuard status."""
        self.client.get("/api/ontoguard/status", name="/api/ontoguard/status")

    @task(1)
    @tag("ontoguard")
    def explain_rule(self):
        """Explain rule."""
        self.client.post(
            "/api/ontoguard/explain",
            json={
                "action": random.choice(ACTIONS),
                "entity_type": random.choice(ENTITIES),
                "context": {"role": random.choice(ROLES)}
            },
            name="/api/ontoguard/explain"
        )


class CacheUser(HttpUser):
    """
    Simulates cache operations.
    """
    wait_time = between(1, 3)
    weight = 1

    @task(5)
    @tag("cache")
    def get_cache_stats(self):
        """Get cache statistics."""
        self.client.get("/api/cache/stats", name="/api/cache/stats")

    @task(2)
    @tag("cache")
    def get_cache_config(self):
        """Get cache configuration."""
        self.client.get("/api/cache/config", name="/api/cache/config")

    @task(1)
    @tag("cache")
    def cleanup_cache(self):
        """Cleanup expired cache entries."""
        self.client.post("/api/cache/cleanup", name="/api/cache/cleanup")


class AuditUser(HttpUser):
    """
    Simulates audit trail operations.
    """
    wait_time = between(1, 3)
    weight = 1

    @task(5)
    @tag("audit")
    def get_audit_logs(self):
        """Get audit logs."""
        limit = random.choice([10, 50, 100])
        self.client.get(
            f"/api/audit/logs?limit={limit}",
            name="/api/audit/logs"
        )

    @task(3)
    @tag("audit")
    def get_audit_logs_filtered(self):
        """Get filtered audit logs."""
        status = random.choice(["success", "error", "denied"])
        self.client.get(
            f"/api/audit/logs?status={status}&limit=50",
            name="/api/audit/logs (filtered)"
        )

    @task(2)
    @tag("audit")
    def get_audit_statistics(self):
        """Get audit statistics."""
        days = random.choice([1, 7, 30])
        self.client.get(
            f"/api/audit/statistics?days={days}",
            name="/api/audit/statistics"
        )

    @task(1)
    @tag("audit")
    def get_audit_config(self):
        """Get audit configuration."""
        self.client.get("/api/audit/config", name="/api/audit/config")


class AlertUser(HttpUser):
    """
    Simulates alerting operations.
    """
    wait_time = between(2, 5)
    weight = 1

    @task(5)
    @tag("alerts")
    def get_channels(self):
        """Get alert channels."""
        self.client.get("/api/alerts/channels", name="/api/alerts/channels")

    @task(3)
    @tag("alerts")
    def get_alert_history(self):
        """Get alert history."""
        limit = random.choice([10, 50, 100])
        self.client.get(
            f"/api/alerts/history?limit={limit}",
            name="/api/alerts/history"
        )

    @task(2)
    @tag("alerts")
    def get_alert_statistics(self):
        """Get alert statistics."""
        days = random.choice([1, 7, 30])
        self.client.get(
            f"/api/alerts/statistics?days={days}",
            name="/api/alerts/statistics"
        )

    @task(1)
    @tag("alerts")
    def get_alert_config(self):
        """Get alert configuration."""
        self.client.get("/api/alerts/config", name="/api/alerts/config")


class SchemaUser(HttpUser):
    """
    Simulates schema drift operations.
    """
    wait_time = between(2, 4)
    weight = 1

    @task(5)
    @tag("schema")
    def get_bindings(self):
        """Get schema bindings."""
        self.client.get("/api/schema/bindings", name="/api/schema/bindings")

    @task(3)
    @tag("schema")
    def get_drift_check(self):
        """Get drift check bindings."""
        self.client.get("/api/schema/drift-check", name="/api/schema/drift-check")

    @task(2)
    @tag("schema")
    def check_drift(self):
        """Check schema drift."""
        self.client.post(
            "/api/schema/drift-check",
            json={
                "schemas": {
                    "PatientRecord": {
                        "id": "integer",
                        "first_name": "text",
                        "last_name": "text"
                    }
                }
            },
            name="/api/schema/drift-check (POST)"
        )


class JWTUser(HttpUser):
    """
    Simulates JWT authentication operations.
    """
    wait_time = between(1, 3)
    weight = 1

    def on_start(self):
        """Register agent for JWT testing."""
        self.agent_id = generate_agent_id()
        self.api_key = None
        self.access_token = None
        self.refresh_token = None

        response = self.client.post(
            "/api/agents/register",
            json={
                "agent_id": self.agent_id,
                "agent_info": {"name": f"JWT Agent {self.agent_id}"}
            }
        )
        if response.status_code == 201:
            self.api_key = response.json().get("api_key")

    def on_stop(self):
        """Cleanup."""
        if self.agent_id:
            self.client.delete(f"/api/agents/{self.agent_id}")

    @task(3)
    @tag("jwt")
    def get_token(self):
        """Get JWT token."""
        if not self.api_key:
            return

        response = self.client.post(
            "/api/auth/token",
            json={"role": random.choice(ROLES)},
            headers={"X-API-Key": self.api_key},
            name="/api/auth/token"
        )
        if response.status_code == 200:
            data = response.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")

    @task(2)
    @tag("jwt")
    def verify_token(self):
        """Verify JWT token."""
        if not self.access_token:
            return

        self.client.post(
            "/api/auth/verify",
            json={"token": self.access_token, "type": "access"},
            name="/api/auth/verify"
        )

    @task(1)
    @tag("jwt")
    def refresh_token_task(self):
        """Refresh access token."""
        if not self.refresh_token:
            return

        response = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
            name="/api/auth/refresh"
        )
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")

    @task(1)
    @tag("jwt")
    def get_jwt_config(self):
        """Get JWT configuration."""
        self.client.get("/api/auth/config", name="/api/auth/config")


class MixedUser(HttpUser):
    """
    Simulates realistic mixed workload with all operation types.
    """
    wait_time = between(0.5, 2)
    weight = 5  # Most common user type

    def on_start(self):
        """Setup agent."""
        self.agent_id = generate_agent_id()
        self.api_key = None
        self.role = random.choice(ROLES)

        response = self.client.post(
            "/api/agents/register",
            json={
                "agent_id": self.agent_id,
                "agent_info": {"name": f"Mixed Agent {self.agent_id}", "role": self.role},
                "rate_limits": {"queries_per_minute": 200}
            }
        )
        if response.status_code == 201:
            self.api_key = response.json().get("api_key")

    def on_stop(self):
        """Cleanup."""
        if self.agent_id:
            self.client.delete(f"/api/agents/{self.agent_id}")

    @task(10)
    @tag("mixed", "ontoguard")
    def validate_action(self):
        """Validate action - most common operation."""
        self.client.post(
            "/api/ontoguard/validate",
            json={
                "action": random.choice(ACTIONS),
                "entity_type": random.choice(ENTITIES),
                "context": {"role": self.role}
            },
            name="/api/ontoguard/validate"
        )

    @task(5)
    @tag("mixed", "cache")
    def cache_stats(self):
        """Check cache stats."""
        self.client.get("/api/cache/stats", name="/api/cache/stats")

    @task(3)
    @tag("mixed", "agents")
    def get_agent(self):
        """Get agent details."""
        self.client.get(f"/api/agents/{self.agent_id}", name="/api/agents/[agent_id]")

    @task(3)
    @tag("mixed", "rate-limits")
    def check_rate_limit(self):
        """Check rate limit status."""
        self.client.get(f"/api/rate-limits/{self.agent_id}", name="/api/rate-limits/[agent_id]")

    @task(2)
    @tag("mixed", "audit")
    def audit_logs(self):
        """Get recent audit logs."""
        self.client.get("/api/audit/logs?limit=20", name="/api/audit/logs")

    @task(1)
    @tag("mixed", "schema")
    def schema_bindings(self):
        """Get schema bindings."""
        self.client.get("/api/schema/bindings", name="/api/schema/bindings")

    @task(1)
    @tag("mixed", "alerts")
    def alert_channels(self):
        """Get alert channels."""
        self.client.get("/api/alerts/channels", name="/api/alerts/channels")


# Event hooks for reporting
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("=" * 60)
    print("Load Test Starting")
    print(f"Target: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("=" * 60)
    print("Load Test Complete")
    print("=" * 60)


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track failed requests."""
    if exception:
        print(f"Request failed: {name} - {exception}")
