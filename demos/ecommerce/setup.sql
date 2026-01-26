-- E-Commerce Demo Database Setup
-- Creates sample e-commerce database with customers, products, orders, etc.

-- Drop existing tables if they exist
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Create categories table
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    country VARCHAR(50) DEFAULT 'USA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_purchase_at TIMESTAMP
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    sku VARCHAR(100) UNIQUE,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    shipping_address TEXT,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50) DEFAULT 'pending'
);

-- Create order_items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

-- Insert sample categories
INSERT INTO categories (name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Home & Garden', 'Home improvement and garden supplies'),
('Books', 'Books and publications'),
('Sports', 'Sports and outdoor equipment'),
('Toys', 'Toys and games'),
('Beauty', 'Beauty and personal care products'),
('Food', 'Food and beverages');

-- Insert sample customers
INSERT INTO customers (email, first_name, last_name, phone, city, state, zip_code, created_at, last_purchase_at) VALUES
('john.doe@example.com', 'John', 'Doe', '555-0101', 'New York', 'NY', '10001', '2023-01-15', '2024-01-10'),
('jane.smith@example.com', 'Jane', 'Smith', '555-0102', 'Los Angeles', 'CA', '90001', '2023-02-20', '2024-01-12'),
('bob.johnson@example.com', 'Bob', 'Johnson', '555-0103', 'Chicago', 'IL', '60601', '2023-03-10', '2024-01-08'),
('alice.williams@example.com', 'Alice', 'Williams', '555-0104', 'Houston', 'TX', '77001', '2023-04-05', '2024-01-15'),
('charlie.brown@example.com', 'Charlie', 'Brown', '555-0105', 'Phoenix', 'AZ', '85001', '2023-05-12', '2024-01-11'),
('diana.davis@example.com', 'Diana', 'Davis', '555-0106', 'Philadelphia', 'PA', '19101', '2023-06-18', '2024-01-09'),
('edward.miller@example.com', 'Edward', 'Miller', '555-0107', 'San Antonio', 'TX', '78201', '2023-07-22', '2024-01-13'),
('fiona.wilson@example.com', 'Fiona', 'Wilson', '555-0108', 'San Diego', 'CA', '92101', '2023-08-30', '2024-01-14'),
('george.moore@example.com', 'George', 'Moore', '555-0109', 'Dallas', 'TX', '75201', '2023-09-14', '2024-01-07'),
('helen.taylor@example.com', 'Helen', 'Taylor', '555-0110', 'San Jose', 'CA', '95101', '2023-10-25', '2024-01-16');

-- Insert sample products
INSERT INTO products (name, description, category_id, price, cost, stock_quantity, sku) VALUES
-- Electronics
('Wireless Headphones', 'Premium noise-cancelling wireless headphones', 1, 199.99, 80.00, 50, 'ELEC-001'),
('Smart Watch', 'Fitness tracking smartwatch with heart rate monitor', 1, 299.99, 120.00, 30, 'ELEC-002'),
('Laptop Stand', 'Adjustable aluminum laptop stand', 1, 49.99, 15.00, 100, 'ELEC-003'),
('USB-C Cable', 'Fast charging USB-C cable, 6ft', 1, 19.99, 5.00, 200, 'ELEC-004'),
('Bluetooth Speaker', 'Portable waterproof Bluetooth speaker', 1, 79.99, 30.00, 75, 'ELEC-005'),

-- Clothing
('Cotton T-Shirt', '100% cotton comfortable t-shirt', 2, 24.99, 8.00, 150, 'CLTH-001'),
('Denim Jeans', 'Classic fit denim jeans', 2, 59.99, 25.00, 80, 'CLTH-002'),
('Winter Jacket', 'Warm winter jacket with hood', 2, 129.99, 50.00, 40, 'CLTH-003'),
('Running Shoes', 'Lightweight running shoes', 2, 89.99, 35.00, 60, 'CLTH-004'),
('Baseball Cap', 'Adjustable baseball cap', 2, 19.99, 6.00, 120, 'CLTH-005'),

-- Home & Garden
('Coffee Maker', 'Programmable drip coffee maker', 3, 79.99, 30.00, 45, 'HOME-001'),
('Garden Tool Set', 'Complete garden tool set with storage', 3, 49.99, 20.00, 35, 'HOME-002'),
('Throw Pillows', 'Set of 2 decorative throw pillows', 3, 29.99, 10.00, 90, 'HOME-003'),
('LED Light Bulbs', 'Pack of 4 energy-efficient LED bulbs', 3, 19.99, 7.00, 150, 'HOME-004'),
('Plant Pot', 'Ceramic plant pot with drainage', 3, 14.99, 5.00, 100, 'HOME-005'),

-- Books
('Python Programming', 'Complete guide to Python programming', 4, 39.99, 12.00, 25, 'BOOK-001'),
('Data Science Handbook', 'Comprehensive data science reference', 4, 49.99, 15.00, 20, 'BOOK-002'),
('Fiction Novel', 'Bestselling fiction novel', 4, 14.99, 5.00, 50, 'BOOK-003'),
('Cookbook', 'Collection of family recipes', 4, 24.99, 8.00, 30, 'BOOK-004'),
('History Book', 'World history comprehensive guide', 4, 34.99, 11.00, 15, 'BOOK-005');

-- Insert sample orders (last 6 months)
INSERT INTO orders (customer_id, order_date, status, total_amount, payment_method, payment_status) VALUES
(1, '2024-01-10 10:30:00', 'completed', 199.99, 'credit_card', 'paid'),
(2, '2024-01-12 14:20:00', 'completed', 299.99, 'paypal', 'paid'),
(3, '2024-01-08 09:15:00', 'completed', 49.99, 'credit_card', 'paid'),
(4, '2024-01-15 16:45:00', 'completed', 79.99, 'credit_card', 'paid'),
(5, '2024-01-11 11:00:00', 'completed', 24.99, 'credit_card', 'paid'),
(6, '2024-01-09 13:30:00', 'completed', 59.99, 'paypal', 'paid'),
(7, '2024-01-13 15:20:00', 'completed', 129.99, 'credit_card', 'paid'),
(8, '2024-01-14 10:00:00', 'completed', 89.99, 'credit_card', 'paid'),
(9, '2024-01-07 12:15:00', 'completed', 19.99, 'paypal', 'paid'),
(10, '2024-01-16 14:00:00', 'completed', 79.99, 'credit_card', 'paid'),

-- More orders for trend analysis
(1, '2023-12-15 10:30:00', 'completed', 49.99, 'credit_card', 'paid'),
(2, '2023-12-20 14:20:00', 'completed', 19.99, 'paypal', 'paid'),
(3, '2023-12-10 09:15:00', 'completed', 24.99, 'credit_card', 'paid'),
(4, '2023-12-25 16:45:00', 'completed', 39.99, 'credit_card', 'paid'),
(5, '2023-12-18 11:00:00', 'completed', 59.99, 'credit_card', 'paid'),
(1, '2023-11-20 10:30:00', 'completed', 79.99, 'credit_card', 'paid'),
(2, '2023-11-25 14:20:00', 'completed', 29.99, 'paypal', 'paid'),
(3, '2023-11-15 09:15:00', 'completed', 19.99, 'credit_card', 'paid'),
(4, '2023-11-30 16:45:00', 'completed', 49.99, 'credit_card', 'paid'),
(5, '2023-11-22 11:00:00', 'completed', 34.99, 'credit_card', 'paid');

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
-- January 2024 orders
(1, 1, 1, 199.99, 199.99),
(2, 2, 1, 299.99, 299.99),
(3, 3, 1, 49.99, 49.99),
(4, 5, 1, 79.99, 79.99),
(5, 6, 1, 24.99, 24.99),
(6, 7, 1, 59.99, 59.99),
(7, 8, 1, 129.99, 129.99),
(8, 9, 1, 89.99, 89.99),
(9, 10, 1, 19.99, 19.99),
(10, 11, 1, 79.99, 79.99),

-- December 2023 orders
(11, 3, 1, 49.99, 49.99),
(12, 4, 1, 19.99, 19.99),
(13, 6, 1, 24.99, 24.99),
(14, 16, 1, 39.99, 39.99),
(15, 7, 1, 59.99, 59.99),
(16, 5, 1, 79.99, 79.99),
(17, 13, 1, 29.99, 29.99),
(18, 4, 1, 19.99, 19.99),
(19, 3, 1, 49.99, 49.99),
(20, 17, 1, 34.99, 34.99);

-- Create indexes for better query performance
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_customers_email ON customers(email);

-- Update order totals (should match sum of order_items)
UPDATE orders o
SET total_amount = (
    SELECT COALESCE(SUM(subtotal), 0)
    FROM order_items oi
    WHERE oi.order_id = o.id
);

-- Display summary
SELECT 
    'Setup Complete!' as status,
    (SELECT COUNT(*) FROM customers) as customers,
    (SELECT COUNT(*) FROM products) as products,
    (SELECT COUNT(*) FROM orders) as orders,
    (SELECT COUNT(*) FROM categories) as categories;

