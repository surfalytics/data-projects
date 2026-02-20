-- =============================================================================
-- 05-sink-to-kafka.sql
-- =============================================================================
-- Demonstrates writing Flink SQL query results back to Kafka topics.
-- This is the "sink" side of a streaming pipeline: source -> transform -> sink.
--
-- Flink supports two Kafka sink modes:
--   1. 'kafka' connector       -- Append-only sink (for INSERT-only results)
--   2. 'upsert-kafka' connector -- Upsert sink (for results with updates/deletes)
--
-- Prerequisites:
--   - Tables from 01-create-kafka-tables.sql must exist.
--   - Sample data must be flowing into the source topics.
-- =============================================================================


-- =============================================================================
-- Sink 1: Enriched orders to Kafka (Append-Only)
-- =============================================================================
-- Creates a sink table for enriched order events.
-- Uses the standard 'kafka' connector for append-only writes.
-- Each enriched order is written once as a new record.
-- =============================================================================

CREATE TABLE enriched_orders_sink (
    order_id        STRING,
    customer_name   STRING,
    customer_email  STRING,
    product_name    STRING,
    product_category STRING,
    quantity        INT,
    amount          DECIMAL(10, 2),
    order_status    STRING,
    order_time      TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',                            -- Standard Kafka connector
    'topic' = 'enriched-orders',                      -- Output topic
    'properties.bootstrap.servers' = 'kafka:29092',   -- Kafka broker
    'format' = 'json',                                -- Output format
    'json.timestamp-format.standard' = 'ISO-8601'     -- Timestamp format
);

-- Insert enriched orders into the sink
-- This creates a continuously running Flink job that reads from source tables,
-- joins them, and writes the enriched result to the 'enriched-orders' topic.
INSERT INTO enriched_orders_sink
SELECT
    o.order_id,
    c.first_name || ' ' || c.last_name  AS customer_name,
    c.email                              AS customer_email,
    p.product_name,
    p.category                           AS product_category,
    o.quantity,
    o.amount,
    o.order_status,
    o.order_time
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
INNER JOIN products AS p
    ON o.product_id = p.product_id;


-- =============================================================================
-- Sink 2: Order metrics per minute to Kafka (Upsert)
-- =============================================================================
-- Creates an upsert-kafka sink for windowed aggregation results.
-- Upsert mode is required because windowed aggregations can produce updates
-- (e.g., late-arriving data updating a window result).
--
-- The PRIMARY KEY defines the upsert key: records with the same key are
-- treated as updates (overwrites), and null-value records are deletes.
-- =============================================================================

CREATE TABLE order_metrics_per_minute_sink (
    window_start    TIMESTAMP(3),        -- Start of the 1-minute window
    window_end      TIMESTAMP(3),        -- End of the 1-minute window
    order_count     BIGINT,              -- Number of orders in the window
    total_revenue   DECIMAL(10, 2),      -- Sum of order amounts
    avg_order_value DECIMAL(10, 2),      -- Average order value
    -- Primary key for upsert semantics
    PRIMARY KEY (window_start) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',                     -- Upsert Kafka connector
    'topic' = 'order-metrics-per-minute',             -- Output topic
    'properties.bootstrap.servers' = 'kafka:29092',   -- Kafka broker
    'key.format' = 'json',                            -- Key serialization format
    'value.format' = 'json'                           -- Value serialization format
);

-- Insert windowed metrics into the sink
INSERT INTO order_metrics_per_minute_sink
SELECT
    TUMBLE_START(order_time, INTERVAL '1' MINUTE)  AS window_start,
    TUMBLE_END(order_time, INTERVAL '1' MINUTE)    AS window_end,
    COUNT(*)                                        AS order_count,
    SUM(amount)                                     AS total_revenue,
    CAST(AVG(amount) AS DECIMAL(10, 2))             AS avg_order_value
FROM orders
GROUP BY TUMBLE(order_time, INTERVAL '1' MINUTE);


-- =============================================================================
-- Sink 3: Revenue by category to Kafka (Upsert)
-- =============================================================================
-- Continuous revenue aggregation by product category.
-- Uses upsert-kafka because this is a non-windowed aggregation that
-- continuously updates as new orders arrive.
-- =============================================================================

CREATE TABLE revenue_by_category_sink (
    category        STRING,              -- Product category
    order_count     BIGINT,              -- Running order count
    total_revenue   DECIMAL(10, 2),      -- Running total revenue
    avg_order_value DECIMAL(10, 2),      -- Running average order value
    PRIMARY KEY (category) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'revenue-by-category',
    'properties.bootstrap.servers' = 'kafka:29092',
    'key.format' = 'json',
    'value.format' = 'json'
);

INSERT INTO revenue_by_category_sink
SELECT
    p.category,
    COUNT(*)                              AS order_count,
    SUM(o.amount)                         AS total_revenue,
    CAST(AVG(o.amount) AS DECIMAL(10, 2)) AS avg_order_value
FROM orders AS o
INNER JOIN products AS p
    ON o.product_id = p.product_id
GROUP BY p.category;


-- =============================================================================
-- Sink 4: Order status changes to Kafka (Append-Only)
-- =============================================================================
-- Forwards the raw order stream filtered to specific statuses.
-- This is a simple filter-and-forward pattern.
-- =============================================================================

CREATE TABLE high_value_orders_sink (
    order_id        STRING,
    customer_id     STRING,
    amount          DECIMAL(10, 2),
    order_status    STRING,
    order_time      TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'high-value-orders',
    'properties.bootstrap.servers' = 'kafka:29092',
    'format' = 'json'
);

-- Only forward orders above $100
INSERT INTO high_value_orders_sink
SELECT
    order_id,
    customer_id,
    amount,
    order_status,
    order_time
FROM orders
WHERE amount > 100.00;
