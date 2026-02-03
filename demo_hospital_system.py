#!/usr/bin/env python3
"""
Hospital Management System Demo

Interactive demonstration of AI Agent Connector with:
- Hospital SQLite database (728 records)
- OntoGuard semantic validation
- Natural language query examples

Usage:
    python demo_hospital_system.py
"""

import json
import os
import sqlite3
import sys
from typing import Dict, Any, List, Optional

# Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "hospital.db")
QUESTIONS_PATH = os.path.join(DATA_DIR, "test_questions.json")


def load_questions() -> Dict[str, Any]:
    """Load test questions from JSON."""
    with open(QUESTIONS_PATH, 'r') as f:
        return json.load(f)


def get_db_connection() -> sqlite3.Connection:
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_subheader(title: str):
    """Print subsection header."""
    print(f"\n--- {title} ---")


def demo_database_stats():
    """Show database statistics."""
    print_header("DATABASE STATISTICS")

    conn = get_db_connection()
    cursor = conn.cursor()

    tables = [
        ("patients", "Patients"),
        ("staff", "Staff Members"),
        ("appointments", "Appointments"),
        ("medical_records", "Medical Records"),
        ("prescriptions", "Prescriptions"),
        ("lab_results", "Lab Results"),
        ("departments", "Departments"),
        ("rooms", "Hospital Rooms"),
        ("medications", "Medications"),
        ("billing", "Billing Records"),
        ("insurance", "Insurance Policies"),
        ("surgeries", "Surgeries"),
        ("emergency_cases", "Emergency Cases"),
        ("audit_log", "Audit Log Entries"),
        ("equipment", "Medical Equipment"),
    ]

    total = 0
    print(f"\n{'Table':<25} {'Records':>10}")
    print("-" * 36)

    for table, label in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total += count
        print(f"{label:<25} {count:>10}")

    print("-" * 36)
    print(f"{'TOTAL':<25} {total:>10}")

    conn.close()


def demo_sample_queries():
    """Demonstrate sample database queries."""
    print_header("SAMPLE QUERIES")

    conn = get_db_connection()
    cursor = conn.cursor()

    queries = [
        ("Top 5 Doctors by Appointments", """
            SELECT s.first_name || ' ' || s.last_name AS doctor,
                   s.specialization,
                   COUNT(a.id) AS appointments
            FROM staff s
            LEFT JOIN appointments a ON s.id = a.doctor_id
            WHERE s.role = 'Doctor'
            GROUP BY s.id
            ORDER BY appointments DESC
            LIMIT 5
        """),

        ("Most Common Diagnoses", """
            SELECT diagnosis, COUNT(*) AS count
            FROM medical_records
            WHERE diagnosis IS NOT NULL
            GROUP BY diagnosis
            ORDER BY count DESC
            LIMIT 5
        """),

        ("Department Statistics", """
            SELECT d.name AS department,
                   COUNT(DISTINCT s.id) AS staff_count,
                   COUNT(DISTINCT a.id) AS appointments
            FROM departments d
            LEFT JOIN staff s ON d.id = s.department_id
            LEFT JOIN appointments a ON d.id = a.department_id
            GROUP BY d.id
            ORDER BY appointments DESC
            LIMIT 5
        """),

        ("Emergency Case Triage Distribution", """
            SELECT triage_level,
                   COUNT(*) AS cases,
                   status
            FROM emergency_cases
            GROUP BY triage_level, status
            ORDER BY triage_level, status
        """),

        ("Prescription Status Summary", """
            SELECT status,
                   COUNT(*) AS count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM prescriptions), 1) AS percentage
            FROM prescriptions
            GROUP BY status
        """),
    ]

    for title, query in queries:
        print_subheader(title)
        try:
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                # Get column names
                columns = [description[0] for description in cursor.description]
                print("  " + " | ".join(f"{col:<15}" for col in columns))
                print("  " + "-" * (17 * len(columns)))

                for row in results:
                    print("  " + " | ".join(f"{str(val):<15}" for val in row))
            else:
                print("  No results")

        except Exception as e:
            print(f"  Error: {e}")

    conn.close()


def demo_role_permissions():
    """Demonstrate role-based permissions."""
    print_header("ROLE-BASED ACCESS CONTROL")

    roles = {
        "Admin": {
            "can_do": ["Full access to all resources", "Delete patient records", "Access audit logs", "Export data"],
            "cannot_do": ["N/A - Admin has full access"]
        },
        "Doctor": {
            "can_do": ["Read patient/medical records", "Create prescriptions", "Update medical records", "Schedule surgeries"],
            "cannot_do": ["Delete patient records", "Access audit logs", "Create patients"]
        },
        "Nurse": {
            "can_do": ["Read patient/medical records", "Update vitals", "Read prescriptions", "Update room status"],
            "cannot_do": ["Create prescriptions", "Prescribe medications", "Delete records"]
        },
        "Receptionist": {
            "can_do": ["Create patient records", "Schedule appointments", "Read basic patient info"],
            "cannot_do": ["Access medical records", "Read prescriptions", "View lab results"]
        },
        "Patient": {
            "can_do": ["View own records", "Schedule appointments", "View own prescriptions"],
            "cannot_do": ["View other patients", "Delete records", "Create prescriptions"]
        },
        "LabTechnician": {
            "can_do": ["Create/update lab results", "Read equipment status"],
            "cannot_do": ["Access medical records", "Read prescriptions"]
        },
        "Pharmacist": {
            "can_do": ["Read prescriptions", "Dispense medications", "Update inventory"],
            "cannot_do": ["Create prescriptions", "Prescribe medications"]
        },
        "InsuranceAgent": {
            "can_do": ["Read billing info", "Approve claims", "Read insurance details"],
            "cannot_do": ["Access medical records", "View prescriptions"]
        },
    }

    for role, permissions in roles.items():
        print(f"\n{role}:")
        print(f"  CAN do:")
        for item in permissions["can_do"]:
            print(f"    + {item}")
        print(f"  CANNOT do:")
        for item in permissions["cannot_do"]:
            print(f"    - {item}")


def demo_test_questions():
    """Show sample test questions."""
    print_header("TEST QUESTIONS BANK")

    questions = load_questions()

    categories = [
        ("simple_queries", "Simple Queries", 3),
        ("complex_analytics", "Complex Analytics", 3),
        ("permission_checks", "Permission Checks", 3),
        ("natural_language", "Natural Language", 3),
        ("hipaa_compliance", "HIPAA Compliance", 2),
    ]

    for cat_key, cat_name, limit in categories:
        if cat_key in questions:
            print_subheader(cat_name)
            items = questions[cat_key].get("questions", [])[:limit]
            for i, item in enumerate(items, 1):
                q = item.get("question") or item.get("scenario", "N/A")
                print(f"  {i}. {q}")
                if "expected_sql" in item:
                    print(f"     SQL: {item['expected_sql'][:60]}...")
                if "expected_validation" in item:
                    v = item["expected_validation"]
                    print(f"     Check: {v.get('role', '?')} -> {v.get('action', '?')} {v.get('entity_type', '?')}")


def demo_hipaa_compliance():
    """Demonstrate HIPAA compliance features."""
    print_header("HIPAA COMPLIANCE")

    conn = get_db_connection()
    cursor = conn.cursor()

    print_subheader("Sensitive Data Protection")

    # Sensitive records
    cursor.execute("SELECT COUNT(*) FROM medical_records WHERE is_sensitive = 1")
    sensitive_count = cursor.fetchone()[0]
    print(f"  Sensitive medical records: {sensitive_count}")

    # PHI fields
    print("\n  Protected Health Information (PHI) fields:")
    print("    - SSN (Social Security Number)")
    print("    - Medical diagnosis")
    print("    - Prescription details")
    print("    - Lab results")

    print_subheader("Audit Logging")

    # Audit log stats
    cursor.execute("""
        SELECT action, COUNT(*) as count
        FROM audit_log
        GROUP BY action
        ORDER BY count DESC
    """)
    audit_stats = cursor.fetchall()

    print("  Audit log by action type:")
    for action, count in audit_stats:
        print(f"    {action}: {count}")

    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM audit_log
        GROUP BY status
    """)
    status_stats = cursor.fetchall()

    print("\n  Audit log by status:")
    for status, count in status_stats:
        print(f"    {status}: {count}")

    print_subheader("Access Control")
    print("  - Role-based access control (RBAC)")
    print("  - Minimum necessary access principle")
    print("  - Audit trail for all PHI access")
    print("  - Denied access logging")

    conn.close()


def demo_api_endpoints():
    """Show available API endpoints."""
    print_header("API ENDPOINTS")

    endpoints = [
        ("GET", "/api/ontoguard/status", "Check OntoGuard status"),
        ("POST", "/api/ontoguard/validate", "Validate action against rules"),
        ("POST", "/api/ontoguard/permissions", "Check role permissions"),
        ("GET", "/api/ontoguard/allowed-actions", "Get allowed actions for role"),
        ("POST", "/api/ontoguard/explain", "Explain rule for action"),
    ]

    print("\nOntoGuard Integration API:")
    print(f"\n{'Method':<8} {'Endpoint':<35} {'Description'}")
    print("-" * 70)

    for method, endpoint, desc in endpoints:
        print(f"{method:<8} {endpoint:<35} {desc}")

    print("\nExample Usage:")
    print("""
  # Validate action
  curl -X POST http://localhost:5001/api/ontoguard/validate \\
       -H "Content-Type: application/json" \\
       -d '{"action": "read", "entity_type": "MedicalRecord", "context": {"role": "Doctor"}}'

  # Check permissions
  curl -X POST http://localhost:5001/api/ontoguard/permissions \\
       -H "Content-Type: application/json" \\
       -d '{"role": "Nurse", "action": "prescribe", "entity_type": "Prescription"}'
    """)


def main():
    """Main demo function."""
    print("\n" + "=" * 60)
    print(" HOSPITAL MANAGEMENT SYSTEM")
    print(" AI Agent Connector Integration Demo")
    print("=" * 60)

    # Check prerequisites
    if not os.path.exists(DB_PATH):
        print(f"\nERROR: Database not found: {DB_PATH}")
        print("Run: python data/setup_hospital_db.py")
        sys.exit(1)

    if not os.path.exists(QUESTIONS_PATH):
        print(f"\nERROR: Questions file not found: {QUESTIONS_PATH}")
        sys.exit(1)

    # Run demos
    demo_database_stats()
    demo_sample_queries()
    demo_role_permissions()
    demo_test_questions()
    demo_hipaa_compliance()
    demo_api_endpoints()

    print_header("DEMO COMPLETE")
    print("""
Files created:
  - ontologies/hospital.owl        (OWL ontology with RBAC rules)
  - data/hospital.db               (SQLite database, 728 records)
  - data/test_questions.json       (75 test questions)
  - config/hospital_ontoguard.yaml (OntoGuard configuration)
  - tests/test_hospital_scenarios.py (Comprehensive test suite)
  - run_hospital_tests.py          (Integration test runner)

To run tests:
  python run_hospital_tests.py --verbose

To start server:
  python main_simple.py
    """)


if __name__ == "__main__":
    main()
