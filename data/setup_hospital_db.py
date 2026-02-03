#!/usr/bin/env python3
"""
Hospital Management System - Database Setup and Test Data Generation

Creates SQLite database with comprehensive test data for AI Agent Connector testing.
Includes: patients, staff, appointments, medical records, prescriptions, etc.
"""

import sqlite3
import os
from datetime import datetime, date, timedelta
import random
from typing import List, Tuple

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "hospital.db")


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all database tables."""
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # ============================================
    # CORE TABLES
    # ============================================

    # Departments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL UNIQUE,
            floor INTEGER,
            phone TEXT,
            head_doctor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Staff (Doctors, Nurses, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('Admin', 'Doctor', 'Nurse', 'Receptionist', 'LabTechnician', 'Pharmacist')),
            department_id INTEGER,
            email TEXT UNIQUE,
            phone TEXT,
            specialization TEXT,
            license_number TEXT,
            hire_date DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)

    # Patients
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL UNIQUE,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth DATE NOT NULL,
            gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
            ssn TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            blood_type TEXT CHECK(blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
            allergies TEXT,
            insurance_provider TEXT,
            insurance_policy_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Appointments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            department_id INTEGER,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            duration_minutes INTEGER DEFAULT 30,
            status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Confirmed', 'In Progress', 'Completed', 'Cancelled', 'No Show')),
            type TEXT CHECK(type IN ('Consultation', 'Follow-up', 'Emergency', 'Routine Check', 'Surgery Prep', 'Lab Work')),
            reason TEXT,
            notes TEXT,
            room_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES staff(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)

    # Medical Records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            visit_date DATE NOT NULL,
            chief_complaint TEXT,
            diagnosis TEXT,
            diagnosis_code TEXT,
            symptoms TEXT,
            vital_signs TEXT,
            treatment_plan TEXT,
            notes TEXT,
            follow_up_date DATE,
            is_sensitive BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES staff(id)
        )
    """)

    # Prescriptions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            medical_record_id INTEGER,
            medication_name TEXT NOT NULL,
            dosage TEXT NOT NULL,
            frequency TEXT NOT NULL,
            duration_days INTEGER,
            quantity INTEGER,
            refills_allowed INTEGER DEFAULT 0,
            refills_remaining INTEGER DEFAULT 0,
            instructions TEXT,
            status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Dispensed', 'Cancelled', 'Expired', 'On Hold')),
            dispensed_by INTEGER,
            dispensed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (doctor_id) REFERENCES staff(id),
            FOREIGN KEY (medical_record_id) REFERENCES medical_records(id),
            FOREIGN KEY (dispensed_by) REFERENCES staff(id)
        )
    """)

    # Lab Results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lab_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            result_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER NOT NULL,
            ordered_by INTEGER NOT NULL,
            performed_by INTEGER,
            test_name TEXT NOT NULL,
            test_code TEXT,
            test_date DATE NOT NULL,
            result_value TEXT,
            result_unit TEXT,
            reference_range TEXT,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
            is_abnormal BOOLEAN DEFAULT 0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (ordered_by) REFERENCES staff(id),
            FOREIGN KEY (performed_by) REFERENCES staff(id)
        )
    """)

    # Rooms
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            department_id INTEGER,
            room_type TEXT CHECK(room_type IN ('Patient Room', 'ICU', 'Operating Room', 'Emergency', 'Lab', 'Consultation')),
            bed_count INTEGER DEFAULT 1,
            floor INTEGER,
            is_occupied BOOLEAN DEFAULT 0,
            current_patient_id INTEGER,
            equipment TEXT,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (current_patient_id) REFERENCES patients(id)
        )
    """)

    # Medications Inventory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medication_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            generic_name TEXT,
            manufacturer TEXT,
            category TEXT,
            dosage_form TEXT CHECK(dosage_form IN ('Tablet', 'Capsule', 'Liquid', 'Injection', 'Cream', 'Inhaler', 'Patch')),
            strength TEXT,
            unit_price DECIMAL(10, 2),
            quantity_in_stock INTEGER DEFAULT 0,
            reorder_level INTEGER DEFAULT 100,
            expiration_date DATE,
            requires_prescription BOOLEAN DEFAULT 1,
            controlled_substance BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Billing
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS billing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER NOT NULL,
            appointment_id INTEGER,
            total_amount DECIMAL(10, 2) NOT NULL,
            insurance_covered DECIMAL(10, 2) DEFAULT 0,
            patient_responsibility DECIMAL(10, 2),
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Submitted', 'Approved', 'Denied', 'Paid', 'Partial')),
            billing_date DATE NOT NULL,
            due_date DATE,
            paid_amount DECIMAL(10, 2) DEFAULT 0,
            payment_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (appointment_id) REFERENCES appointments(id)
        )
    """)

    # Insurance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insurance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            provider_name TEXT NOT NULL,
            policy_number TEXT NOT NULL,
            group_number TEXT,
            plan_type TEXT CHECK(plan_type IN ('HMO', 'PPO', 'EPO', 'POS', 'Medicare', 'Medicaid')),
            coverage_start_date DATE,
            coverage_end_date DATE,
            copay DECIMAL(10, 2),
            deductible DECIMAL(10, 2),
            deductible_met DECIMAL(10, 2) DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    # Surgeries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS surgeries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            surgery_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER NOT NULL,
            surgeon_id INTEGER NOT NULL,
            procedure_name TEXT NOT NULL,
            procedure_code TEXT,
            scheduled_date DATE,
            scheduled_time TIME,
            actual_start_time TIMESTAMP,
            actual_end_time TIMESTAMP,
            operating_room TEXT,
            status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'In Progress', 'Completed', 'Cancelled', 'Postponed')),
            anesthesia_type TEXT,
            pre_op_diagnosis TEXT,
            post_op_diagnosis TEXT,
            complications TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (surgeon_id) REFERENCES staff(id)
        )
    """)

    # Emergency Cases
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL UNIQUE,
            patient_id INTEGER,
            arrival_time TIMESTAMP NOT NULL,
            triage_level INTEGER CHECK(triage_level BETWEEN 1 AND 5),
            chief_complaint TEXT NOT NULL,
            assigned_doctor_id INTEGER,
            assigned_nurse_id INTEGER,
            room_number TEXT,
            status TEXT DEFAULT 'Waiting' CHECK(status IN ('Waiting', 'Triage', 'Treatment', 'Observation', 'Admitted', 'Discharged', 'Transferred')),
            vital_signs TEXT,
            diagnosis TEXT,
            treatment TEXT,
            disposition TEXT,
            discharge_time TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (assigned_doctor_id) REFERENCES staff(id),
            FOREIGN KEY (assigned_nurse_id) REFERENCES staff(id)
        )
    """)

    # Audit Log (HIPAA Compliance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER,
            user_role TEXT,
            action TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            resource_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            status TEXT CHECK(status IN ('Success', 'Denied', 'Error')),
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES staff(id)
        )
    """)

    # Equipment
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            type TEXT,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            department_id INTEGER,
            room_id INTEGER,
            purchase_date DATE,
            warranty_expiration DATE,
            last_maintenance_date DATE,
            next_maintenance_date DATE,
            status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'In Use', 'Maintenance', 'Out of Service')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    """)

    conn.commit()
    print("Schema created successfully!")


def insert_test_data(conn: sqlite3.Connection) -> None:
    """Insert comprehensive test data."""
    cursor = conn.cursor()

    # ============================================
    # DEPARTMENTS
    # ============================================
    departments = [
        ("Cardiology", "CARD", 3, "555-0101"),
        ("Neurology", "NEUR", 4, "555-0102"),
        ("Oncology", "ONCO", 5, "555-0103"),
        ("Pediatrics", "PEDI", 2, "555-0104"),
        ("Emergency", "EMER", 1, "555-0105"),
        ("Orthopedics", "ORTH", 3, "555-0106"),
        ("Radiology", "RADI", 1, "555-0107"),
        ("Laboratory", "LAB", 1, "555-0108"),
        ("Pharmacy", "PHAR", 1, "555-0109"),
        ("Surgery", "SURG", 4, "555-0110"),
        ("Internal Medicine", "INTM", 2, "555-0111"),
        ("Psychiatry", "PSYC", 5, "555-0112")
    ]

    cursor.executemany("""
        INSERT INTO departments (name, code, floor, phone)
        VALUES (?, ?, ?, ?)
    """, departments)

    # ============================================
    # STAFF
    # ============================================
    staff_data = [
        # Admins
        ("EMP001", "John", "Administrator", "Admin", None, "admin@hospital.org", "555-1001", None, None, "2020-01-15"),
        ("EMP002", "Sarah", "SystemAdmin", "Admin", None, "sarah.admin@hospital.org", "555-1002", None, None, "2019-06-01"),

        # Doctors (various specializations)
        ("EMP010", "Michael", "Chen", "Doctor", 1, "m.chen@hospital.org", "555-1010", "Cardiologist", "MD-12345", "2018-03-01"),
        ("EMP011", "Emily", "Rodriguez", "Doctor", 1, "e.rodriguez@hospital.org", "555-1011", "Cardiac Surgeon", "MD-12346", "2017-05-15"),
        ("EMP012", "David", "Williams", "Doctor", 2, "d.williams@hospital.org", "555-1012", "Neurologist", "MD-12347", "2019-01-10"),
        ("EMP013", "Jennifer", "Brown", "Doctor", 3, "j.brown@hospital.org", "555-1013", "Oncologist", "MD-12348", "2016-08-20"),
        ("EMP014", "Robert", "Johnson", "Doctor", 4, "r.johnson@hospital.org", "555-1014", "Pediatrician", "MD-12349", "2020-02-01"),
        ("EMP015", "Lisa", "Davis", "Doctor", 5, "l.davis@hospital.org", "555-1015", "Emergency Medicine", "MD-12350", "2018-11-15"),
        ("EMP016", "James", "Wilson", "Doctor", 6, "j.wilson@hospital.org", "555-1016", "Orthopedic Surgeon", "MD-12351", "2015-04-01"),
        ("EMP017", "Patricia", "Taylor", "Doctor", 10, "p.taylor@hospital.org", "555-1017", "General Surgeon", "MD-12352", "2017-09-01"),
        ("EMP018", "Christopher", "Martinez", "Doctor", 11, "c.martinez@hospital.org", "555-1018", "Internist", "MD-12353", "2019-07-15"),
        ("EMP019", "Amanda", "Anderson", "Doctor", 12, "a.anderson@hospital.org", "555-1019", "Psychiatrist", "MD-12354", "2018-02-28"),

        # Nurses
        ("EMP020", "Nancy", "Thompson", "Nurse", 1, "n.thompson@hospital.org", "555-1020", "Cardiac Care", "RN-5001", "2019-03-15"),
        ("EMP021", "Karen", "White", "Nurse", 2, "k.white@hospital.org", "555-1021", "Neurology", "RN-5002", "2018-06-01"),
        ("EMP022", "Michelle", "Harris", "Nurse", 5, "m.harris@hospital.org", "555-1022", "Emergency", "RN-5003", "2017-09-20"),
        ("EMP023", "Linda", "Clark", "Nurse", 4, "l.clark@hospital.org", "555-1023", "Pediatrics", "RN-5004", "2020-01-10"),
        ("EMP024", "Betty", "Lewis", "Nurse", 10, "b.lewis@hospital.org", "555-1024", "Surgery", "RN-5005", "2016-11-15"),
        ("EMP025", "Dorothy", "Robinson", "Nurse", 3, "d.robinson@hospital.org", "555-1025", "Oncology", "RN-5006", "2019-05-01"),

        # Receptionists
        ("EMP030", "Susan", "Walker", "Receptionist", None, "s.walker@hospital.org", "555-1030", None, None, "2020-06-01"),
        ("EMP031", "Jessica", "Hall", "Receptionist", None, "j.hall@hospital.org", "555-1031", None, None, "2019-09-15"),
        ("EMP032", "Mary", "Young", "Receptionist", 5, "m.young@hospital.org", "555-1032", None, None, "2018-12-01"),

        # Lab Technicians
        ("EMP040", "Thomas", "King", "LabTechnician", 8, "t.king@hospital.org", "555-1040", "Clinical Lab", "CLT-3001", "2017-04-15"),
        ("EMP041", "Margaret", "Wright", "LabTechnician", 8, "m.wright@hospital.org", "555-1041", "Pathology", "CLT-3002", "2018-08-01"),
        ("EMP042", "Daniel", "Lopez", "LabTechnician", 8, "d.lopez@hospital.org", "555-1042", "Microbiology", "CLT-3003", "2019-02-20"),

        # Pharmacists
        ("EMP050", "Elizabeth", "Hill", "Pharmacist", 9, "e.hill@hospital.org", "555-1050", "Clinical Pharmacy", "RPH-2001", "2016-06-15"),
        ("EMP051", "William", "Scott", "Pharmacist", 9, "w.scott@hospital.org", "555-1051", "Oncology Pharmacy", "RPH-2002", "2018-10-01"),
    ]

    cursor.executemany("""
        INSERT INTO staff (employee_id, first_name, last_name, role, department_id, email, phone, specialization, license_number, hire_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, staff_data)

    # ============================================
    # PATIENTS (50 patients with diverse data)
    # ============================================
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
                   "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
                   "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]

    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

    blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    genders = ["Male", "Female"]
    states = ["CA", "NY", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
    insurance_providers = ["Blue Cross Blue Shield", "Aetna", "UnitedHealth", "Cigna", "Kaiser Permanente", "Humana", "Medicare", "Medicaid"]

    allergies_list = [
        None, "Penicillin", "Sulfa drugs", "Latex", "Peanuts", "Shellfish",
        "Aspirin", "Ibuprofen", "Codeine", "Morphine", "Eggs", "Dairy"
    ]

    patients = []
    for i in range(1, 51):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        dob = date(random.randint(1940, 2010), random.randint(1, 12), random.randint(1, 28))
        gender = random.choice(genders)
        ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        blood = random.choice(blood_types)
        allergy = random.choice(allergies_list)
        state = random.choice(states)
        insurance = random.choice(insurance_providers)

        patients.append((
            f"PAT{i:05d}",
            fname,
            lname,
            dob.isoformat(),
            gender,
            ssn,
            f"{fname.lower()}.{lname.lower()}{i}@email.com",
            f"555-{random.randint(2000, 9999)}",
            f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Maple', 'Cedar'])} {random.choice(['St', 'Ave', 'Blvd', 'Dr'])}",
            random.choice(["Los Angeles", "New York", "Chicago", "Houston", "Phoenix"]),
            state,
            f"{random.randint(10000, 99999)}",
            f"{random.choice(first_names)} {random.choice(last_names)}",
            f"555-{random.randint(2000, 9999)}",
            blood,
            allergy,
            insurance,
            f"POL{random.randint(100000, 999999)}"
        ))

    cursor.executemany("""
        INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, ssn, email, phone,
                            address, city, state, zip_code, emergency_contact_name, emergency_contact_phone,
                            blood_type, allergies, insurance_provider, insurance_policy_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, patients)

    # ============================================
    # APPOINTMENTS (100 appointments)
    # ============================================
    appointment_types = ["Consultation", "Follow-up", "Emergency", "Routine Check", "Surgery Prep", "Lab Work"]
    appointment_statuses = ["Scheduled", "Confirmed", "Completed", "Cancelled"]

    appointments = []
    for i in range(1, 101):
        appt_date = date.today() + timedelta(days=random.randint(-30, 60))
        hour = random.randint(8, 17)
        minute = random.choice([0, 15, 30, 45])

        appointments.append((
            f"APT{i:06d}",
            random.randint(1, 50),  # patient_id
            random.randint(3, 12),  # doctor_id (staff IDs 3-12 are doctors)
            random.randint(1, 12),  # department_id
            appt_date.isoformat(),
            f"{hour:02d}:{minute:02d}",
            random.choice([15, 30, 45, 60]),
            random.choice(appointment_statuses),
            random.choice(appointment_types),
            f"Patient complaint: {random.choice(['headache', 'chest pain', 'back pain', 'fever', 'cough', 'fatigue', 'dizziness'])}",
            f"Room {random.randint(100, 500)}"
        ))

    cursor.executemany("""
        INSERT INTO appointments (appointment_id, patient_id, doctor_id, department_id, appointment_date,
                                 appointment_time, duration_minutes, status, type, reason, room_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, appointments)

    # ============================================
    # MEDICAL RECORDS (75 records)
    # ============================================
    diagnoses = [
        ("Hypertension", "I10"),
        ("Type 2 Diabetes", "E11.9"),
        ("Acute Bronchitis", "J20.9"),
        ("Osteoarthritis", "M19.90"),
        ("Major Depression", "F32.9"),
        ("Migraine", "G43.909"),
        ("GERD", "K21.0"),
        ("Asthma", "J45.909"),
        ("Anxiety Disorder", "F41.9"),
        ("Pneumonia", "J18.9"),
        ("Coronary Artery Disease", "I25.10"),
        ("Chronic Kidney Disease", "N18.9"),
        ("Atrial Fibrillation", "I48.91"),
        ("Heart Failure", "I50.9"),
        ("COPD", "J44.9")
    ]

    symptoms_list = [
        "Chest pain, shortness of breath",
        "Persistent headache, nausea",
        "Joint pain and stiffness",
        "Fatigue, weight loss, loss of appetite",
        "Cough, fever, difficulty breathing",
        "Dizziness, palpitations",
        "Abdominal pain, bloating",
        "Muscle weakness, numbness",
        "Anxiety, insomnia, irritability",
        "Back pain radiating to legs"
    ]

    medical_records = []
    for i in range(1, 76):
        diagnosis = random.choice(diagnoses)
        visit_date = date.today() - timedelta(days=random.randint(0, 365))

        medical_records.append((
            f"MED{i:06d}",
            random.randint(1, 50),  # patient_id
            random.randint(3, 12),  # doctor_id
            visit_date.isoformat(),
            random.choice(symptoms_list),
            diagnosis[0],
            diagnosis[1],
            random.choice(symptoms_list),
            f"BP: {random.randint(110, 160)}/{random.randint(60, 100)}, HR: {random.randint(60, 100)}, Temp: {round(random.uniform(97.0, 101.0), 1)}F",
            f"Continue current medications. Follow up in {random.choice([2, 4, 6, 8])} weeks.",
            (visit_date + timedelta(weeks=random.randint(2, 8))).isoformat(),
            random.choice([0, 0, 0, 1])  # 25% are sensitive
        ))

    cursor.executemany("""
        INSERT INTO medical_records (record_id, patient_id, doctor_id, visit_date, chief_complaint,
                                    diagnosis, diagnosis_code, symptoms, vital_signs, treatment_plan,
                                    follow_up_date, is_sensitive)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, medical_records)

    # ============================================
    # PRESCRIPTIONS (60 prescriptions)
    # ============================================
    medications_rx = [
        ("Lisinopril", "10mg", "Once daily", "Tablet"),
        ("Metformin", "500mg", "Twice daily", "Tablet"),
        ("Atorvastatin", "20mg", "Once daily at bedtime", "Tablet"),
        ("Omeprazole", "20mg", "Once daily before breakfast", "Capsule"),
        ("Amlodipine", "5mg", "Once daily", "Tablet"),
        ("Metoprolol", "25mg", "Twice daily", "Tablet"),
        ("Gabapentin", "300mg", "Three times daily", "Capsule"),
        ("Sertraline", "50mg", "Once daily", "Tablet"),
        ("Hydrochlorothiazide", "25mg", "Once daily", "Tablet"),
        ("Losartan", "50mg", "Once daily", "Tablet"),
        ("Levothyroxine", "50mcg", "Once daily on empty stomach", "Tablet"),
        ("Alprazolam", "0.5mg", "As needed for anxiety", "Tablet"),
        ("Prednisone", "10mg", "Once daily with food", "Tablet"),
        ("Amoxicillin", "500mg", "Three times daily", "Capsule"),
        ("Ibuprofen", "400mg", "Every 6 hours as needed", "Tablet")
    ]

    prescriptions = []
    for i in range(1, 61):
        med = random.choice(medications_rx)

        prescriptions.append((
            f"RX{i:06d}",
            random.randint(1, 50),  # patient_id
            random.randint(3, 12),  # doctor_id
            random.randint(1, 75) if random.random() > 0.3 else None,  # medical_record_id
            med[0],  # medication_name
            med[1],  # dosage
            med[2],  # frequency
            random.choice([7, 14, 30, 60, 90]),  # duration_days
            random.choice([30, 60, 90]),  # quantity
            random.choice([0, 1, 2, 3]),  # refills_allowed
            random.choice(["Active", "Dispensed", "Active", "Active"]),  # status
            med[3]  # instructions (using dosage form)
        ))

    cursor.executemany("""
        INSERT INTO prescriptions (prescription_id, patient_id, doctor_id, medical_record_id,
                                  medication_name, dosage, frequency, duration_days, quantity,
                                  refills_allowed, status, instructions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, prescriptions)

    # ============================================
    # LAB RESULTS (80 results)
    # ============================================
    lab_tests = [
        ("Complete Blood Count (CBC)", "CBC", "mg/dL"),
        ("Basic Metabolic Panel", "BMP", "mg/dL"),
        ("Lipid Panel", "LIP", "mg/dL"),
        ("Hemoglobin A1C", "A1C", "%"),
        ("Thyroid Panel (TSH)", "TSH", "mIU/L"),
        ("Liver Function Test", "LFT", "U/L"),
        ("Urinalysis", "UA", None),
        ("Vitamin D", "VITD", "ng/mL"),
        ("Vitamin B12", "B12", "pg/mL"),
        ("Iron Panel", "IRON", "mcg/dL"),
        ("PSA", "PSA", "ng/mL"),
        ("Creatinine", "CRE", "mg/dL"),
        ("Blood Glucose", "GLU", "mg/dL"),
        ("Potassium", "K", "mEq/L"),
        ("Sodium", "NA", "mEq/L")
    ]

    lab_results = []
    for i in range(1, 81):
        test = random.choice(lab_tests)
        test_date = date.today() - timedelta(days=random.randint(0, 180))

        lab_results.append((
            f"LAB{i:06d}",
            random.randint(1, 50),  # patient_id
            random.randint(3, 12),  # ordered_by (doctor)
            random.randint(21, 23) if random.random() > 0.2 else None,  # performed_by (lab tech)
            test[0],  # test_name
            test[1],  # test_code
            test_date.isoformat(),
            f"{round(random.uniform(50, 200), 1)}",  # result_value
            test[2],  # result_unit
            "60-120",  # reference_range
            random.choice(["Completed", "Completed", "Pending", "In Progress"]),
            random.choice([0, 0, 0, 1])  # 25% abnormal
        ))

    cursor.executemany("""
        INSERT INTO lab_results (result_id, patient_id, ordered_by, performed_by, test_name, test_code,
                                test_date, result_value, result_unit, reference_range, status, is_abnormal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, lab_results)

    # ============================================
    # ROOMS (40 rooms)
    # ============================================
    room_types = ["Patient Room", "ICU", "Operating Room", "Emergency", "Lab", "Consultation"]

    rooms = []
    for floor in range(1, 6):
        for room_num in range(1, 9):
            room_type = random.choice(room_types)
            rooms.append((
                f"{floor}{room_num:02d}",
                random.randint(1, 12),  # department_id
                room_type,
                1 if room_type in ["Consultation", "Lab"] else random.randint(1, 4),
                floor,
                random.choice([0, 0, 1])  # 33% occupied
            ))

    cursor.executemany("""
        INSERT INTO rooms (room_number, department_id, room_type, bed_count, floor, is_occupied)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rooms)

    # ============================================
    # MEDICATIONS INVENTORY (30 medications)
    # ============================================
    medications_inv = [
        ("MED001", "Lisinopril", "Lisinopril", "Pfizer", "Cardiovascular", "Tablet", "10mg", 5.99, 500),
        ("MED002", "Metformin", "Metformin HCl", "Merck", "Diabetes", "Tablet", "500mg", 8.99, 750),
        ("MED003", "Atorvastatin", "Atorvastatin Calcium", "Pfizer", "Cardiovascular", "Tablet", "20mg", 12.99, 400),
        ("MED004", "Omeprazole", "Omeprazole", "AstraZeneca", "Gastrointestinal", "Capsule", "20mg", 15.99, 300),
        ("MED005", "Amlodipine", "Amlodipine Besylate", "Pfizer", "Cardiovascular", "Tablet", "5mg", 7.99, 600),
        ("MED006", "Metoprolol", "Metoprolol Tartrate", "AstraZeneca", "Cardiovascular", "Tablet", "25mg", 9.99, 450),
        ("MED007", "Gabapentin", "Gabapentin", "Pfizer", "Neurological", "Capsule", "300mg", 18.99, 350),
        ("MED008", "Sertraline", "Sertraline HCl", "Pfizer", "Psychiatric", "Tablet", "50mg", 14.99, 400),
        ("MED009", "Losartan", "Losartan Potassium", "Merck", "Cardiovascular", "Tablet", "50mg", 11.99, 500),
        ("MED010", "Levothyroxine", "Levothyroxine Sodium", "AbbVie", "Endocrine", "Tablet", "50mcg", 6.99, 800),
        ("MED011", "Hydrochlorothiazide", "Hydrochlorothiazide", "Merck", "Cardiovascular", "Tablet", "25mg", 4.99, 650),
        ("MED012", "Amoxicillin", "Amoxicillin", "Teva", "Antibiotic", "Capsule", "500mg", 8.49, 1000),
        ("MED013", "Prednisone", "Prednisone", "Pfizer", "Anti-inflammatory", "Tablet", "10mg", 5.49, 450),
        ("MED014", "Ibuprofen", "Ibuprofen", "Johnson & Johnson", "Pain Relief", "Tablet", "400mg", 3.99, 1200),
        ("MED015", "Alprazolam", "Alprazolam", "Pfizer", "Psychiatric", "Tablet", "0.5mg", 22.99, 200),
        ("MED016", "Morphine", "Morphine Sulfate", "Purdue", "Pain Relief", "Injection", "10mg/mL", 45.99, 100),
        ("MED017", "Insulin Glargine", "Insulin Glargine", "Sanofi", "Diabetes", "Injection", "100U/mL", 89.99, 150),
        ("MED018", "Warfarin", "Warfarin Sodium", "Bristol-Myers", "Anticoagulant", "Tablet", "5mg", 7.49, 400),
        ("MED019", "Clopidogrel", "Clopidogrel Bisulfate", "Bristol-Myers", "Antiplatelet", "Tablet", "75mg", 19.99, 300),
        ("MED020", "Furosemide", "Furosemide", "Sanofi", "Diuretic", "Tablet", "40mg", 4.49, 550),
    ]

    cursor.executemany("""
        INSERT INTO medications (medication_id, name, generic_name, manufacturer, category,
                                dosage_form, strength, unit_price, quantity_in_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, medications_inv)

    # ============================================
    # BILLING (40 invoices)
    # ============================================
    billing_data = []
    for i in range(1, 41):
        total = round(random.uniform(100, 5000), 2)
        insurance_covered = round(total * random.uniform(0.5, 0.9), 2)
        patient_resp = round(total - insurance_covered, 2)
        billing_date = date.today() - timedelta(days=random.randint(0, 90))

        billing_data.append((
            f"INV{i:06d}",
            random.randint(1, 50),  # patient_id
            random.randint(1, 100) if random.random() > 0.3 else None,  # appointment_id
            total,
            insurance_covered,
            patient_resp,
            random.choice(["Pending", "Submitted", "Approved", "Paid", "Partial"]),
            billing_date.isoformat(),
            (billing_date + timedelta(days=30)).isoformat()
        ))

    cursor.executemany("""
        INSERT INTO billing (invoice_id, patient_id, appointment_id, total_amount, insurance_covered,
                           patient_responsibility, status, billing_date, due_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, billing_data)

    # ============================================
    # INSURANCE (50 policies - one per patient)
    # ============================================
    plan_types = ["HMO", "PPO", "EPO", "Medicare", "Medicaid"]

    insurance_data = []
    for i in range(1, 51):
        start_date = date.today() - timedelta(days=random.randint(30, 365))

        insurance_data.append((
            i,  # patient_id
            random.choice(insurance_providers),
            f"POL{random.randint(100000, 999999)}",
            f"GRP{random.randint(1000, 9999)}",
            random.choice(plan_types),
            start_date.isoformat(),
            (start_date + timedelta(days=365)).isoformat(),
            random.choice([20, 25, 30, 40, 50]),  # copay
            random.choice([500, 1000, 2000, 3000, 5000]),  # deductible
            round(random.uniform(0, 5000), 2)  # deductible_met
        ))

    cursor.executemany("""
        INSERT INTO insurance (patient_id, provider_name, policy_number, group_number, plan_type,
                              coverage_start_date, coverage_end_date, copay, deductible, deductible_met)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, insurance_data)

    # ============================================
    # SURGERIES (20 surgeries)
    # ============================================
    procedures = [
        ("Coronary Artery Bypass", "33533"),
        ("Hip Replacement", "27130"),
        ("Knee Arthroscopy", "29881"),
        ("Appendectomy", "44970"),
        ("Cholecystectomy", "47562"),
        ("Hernia Repair", "49650"),
        ("Cataract Surgery", "66984"),
        ("Spinal Fusion", "22612"),
        ("Mastectomy", "19303"),
        ("Thyroidectomy", "60240")
    ]

    surgeries = []
    for i in range(1, 21):
        proc = random.choice(procedures)
        sched_date = date.today() + timedelta(days=random.randint(-30, 60))

        surgeries.append((
            f"SUR{i:06d}",
            random.randint(1, 50),  # patient_id
            random.choice([4, 8, 9, 11]),  # surgeon_id (doctors who do surgery)
            proc[0],
            proc[1],
            sched_date.isoformat(),
            f"{random.randint(7, 15):02d}:00",
            f"OR-{random.randint(1, 5)}",
            random.choice(["Scheduled", "Completed", "In Progress"]),
            random.choice(["General", "Local", "Spinal", "Epidural"])
        ))

    cursor.executemany("""
        INSERT INTO surgeries (surgery_id, patient_id, surgeon_id, procedure_name, procedure_code,
                              scheduled_date, scheduled_time, operating_room, status, anesthesia_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, surgeries)

    # ============================================
    # EMERGENCY CASES (25 cases)
    # ============================================
    emergency_complaints = [
        "Severe chest pain",
        "Difficulty breathing",
        "Severe abdominal pain",
        "Head injury",
        "Broken bone",
        "Severe allergic reaction",
        "High fever",
        "Loss of consciousness",
        "Severe bleeding",
        "Stroke symptoms"
    ]

    emergency_cases = []
    for i in range(1, 26):
        arrival = datetime.now() - timedelta(hours=random.randint(1, 72))

        emergency_cases.append((
            f"ER{i:06d}",
            random.randint(1, 50) if random.random() > 0.2 else None,  # patient_id (some unidentified)
            arrival.isoformat(),
            random.randint(1, 5),  # triage_level
            random.choice(emergency_complaints),
            random.choice([6, 7, 8, 13]),  # assigned_doctor_id (ER doctors)
            random.randint(17, 20),  # assigned_nurse_id
            f"ER-{random.randint(1, 10)}",
            random.choice(["Waiting", "Triage", "Treatment", "Observation", "Discharged"])
        ))

    cursor.executemany("""
        INSERT INTO emergency_cases (case_id, patient_id, arrival_time, triage_level, chief_complaint,
                                    assigned_doctor_id, assigned_nurse_id, room_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, emergency_cases)

    # ============================================
    # EQUIPMENT (30 items)
    # ============================================
    equipment_items = [
        ("Ultrasound Machine", "Diagnostic", "GE Healthcare"),
        ("X-Ray Machine", "Diagnostic", "Siemens"),
        ("MRI Scanner", "Diagnostic", "Philips"),
        ("CT Scanner", "Diagnostic", "Siemens"),
        ("ECG Machine", "Cardiac", "GE Healthcare"),
        ("Defibrillator", "Emergency", "Philips"),
        ("Ventilator", "Respiratory", "Medtronic"),
        ("Infusion Pump", "Drug Delivery", "Baxter"),
        ("Patient Monitor", "Monitoring", "Philips"),
        ("Anesthesia Machine", "Surgery", "Drager")
    ]

    equipment_data = []
    for i in range(1, 31):
        item = random.choice(equipment_items)
        purchase_date = date.today() - timedelta(days=random.randint(365, 1825))

        equipment_data.append((
            f"EQP{i:06d}",
            item[0],
            item[1],
            item[2],
            f"Model-{random.randint(1000, 9999)}",
            f"SN-{random.randint(100000, 999999)}",
            random.randint(1, 12),  # department_id
            purchase_date.isoformat(),
            (purchase_date + timedelta(days=1095)).isoformat(),  # 3-year warranty
            random.choice(["Available", "In Use", "Maintenance", "Available"])
        ))

    cursor.executemany("""
        INSERT INTO equipment (equipment_id, name, type, manufacturer, model, serial_number,
                              department_id, purchase_date, warranty_expiration, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, equipment_data)

    # ============================================
    # AUDIT LOG (100 entries)
    # ============================================
    actions = ["READ", "CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "EXPORT"]
    resources = ["PatientRecord", "MedicalRecord", "Prescription", "Appointment", "LabResult", "Billing"]

    audit_entries = []
    for i in range(1, 101):
        event_time = datetime.now() - timedelta(hours=random.randint(1, 720))
        user_id = random.randint(1, 25)

        audit_entries.append((
            event_time.isoformat(),
            user_id,
            random.choice(["Admin", "Doctor", "Nurse", "Receptionist", "LabTechnician", "Pharmacist"]),
            random.choice(actions),
            random.choice(resources),
            f"ID-{random.randint(1, 100)}",
            f"192.168.1.{random.randint(1, 254)}",
            random.choice(["Success", "Success", "Success", "Denied", "Error"])
        ))

    cursor.executemany("""
        INSERT INTO audit_log (event_time, user_id, user_role, action, resource_type, resource_id, ip_address, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, audit_entries)

    conn.commit()
    print("Test data inserted successfully!")


def print_statistics(conn: sqlite3.Connection) -> None:
    """Print database statistics."""
    cursor = conn.cursor()

    tables = [
        "departments", "staff", "patients", "appointments", "medical_records",
        "prescriptions", "lab_results", "rooms", "medications", "billing",
        "insurance", "surgeries", "emergency_cases", "audit_log", "equipment"
    ]

    print("\n" + "=" * 50)
    print("DATABASE STATISTICS")
    print("=" * 50)

    total = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total += count
        print(f"{table:25} {count:>6} records")

    print("-" * 50)
    print(f"{'TOTAL':25} {total:>6} records")
    print("=" * 50)


def main():
    """Main function to setup database."""
    # Remove existing database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Removed existing database: {DB_PATH}")

    # Create data directory if not exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Connect and setup
    conn = sqlite3.connect(DB_PATH)

    try:
        create_schema(conn)
        insert_test_data(conn)
        print_statistics(conn)
        print(f"\nDatabase created successfully at: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
