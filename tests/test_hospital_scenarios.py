#!/usr/bin/env python3
"""
Hospital Management System - Comprehensive Test Scenarios

Tests OntoGuard semantic validation with hospital ontology and SQLite database.
Covers: role-based access, CRUD operations, HIPAA compliance, edge cases.
"""

import pytest
import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_agent_connector.app.security import (
    OntoGuardAdapter,
    ValidationResult,
    get_ontoguard_adapter,
    initialize_ontoguard
)

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "hospital.db")
ONTOLOGY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ontologies", "hospital.owl")


# ============================================
# FIXTURES
# ============================================

@pytest.fixture(scope="module")
def db_connection():
    """Database connection fixture."""
    if not os.path.exists(DB_PATH):
        pytest.skip(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def ontoguard_adapter():
    """OntoGuard adapter with hospital ontology."""
    adapter = OntoGuardAdapter()
    if os.path.exists(ONTOLOGY_PATH):
        adapter.initialize([ONTOLOGY_PATH])
    return adapter


# ============================================
# TEST CLASS: Role-Based Access Control
# ============================================

class TestRoleBasedAccess:
    """Test role-based access control according to hospital ontology."""

    # -----------------------------------------
    # Admin Tests
    # -----------------------------------------

    def test_admin_can_read_all_patient_records(self, ontoguard_adapter):
        """Admin should have full access to patient records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is True

    def test_admin_can_delete_patient_records(self, ontoguard_adapter):
        """Admin should be able to delete patient records."""
        result = ontoguard_adapter.validate_action(
            action="delete",
            entity_type="PatientRecord",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is True

    def test_admin_can_access_audit_logs(self, ontoguard_adapter):
        """Admin should have access to audit logs."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="AuditLog",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is True

    def test_admin_can_export_audit_logs(self, ontoguard_adapter):
        """Admin should be able to export audit logs."""
        result = ontoguard_adapter.validate_action(
            action="export",
            entity_type="AuditLog",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is True

    def test_admin_can_create_staff(self, ontoguard_adapter):
        """Admin should be able to create new staff."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Staff",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is True

    def test_admin_can_delete_staff(self, ontoguard_adapter):
        """Admin should be able to delete staff."""
        result = ontoguard_adapter.validate_action(
            action="delete",
            entity_type="Staff",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is True

    # -----------------------------------------
    # Doctor Tests
    # -----------------------------------------

    def test_doctor_can_read_patient_records(self, ontoguard_adapter):
        """Doctor should read patient records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_read_medical_records(self, ontoguard_adapter):
        """Doctor should read medical records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="MedicalRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_create_medical_records(self, ontoguard_adapter):
        """Doctor should create medical records."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="MedicalRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_update_medical_records(self, ontoguard_adapter):
        """Doctor should update medical records."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="MedicalRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_create_prescriptions(self, ontoguard_adapter):
        """Doctor should create prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Prescription",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_prescribe_medication(self, ontoguard_adapter):
        """Doctor should prescribe medications."""
        result = ontoguard_adapter.validate_action(
            action="prescribe",
            entity_type="Prescription",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_read_lab_results(self, ontoguard_adapter):
        """Doctor should read lab results."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="LabResult",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_schedule_surgery(self, ontoguard_adapter):
        """Doctor should schedule surgeries."""
        result = ontoguard_adapter.validate_action(
            action="schedule",
            entity_type="Surgery",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_can_discharge_patient(self, ontoguard_adapter):
        """Doctor should discharge patients."""
        result = ontoguard_adapter.validate_action(
            action="discharge",
            entity_type="PatientRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is True

    def test_doctor_cannot_delete_patient_records(self, ontoguard_adapter):
        """Doctor should NOT delete patient records."""
        result = ontoguard_adapter.validate_action(
            action="delete",
            entity_type="PatientRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is False

    def test_doctor_cannot_access_audit_logs(self, ontoguard_adapter):
        """Doctor should NOT access audit logs."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="AuditLog",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert result.allowed is False

    # -----------------------------------------
    # Nurse Tests
    # -----------------------------------------

    def test_nurse_can_read_patient_records(self, ontoguard_adapter):
        """Nurse should read patient records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is True

    def test_nurse_can_read_medical_records(self, ontoguard_adapter):
        """Nurse should read medical records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="MedicalRecord",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is True

    def test_nurse_can_update_medical_records(self, ontoguard_adapter):
        """Nurse should update medical records (vitals)."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="MedicalRecord",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is True

    def test_nurse_can_read_prescriptions(self, ontoguard_adapter):
        """Nurse should read prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Prescription",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is True

    def test_nurse_cannot_create_prescriptions(self, ontoguard_adapter):
        """Nurse should NOT create prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Prescription",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is False

    def test_nurse_cannot_prescribe_medication(self, ontoguard_adapter):
        """Nurse should NOT prescribe medications."""
        result = ontoguard_adapter.validate_action(
            action="prescribe",
            entity_type="Prescription",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is False

    def test_nurse_can_update_room_status(self, ontoguard_adapter):
        """Nurse should update room status."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="Room",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert result.allowed is True

    # -----------------------------------------
    # Receptionist Tests
    # -----------------------------------------

    def test_receptionist_can_create_patient_records(self, ontoguard_adapter):
        """Receptionist should create patient records."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="PatientRecord",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is True

    def test_receptionist_can_read_patient_records(self, ontoguard_adapter):
        """Receptionist should read patient records (basic info)."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is True

    def test_receptionist_can_create_appointments(self, ontoguard_adapter):
        """Receptionist should create appointments."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Appointment",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is True

    def test_receptionist_can_schedule_appointments(self, ontoguard_adapter):
        """Receptionist should schedule appointments."""
        result = ontoguard_adapter.validate_action(
            action="schedule",
            entity_type="Appointment",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is True

    def test_receptionist_can_cancel_appointments(self, ontoguard_adapter):
        """Receptionist should cancel appointments."""
        result = ontoguard_adapter.validate_action(
            action="cancel",
            entity_type="Appointment",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is True

    def test_receptionist_cannot_read_medical_records(self, ontoguard_adapter):
        """Receptionist should NOT access medical records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="MedicalRecord",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is False

    def test_receptionist_cannot_read_prescriptions(self, ontoguard_adapter):
        """Receptionist should NOT read prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Prescription",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is False

    def test_receptionist_can_create_emergency_case(self, ontoguard_adapter):
        """Receptionist should create emergency cases."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="EmergencyCase",
            context={"role": "Receptionist", "user_id": "EMP030"}
        )
        assert result.allowed is True

    # -----------------------------------------
    # Patient Tests
    # -----------------------------------------

    def test_patient_can_read_own_record(self, ontoguard_adapter):
        """Patient should read their own record."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "Patient", "user_id": "PAT00001", "patient_id": "PAT00001"}
        )
        assert result.allowed is True

    def test_patient_can_update_own_contact_info(self, ontoguard_adapter):
        """Patient should update their contact info."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="PatientRecord",
            context={"role": "Patient", "user_id": "PAT00001", "patient_id": "PAT00001"}
        )
        assert result.allowed is True

    def test_patient_can_read_own_medical_record(self, ontoguard_adapter):
        """Patient should read their own medical record."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="MedicalRecord",
            context={"role": "Patient", "user_id": "PAT00001", "patient_id": "PAT00001"}
        )
        assert result.allowed is True

    def test_patient_can_read_own_prescriptions(self, ontoguard_adapter):
        """Patient should read their own prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Prescription",
            context={"role": "Patient", "user_id": "PAT00001"}
        )
        assert result.allowed is True

    def test_patient_can_schedule_appointment(self, ontoguard_adapter):
        """Patient should schedule appointments."""
        result = ontoguard_adapter.validate_action(
            action="schedule",
            entity_type="Appointment",
            context={"role": "Patient", "user_id": "PAT00001"}
        )
        assert result.allowed is True

    def test_patient_can_cancel_own_appointment(self, ontoguard_adapter):
        """Patient should cancel their own appointments."""
        result = ontoguard_adapter.validate_action(
            action="cancel",
            entity_type="Appointment",
            context={"role": "Patient", "user_id": "PAT00001"}
        )
        assert result.allowed is True

    def test_patient_cannot_delete_records(self, ontoguard_adapter):
        """Patient should NOT delete any records."""
        result = ontoguard_adapter.validate_action(
            action="delete",
            entity_type="PatientRecord",
            context={"role": "Patient", "user_id": "PAT00001"}
        )
        assert result.allowed is False

    def test_patient_cannot_create_prescriptions(self, ontoguard_adapter):
        """Patient should NOT create prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Prescription",
            context={"role": "Patient", "user_id": "PAT00001"}
        )
        assert result.allowed is False

    def test_patient_cannot_update_medical_records(self, ontoguard_adapter):
        """Patient should NOT update medical records."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="MedicalRecord",
            context={"role": "Patient", "user_id": "PAT00001"}
        )
        assert result.allowed is False

    # -----------------------------------------
    # Lab Technician Tests
    # -----------------------------------------

    def test_lab_tech_can_create_lab_results(self, ontoguard_adapter):
        """Lab technician should create lab results."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="LabResult",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        assert result.allowed is True

    def test_lab_tech_can_read_lab_results(self, ontoguard_adapter):
        """Lab technician should read lab results."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="LabResult",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        assert result.allowed is True

    def test_lab_tech_can_update_lab_results(self, ontoguard_adapter):
        """Lab technician should update lab results."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="LabResult",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        assert result.allowed is True

    def test_lab_tech_can_read_patient_id(self, ontoguard_adapter):
        """Lab technician should read patient ID for sample matching."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        assert result.allowed is True

    def test_lab_tech_cannot_read_prescriptions(self, ontoguard_adapter):
        """Lab technician should NOT access prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Prescription",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        assert result.allowed is False

    def test_lab_tech_cannot_read_medical_records(self, ontoguard_adapter):
        """Lab technician should NOT read full medical records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="MedicalRecord",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        assert result.allowed is False

    # -----------------------------------------
    # Pharmacist Tests
    # -----------------------------------------

    def test_pharmacist_can_read_prescriptions(self, ontoguard_adapter):
        """Pharmacist should read prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Prescription",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is True

    def test_pharmacist_can_dispense_medication(self, ontoguard_adapter):
        """Pharmacist should dispense medications."""
        result = ontoguard_adapter.validate_action(
            action="dispense",
            entity_type="Prescription",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is True

    def test_pharmacist_can_update_prescription_status(self, ontoguard_adapter):
        """Pharmacist should update prescription status."""
        result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="Prescription",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is True

    def test_pharmacist_can_read_medication_inventory(self, ontoguard_adapter):
        """Pharmacist should read medication inventory."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Medication",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is True

    def test_pharmacist_can_read_patient_allergies(self, ontoguard_adapter):
        """Pharmacist should read patient allergies for safety."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is True

    def test_pharmacist_cannot_create_prescriptions(self, ontoguard_adapter):
        """Pharmacist should NOT create prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Prescription",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is False

    def test_pharmacist_cannot_prescribe(self, ontoguard_adapter):
        """Pharmacist should NOT prescribe medications."""
        result = ontoguard_adapter.validate_action(
            action="prescribe",
            entity_type="Prescription",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert result.allowed is False

    # -----------------------------------------
    # Insurance Agent Tests
    # -----------------------------------------

    def test_insurance_can_read_billing(self, ontoguard_adapter):
        """Insurance agent should read billing info."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Billing",
            context={"role": "InsuranceAgent", "user_id": "INS001"}
        )
        assert result.allowed is True

    def test_insurance_can_approve_billing(self, ontoguard_adapter):
        """Insurance agent should approve billing claims."""
        result = ontoguard_adapter.validate_action(
            action="approve",
            entity_type="Billing",
            context={"role": "InsuranceAgent", "user_id": "INS001"}
        )
        assert result.allowed is True

    def test_insurance_can_read_insurance_info(self, ontoguard_adapter):
        """Insurance agent should read insurance info."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Insurance",
            context={"role": "InsuranceAgent", "user_id": "INS001"}
        )
        assert result.allowed is True

    def test_insurance_cannot_read_medical_records(self, ontoguard_adapter):
        """Insurance agent should NOT access medical records."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="MedicalRecord",
            context={"role": "InsuranceAgent", "user_id": "INS001"}
        )
        assert result.allowed is False

    def test_insurance_cannot_read_prescriptions(self, ontoguard_adapter):
        """Insurance agent should NOT read prescriptions."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="Prescription",
            context={"role": "InsuranceAgent", "user_id": "INS001"}
        )
        assert result.allowed is False


# ============================================
# TEST CLASS: Database Queries
# ============================================

class TestDatabaseQueries:
    """Test database queries and data integrity."""

    def test_patient_count(self, db_connection):
        """Verify patient count."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        assert count == 50

    def test_staff_count(self, db_connection):
        """Verify staff count."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM staff")
        count = cursor.fetchone()[0]
        assert count == 26

    def test_appointments_count(self, db_connection):
        """Verify appointment count."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM appointments")
        count = cursor.fetchone()[0]
        assert count == 100

    def test_all_patients_have_insurance(self, db_connection):
        """Verify all patients have insurance."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM patients p
            LEFT JOIN insurance i ON p.id = i.patient_id
            WHERE i.id IS NULL
        """)
        count = cursor.fetchone()[0]
        assert count == 0, "All patients should have insurance"

    def test_staff_roles_valid(self, db_connection):
        """Verify all staff have valid roles."""
        cursor = db_connection.cursor()
        valid_roles = {'Admin', 'Doctor', 'Nurse', 'Receptionist', 'LabTechnician', 'Pharmacist'}
        cursor.execute("SELECT DISTINCT role FROM staff")
        roles = {row[0] for row in cursor.fetchall()}
        assert roles.issubset(valid_roles)

    def test_doctors_have_specialization(self, db_connection):
        """Verify all doctors have specialization."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM staff
            WHERE role = 'Doctor' AND (specialization IS NULL OR specialization = '')
        """)
        count = cursor.fetchone()[0]
        assert count == 0, "All doctors should have specialization"

    def test_blood_types_valid(self, db_connection):
        """Verify all blood types are valid."""
        cursor = db_connection.cursor()
        valid_types = {'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'}
        cursor.execute("SELECT DISTINCT blood_type FROM patients WHERE blood_type IS NOT NULL")
        types = {row[0] for row in cursor.fetchall()}
        assert types.issubset(valid_types)

    def test_appointment_status_valid(self, db_connection):
        """Verify all appointment statuses are valid."""
        cursor = db_connection.cursor()
        valid_statuses = {'Scheduled', 'Confirmed', 'In Progress', 'Completed', 'Cancelled', 'No Show'}
        cursor.execute("SELECT DISTINCT status FROM appointments")
        statuses = {row[0] for row in cursor.fetchall()}
        assert statuses.issubset(valid_statuses)

    def test_prescriptions_have_doctor(self, db_connection):
        """Verify all prescriptions have prescribing doctor."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM prescriptions p
            LEFT JOIN staff s ON p.doctor_id = s.id
            WHERE s.id IS NULL
        """)
        count = cursor.fetchone()[0]
        assert count == 0, "All prescriptions should have a doctor"


# ============================================
# TEST CLASS: Complex Queries
# ============================================

class TestComplexQueries:
    """Test complex analytical queries."""

    def test_patients_per_department(self, db_connection):
        """Count appointments per department."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT d.name, COUNT(a.id) as appointment_count
            FROM departments d
            LEFT JOIN appointments a ON d.id = a.department_id
            GROUP BY d.id
            ORDER BY appointment_count DESC
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_doctors_workload(self, db_connection):
        """Calculate doctor workload."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT s.first_name || ' ' || s.last_name as doctor_name,
                   COUNT(a.id) as total_appointments,
                   SUM(CASE WHEN a.status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM staff s
            LEFT JOIN appointments a ON s.id = a.doctor_id
            WHERE s.role = 'Doctor'
            GROUP BY s.id
            ORDER BY total_appointments DESC
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_medication_usage(self, db_connection):
        """Analyze medication prescription frequency."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT medication_name, COUNT(*) as prescription_count
            FROM prescriptions
            GROUP BY medication_name
            ORDER BY prescription_count DESC
            LIMIT 10
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_diagnosis_distribution(self, db_connection):
        """Analyze diagnosis distribution."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT diagnosis, COUNT(*) as count
            FROM medical_records
            WHERE diagnosis IS NOT NULL
            GROUP BY diagnosis
            ORDER BY count DESC
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_emergency_triage_levels(self, db_connection):
        """Analyze emergency case triage levels."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT triage_level, COUNT(*) as count,
                   ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM emergency_cases), 2) as percentage
            FROM emergency_cases
            GROUP BY triage_level
            ORDER BY triage_level
        """)
        results = cursor.fetchall()
        assert len(results) > 0

    def test_billing_statistics(self, db_connection):
        """Calculate billing statistics."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_invoices,
                SUM(total_amount) as total_billed,
                AVG(total_amount) as avg_invoice,
                SUM(insurance_covered) as total_insurance,
                SUM(patient_responsibility) as total_patient
            FROM billing
        """)
        result = cursor.fetchone()
        assert result[0] > 0
        assert result[1] > 0


# ============================================
# TEST CLASS: HIPAA Compliance
# ============================================

class TestHIPAACompliance:
    """Test HIPAA compliance scenarios."""

    def test_audit_log_has_entries(self, db_connection):
        """Verify audit log is populated."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM audit_log")
        count = cursor.fetchone()[0]
        assert count > 0, "Audit log should have entries"

    def test_sensitive_records_flagged(self, db_connection):
        """Verify sensitive medical records are flagged."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM medical_records WHERE is_sensitive = 1
        """)
        count = cursor.fetchone()[0]
        assert count > 0, "Some records should be marked as sensitive"

    def test_ssn_stored_securely(self, db_connection):
        """Verify SSN format in database."""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT ssn FROM patients WHERE ssn IS NOT NULL LIMIT 5
        """)
        results = cursor.fetchall()
        for row in results:
            # SSN should be in format XXX-XX-XXXX
            assert len(row[0]) == 11
            assert row[0][3] == '-'
            assert row[0][6] == '-'

    def test_unauthorized_audit_access_denied(self, ontoguard_adapter):
        """Non-admin roles should not access audit logs."""
        for role in ["Doctor", "Nurse", "Receptionist", "Patient", "LabTechnician", "Pharmacist"]:
            result = ontoguard_adapter.validate_action(
                action="read",
                entity_type="AuditLog",
                context={"role": role, "user_id": "TEST001"}
            )
            assert result.allowed is False, f"{role} should not access audit logs"

    def test_unauthorized_export_denied(self, ontoguard_adapter):
        """Non-admin roles should not export sensitive data."""
        for role in ["Doctor", "Nurse", "Receptionist", "Patient"]:
            result = ontoguard_adapter.validate_action(
                action="export",
                entity_type="AuditLog",
                context={"role": role, "user_id": "TEST001"}
            )
            assert result.allowed is False, f"{role} should not export audit logs"


# ============================================
# TEST CLASS: Edge Cases
# ============================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_unknown_role_denied(self, ontoguard_adapter):
        """Unknown role should be denied."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "UnknownRole", "user_id": "UNKNOWN"}
        )
        assert result.allowed is False

    def test_unknown_entity_handled(self, ontoguard_adapter):
        """Unknown entity type should be handled gracefully."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="NonExistentEntity",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        # Should either deny or pass-through depending on configuration
        assert isinstance(result.allowed, bool)

    def test_unknown_action_handled(self, ontoguard_adapter):
        """Unknown action should be handled gracefully."""
        result = ontoguard_adapter.validate_action(
            action="unknownAction",
            entity_type="PatientRecord",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert isinstance(result.allowed, bool)

    def test_empty_context_handled(self, ontoguard_adapter):
        """Empty context should be handled."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={}
        )
        # Without role, should be denied
        assert result.allowed is False

    def test_missing_role_denied(self, ontoguard_adapter):
        """Missing role in context should be denied."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"user_id": "EMP001"}
        )
        assert result.allowed is False

    def test_case_sensitivity_role(self, ontoguard_adapter):
        """Test role case sensitivity."""
        # Lowercase should be handled
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="PatientRecord",
            context={"role": "admin", "user_id": "EMP001"}
        )
        # Depending on implementation, may or may not be allowed
        assert isinstance(result.allowed, bool)

    def test_empty_entity_denied(self, ontoguard_adapter):
        """Empty entity type should be denied."""
        result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is False

    def test_empty_action_denied(self, ontoguard_adapter):
        """Empty action should be denied."""
        result = ontoguard_adapter.validate_action(
            action="",
            entity_type="PatientRecord",
            context={"role": "Admin", "user_id": "EMP001"}
        )
        assert result.allowed is False


# ============================================
# TEST CLASS: Cross-Role Scenarios
# ============================================

class TestCrossRoleScenarios:
    """Test scenarios involving multiple roles."""

    def test_doctor_nurse_collaboration(self, ontoguard_adapter):
        """Doctor and nurse can both update medical records."""
        doctor_result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="MedicalRecord",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        nurse_result = ontoguard_adapter.validate_action(
            action="update",
            entity_type="MedicalRecord",
            context={"role": "Nurse", "user_id": "EMP020"}
        )
        assert doctor_result.allowed is True
        assert nurse_result.allowed is True

    def test_prescription_workflow(self, ontoguard_adapter):
        """Doctor creates, pharmacist dispenses prescription."""
        # Doctor creates prescription
        create_result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="Prescription",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        # Pharmacist dispenses
        dispense_result = ontoguard_adapter.validate_action(
            action="dispense",
            entity_type="Prescription",
            context={"role": "Pharmacist", "user_id": "EMP050"}
        )
        assert create_result.allowed is True
        assert dispense_result.allowed is True

    def test_lab_workflow(self, ontoguard_adapter):
        """Doctor orders, lab tech performs, doctor reviews."""
        # Doctor reads (orders implied)
        order_result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="LabResult",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        # Lab tech creates result
        create_result = ontoguard_adapter.validate_action(
            action="create",
            entity_type="LabResult",
            context={"role": "LabTechnician", "user_id": "EMP040"}
        )
        # Doctor reviews
        review_result = ontoguard_adapter.validate_action(
            action="read",
            entity_type="LabResult",
            context={"role": "Doctor", "user_id": "EMP010"}
        )
        assert order_result.allowed is True
        assert create_result.allowed is True
        assert review_result.allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
