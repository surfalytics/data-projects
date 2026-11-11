-- =============================================================================
-- 02-aggregations.sql
-- =============================================================================
-- Demonstrates Flink SQL windowed aggregations on the orders stream.
-- These queries produce real-time analytics by grouping events into time windows.
--
-- Prerequisites:
-- - Tables from 01-create-kafka-tables.sql must exist.
-- - Sample data must be flowing into the 'orders' Kafka topic.
--
-- Window Types Demonstrated:
-- 1. TUMBLE  -- Non-overlapping fixed-size windows
-- 2. HOP     -- Overlapping (sliding) windows
-- 3. SESSION -- Activity-based windows that close after a gap
--
-- Syntax: these use the window table-valued functions (window TVFs).
-- FROM TABLE(TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' MINUTE))
-- The function adds window_start, window_end and window_time columns.
-- Then you GROUP BY window_start, window_end.
-- The old group window syntax (GROUP BY TUMBLE(...) with TUMBLE_START) still
-- plans in Flink 2.2, but it is not used in this module.
-- =============================================================================
-- =============================================================================
-- Query 1: Orders per minute (Tumbling Window)
-- =============================================================================
-- Counts the number of orders and total revenue in each 1-minute window.
-- TUMBLE creates non-overlapping windows: [00:00, 00:01), [00:01, 00:02), ...
-- Each order belongs to exactly one window.
-- =============================================================================
select
    window_start,
    window_end,
    count(*) as order_count,
    sum(amount) as total_revenue,
    avg(amount) as avg_order_value,
    min(amount) as min_order_value,
    max(amount) as max_order_value
from table(tumble(table orders, descriptor(order_time), interval '1' minute))
group by window_start, window_end
;


-- =============================================================================
-- Query 2: Revenue by order status per 5-minute window (Tumbling)
-- =============================================================================
-- Groups orders by order status and computes revenue metrics.
-- (For revenue by product category, see 04-joins-and-enrichment.sql.)
-- =============================================================================
select
    window_start,
    window_end,
    order_status as status,
    count(*) as order_count,
    sum(amount) as total_revenue,
    avg(amount) as avg_order_value
from table(tumble(table orders, descriptor(order_time), interval '5' minute))
group by window_start, window_end, order_status
;


-- =============================================================================
-- Query 3: Rolling 10-minute order count (Sliding / Hopping Window)
-- =============================================================================
-- HOP creates overlapping windows. Here we use a 10-minute window that
-- "hops" (slides) every 1 minute. This means at any given minute, we see
-- the total orders from the past 10 minutes.
--
-- An order placed at 10:05:30 will appear in windows:
-- [09:56, 10:06), [09:57, 10:07), ..., [10:05, 10:15)
-- =============================================================================
-- HOP(TABLE t, DESCRIPTOR(time_col), SLIDE, SIZE): the slide comes first.
select
    window_start,
    window_end,
    count(*) as rolling_order_count,
    sum(amount) as rolling_revenue
from
    table(
        hop(
            table orders,
            descriptor(order_time),
            interval '1' minute,
            interval '10' minute
        )
    )
group by window_start, window_end
;


-- =============================================================================
-- Query 4: Customer session activity (Session Window)
-- =============================================================================
-- SESSION windows group events per key (customer_id) that occur close
-- together in time. A session closes after 5 minutes of inactivity for
-- that customer. Useful for analyzing user engagement patterns.
-- =============================================================================
-- SESSION needs PARTITION BY to give one session per key.
select
    window_start as session_start,
    window_end as session_end,
    customer_id,
    count(*) as orders_in_session,
    sum(amount) as session_revenue,
    timestampdiff(second, min(order_time), max(order_time)) as session_seconds
from
    table(
        session(
            table orders
            partition by customer_id, descriptor(order_time), interval '5' minute
        )
    )
group by window_start, window_end, customer_id
;


-- =============================================================================
-- Query 5: Top order statuses per minute
-- =============================================================================
-- Counts orders grouped by status within each 1-minute tumbling window.
-- Useful for monitoring order pipeline health in real time.
-- =============================================================================
select
    window_start, order_status, count(*) as status_count, sum(amount) as status_revenue
from table(tumble(table orders, descriptor(order_time), interval '1' minute))
group by window_start, window_end, order_status
;


-- =============================================================================
-- Query 6: Cumulative order count (non-windowed aggregation)
-- =============================================================================
-- A non-windowed (global) aggregation that maintains a running total.
-- Flink continuously updates this result as new events arrive.
-- Note: This produces an updating (changelog) stream, not an append-only stream.
-- =============================================================================
select
    count(*) as total_orders,
    sum(amount) as total_revenue,
    avg(amount) as avg_order_value
from orders
;
