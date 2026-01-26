-- SaaS Metrics Demo Database Setup
-- Creates sample SaaS database with users, subscriptions, plans, and events

-- Drop existing tables if they exist
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS subscriptions CASCADE;
DROP TABLE IF EXISTS plans CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

-- Create plans table
CREATE TABLE plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10, 2) NOT NULL,
    price_yearly DECIMAL(10, 2),
    features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create subscriptions table
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    plan_id INTEGER REFERENCES plans(id),
    status VARCHAR(50) DEFAULT 'active',
    billing_cycle VARCHAR(20) DEFAULT 'monthly',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    next_billing_date DATE,
    mrr DECIMAL(10, 2) NOT NULL
);

-- Create events table (user activity)
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample plans
INSERT INTO plans (name, description, price_monthly, price_yearly, features) VALUES
('Free', 'Basic features for individuals', 0.00, 0.00, '{"storage": "1GB", "users": 1, "support": "community"}'),
('Starter', 'Perfect for small teams', 29.99, 299.99, '{"storage": "10GB", "users": 5, "support": "email"}'),
('Professional', 'For growing businesses', 99.99, 999.99, '{"storage": "100GB", "users": 25, "support": "priority"}'),
('Enterprise', 'For large organizations', 299.99, 2999.99, '{"storage": "unlimited", "users": "unlimited", "support": "dedicated"}');

-- Insert sample users (last 12 months)
INSERT INTO users (email, first_name, last_name, company_name, created_at, last_login_at, status) VALUES
('user1@example.com', 'Alice', 'Johnson', 'Tech Corp', '2023-02-15', '2024-01-15', 'active'),
('user2@example.com', 'Bob', 'Smith', 'StartupXYZ', '2023-03-20', '2024-01-14', 'active'),
('user3@example.com', 'Charlie', 'Brown', 'Design Co', '2023-04-10', '2024-01-13', 'active'),
('user4@example.com', 'Diana', 'Williams', 'Marketing Pro', '2023-05-05', '2024-01-12', 'active'),
('user5@example.com', 'Edward', 'Davis', 'Consulting LLC', '2023-06-12', '2024-01-11', 'active'),
('user6@example.com', 'Fiona', 'Miller', 'Dev Studio', '2023-07-18', '2024-01-10', 'active'),
('user7@example.com', 'George', 'Wilson', 'Agency Inc', '2023-08-22', '2024-01-09', 'active'),
('user8@example.com', 'Helen', 'Moore', 'Services Co', '2023-09-30', '2024-01-08', 'active'),
('user9@example.com', 'Ivan', 'Taylor', 'Solutions Ltd', '2023-10-14', '2024-01-07', 'active'),
('user10@example.com', 'Julia', 'Anderson', 'Innovation Hub', '2023-11-25', '2024-01-06', 'active'),
('user11@example.com', 'Kevin', 'Thomas', 'Digital Works', '2023-12-10', '2024-01-05', 'active'),
('user12@example.com', 'Laura', 'Jackson', 'Creative Lab', '2024-01-02', '2024-01-16', 'active'),
('user13@example.com', 'Mike', 'White', 'Business Pro', '2024-01-05', '2024-01-15', 'active'),
('user14@example.com', 'Nancy', 'Harris', 'Growth Co', '2024-01-08', '2024-01-14', 'active'),
('user15@example.com', 'Oscar', 'Martin', 'Scale Inc', '2024-01-10', '2024-01-13', 'active'),
('churned1@example.com', 'Churned', 'User1', 'Old Corp', '2023-01-15', '2023-06-15', 'churned'),
('churned2@example.com', 'Churned', 'User2', 'Old Startup', '2023-02-20', '2023-07-20', 'churned'),
('churned3@example.com', 'Churned', 'User3', 'Old Design', '2023-03-10', '2023-08-10', 'churned');

-- Insert sample subscriptions
INSERT INTO subscriptions (user_id, plan_id, status, billing_cycle, started_at, next_billing_date, mrr) VALUES
-- Active subscriptions
(1, 2, 'active', 'monthly', '2023-02-15', '2024-02-15', 29.99),
(2, 3, 'active', 'monthly', '2023-03-20', '2024-02-20', 99.99),
(3, 2, 'active', 'yearly', '2023-04-10', '2024-04-10', 24.99),
(4, 3, 'active', 'monthly', '2023-05-05', '2024-02-05', 99.99),
(5, 4, 'active', 'monthly', '2023-06-12', '2024-02-12', 299.99),
(6, 2, 'active', 'monthly', '2023-07-18', '2024-02-18', 29.99),
(7, 3, 'active', 'yearly', '2023-08-22', '2024-08-22', 83.33),
(8, 2, 'active', 'monthly', '2023-09-30', '2024-02-29', 29.99),
(9, 3, 'active', 'monthly', '2023-10-14', '2024-02-14', 99.99),
(10, 4, 'active', 'monthly', '2023-11-25', '2024-02-25', 299.99),
(11, 2, 'active', 'monthly', '2023-12-10', '2024-02-10', 29.99),
(12, 3, 'active', 'monthly', '2024-01-02', '2024-02-02', 99.99),
(13, 2, 'active', 'monthly', '2024-01-05', '2024-02-05', 29.99),
(14, 3, 'active', 'monthly', '2024-01-08', '2024-02-08', 99.99),
(15, 4, 'active', 'monthly', '2024-01-10', '2024-02-10', 299.99),
-- Free tier users
(1, 1, 'active', 'monthly', '2023-01-15', NULL, 0.00),
-- Churned subscriptions
(16, 2, 'cancelled', 'monthly', '2023-01-15', NULL, 0.00),
(17, 3, 'cancelled', 'monthly', '2023-02-20', NULL, 0.00),
(18, 2, 'cancelled', 'monthly', '2023-03-10', NULL, 0.00);

-- Update cancelled_at for churned subscriptions
UPDATE subscriptions SET cancelled_at = started_at + INTERVAL '6 months' WHERE status = 'cancelled';

-- Insert sample events (user activity)
INSERT INTO events (user_id, event_type, event_data, created_at) VALUES
(1, 'user_signup', '{"source": "organic"}', '2023-02-15 10:00:00'),
(1, 'subscription_created', '{"plan": "starter"}', '2023-02-15 10:05:00'),
(1, 'feature_used', '{"feature": "dashboard"}', '2023-02-16 09:00:00'),
(2, 'user_signup', '{"source": "paid"}', '2023-03-20 11:00:00'),
(2, 'subscription_created', '{"plan": "professional"}', '2023-03-20 11:10:00'),
(2, 'feature_used', '{"feature": "api"}', '2023-03-21 10:00:00'),
(3, 'user_signup', '{"source": "referral"}', '2023-04-10 14:00:00'),
(3, 'subscription_created', '{"plan": "starter"}', '2023-04-10 14:15:00'),
(4, 'user_signup', '{"source": "organic"}', '2023-05-05 09:00:00'),
(4, 'subscription_created', '{"plan": "professional"}', '2023-05-05 09:20:00'),
(5, 'user_signup', '{"source": "paid"}', '2023-06-12 15:00:00'),
(5, 'subscription_created', '{"plan": "enterprise"}', '2023-06-12 15:30:00'),
(12, 'user_signup', '{"source": "organic"}', '2024-01-02 10:00:00'),
(12, 'subscription_created', '{"plan": "professional"}', '2024-01-02 10:10:00'),
(13, 'user_signup', '{"source": "paid"}', '2024-01-05 11:00:00'),
(13, 'subscription_created', '{"plan": "starter"}', '2024-01-05 11:05:00'),
(14, 'user_signup', '{"source": "referral"}', '2024-01-08 12:00:00'),
(14, 'subscription_created', '{"plan": "professional"}', '2024-01-08 12:15:00'),
(15, 'user_signup', '{"source": "organic"}', '2024-01-10 13:00:00'),
(15, 'subscription_created', '{"plan": "enterprise"}', '2024-01-10 13:20:00');

-- Create indexes for better query performance
CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_plan_id ON subscriptions(plan_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_started_at ON subscriptions(started_at);
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_events_created_at ON events(created_at);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_status ON users(status);

-- Display summary
SELECT 
    'Setup Complete!' as status,
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as active_subscriptions,
    (SELECT COUNT(*) FROM plans) as plans,
    (SELECT ROUND(SUM(mrr), 2) FROM subscriptions WHERE status = 'active') as total_mrr;

