-- Finance Database Schema for OntoGuard Testing
-- ==============================================

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(30) NOT NULL,  -- savings, checking, corporate
    balance DECIMAL(15, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20) DEFAULT 'active',
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    transaction_type VARCHAR(30) NOT NULL,  -- deposit, withdrawal, transfer, payment
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    counterparty VARCHAR(100),
    description TEXT,
    status VARCHAR(20) DEFAULT 'completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loans table
CREATE TABLE IF NOT EXISTS loans (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    loan_type VARCHAR(30) NOT NULL,  -- mortgage, auto, personal, business
    principal DECIMAL(15, 2) NOT NULL,
    interest_rate DECIMAL(5, 2) NOT NULL,
    term_months INTEGER NOT NULL,
    monthly_payment DECIMAL(12, 2),
    status VARCHAR(20) DEFAULT 'active',  -- active, paid_off, defaulted, pending
    approved_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cards table
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    card_number VARCHAR(19) NOT NULL,
    card_type VARCHAR(20) NOT NULL,  -- debit, credit, corporate
    credit_limit DECIMAL(12, 2),
    expiry_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',  -- active, blocked, expired
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer profiles table
CREATE TABLE IF NOT EXISTS customer_profiles (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    customer_type VARCHAR(20) NOT NULL,  -- individual, corporate
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    tax_id VARCHAR(20),
    risk_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    report_type VARCHAR(50) NOT NULL,  -- monthly_statement, risk_analysis, audit, compliance
    title VARCHAR(200) NOT NULL,
    content TEXT,
    created_by VARCHAR(100),
    period_start DATE,
    period_end DATE,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    performed_by VARCHAR(100),
    role VARCHAR(50),
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================
-- Test Data
-- ==============================================

-- Customer profiles (8 customers)
INSERT INTO customer_profiles (full_name, customer_type, email, phone, address, tax_id, risk_score) VALUES
    ('Иванов Алексей Петрович', 'individual', 'ivanov@mail.ru', '+7-900-111-2233', 'Москва, ул. Ленина 15', '770112345678', 15),
    ('Петрова Мария Сергеевна', 'individual', 'petrova@gmail.com', '+7-900-222-3344', 'Санкт-Петербург, Невский 42', '780298765432', 8),
    ('ООО "ТехноСтарт"', 'corporate', 'info@technostart.ru', '+7-495-555-1234', 'Москва, Пресненская наб. 8', '7701234567', 22),
    ('Сидоров Дмитрий Иванович', 'individual', 'sidorov@yandex.ru', '+7-900-333-4455', 'Казань, ул. Баумана 33', '160387654321', 5),
    ('АО "ГлобалТрейд"', 'corporate', 'office@globaltrade.com', '+7-495-666-7890', 'Москва, Тверская 22', '7709876543', 35),
    ('Козлова Анна Владимировна', 'individual', 'kozlova@mail.ru', '+7-900-444-5566', 'Екатеринбург, ул. Мира 7', '660412345678', 12),
    ('ИП Морозов В.А.', 'corporate', 'morozov@bk.ru', '+7-900-555-6677', 'Новосибирск, Красный пр. 50', '5401234567', 18),
    ('Белова Елена Николаевна', 'individual', 'belova@gmail.com', '+7-900-666-7788', 'Сочи, ул. Навагинская 12', '230598765432', 3);

-- Accounts (10 accounts)
INSERT INTO accounts (account_number, owner_name, account_type, balance, currency, status) VALUES
    ('40817810100000001', 'Иванов Алексей Петрович', 'checking', 125000.50, 'RUB', 'active'),
    ('40817810100000002', 'Петрова Мария Сергеевна', 'savings', 890000.00, 'RUB', 'active'),
    ('40702810100000003', 'ООО "ТехноСтарт"', 'corporate', 3500000.00, 'RUB', 'active'),
    ('40817810100000004', 'Сидоров Дмитрий Иванович', 'checking', 45600.75, 'RUB', 'active'),
    ('40702810100000005', 'АО "ГлобалТрейд"', 'corporate', 12800000.00, 'RUB', 'active'),
    ('40817840100000006', 'Козлова Анна Владимировна', 'savings', 5200.00, 'USD', 'active'),
    ('40702810100000007', 'ИП Морозов В.А.', 'corporate', 780000.00, 'RUB', 'active'),
    ('40817810100000008', 'Белова Елена Николаевна', 'checking', 67800.25, 'RUB', 'active'),
    ('40817978100000009', 'Иванов Алексей Петрович', 'savings', 2300.00, 'EUR', 'active'),
    ('40817810100000010', 'Петрова Мария Сергеевна', 'checking', 210000.00, 'RUB', 'blocked');

-- Transactions (15 transactions)
INSERT INTO transactions (account_id, transaction_type, amount, currency, counterparty, description, status) VALUES
    (1, 'deposit', 50000.00, 'RUB', 'Работодатель ООО "Альфа"', 'Зарплата за январь', 'completed'),
    (1, 'withdrawal', 15000.00, 'RUB', 'ATM', 'Снятие наличных', 'completed'),
    (1, 'payment', 8500.00, 'RUB', 'МТС', 'Оплата связи и интернета', 'completed'),
    (2, 'deposit', 100000.00, 'RUB', NULL, 'Пополнение вклада', 'completed'),
    (3, 'transfer', 500000.00, 'RUB', 'ООО "Поставщик"', 'Оплата по договору №123', 'completed'),
    (3, 'transfer', 1200000.00, 'RUB', 'АО "ГлобалТрейд"', 'Оплата за услуги', 'pending'),
    (4, 'deposit', 35000.00, 'RUB', 'Фриланс', 'Оплата проекта', 'completed'),
    (5, 'transfer', 5000000.00, 'RUB', 'Зарубежный контрагент', 'Экспортная сделка', 'pending'),
    (5, 'payment', 250000.00, 'RUB', 'ФНС', 'Уплата НДС', 'completed'),
    (6, 'deposit', 1000.00, 'USD', NULL, 'Пополнение валютного счёта', 'completed'),
    (7, 'transfer', 150000.00, 'RUB', 'Арендодатель', 'Аренда офиса февраль', 'completed'),
    (8, 'payment', 12500.00, 'RUB', 'Сбербанк Страхование', 'Страховой взнос', 'completed'),
    (1, 'transfer', 30000.00, 'RUB', 'Петрова М.С.', 'Перевод другу', 'completed'),
    (9, 'deposit', 500.00, 'EUR', NULL, 'Пополнение EUR счёта', 'completed'),
    (3, 'payment', 85000.00, 'RUB', 'ФНС', 'Налог на прибыль', 'completed');

-- Loans (6 loans)
INSERT INTO loans (account_id, loan_type, principal, interest_rate, term_months, monthly_payment, status, approved_by) VALUES
    (1, 'personal', 300000.00, 14.5, 24, 14500.00, 'active', 'Менеджер Кузнецов'),
    (2, 'mortgage', 5000000.00, 9.8, 240, 47500.00, 'active', 'Менеджер Волков'),
    (3, 'business', 2000000.00, 12.0, 36, 66500.00, 'active', 'Менеджер Кузнецов'),
    (4, 'auto', 800000.00, 11.5, 60, 17600.00, 'active', 'Менеджер Волков'),
    (5, 'business', 10000000.00, 10.5, 48, 255000.00, 'pending', NULL),
    (8, 'personal', 150000.00, 15.0, 12, 13500.00, 'paid_off', 'Менеджер Кузнецов');

-- Cards (8 cards)
INSERT INTO cards (account_id, card_number, card_type, credit_limit, expiry_date, status) VALUES
    (1, '4276 **** **** 1234', 'debit', NULL, '2028-06-01', 'active'),
    (1, '5536 **** **** 5678', 'credit', 200000.00, '2027-12-01', 'active'),
    (2, '4276 **** **** 9012', 'debit', NULL, '2028-03-01', 'active'),
    (3, '4274 **** **** 3456', 'corporate', 1000000.00, '2027-09-01', 'active'),
    (4, '4276 **** **** 7890', 'debit', NULL, '2028-01-01', 'active'),
    (5, '4274 **** **** 2345', 'corporate', 5000000.00, '2028-06-01', 'active'),
    (6, '4276 **** **** 6789', 'debit', NULL, '2027-11-01', 'blocked'),
    (8, '5536 **** **** 0123', 'credit', 100000.00, '2028-09-01', 'active');

-- Reports (5 reports)
INSERT INTO reports (report_type, title, content, created_by, period_start, period_end, status) VALUES
    ('monthly_statement', 'Месячный отчёт январь 2026', 'Общий оборот: 8.5M RUB, новых клиентов: 12', 'Аналитик Смирнова', '2026-01-01', '2026-01-31', 'published'),
    ('risk_analysis', 'Анализ рисков Q4 2025', 'Выявлено 3 клиента с повышенным риском', 'Аналитик Смирнова', '2025-10-01', '2025-12-31', 'published'),
    ('compliance', 'Отчёт комплаенс январь 2026', 'Проверено 45 транзакций, 2 подозрительные', 'Комплаенс-офицер Орлов', '2026-01-01', '2026-01-31', 'draft'),
    ('audit', 'Аудиторский отчёт 2025', 'Годовой аудит: замечаний нет', 'Аудитор Федорова', '2025-01-01', '2025-12-31', 'published'),
    ('monthly_statement', 'Месячный отчёт декабрь 2025', 'Общий оборот: 12.1M RUB, закрыто счетов: 3', 'Аналитик Смирнова', '2025-12-01', '2025-12-31', 'published');

-- Audit log (10 entries)
INSERT INTO audit_log (action, entity_type, entity_id, performed_by, role, details, ip_address) VALUES
    ('create', 'Account', 1, 'Операционист Новикова', 'Teller', 'Открытие счёта для Иванов А.П.', '192.168.1.10'),
    ('read', 'Account', 5, 'Менеджер Кузнецов', 'Manager', 'Просмотр счёта АО "ГлобалТрейд"', '192.168.1.15'),
    ('approve', 'Loan', 1, 'Менеджер Кузнецов', 'Manager', 'Одобрение кредита 300K RUB', '192.168.1.15'),
    ('transfer', 'Transaction', 5, 'Операционист Новикова', 'Teller', 'Перевод 500K ООО "Поставщик"', '192.168.1.10'),
    ('block', 'Card', 7, 'Комплаенс-офицер Орлов', 'ComplianceOfficer', 'Блокировка карты по подозрению в мошенничестве', '192.168.1.20'),
    ('read', 'Report', 2, 'Аудитор Федорова', 'Auditor', 'Просмотр анализа рисков', '192.168.1.25'),
    ('export', 'Report', 1, 'Аналитик Смирнова', 'Analyst', 'Экспорт месячного отчёта', '192.168.1.30'),
    ('update', 'CustomerProfile', 3, 'Операционист Новикова', 'Teller', 'Обновление адреса ООО "ТехноСтарт"', '192.168.1.10'),
    ('read', 'AuditLog', NULL, 'Аудитор Федорова', 'Auditor', 'Просмотр журнала аудита', '192.168.1.25'),
    ('create', 'Transaction', 8, 'Клиент Иванов А.П.', 'IndividualCustomer', 'Перевод 30K на счёт Петровой', '10.0.0.5');

-- ==============================================
-- Verification
-- ==============================================
SELECT 'Finance database initialized successfully!' as status;
SELECT 'Tables: accounts, transactions, loans, cards, customer_profiles, reports, audit_log' as info;
SELECT
    (SELECT COUNT(*) FROM accounts) as accounts_count,
    (SELECT COUNT(*) FROM transactions) as transactions_count,
    (SELECT COUNT(*) FROM loans) as loans_count,
    (SELECT COUNT(*) FROM cards) as cards_count,
    (SELECT COUNT(*) FROM customer_profiles) as profiles_count,
    (SELECT COUNT(*) FROM reports) as reports_count,
    (SELECT COUNT(*) FROM audit_log) as audit_count;
