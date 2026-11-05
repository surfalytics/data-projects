-- ============================================================
-- E-Commerce Schema for CDC with Debezium (Module 05)
-- ============================================================
-- This schema creates a realistic e-commerce database that
-- demonstrates various CDC scenarios: inserts, updates, deletes,
-- foreign key relationships, and ENUM columns.
-- ============================================================

USE ecommerce;

-- ----------------------------------------------------------
-- Customers
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    email       VARCHAR(255) NOT NULL UNIQUE,
    first_name  VARCHAR(100) NOT NULL,
    last_name   VARCHAR(100) NOT NULL,
    phone       VARCHAR(20),
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_customers_email (email),
    INDEX idx_customers_name (last_name, first_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Addresses
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS addresses (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    customer_id  INT NOT NULL,
    street       VARCHAR(255) NOT NULL,
    city         VARCHAR(100) NOT NULL,
    state        VARCHAR(50) NOT NULL,
    zip_code     VARCHAR(20) NOT NULL,
    country      VARCHAR(50) NOT NULL DEFAULT 'US',
    is_default   BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_addresses_customer FOREIGN KEY (customer_id)
        REFERENCES customers (id) ON DELETE CASCADE,
    INDEX idx_addresses_customer (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Products
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    sku             VARCHAR(50) NOT NULL UNIQUE,
    price           DECIMAL(10, 2) NOT NULL,
    category        VARCHAR(100) NOT NULL,
    stock_quantity  INT NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_products_sku (sku),
    INDEX idx_products_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Orders
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id                   INT AUTO_INCREMENT PRIMARY KEY,
    customer_id          INT NOT NULL,
    shipping_address_id  INT,
    status               ENUM('pending', 'confirmed', 'shipped', 'delivered', 'cancelled', 'returned')
                         NOT NULL DEFAULT 'pending',
    total_amount         DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id)
        REFERENCES customers (id) ON DELETE CASCADE,
    CONSTRAINT fk_orders_address FOREIGN KEY (shipping_address_id)
        REFERENCES addresses (id) ON DELETE SET NULL,
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Order Items
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS order_items (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    order_id    INT NOT NULL,
    product_id  INT NOT NULL,
    quantity    INT NOT NULL DEFAULT 1,
    unit_price  DECIMAL(10, 2) NOT NULL,
    subtotal    DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id)
        REFERENCES orders (id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id)
        REFERENCES products (id) ON DELETE CASCADE,
    INDEX idx_order_items_order (order_id),
    INDEX idx_order_items_product (product_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ----------------------------------------------------------
-- Inventory
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    product_id    INT NOT NULL,
    warehouse     VARCHAR(100) NOT NULL,
    quantity      INT NOT NULL DEFAULT 0,
    last_updated  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id)
        REFERENCES products (id) ON DELETE CASCADE,
    INDEX idx_inventory_product (product_id),
    INDEX idx_inventory_warehouse (warehouse)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- ============================================================
-- Seed Data
-- ============================================================

-- 10 Products
INSERT INTO products (name, description, sku, price, category, stock_quantity) VALUES
    ('Wireless Mouse',        'Ergonomic wireless mouse with USB receiver',     'ELEC-MOUSE-001', 29.99,  'Electronics',    150),
    ('Mechanical Keyboard',   'RGB mechanical keyboard with Cherry MX switches','ELEC-KEYBD-001', 89.99,  'Electronics',    75),
    ('USB-C Hub',             '7-in-1 USB-C hub with HDMI and ethernet',       'ELEC-HUB-001',   49.99,  'Electronics',    200),
    ('Laptop Stand',          'Adjustable aluminum laptop stand',               'ACCS-STAND-001', 39.99,  'Accessories',    120),
    ('Webcam HD',             '1080p HD webcam with built-in microphone',       'ELEC-WCAM-001',  59.99,  'Electronics',    90),
    ('Noise-Cancelling Headphones', 'Over-ear ANC headphones with 30h battery','AUDIO-HDPH-001', 199.99, 'Audio',          60),
    ('Monitor 27"',           '27-inch 4K IPS monitor',                        'DISP-MON-001',   349.99, 'Displays',       40),
    ('Desk Lamp',             'LED desk lamp with adjustable brightness',       'ACCS-LAMP-001',  24.99,  'Accessories',    180),
    ('Cable Management Kit',  'Cable clips, sleeves, and ties bundle',         'ACCS-CABLE-001', 14.99,  'Accessories',    300),
    ('Portable SSD 1TB',      '1TB NVMe portable SSD, USB 3.2',               'STOR-SSD-001',   99.99,  'Storage',        100);

-- 5 Customers
INSERT INTO customers (email, first_name, last_name, phone) VALUES
    ('john.doe@example.com',    'John',    'Doe',      '555-0101'),
    ('jane.smith@example.com',  'Jane',    'Smith',    '555-0102'),
    ('bob.wilson@example.com',  'Bob',     'Wilson',   '555-0103'),
    ('alice.brown@example.com', 'Alice',   'Brown',    '555-0104'),
    ('charlie.davis@example.com','Charlie', 'Davis',   '555-0105');

-- Addresses for customers
INSERT INTO addresses (customer_id, street, city, state, zip_code, country, is_default) VALUES
    (1, '123 Main St',    'Springfield', 'IL', '62701', 'US', TRUE),
    (2, '456 Oak Ave',    'Portland',    'OR', '97201', 'US', TRUE),
    (3, '789 Pine Rd',    'Austin',      'TX', '73301', 'US', TRUE),
    (4, '321 Elm Blvd',   'Denver',      'CO', '80201', 'US', TRUE),
    (5, '654 Maple Dr',   'Seattle',     'WA', '98101', 'US', TRUE);

-- A few initial orders
INSERT INTO orders (customer_id, shipping_address_id, status, total_amount) VALUES
    (1, 1, 'delivered',  119.97),
    (2, 2, 'shipped',     89.99),
    (3, 3, 'pending',    249.98);

-- Order items for the initial orders
INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) VALUES
    (1, 1, 1, 29.99,  29.99),
    (1, 2, 1, 89.99,  89.99),
    (2, 2, 1, 89.99,  89.99),
    (3, 6, 1, 199.99, 199.99),
    (3, 4, 1, 39.99,  39.99);  -- Note: subtotal intentionally 39.99, total is 249.98 to include tax concept

-- Inventory across warehouses
INSERT INTO inventory (product_id, warehouse, quantity) VALUES
    (1,  'warehouse-east', 80),
    (1,  'warehouse-west', 70),
    (2,  'warehouse-east', 40),
    (2,  'warehouse-west', 35),
    (3,  'warehouse-east', 100),
    (3,  'warehouse-west', 100),
    (4,  'warehouse-east', 60),
    (5,  'warehouse-east', 50),
    (5,  'warehouse-west', 40),
    (6,  'warehouse-east', 30),
    (6,  'warehouse-west', 30),
    (7,  'warehouse-east', 25),
    (7,  'warehouse-west', 15),
    (8,  'warehouse-east', 90),
    (8,  'warehouse-west', 90),
    (9,  'warehouse-east', 150),
    (9,  'warehouse-west', 150),
    (10, 'warehouse-east', 50),
    (10, 'warehouse-west', 50);
