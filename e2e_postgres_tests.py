#!/usr/bin/env python3
"""
E2E Tests with PostgreSQL Database

Tests OntoGuard semantic validation + real SQL query execution.

Usage:
    python e2e_postgres_tests.py
"""

import requests
import json
import sys
from dataclasses import dataclass
from typing import Optional, Any, List
from enum import Enum


# Configuration
BASE_URL = "http://localhost:5000/api"
POSTGRES_CONFIG = {
    "type": "postgresql",
    "host": "localhost",
    "port": 5433,  # Our PostgreSQL is on 5433
    "database": "hospital_db",
    "user": "uac_user",
    "password": "uac_password"
}


class TestStatus(Enum):
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    ERROR = "⚠️ ERROR"


@dataclass
class TestResult:
    test_id: str
    description: str
    status: TestStatus
    expected: str
    actual: str
    details: Optional[str] = None


class E2ETestRunner:
    """E2E test runner with PostgreSQL."""

    def __init__(self):
        self.results: List[TestResult] = []
        self.agents = {}  # agent_id -> api_key

    def register_agent(self, agent_id: str, name: str, role: str) -> Optional[str]:
        """Register an agent with PostgreSQL database."""
        response = requests.post(
            f"{BASE_URL}/agents/register",
            json={
                "agent_id": agent_id,
                "agent_info": {
                    "name": name,
                    "role": role
                },
                # agent_credentials required when linking database (api_key, api_secret format)
                "agent_credentials": {
                    "api_key": f"{agent_id}-key",
                    "api_secret": f"{agent_id}-secret"
                },
                "database": POSTGRES_CONFIG
            }
        )

        # API returns 201 for created resources
        if response.status_code in (200, 201):
            data = response.json()
            api_key = data.get("api_key")
            # Check if database was linked
            if data.get("database"):
                self.agents[agent_id] = api_key
                print(f"  ✅ Registered {agent_id} ({role}) with database")
                return api_key
            else:
                # Still registered, but without database - store api_key anyway
                self.agents[agent_id] = api_key
                print(f"  ⚠️ Registered {agent_id} ({role}) but database not linked")
                return api_key
        else:
            print(f"  ❌ Failed to register {agent_id}: {response.json()}")
            return None

    def grant_permission(self, agent_id: str, resource: str, permissions: list) -> bool:
        """Grant permissions to agent for a resource."""
        response = requests.put(
            f"{BASE_URL}/agents/{agent_id}/permissions/resources",
            json={
                "resource_id": resource,
                "permissions": permissions
            }
        )
        return response.status_code == 200

    def execute_query(self, agent_id: str, query: str, role: str) -> dict:
        """Execute SQL query as agent with role."""
        api_key = self.agents.get(agent_id)
        if not api_key:
            return {"error": f"Agent {agent_id} not registered"}

        response = requests.post(
            f"{BASE_URL}/agents/{agent_id}/query",
            headers={
                "X-API-Key": api_key,
                "X-User-Role": role
            },
            json={"query": query}
        )

        return {
            "status_code": response.status_code,
            "data": response.json()
        }

    def run_test(self, test_id: str, description: str, agent_id: str,
                 role: str, query: str, expected_allowed: bool) -> TestResult:
        """Run a single test case."""
        result = self.execute_query(agent_id, query, role)

        # Check result - handle case when agent not registered
        if "error" in result and "status_code" not in result:
            # Agent registration error
            return TestResult(
                test_id=test_id,
                description=description,
                status=TestStatus.ERROR,
                expected="ALLOWED" if expected_allowed else "DENIED",
                actual=f"ERROR: {result['error']}",
                details="Agent not properly registered"
            )

        is_allowed = result.get("status_code") == 200

        if is_allowed == expected_allowed:
            status = TestStatus.PASSED
        else:
            status = TestStatus.FAILED

        expected = "ALLOWED" if expected_allowed else "DENIED"
        if is_allowed:
            actual = "ALLOWED"
        else:
            error_msg = result['data'].get('error', 'Unknown')
            message = result['data'].get('message', '')
            reason = result['data'].get('reason', '')
            actual = f"DENIED ({error_msg}: {message or reason})"

        # Get details for denied requests
        details = None
        if not is_allowed:
            data = result["data"]
            if "reason" in data:
                details = f"Reason: {data['reason']}"
            elif "constraints" in data:
                details = f"Constraints: {data['constraints']}"
        elif is_allowed:
            data = result["data"]
            if "row_count" in data:
                details = f"Rows returned: {data['row_count']}"

        test_result = TestResult(
            test_id=test_id,
            description=description,
            status=status,
            expected=expected,
            actual=actual,
            details=details
        )
        self.results.append(test_result)
        return test_result

    def setup_agents(self):
        """Register all test agents."""
        print("\n📋 Registering agents with PostgreSQL...")

        agents = [
            ("doctor-pg", "Dr. Smith", "Doctor"),
            ("nurse-pg", "Nurse Johnson", "Nurse"),
            ("admin-pg", "Admin User", "Admin"),
            ("labtech-pg", "Lab Tech", "LabTechnician"),
            ("receptionist-pg", "Front Desk", "Receptionist"),
        ]

        for agent_id, name, role in agents:
            self.register_agent(agent_id, name, role)

    def setup_permissions(self):
        """Grant permissions to agents."""
        print("\n🔐 Granting permissions...")

        # All agents get read, write, delete on common tables
        tables = ["patients", "medical_records", "lab_results", "appointments", "billing", "staff"]

        for agent_id in self.agents.keys():
            for table in tables:
                # Grant all permissions (read, write, delete) - OntoGuard will do semantic filtering
                self.grant_permission(agent_id, table, ["read", "write", "delete"])
            print(f"  ✅ Permissions granted to {agent_id}")

    def run_all_tests(self):
        """Run all E2E tests."""
        print("\n" + "=" * 70)
        print("E2E PostgreSQL Tests - OntoGuard + Real Database")
        print("=" * 70)

        # Setup
        self.setup_agents()
        self.setup_permissions()

        print("\n🧪 Running tests...\n")

        # Test Cases
        test_cases = [
            # === ALLOWED cases (should return data) ===
            ("E2E-01", "Doctor SELECT patients", "doctor-pg", "Doctor",
             "SELECT * FROM patients", True),

            ("E2E-02", "Admin SELECT all staff", "admin-pg", "Admin",
             "SELECT * FROM staff", True),

            ("E2E-03", "LabTech SELECT lab_results", "labtech-pg", "LabTechnician",
             "SELECT * FROM lab_results", True),

            ("E2E-04", "Receptionist SELECT appointments", "receptionist-pg", "Receptionist",
             "SELECT * FROM appointments WHERE status = 'scheduled'", True),

            ("E2E-05", "Nurse SELECT patients", "nurse-pg", "Nurse",
             "SELECT name, diagnosis FROM patients", True),

            ("E2E-06", "Admin DELETE staff (soft delete test)", "admin-pg", "Admin",
             "DELETE FROM staff WHERE id = 999", True),  # Non-existent ID, just testing permission

            # === DENIED cases (OntoGuard should block) ===
            ("E2E-07", "Nurse DELETE patients (no delete permission)", "nurse-pg", "Nurse",
             "DELETE FROM patients WHERE id = 1", False),

            ("E2E-08", "Receptionist DELETE medical_records (no delete)", "receptionist-pg", "Receptionist",
             "DELETE FROM medical_records WHERE id = 1", False),

            ("E2E-09", "LabTech DELETE lab_results (no delete)", "labtech-pg", "LabTechnician",
             "DELETE FROM lab_results WHERE id = 1", False),

            ("E2E-10", "Doctor UPDATE patients (OWL: no update for Doctor)", "doctor-pg", "Doctor",
             "UPDATE patients SET diagnosis = 'Updated' WHERE id = 1", False),

            # === More complex queries ===
            ("E2E-11", "Doctor SELECT with JOIN", "doctor-pg", "Doctor",
             """SELECT p.name, m.content
                FROM patients p
                JOIN medical_records m ON p.id = m.patient_id
                WHERE p.id = 1""", True),

            ("E2E-12", "Admin SELECT billing", "admin-pg", "Admin",
             "SELECT * FROM billing WHERE status = 'pending'", True),

            ("E2E-13", "Receptionist INSERT appointment", "receptionist-pg", "Receptionist",
             """INSERT INTO appointments (patient_id, doctor_id, appointment_date, status)
                VALUES (1, 1, '2026-02-15', 'scheduled')""", True),

            ("E2E-14", "Nurse INSERT patients (OWL: no create)", "nurse-pg", "Nurse",
             """INSERT INTO patients (name, date_of_birth, diagnosis)
                VALUES ('Test Patient', '2000-01-01', 'Test')""", False),

            ("E2E-15", "Admin UPDATE billing (OWL: can only update PatientRecord)", "admin-pg", "Admin",
             "UPDATE billing SET status = 'paid' WHERE id = 1", False),
        ]

        # Run tests
        for test_id, description, agent_id, role, query, expected in test_cases:
            result = self.run_test(test_id, description, agent_id, role, query, expected)

            status_icon = result.status.value
            print(f"  {status_icon} {test_id}: {description}")
            if result.details:
                print(f"       Details: {result.details}")

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        total = len(self.results)

        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"Pass Rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")

        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if r.status == TestStatus.FAILED:
                    print(f"  - {r.test_id}: {r.description}")
                    print(f"    Expected: {r.expected}, Got: {r.actual}")

        print("=" * 70)

        return passed == total


def check_server():
    """Check if server is running."""
    try:
        response = requests.get(f"{BASE_URL}/ontoguard/status", timeout=5)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


def main():
    # Check server
    print("🔍 Checking server status...")
    if not check_server():
        print("❌ Server is not running. Start it with: python main_simple.py")
        sys.exit(1)
    print("✅ Server is running")

    # Check database
    print("🔍 Checking PostgreSQL connection...")
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="hospital_db",
            user="uac_user",
            password="uac_password"
        )
        conn.close()
        print("✅ PostgreSQL is accessible")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   Make sure Docker container is running: docker-compose up -d")
        sys.exit(1)

    # Run tests
    runner = E2ETestRunner()
    success = runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
