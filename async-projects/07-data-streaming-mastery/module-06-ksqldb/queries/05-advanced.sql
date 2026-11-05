-- =============================================================================
-- 05-advanced.sql
-- Advanced ksqlDB features: session windows, TOPK, filtered streams,
-- CASE expressions, and conditional logic.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Session windows on clickstream data
--
-- SESSION windows group events by activity. A session closes when no new
-- events arrive for the specified inactivity gap (here, 5 minutes).
-- Each user_id gets independent sessions.
--
-- Use case: measure user engagement -- how many pages per browsing session?
-- ---------------------------------------------------------------------------
SELECT
    user_id,
    COUNT(*)        AS pages_viewed,
    WINDOWSTART     AS session_start,
    WINDOWEND       AS session_end
FROM clickstream_stream
WINDOW SESSION (5 MINUTES)
GROUP BY user_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 2. TOPK: top 3 most expensive orders per 5-minute window
--
-- TOPK(column, k) returns the k largest values in the group.
-- Useful for leaderboards and anomaly detection.
-- ---------------------------------------------------------------------------
SELECT
    product_id,
    TOPK(price, 3)  AS top_3_prices
FROM orders_stream
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 3. TOPKDISTINCT: top 3 distinct order totals per customer
--
-- Unlike TOPK, TOPKDISTINCT removes duplicates before ranking.
-- ---------------------------------------------------------------------------
SELECT
    customer_id,
    TOPKDISTINCT(price * quantity, 3) AS top_3_distinct_totals
FROM orders_stream
WINDOW TUMBLING (SIZE 10 MINUTES)
GROUP BY customer_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 4. Filtered stream: high-value orders only
--
-- CREATE STREAM ... AS SELECT with a WHERE clause produces a new stream
-- containing only orders above $100 in total value. This runs as a
-- persistent query writing to a new Kafka topic.
-- ---------------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS high_value_orders AS
SELECT
    order_id,
    customer_id,
    product_id,
    quantity,
    price,
    (price * quantity) AS order_total,
    `timestamp`
FROM orders_stream
WHERE (price * quantity) > 100.0
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 5. CASE expressions: categorize orders by value tier
--
-- CASE works like a SQL CASE/WHEN. Here we classify every order into a
-- tier: 'small', 'medium', or 'large' based on total value.
-- ---------------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS categorized_orders AS
SELECT
    order_id,
    customer_id,
    product_id,
    quantity,
    price,
    (price * quantity) AS order_total,
    CASE
        WHEN (price * quantity) < 50    THEN 'small'
        WHEN (price * quantity) < 200   THEN 'medium'
        ELSE 'large'
    END AS order_tier,
    `timestamp`
FROM orders_stream
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 6. Aggregation on categorized orders: count by tier per 5 minutes
--
-- Now we can answer: how many small/medium/large orders per window?
-- ---------------------------------------------------------------------------
SELECT
    order_tier,
    COUNT(*)                    AS tier_count,
    SUM(order_total)            AS tier_revenue
FROM categorized_orders
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY order_tier
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 7. Clickstream: most visited pages per 10-minute window
--
-- Count page views grouped by page URL.
-- ---------------------------------------------------------------------------
SELECT
    page,
    COUNT(*)        AS view_count
FROM clickstream_stream
WINDOW TUMBLING (SIZE 10 MINUTES)
GROUP BY page
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 8. Clickstream: referrer analysis per 10-minute window
--
-- Which referrers drive the most traffic?
-- ---------------------------------------------------------------------------
SELECT
    referrer,
    COUNT(*)        AS referral_count
FROM clickstream_stream
WINDOW TUMBLING (SIZE 10 MINUTES)
GROUP BY referrer
EMIT CHANGES;
