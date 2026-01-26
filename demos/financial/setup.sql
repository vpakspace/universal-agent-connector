-- Financial Reporting Demo Database Setup
-- Creates sample financial database with accounts, transactions, categories, and budgets

-- Drop existing tables if they exist
DROP TABLE IF EXISTS budgets CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;

-- Create accounts table
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    account_number VARCHAR(100),
    balance DECIMAL(15, 2) DEFAULT 0.00,
    currency VARCHAR(10) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category_type VARCHAR(50) NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    category_id INTEGER REFERENCES categories(id),
    transaction_date DATE NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,
    description TEXT,
    transaction_type VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create budgets table
CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    budgeted_amount DECIMAL(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample accounts
INSERT INTO accounts (name, account_type, account_number, balance, currency) VALUES
('Main Checking', 'checking', 'CHK-001', 50000.00, 'USD'),
('Savings Account', 'savings', 'SAV-001', 150000.00, 'USD'),
('Business Account', 'checking', 'CHK-002', 75000.00, 'USD'),
('Investment Account', 'investment', 'INV-001', 250000.00, 'USD'),
('Credit Card', 'credit', 'CC-001', -5000.00, 'USD');

-- Insert revenue categories
INSERT INTO categories (name, category_type, parent_id) VALUES
('Revenue', 'revenue', NULL),
('Product Sales', 'revenue', 1),
('Service Revenue', 'revenue', 1),
('Subscription Revenue', 'revenue', 1),
('Other Income', 'revenue', 1);

-- Insert expense categories
INSERT INTO categories (name, category_type, parent_id) VALUES
('Expenses', 'expense', NULL),
('Salaries', 'expense', 7),
('Marketing', 'expense', 7),
('Office Rent', 'expense', 7),
('Software', 'expense', 7),
('Utilities', 'expense', 7),
('Travel', 'expense', 7),
('Professional Services', 'expense', 7),
('Supplies', 'expense', 7);

-- Insert sample transactions (last 6 months)
INSERT INTO transactions (account_id, category_id, transaction_date, amount, description, transaction_type, reference_number) VALUES
-- Revenue transactions
(1, 2, '2024-01-15', 5000.00, 'Product sale - Q1', 'credit', 'INV-2024-001'),
(1, 2, '2024-01-20', 3200.00, 'Product sale - Q2', 'credit', 'INV-2024-002'),
(1, 3, '2024-01-25', 1500.00, 'Consulting services', 'credit', 'INV-2024-003'),
(1, 4, '2024-01-01', 12000.00, 'Monthly subscriptions', 'credit', 'SUB-2024-01'),
(1, 2, '2024-01-10', 2800.00, 'Product sale - Q3', 'credit', 'INV-2024-004'),

(1, 2, '2023-12-15', 4500.00, 'Product sale - Dec', 'credit', 'INV-2023-120'),
(1, 3, '2023-12-20', 2000.00, 'Consulting services', 'credit', 'INV-2023-121'),
(1, 4, '2023-12-01', 12000.00, 'Monthly subscriptions', 'credit', 'SUB-2023-12'),
(1, 2, '2023-12-10', 3500.00, 'Product sale - Dec', 'credit', 'INV-2023-119'),

(1, 2, '2023-11-15', 4200.00, 'Product sale - Nov', 'credit', 'INV-2023-110'),
(1, 3, '2023-11-20', 1800.00, 'Consulting services', 'credit', 'INV-2023-111'),
(1, 4, '2023-11-01', 12000.00, 'Monthly subscriptions', 'credit', 'SUB-2023-11'),

-- Expense transactions
(1, 8, '2024-01-05', -50000.00, 'Monthly payroll', 'debit', 'PAY-2024-01'),
(1, 9, '2024-01-10', -5000.00, 'Marketing campaign', 'debit', 'MKT-2024-01'),
(1, 10, '2024-01-01', -8000.00, 'Office rent - January', 'debit', 'RENT-2024-01'),
(1, 11, '2024-01-15', -2000.00, 'Software subscriptions', 'debit', 'SW-2024-01'),
(1, 12, '2024-01-20', -1500.00, 'Utilities - January', 'debit', 'UTIL-2024-01'),
(1, 13, '2024-01-25', -3000.00, 'Business travel', 'debit', 'TRV-2024-01'),

(1, 8, '2023-12-05', -50000.00, 'Monthly payroll', 'debit', 'PAY-2023-12'),
(1, 9, '2023-12-10', -4500.00, 'Marketing campaign', 'debit', 'MKT-2023-12'),
(1, 10, '2023-12-01', -8000.00, 'Office rent - December', 'debit', 'RENT-2023-12'),
(1, 11, '2023-12-15', -2000.00, 'Software subscriptions', 'debit', 'SW-2023-12'),
(1, 12, '2023-12-20', -1500.00, 'Utilities - December', 'debit', 'UTIL-2023-12'),

(1, 8, '2023-11-05', -50000.00, 'Monthly payroll', 'debit', 'PAY-2023-11'),
(1, 9, '2023-11-10', -4000.00, 'Marketing campaign', 'debit', 'MKT-2023-11'),
(1, 10, '2023-11-01', -8000.00, 'Office rent - November', 'debit', 'RENT-2023-11'),
(1, 11, '2023-11-15', -2000.00, 'Software subscriptions', 'debit', 'SW-2023-11'),
(1, 12, '2023-11-20', -1500.00, 'Utilities - November', 'debit', 'UTIL-2023-11');

-- Insert sample budgets
INSERT INTO budgets (category_id, period_start, period_end, budgeted_amount) VALUES
(8, '2024-01-01', '2024-12-31', 600000.00),  -- Annual salary budget
(9, '2024-01-01', '2024-12-31', 60000.00),   -- Annual marketing budget
(10, '2024-01-01', '2024-12-31', 96000.00),  -- Annual rent budget
(11, '2024-01-01', '2024-12-31', 24000.00),  -- Annual software budget
(12, '2024-01-01', '2024-12-31', 18000.00);  -- Annual utilities budget

-- Create indexes for better query performance
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_transaction_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_transaction_type ON transactions(transaction_type);
CREATE INDEX idx_categories_category_type ON categories(category_type);
CREATE INDEX idx_budgets_category_id ON budgets(category_id);
CREATE INDEX idx_budgets_period ON budgets(period_start, period_end);

-- Update account balances based on transactions
UPDATE accounts a
SET balance = (
    SELECT COALESCE(SUM(
        CASE 
            WHEN t.transaction_type = 'credit' THEN t.amount
            WHEN t.transaction_type = 'debit' THEN -t.amount
            ELSE 0
        END
    ), 0)
    FROM transactions t
    WHERE t.account_id = a.id
) + (
    CASE 
        WHEN a.account_type = 'credit' THEN -5000.00
        ELSE 0
    END
)
WHERE a.id IN (1, 2, 3, 4, 5);

-- Display summary
SELECT 
    'Setup Complete!' as status,
    (SELECT COUNT(*) FROM accounts) as accounts,
    (SELECT COUNT(*) FROM transactions) as transactions,
    (SELECT COUNT(*) FROM categories) as categories,
    (SELECT COUNT(*) FROM budgets) as budgets,
    (SELECT ROUND(SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END), 2) 
     FROM transactions WHERE transaction_date >= '2024-01-01') as january_net;

