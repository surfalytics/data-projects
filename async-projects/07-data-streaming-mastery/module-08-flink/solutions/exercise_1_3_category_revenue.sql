-- =============================================================================
-- Solution: Exercise 1.3 -- Multi-Table Join with Windowed Output
-- =============================================================================
-- Enriches orders with customer and product data, then aggregates revenue
-- by product category within 1-minute tumbling windows.
--
-- Run the table creation from sql/01-create-kafka-tables.sql first.
-- =============================================================================

-- Step 1: Create the Kafka sink table
CREATE TABLE revenue_by_category_per_minute_sink (
    window_start     TIMESTAMP(3),
    window_end       TIMESTAMP(3),
    category         STRING,
    order_count      BIGINT,
    total_revenue    DECIMAL(12, 2),
    avg_order_value  DECIMAL(10, 2),
    PRIMARY KEY (window_start, category) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'revenue-by-category-per-minute',
    'properties.bootstrap.servers' = 'kafka:29092',
    'key.format' = 'json',
    'value.format' = 'json'
);

-- Step 2: Join orders with customers and products, then aggregate by category
INSERT INTO revenue_by_category_per_minute_sink
SELECT
    TUMBLE_START(o.order_time, INTERVAL '1' MINUTE)     AS window_start,
    TUMBLE_END(o.order_time, INTERVAL '1' MINUTE)       AS window_end,
    p.category,
    COUNT(*)                                             AS order_count,
    SUM(o.amount)                                        AS total_revenue,
    CAST(AVG(o.amount) AS DECIMAL(10, 2))                AS avg_order_value
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
INNER JOIN products AS p
    ON o.product_id = p.product_id
GROUP BY
    TUMBLE(o.order_time, INTERVAL '1' MINUTE),
    p.category;
