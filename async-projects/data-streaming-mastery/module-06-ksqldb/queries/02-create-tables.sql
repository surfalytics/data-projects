-- =============================================================================
-- 02-create-tables.sql
-- Create ksqlDB TABLES from Kafka topics.
--
-- Tables represent the *latest state* for each key. When a new message
-- arrives with the same PRIMARY KEY, ksqlDB updates the row (upsert).
-- This makes tables ideal for reference/lookup data like customers and
-- products.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Table: customers_table
-- Source topic: "customers"
-- PRIMARY KEY = customer_id: ksqlDB will keep only the latest record per
-- customer. If a customer updates their email, the table reflects the change.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customers_table (
    customer_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    email VARCHAR,
    region VARCHAR
) WITH (
    KAFKA_TOPIC = 'customers',
    VALUE_FORMAT = 'JSON'
);

-- ---------------------------------------------------------------------------
-- Table: products_table
-- Source topic: "products"
-- PRIMARY KEY = product_id: latest product details per product.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products_table (
    product_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    category VARCHAR,
    price DOUBLE
) WITH (
    KAFKA_TOPIC = 'products',
    VALUE_FORMAT = 'JSON'
);

-- ---------------------------------------------------------------------------
-- Verify: list all tables to confirm creation.
-- ---------------------------------------------------------------------------
-- SHOW TABLES;
