-- =============================================================================
-- 03-aggregations.sql
-- Windowed and non-windowed aggregations on streams.
--
-- Key concepts:
--   - All aggregations require GROUP BY.
--   - Aggregations on streams produce tables (the result is keyed by group).
--   - Windowed aggregations bound the time range over which we aggregate.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Orders per minute (Tumbling Window, 1 minute)
--
-- TUMBLING windows are fixed-size, non-overlapping, and contiguous.
-- Every order falls into exactly one 1-minute window.
-- WINDOWSTART and WINDOWEND give the window boundaries as epoch millis.
-- ---------------------------------------------------------------------------
SELECT
    product_id,
    COUNT(*)                    AS order_count,
    SUM(price * quantity)       AS total_revenue,
    WINDOWSTART                 AS window_start,
    WINDOWEND                   AS window_end
FROM orders_stream
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 2. Revenue by product (Tumbling Window, 5 minutes)
--
-- Larger window captures more orders, smoothing out fluctuations.
-- Useful for dashboards that refresh every 5 minutes.
-- ---------------------------------------------------------------------------
SELECT
    product_id,
    SUM(price * quantity)       AS revenue_5min,
    COUNT(*)                    AS orders_5min,
    AVG(price)                  AS avg_price
FROM orders_stream
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 3. Running total per customer (no window -- unbounded aggregation)
--
-- Without a WINDOW clause the aggregation runs over the entire stream
-- history. The result updates every time a new order arrives for that
-- customer. Be aware this can grow unbounded in production.
-- ---------------------------------------------------------------------------
SELECT
    customer_id,
    COUNT(*)                    AS lifetime_orders,
    SUM(price * quantity)       AS lifetime_revenue,
    AVG(price)                  AS avg_order_price
FROM orders_stream
GROUP BY customer_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 4. Hopping window: orders per product (10-min window, 2-min advance)
--
-- HOPPING windows overlap. Each order can appear in up to 5 windows
-- (10 / 2 = 5). Useful for smoothed moving averages.
-- ---------------------------------------------------------------------------
SELECT
    product_id,
    COUNT(*)                    AS order_count,
    SUM(price * quantity)       AS revenue
FROM orders_stream
WINDOW HOPPING (SIZE 10 MINUTES, ADVANCE BY 2 MINUTES)
GROUP BY product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 5. Orders per region per minute
--
-- This query requires a join with the customers table to get the region.
-- It is included here conceptually; the actual join-based version is in
-- 04-joins.sql. Below is a placeholder that groups by customer_id.
-- ---------------------------------------------------------------------------
SELECT
    customer_id,
    COUNT(*)                    AS orders_per_min,
    SUM(price * quantity)       AS revenue_per_min
FROM orders_stream
WINDOW TUMBLING (SIZE 1 MINUTE)
GROUP BY customer_id
EMIT CHANGES;
