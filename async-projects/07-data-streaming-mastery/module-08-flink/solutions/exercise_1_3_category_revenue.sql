-- =============================================================================
-- Solution: Exercise 1.3 -- Join with Windowed Output
-- =============================================================================
-- Aggregates revenue by product category within 1-minute tumbling windows.
-- (Orders are windowed per product, then joined to products.)
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

-- Step 2: Window the orders per product, then join and group by category.
-- The window must come before the join. A regular join removes the
-- time attribute, and window functions need it.
INSERT INTO revenue_by_category_per_minute_sink
SELECT
    w.window_start,
    w.window_end,
    p.category,
    SUM(w.order_count)                                   AS order_count,
    CAST(SUM(w.total_revenue) AS DECIMAL(12, 2))         AS total_revenue,
    CAST(SUM(w.total_revenue) / SUM(w.order_count) AS DECIMAL(10, 2)) AS avg_order_value
FROM (
    SELECT
        window_start,
        window_end,
        product_id,
        COUNT(*)                                         AS order_count,
        SUM(amount)                                      AS total_revenue
    FROM TABLE(
        TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE))
    GROUP BY window_start, window_end, product_id
) AS w
INNER JOIN products AS p
    ON w.product_id = p.product_id
GROUP BY w.window_start, w.window_end, p.category;
