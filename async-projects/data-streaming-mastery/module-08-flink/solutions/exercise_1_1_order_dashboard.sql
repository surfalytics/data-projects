-- =============================================================================
-- Solution: Exercise 1.1 -- Real-Time Order Dashboard
-- =============================================================================
-- Creates a 5-minute tumbling window aggregation of order metrics and writes
-- the results to a Kafka upsert topic.
--
-- Run the table creation from sql/01-create-kafka-tables.sql first.
-- =============================================================================

-- Step 1: Create the sink table for the dashboard
CREATE TABLE order_dashboard_5min_sink (
    window_start      TIMESTAMP(3),
    window_end        TIMESTAMP(3),
    order_count       BIGINT,
    total_revenue     DECIMAL(12, 2),
    avg_order_value   DECIMAL(10, 2),
    distinct_customers BIGINT,
    PRIMARY KEY (window_start) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'order-dashboard-5min',
    'properties.bootstrap.servers' = 'kafka:29092',
    'key.format' = 'json',
    'value.format' = 'json'
);

-- Step 2: Insert windowed aggregation results
INSERT INTO order_dashboard_5min_sink
SELECT
    TUMBLE_START(order_time, INTERVAL '5' MINUTE)       AS window_start,
    TUMBLE_END(order_time, INTERVAL '5' MINUTE)         AS window_end,
    COUNT(*)                                             AS order_count,
    SUM(amount)                                          AS total_revenue,
    CAST(AVG(amount) AS DECIMAL(10, 2))                  AS avg_order_value,
    COUNT(DISTINCT customer_id)                          AS distinct_customers
FROM orders
GROUP BY TUMBLE(order_time, INTERVAL '5' MINUTE);
