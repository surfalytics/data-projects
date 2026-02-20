-- =============================================================================
-- Solution: Exercise 1.2 -- Sliding Window Anomaly Detection
-- =============================================================================
-- Detects periods of high order volume using a 10-minute sliding window
-- that advances every 1 minute. Only emits windows with > 15 orders.
--
-- Run the table creation from sql/01-create-kafka-tables.sql first.
-- =============================================================================

-- Step 1: Create a print sink for observing anomalies
CREATE TABLE anomaly_print_sink (
    window_start    TIMESTAMP(3),
    window_end      TIMESTAMP(3),
    order_count     BIGINT,
    avg_order_value DECIMAL(10, 2),
    total_revenue   DECIMAL(12, 2)
) WITH (
    'connector' = 'print'
);

-- Step 2: Insert sliding window results filtered by threshold
INSERT INTO anomaly_print_sink
SELECT
    HOP_START(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE) AS window_start,
    HOP_END(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)   AS window_end,
    COUNT(*)                                                          AS order_count,
    CAST(AVG(amount) AS DECIMAL(10, 2))                               AS avg_order_value,
    SUM(amount)                                                       AS total_revenue
FROM orders
GROUP BY HOP(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)
HAVING COUNT(*) > 15;
