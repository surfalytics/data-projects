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
--
-- Syntax: these use the window table-valued functions (window TVFs).
--   FROM TABLE(TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE))
-- The function adds window_start, window_end and window_time columns.
-- Then you GROUP BY window_start, window_end.
-- The old group window syntax (GROUP BY TUMBLE(...) with TUMBLE_START) is
-- not used in this module. See the README for the Flink 2.x status.
-- =============================================================================


-- =============================================================================
-- Query 1: Orders per minute (Tumbling Window)
-- =============================================================================
-- Counts the number of orders and total revenue in each 1-minute window.
-- TUMBLE creates non-overlapping windows: [00:00, 00:01), [00:01, 00:02), ...
-- Each order belongs to exactly one window.
-- =============================================================================

SELECT
    window_start,
    window_end,
    COUNT(*)                                         AS order_count,
    SUM(amount)                                      AS total_revenue,
    AVG(amount)                                      AS avg_order_value,
    MIN(amount)                                      AS min_order_value,
    MAX(amount)                                      AS max_order_value
FROM TABLE(
    TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE))
GROUP BY window_start, window_end;


-- =============================================================================
-- Query 2: Revenue by order status per 5-minute window (Tumbling)
-- =============================================================================
-- Groups orders by order status and computes revenue metrics.
-- (For revenue by product category, see 04-joins-and-enrichment.sql.)
-- =============================================================================

SELECT
    window_start,
    window_end,
    order_status                                      AS status,
    COUNT(*)                                          AS order_count,
    SUM(amount)                                       AS total_revenue,
    AVG(amount)                                       AS avg_order_value
FROM TABLE(
    TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '5' MINUTE))
GROUP BY window_start, window_end, order_status;


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

-- HOP(TABLE t, DESCRIPTOR(time_col), SLIDE, SIZE): the slide comes first.

SELECT
    window_start,
    window_end,
    COUNT(*)                                                          AS rolling_order_count,
    SUM(amount)                                                       AS rolling_revenue
FROM TABLE(
    HOP(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE, INTERVAL '10' MINUTE))
GROUP BY window_start, window_end;


-- =============================================================================
-- Query 4: Customer session activity (Session Window)
-- =============================================================================
-- SESSION windows group events per key (customer_id) that occur close
-- together in time. A session closes after 5 minutes of inactivity for
-- that customer. Useful for analyzing user engagement patterns.
-- =============================================================================

-- SESSION needs PARTITION BY to give one session per key.

SELECT
    window_start                                    AS session_start,
    window_end                                      AS session_end,
    customer_id,
    COUNT(*)                                        AS orders_in_session,
    SUM(amount)                                     AS session_revenue,
    TIMESTAMPDIFF(SECOND, MIN(order_time), MAX(order_time)) AS session_seconds
FROM TABLE(
    SESSION(TABLE orders PARTITION BY customer_id, DESCRIPTOR(order_time), INTERVAL '5' MINUTE))
GROUP BY window_start, window_end, customer_id;


-- =============================================================================
-- Query 5: Top order statuses per minute
-- =============================================================================
-- Counts orders grouped by status within each 1-minute tumbling window.
-- Useful for monitoring order pipeline health in real time.
-- =============================================================================

SELECT
    window_start,
    order_status,
    COUNT(*)                                       AS status_count,
    SUM(amount)                                    AS status_revenue
FROM TABLE(
    TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE))
GROUP BY window_start, window_end, order_status;


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
