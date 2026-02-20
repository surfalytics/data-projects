-- =============================================================
-- Module 9 Capstone: E-Commerce MySQL Schema
-- This script initializes the transactional database that
-- Debezium will capture changes from via CDC.
-- =============================================================

CREATE DATABASE IF NOT EXISTS ecommerce;
USE ecommerce;

-- ----- Customers -----
CREATE TABLE IF NOT EXISTS customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ----- Products -----
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(50) NOT NULL UNIQUE,
    price DECIMAL(10,2) NOT NULL,
    category VARCHAR(100) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ----- Orders -----
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    status ENUM('pending','confirmed','shipped','delivered','cancelled','returned') DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

-- ----- Order Items -----
CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- ----- Inventory Log -----
CREATE TABLE IF NOT EXISTS inventory_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    change_quantity INT NOT NULL,
    reason VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- =============================================================
-- Seed Data: 20 Products across 5 Categories
-- =============================================================

INSERT INTO products (name, description, sku, price, category, stock_quantity) VALUES
-- Electronics (4 products)
('Wireless Bluetooth Headphones', 'Premium noise-cancelling over-ear headphones with 30-hour battery life', 'ELEC-HP-001', 149.99, 'Electronics', 200),
('USB-C Fast Charger 65W', 'GaN technology charger compatible with laptops, tablets, and phones', 'ELEC-CH-002', 39.99, 'Electronics', 500),
('4K Webcam with Microphone', 'Ultra HD webcam with auto-focus and built-in noise-reducing mic', 'ELEC-WC-003', 89.99, 'Electronics', 150),
('Portable Bluetooth Speaker', 'Waterproof speaker with 360-degree sound and 12-hour playtime', 'ELEC-SP-004', 59.99, 'Electronics', 300),

-- Clothing (4 products)
('Classic Fit Cotton T-Shirt', '100% organic cotton crew neck tee in multiple colors', 'CLTH-TS-001', 24.99, 'Clothing', 1000),
('Slim Fit Stretch Jeans', 'Comfortable stretch denim with modern slim fit', 'CLTH-JN-002', 69.99, 'Clothing', 400),
('Lightweight Running Jacket', 'Water-resistant jacket with reflective details for night runs', 'CLTH-JK-003', 89.99, 'Clothing', 250),
('Merino Wool Beanie', 'Soft breathable beanie perfect for cold weather', 'CLTH-BN-004', 29.99, 'Clothing', 600),

-- Home & Kitchen (4 products)
('Stainless Steel French Press', '34oz double-wall insulated French press coffee maker', 'HOME-FP-001', 34.99, 'Home & Kitchen', 350),
('Non-Stick Ceramic Frying Pan', '12-inch pan with PFOA-free ceramic coating', 'HOME-FP-002', 44.99, 'Home & Kitchen', 280),
('Bamboo Cutting Board Set', 'Set of 3 eco-friendly cutting boards in graduated sizes', 'HOME-CB-003', 27.99, 'Home & Kitchen', 450),
('Smart LED Desk Lamp', 'Adjustable color temperature desk lamp with USB charging port', 'HOME-DL-004', 54.99, 'Home & Kitchen', 200),

-- Sports & Outdoors (4 products)
('Yoga Mat Premium 6mm', 'Non-slip TPE yoga mat with alignment markers', 'SPRT-YM-001', 39.99, 'Sports & Outdoors', 500),
('Resistance Band Set', '5-piece latex resistance bands with door anchor and carry bag', 'SPRT-RB-002', 19.99, 'Sports & Outdoors', 700),
('Insulated Water Bottle 32oz', 'Vacuum insulated stainless steel bottle keeps drinks cold 24hrs', 'SPRT-WB-003', 29.99, 'Sports & Outdoors', 800),
('Hiking Backpack 40L', 'Lightweight daypack with hydration system compatibility', 'SPRT-BP-004', 79.99, 'Sports & Outdoors', 180),

-- Books & Media (4 products)
('Data Streaming Fundamentals', 'Comprehensive guide to event-driven architectures', 'BOOK-DS-001', 49.99, 'Books & Media', 150),
('The Art of Clean Code', 'Best practices for writing maintainable software', 'BOOK-CC-002', 39.99, 'Books & Media', 200),
('Wireless Earbuds Audiobook Bundle', 'Earbuds bundled with 3-month audiobook subscription', 'BOOK-AB-003', 79.99, 'Books & Media', 100),
('Programming Puzzle Cards', 'Deck of 52 coding challenges for daily practice', 'BOOK-PC-004', 14.99, 'Books & Media', 900);

-- =============================================================
-- Seed Data: 10 Initial Customers
-- =============================================================

INSERT INTO customers (email, first_name, last_name, phone) VALUES
('alice.johnson@example.com', 'Alice', 'Johnson', '+1-555-0101'),
('bob.smith@example.com', 'Bob', 'Smith', '+1-555-0102'),
('carol.williams@example.com', 'Carol', 'Williams', '+1-555-0103'),
('david.brown@example.com', 'David', 'Brown', '+1-555-0104'),
('emma.davis@example.com', 'Emma', 'Davis', '+1-555-0105'),
('frank.miller@example.com', 'Frank', 'Miller', '+1-555-0106'),
('grace.wilson@example.com', 'Grace', 'Wilson', '+1-555-0107'),
('henry.moore@example.com', 'Henry', 'Moore', '+1-555-0108'),
('irene.taylor@example.com', 'Irene', 'Taylor', '+1-555-0109'),
('jack.anderson@example.com', 'Jack', 'Anderson', '+1-555-0110');
