-- =============================================================
-- Module 9 Capstone: PostgreSQL Analytics Sink Tables
-- These tables receive aggregated and enriched data from
-- ksqlDB via the JDBC Sink Connector or Python consumer.
-- =============================================================

-- ----- Enriched Orders -----
-- Each row represents an order joined with customer information.
CREATE TABLE IF NOT EXISTS orders_enriched (
    order_id INT PRIMARY KEY,
    customer_name VARCHAR(255),
    customer_email VARCHAR(255),
    status VARCHAR(50),
    total_amount DECIMAL(10,2),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- ----- Revenue Per Minute -----
-- Tumbling window (1 minute) aggregate of order revenue.
CREATE TABLE IF NOT EXISTS revenue_per_minute (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    total_revenue DECIMAL(12,2),
    order_count INT,
    avg_order_value DECIMAL(10,2),
    PRIMARY KEY (window_start, window_end)
);

-- ----- Revenue Per Category -----
-- Tumbling window (5 minutes) revenue breakdown by product category.
CREATE TABLE IF NOT EXISTS revenue_per_category (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    category VARCHAR(100) NOT NULL,
    revenue DECIMAL(12,2),
    order_count INT,
    PRIMARY KEY (window_start, window_end, category)
);

-- ----- Top Customers -----
-- Tumbling window (10 minutes) ranking of highest-spending customers.
CREATE TABLE IF NOT EXISTS top_customers (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    customer_id INT NOT NULL,
    customer_name VARCHAR(255),
    total_spent DECIMAL(12,2),
    order_count INT,
    PRIMARY KEY (window_start, window_end, customer_id)
);

-- ----- Order Status Counts -----
-- Current distribution of order statuses (continuously updated).
CREATE TABLE IF NOT EXISTS order_status_counts (
    status VARCHAR(50) PRIMARY KEY,
    count INT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Seed initial status rows so upserts work cleanly
INSERT INTO order_status_counts (status, count) VALUES
    ('pending', 0),
    ('confirmed', 0),
    ('shipped', 0),
    ('delivered', 0),
    ('cancelled', 0),
    ('returned', 0)
ON CONFLICT (status) DO NOTHING;
