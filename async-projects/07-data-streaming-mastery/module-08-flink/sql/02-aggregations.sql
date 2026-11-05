-- =============================================================================
-- 02-aggregations.sql
-- =============================================================================
-- Demonstrates Flink SQL windowed aggregations on the orders stream.
-- These queries produce real-time analytics by grouping events into time windows.
--
-- Prerequisites:
--   - Tables from 01-create-kafka-tables.sql must exist.
--   - Sample data must be flowing into the 'orders' Kafka topic.
--
-- Window Types Demonstrated:
--   1. TUMBLE  -- Non-overlapping fixed-size windows
--   2. HOP     -- Overlapping (sliding) windows
--   3. SESSION -- Activity-based windows that close after a gap
-- =============================================================================


-- =============================================================================
-- Query 1: Orders per minute (Tumbling Window)
-- =============================================================================
-- Counts the number of orders and total revenue in each 1-minute window.
-- TUMBLE creates non-overlapping windows: [00:00, 00:01), [00:01, 00:02), ...
-- Each order belongs to exactly one window.
-- =============================================================================

SELECT
    TUMBLE_START(order_time, INTERVAL '1' MINUTE)   AS window_start,
    TUMBLE_END(order_time, INTERVAL '1' MINUTE)     AS window_end,
    COUNT(*)                                         AS order_count,
    SUM(amount)                                      AS total_revenue,
    AVG(amount)                                      AS avg_order_value,
    MIN(amount)                                      AS min_order_value,
    MAX(amount)                                      AS max_order_value
FROM orders
GROUP BY TUMBLE(order_time, INTERVAL '1' MINUTE);


-- =============================================================================
-- Query 2: Revenue by category per 5-minute window (Tumbling)
-- =============================================================================
-- Groups orders by product category and computes revenue metrics.
-- This requires a join with the products table to get the category.
-- Note: This is a temporal join using the product's latest known value.
-- For simplicity, we assume product_id maps directly to a category via a
-- lookup. In production, you would use a versioned (temporal) table join.
-- =============================================================================

SELECT
    TUMBLE_START(o.order_time, INTERVAL '5' MINUTE)  AS window_start,
    TUMBLE_END(o.order_time, INTERVAL '5' MINUTE)    AS window_end,
    o.order_status                                    AS status,
    COUNT(*)                                          AS order_count,
    SUM(o.amount)                                     AS total_revenue,
    AVG(o.amount)                                     AS avg_order_value
FROM orders o
GROUP BY
    TUMBLE(o.order_time, INTERVAL '5' MINUTE),
    o.order_status;


-- =============================================================================
-- Query 3: Rolling 10-minute order count (Sliding / Hopping Window)
-- =============================================================================
-- HOP creates overlapping windows. Here we use a 10-minute window that
-- "hops" (slides) every 1 minute. This means at any given minute, we see
-- the total orders from the past 10 minutes.
--
-- An order placed at 10:05:30 will appear in windows:
--   [09:56, 10:06), [09:57, 10:07), ..., [10:05, 10:15)
-- =============================================================================

SELECT
    HOP_START(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE) AS window_start,
    HOP_END(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)   AS window_end,
    COUNT(*)                                                          AS rolling_order_count,
    SUM(amount)                                                       AS rolling_revenue
FROM orders
GROUP BY HOP(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE);


-- =============================================================================
-- Query 4: Customer session activity (Session Window)
-- =============================================================================
-- SESSION windows group events per key (customer_id) that occur close
-- together in time. A session closes after 5 minutes of inactivity for
-- that customer. Useful for analyzing user engagement patterns.
-- =============================================================================

SELECT
    SESSION_START(order_time, INTERVAL '5' MINUTE) AS session_start,
    SESSION_END(order_time, INTERVAL '5' MINUTE)   AS session_end,
    customer_id,
    COUNT(*)                                        AS orders_in_session,
    SUM(amount)                                     AS session_revenue,
    MAX(order_time) - MIN(order_time)               AS session_duration
FROM orders
GROUP BY SESSION(order_time, INTERVAL '5' MINUTE), customer_id;


-- =============================================================================
-- Query 5: Top order statuses per minute
-- =============================================================================
-- Counts orders grouped by status within each 1-minute tumbling window.
-- Useful for monitoring order pipeline health in real time.
-- =============================================================================

SELECT
    TUMBLE_START(order_time, INTERVAL '1' MINUTE) AS window_start,
    order_status,
    COUNT(*)                                       AS status_count,
    SUM(amount)                                    AS status_revenue
FROM orders
GROUP BY
    TUMBLE(order_time, INTERVAL '1' MINUTE),
    order_status;


-- =============================================================================
-- Query 6: Cumulative order count (non-windowed aggregation)
-- =============================================================================
-- A non-windowed (global) aggregation that maintains a running total.
-- Flink continuously updates this result as new events arrive.
-- Note: This produces an updating (changelog) stream, not an append-only stream.
-- =============================================================================

SELECT
    COUNT(*)    AS total_orders,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value
FROM orders;
