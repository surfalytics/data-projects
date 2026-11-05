-- =============================================================
-- Module 9 Capstone: ksqlDB Streams and Tables
-- These queries create the real-time stream processing layer
-- that enriches, joins, and aggregates CDC events.
-- =============================================================

-- -------------------------------------------------------
-- 1. Source Streams from Debezium CDC Topics
-- -------------------------------------------------------

-- Orders stream from Debezium CDC
CREATE STREAM IF NOT EXISTS orders_stream (
    id INT KEY,
    customer_id INT,
    status VARCHAR,
    total_amount DOUBLE,
    created_at BIGINT,
    updated_at BIGINT
) WITH (
    KAFKA_TOPIC = 'ecommerce.ecommerce.orders',
    VALUE_FORMAT = 'AVRO'
);

-- Order items stream from Debezium CDC
CREATE STREAM IF NOT EXISTS order_items_stream (
    id INT KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DOUBLE,
    subtotal DOUBLE
) WITH (
    KAFKA_TOPIC = 'ecommerce.ecommerce.order_items',
    VALUE_FORMAT = 'AVRO'
);

-- -------------------------------------------------------
-- 2. Source Tables from Debezium CDC Topics
-- -------------------------------------------------------

-- Customers table (materialized from CDC log-compacted topic)
CREATE TABLE IF NOT EXISTS customers_table (
    id INT PRIMARY KEY,
    email VARCHAR,
    first_name VARCHAR,
    last_name VARCHAR,
    phone VARCHAR,
    created_at BIGINT,
    updated_at BIGINT
) WITH (
    KAFKA_TOPIC = 'ecommerce.ecommerce.customers',
    VALUE_FORMAT = 'AVRO'
);

-- Products table (materialized from CDC log-compacted topic)
CREATE TABLE IF NOT EXISTS products_table (
    id INT PRIMARY KEY,
    name VARCHAR,
    description VARCHAR,
    sku VARCHAR,
    price DOUBLE,
    category VARCHAR,
    stock_quantity INT,
    created_at BIGINT
) WITH (
    KAFKA_TOPIC = 'ecommerce.ecommerce.products',
    VALUE_FORMAT = 'AVRO'
);

-- -------------------------------------------------------
-- 3. Enriched Orders Stream
--    Join orders with customers to get customer details.
-- -------------------------------------------------------

CREATE STREAM IF NOT EXISTS orders_enriched
WITH (
    KAFKA_TOPIC = 'ORDERS_ENRICHED',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    o.id AS order_id,
    c.first_name + ' ' + c.last_name AS customer_name,
    c.email AS customer_email,
    o.status AS status,
    o.total_amount AS total_amount,
    o.created_at AS created_at,
    o.updated_at AS updated_at
FROM orders_stream o
LEFT JOIN customers_table c ON o.customer_id = c.id
EMIT CHANGES;

-- -------------------------------------------------------
-- 4. Revenue Per Minute (1-minute tumbling window)
-- -------------------------------------------------------

CREATE TABLE IF NOT EXISTS revenue_per_minute
WITH (
    KAFKA_TOPIC = 'REVENUE_PER_MINUTE',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    SUM(total_amount) AS total_revenue,
    COUNT(*) AS order_count,
    SUM(total_amount) / COUNT(*) AS avg_order_value
FROM orders_stream
WINDOW TUMBLING (SIZE 1 MINUTE)
WHERE status != 'cancelled' AND status != 'returned'
GROUP BY 1
EMIT CHANGES;

-- -------------------------------------------------------
-- 5. Revenue Per Category (5-minute tumbling window)
--    Join order_items with products to get category.
-- -------------------------------------------------------

CREATE STREAM IF NOT EXISTS order_items_with_category
WITH (
    KAFKA_TOPIC = 'ORDER_ITEMS_WITH_CATEGORY',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    oi.id AS item_id,
    oi.order_id AS order_id,
    p.category AS category,
    oi.subtotal AS subtotal,
    oi.quantity AS quantity
FROM order_items_stream oi
LEFT JOIN products_table p ON oi.product_id = p.id
EMIT CHANGES;

CREATE TABLE IF NOT EXISTS revenue_per_category
WITH (
    KAFKA_TOPIC = 'REVENUE_PER_CATEGORY',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    category,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    SUM(subtotal) AS revenue,
    COUNT(*) AS order_count
FROM order_items_with_category
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY category
EMIT CHANGES;

-- -------------------------------------------------------
-- 6. Top Customers (10-minute tumbling window)
-- -------------------------------------------------------

CREATE TABLE IF NOT EXISTS top_customers
WITH (
    KAFKA_TOPIC = 'TOP_CUSTOMERS',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    o.customer_id AS customer_id,
    LATEST_BY_OFFSET(c.first_name) + ' ' + LATEST_BY_OFFSET(c.last_name) AS customer_name,
    WINDOWSTART AS window_start,
    WINDOWEND AS window_end,
    SUM(o.total_amount) AS total_spent,
    COUNT(*) AS order_count
FROM orders_stream o
LEFT JOIN customers_table c ON o.customer_id = c.id
WINDOW TUMBLING (SIZE 10 MINUTES)
WHERE o.status != 'cancelled' AND o.status != 'returned'
GROUP BY o.customer_id
EMIT CHANGES;

-- -------------------------------------------------------
-- 7. Order Status Distribution
-- -------------------------------------------------------

CREATE TABLE IF NOT EXISTS order_status_counts
WITH (
    KAFKA_TOPIC = 'ORDER_STATUS_COUNTS',
    VALUE_FORMAT = 'AVRO',
    PARTITIONS = 1
) AS
SELECT
    status,
    COUNT(*) AS count
FROM orders_stream
GROUP BY status
EMIT CHANGES;
