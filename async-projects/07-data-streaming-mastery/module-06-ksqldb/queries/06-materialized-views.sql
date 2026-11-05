-- =============================================================================
-- 06-materialized-views.sql
-- Persistent queries and materialized views.
--
-- A persistent query runs continuously in the ksqlDB cluster. It reads from
-- input streams/tables, processes data, and writes results to an output
-- topic. The output can be queried with pull queries (point-in-time lookups).
--
-- Materialized views are created with CREATE TABLE ... AS SELECT.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Materialized view: total orders per customer (lifetime)
--
-- This persistent query maintains a running count and revenue total for
-- each customer. It updates in real time as new orders arrive.
-- The resulting table supports pull queries by customer_id.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS customer_order_summary AS
SELECT
    customer_id,
    COUNT(*)                    AS total_orders,
    SUM(price * quantity)       AS total_revenue,
    AVG(price)                  AS avg_order_price,
    MIN(price)                  AS min_order_price,
    MAX(price)                  AS max_order_price
FROM orders_stream
GROUP BY customer_id
EMIT CHANGES;

-- Pull query example (run interactively):
-- SELECT * FROM customer_order_summary WHERE customer_id = 'C0001';

-- ---------------------------------------------------------------------------
-- 2. Materialized view: product popularity
--
-- Tracks how many times each product has been ordered and total quantity
-- sold. Useful for inventory planning and recommendations.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS product_popularity AS
SELECT
    product_id,
    COUNT(*)                    AS times_ordered,
    SUM(quantity)               AS total_quantity_sold,
    SUM(price * quantity)       AS total_revenue
FROM orders_stream
GROUP BY product_id
EMIT CHANGES;

-- Pull query example:
-- SELECT * FROM product_popularity WHERE product_id = 'P0001';

-- ---------------------------------------------------------------------------
-- 3. Materialized view: orders per customer (windowed, 1 hour)
--
-- Windowed materialized views let you answer questions like:
-- "How many orders did customer C0001 place in the last hour?"
--
-- Pull queries on windowed tables require specifying the window bounds:
--   SELECT * FROM hourly_customer_orders
--   WHERE customer_id = 'C0001'
--     AND WINDOWSTART >= '2024-01-01T00:00:00'
--     AND WINDOWEND   <= '2024-01-01T01:00:00';
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hourly_customer_orders AS
SELECT
    customer_id,
    COUNT(*)                    AS orders_this_hour,
    SUM(price * quantity)       AS revenue_this_hour
FROM orders_stream
WINDOW TUMBLING (SIZE 1 HOUR)
GROUP BY customer_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 4. Materialized view: clickstream session summary
--
-- Aggregates clickstream data into session-based summaries.
-- Each row represents one user session (bounded by 5 min inactivity gap).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clickstream_sessions AS
SELECT
    user_id,
    COUNT(*)                    AS pages_per_session,
    WINDOWSTART                 AS session_start,
    WINDOWEND                   AS session_end
FROM clickstream_stream
WINDOW SESSION (5 MINUTES)
GROUP BY user_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 5. Materialized view: category revenue
--
-- Requires the enriched_orders stream from 04-joins.sql.
-- If enriched_orders does not exist, skip this query.
-- Tracks revenue by product category (available after joins are set up).
-- ---------------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS category_revenue AS
-- SELECT
--     product_category,
--     COUNT(*)                  AS order_count,
--     SUM(order_total)          AS total_revenue
-- FROM enriched_orders_with_products
-- GROUP BY product_category
-- EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- Management commands (run interactively):
-- ---------------------------------------------------------------------------

-- List all persistent queries:
-- SHOW QUERIES;

-- Get details about a specific query:
-- EXPLAIN CSAS_CUSTOMER_ORDER_SUMMARY_0;

-- Terminate a persistent query:
-- TERMINATE CSAS_CUSTOMER_ORDER_SUMMARY_0;

-- Drop a materialized view (must terminate query first):
-- DROP TABLE customer_order_summary;
