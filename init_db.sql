-- Hospital Database Schema for OntoGuard Testing
-- ==============================================

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    diagnosis VARCHAR(255),
    doctor_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medical records table
CREATE TABLE IF NOT EXISTS medical_records (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    record_type VARCHAR(50),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lab results table
CREATE TABLE IF NOT EXISTS lab_results (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    test_name VARCHAR(100),
    result VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Appointments table
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    doctor_id INTEGER,
    appointment_date DATE,
    status VARCHAR(50) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Billing table
CREATE TABLE IF NOT EXISTS billing (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staff table
CREATE TABLE IF NOT EXISTS staff (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(50),
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- Test Data
-- ==============================================

-- Patients
INSERT INTO patients (name, date_of_birth, diagnosis, doctor_id) VALUES
    ('John Doe', '1990-01-15', 'Flu', 1),
    ('Jane Smith', '1985-05-20', 'Annual Checkup', 1),
    ('Bob Wilson', '1978-12-03', 'Diabetes Type 2', 2),
    ('Alice Brown', '1995-08-22', 'Migraine', 2),
    ('Charlie Davis', '1982-03-10', 'Hypertension', 1);

-- Medical Records
INSERT INTO medical_records (patient_id, record_type, content) VALUES
    (1, 'diagnosis', 'Patient presents with flu symptoms: fever 38.5C, cough, fatigue'),
    (1, 'prescription', 'Prescribed Tamiflu 75mg twice daily for 5 days'),
    (2, 'checkup', 'Annual checkup completed. All vitals normal. BMI: 22.5'),
    (3, 'diagnosis', 'Diabetes Type 2 confirmed. HbA1c: 7.2%'),
    (3, 'treatment', 'Started on Metformin 500mg twice daily'),
    (4, 'diagnosis', 'Chronic migraine with aura. MRI clear'),
    (5, 'diagnosis', 'Essential hypertension. BP: 145/95');

-- Lab Results
INSERT INTO lab_results (patient_id, test_name, result) VALUES
    (1, 'Blood Test', 'WBC elevated, other values normal'),
    (1, 'COVID-19 PCR', 'Negative'),
    (2, 'Complete Blood Count', 'All values within normal range'),
    (2, 'Lipid Panel', 'Total cholesterol: 185 mg/dL - Normal'),
    (3, 'HbA1c', '7.2% - Above target'),
    (3, 'Fasting Glucose', '142 mg/dL - Elevated'),
    (4, 'MRI Brain', 'No abnormalities detected'),
    (5, 'Kidney Function', 'eGFR: 85 - Normal');

-- Appointments
INSERT INTO appointments (patient_id, doctor_id, appointment_date, status) VALUES
    (1, 1, '2026-01-29', 'scheduled'),
    (2, 1, '2026-01-30', 'scheduled'),
    (3, 2, '2026-02-01', 'scheduled'),
    (4, 2, '2026-02-05', 'scheduled'),
    (5, 1, '2026-02-10', 'scheduled'),
    (1, 1, '2026-01-20', 'completed'),
    (3, 2, '2026-01-15', 'completed');

-- Billing
INSERT INTO billing (patient_id, amount, status) VALUES
    (1, 150.00, 'pending'),
    (1, 75.00, 'paid'),
    (2, 200.00, 'paid'),
    (3, 350.00, 'pending'),
    (3, 125.00, 'paid'),
    (4, 500.00, 'pending'),
    (5, 180.00, 'paid');

-- Staff
INSERT INTO staff (name, role, department) VALUES
    ('Dr. Sarah Johnson', 'Doctor', 'General Medicine'),
    ('Dr. Michael Chen', 'Doctor', 'Endocrinology'),
    ('Emily Watson', 'Nurse', 'General Medicine'),
    ('James Miller', 'Nurse', 'Emergency'),
    ('Lisa Anderson', 'LabTechnician', 'Laboratory'),
    ('Robert Taylor', 'Receptionist', 'Front Desk'),
    ('Admin User', 'Admin', 'Administration');

-- ==============================================
-- Verification
-- ==============================================
SELECT 'Database initialized successfully!' as status;
SELECT 'Tables created: patients, medical_records, lab_results, appointments, billing, staff' as info;
SELECT
    (SELECT COUNT(*) FROM patients) as patients_count,
    (SELECT COUNT(*) FROM medical_records) as records_count,
    (SELECT COUNT(*) FROM lab_results) as lab_count,
    (SELECT COUNT(*) FROM appointments) as appointments_count,
    (SELECT COUNT(*) FROM billing) as billing_count,
    (SELECT COUNT(*) FROM staff) as staff_count;
