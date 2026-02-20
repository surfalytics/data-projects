-- =============================================================================
-- 01-create-kafka-tables.sql
-- =============================================================================
-- Creates Flink SQL tables backed by Kafka topics.
-- These tables act as the streaming sources for all subsequent SQL exercises.
--
-- Prerequisites:
--   - Kafka is running with the following topics pre-created (or auto-create enabled):
--     * orders
--     * customers
--     * products
--   - The Flink SQL Client is connected to the Flink cluster.
--   - The Kafka SQL connector JAR is available in Flink's classpath.
--
-- Usage:
--   Run these statements in the Flink SQL Client or submit via sql-client.sh.
-- =============================================================================

-- =============================================================================
-- Table: orders
-- =============================================================================
-- Represents a stream of incoming customer orders.
-- Each record contains the order details and an event timestamp.
-- The WATERMARK declaration tells Flink to use order_time as the event-time
-- column and tolerate up to 5 seconds of out-of-order-ness.
-- =============================================================================

CREATE TABLE orders (
    order_id        STRING,          -- Unique order identifier (UUID)
    customer_id     STRING,          -- FK to customers table
    product_id      STRING,          -- FK to products table
    quantity        INT,             -- Number of items ordered
    amount          DECIMAL(10, 2),  -- Total order amount in USD
    order_status    STRING,          -- Status: 'pending', 'confirmed', 'shipped', 'delivered'
    order_time      TIMESTAMP(3),    -- When the order was placed (event time)
    -- Watermark: allow events up to 5 seconds late
    WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',                                -- Use Kafka connector
    'topic' = 'orders',                                   -- Kafka topic name
    'properties.bootstrap.servers' = 'kafka:29092',       -- Kafka broker address
    'properties.group.id' = 'flink-orders-consumer',      -- Consumer group ID
    'scan.startup.mode' = 'earliest-offset',              -- Read from beginning
    'format' = 'json',                                    -- Message format
    'json.fail-on-missing-field' = 'false',               -- Don't fail on missing fields
    'json.ignore-parse-errors' = 'true'                   -- Skip malformed messages
);


-- =============================================================================
-- Table: customers
-- =============================================================================
-- Represents a stream of customer profile events.
-- In a real system, this might be a CDC stream from a customer database or
-- a compacted Kafka topic acting as a lookup table.
-- =============================================================================

CREATE TABLE customers (
    customer_id     STRING,          -- Unique customer identifier
    first_name      STRING,          -- Customer first name
    last_name       STRING,          -- Customer last name
    email           STRING,          -- Customer email address
    city            STRING,          -- City of residence
    state           STRING,          -- State/province
    country         STRING,          -- Country code (US, CA, etc.)
    created_at      TIMESTAMP(3),    -- When the customer record was created
    -- Watermark for event time processing
    WATERMARK FOR created_at AS created_at - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'customers',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-customers-consumer',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    'json.fail-on-missing-field' = 'false',
    'json.ignore-parse-errors' = 'true'
);


-- =============================================================================
-- Table: products
-- =============================================================================
-- Represents a stream of product catalog events.
-- Similar to customers, this might be a CDC stream or a compacted topic.
-- =============================================================================

CREATE TABLE products (
    product_id      STRING,          -- Unique product identifier
    product_name    STRING,          -- Human-readable product name
    category        STRING,          -- Product category (Electronics, Books, etc.)
    price           DECIMAL(10, 2),  -- Unit price in USD
    brand           STRING,          -- Brand name
    updated_at      TIMESTAMP(3),    -- When the product record was last updated
    -- Watermark for event time processing
    WATERMARK FOR updated_at AS updated_at - INTERVAL '10' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'products',
    'properties.bootstrap.servers' = 'kafka:29092',
    'properties.group.id' = 'flink-products-consumer',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json',
    'json.fail-on-missing-field' = 'false',
    'json.ignore-parse-errors' = 'true'
);


-- =============================================================================
-- Verification: Check that all tables were created
-- =============================================================================
-- After running the above CREATE TABLE statements, verify with:
-- SHOW TABLES;
--
-- Expected output:
--   orders
--   customers
--   products
-- =============================================================================
