-- =============================================================================
-- 04-joins-and-enrichment.sql
-- =============================================================================
-- Demonstrates Flink SQL joins for enriching streaming data.
-- Flink supports several join types for streams and changelog tables.
--
-- Join Types in Flink SQL:
--   1. Regular Join      -- Joins two dynamic tables; both sides can change
--   2. Temporal Join     -- Joins a stream with a versioned (temporal) table
--   3. Lookup Join       -- Joins a stream with an external lookup source
--   4. Interval Join     -- Joins two streams within a time interval
--
-- Prerequisites:
--   - Kafka tables from 01-create-kafka-tables.sql
--   - CDC tables from 03-cdc-source.sql
-- =============================================================================


-- =============================================================================
-- Join 1: Enrich orders with customer data (Regular Join)
-- =============================================================================
-- Regular joins on dynamic tables produce a continuously updating result.
-- When either side changes, affected rows are updated in the output.
--
-- IMPORTANT: Regular joins on two append-only streams require the state to
-- grow indefinitely (Flink must remember all rows from both sides).
-- Use interval joins or temporal joins for production workloads.
-- =============================================================================

SELECT
    o.order_id,
    o.amount,
    o.order_status,
    o.order_time,
    c.first_name,
    c.last_name,
    c.email,
    c.city,
    c.state
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id;


-- =============================================================================
-- Join 2: Enrich orders with product data (Regular Join)
-- =============================================================================
-- Adds product name, category, and brand to each order.
-- =============================================================================

SELECT
    o.order_id,
    o.customer_id,
    o.quantity,
    o.amount,
    o.order_time,
    p.product_name,
    p.category,
    p.brand,
    p.price AS unit_price
FROM orders AS o
INNER JOIN products AS p
    ON o.product_id = p.product_id;


-- =============================================================================
-- Join 3: Full order enrichment (three-way join)
-- =============================================================================
-- Combines orders with both customer and product dimensions.
-- This is the typical "enriched order" pattern in streaming pipelines.
-- =============================================================================

SELECT
    o.order_id,
    o.order_time,
    o.quantity,
    o.amount,
    o.order_status,
    -- Customer details
    c.first_name || ' ' || c.last_name AS customer_name,
    c.email                             AS customer_email,
    c.city                              AS customer_city,
    c.country                           AS customer_country,
    -- Product details
    p.product_name,
    p.category                          AS product_category,
    p.brand                             AS product_brand,
    p.price                             AS unit_price
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
INNER JOIN products AS p
    ON o.product_id = p.product_id;


-- =============================================================================
-- Join 4: Interval Join (time-bounded)
-- =============================================================================
-- Joins two streams where events must occur within a specific time interval.
-- This is more efficient than a regular join because Flink can discard old
-- state once the interval expires.
--
-- Example: Match orders with customer events that occurred within 1 hour
-- before the order (e.g., customer logged in, then placed an order).
-- =============================================================================

SELECT
    o.order_id,
    o.amount,
    o.order_time,
    c.customer_id,
    c.first_name,
    c.created_at AS customer_event_time
FROM orders AS o
INNER JOIN customers AS c
    ON o.customer_id = c.customer_id
    AND c.created_at BETWEEN o.order_time - INTERVAL '1' HOUR
                         AND o.order_time;


-- =============================================================================
-- Join 5: CDC-enriched orders (using MySQL CDC tables)
-- =============================================================================
-- Joins the Kafka orders stream with CDC dimension tables from MySQL.
-- The CDC tables act as continuously-updated dimension tables.
-- When a customer's address changes in MySQL, it is reflected here in real time.
-- =============================================================================

SELECT
    o.order_id,
    o.amount,
    o.order_time,
    o.order_status,
    -- Customer info from MySQL CDC
    mc.first_name || ' ' || mc.last_name AS customer_name,
    mc.email,
    mc.city,
    -- Product info from MySQL CDC
    mp.product_name,
    mp.category,
    mp.brand
FROM orders AS o
LEFT JOIN mysql_customers AS mc
    ON o.customer_id = CAST(mc.customer_id AS STRING)
LEFT JOIN mysql_products AS mp
    ON o.product_id = CAST(mp.product_id AS STRING);


-- =============================================================================
-- Join 6: Aggregation after enrichment
-- =============================================================================
-- After enriching orders, compute revenue by product category per 5-minute
-- window. This pattern is extremely common in real-time analytics pipelines.
-- =============================================================================

SELECT
    TUMBLE_START(o.order_time, INTERVAL '5' MINUTE) AS window_start,
    TUMBLE_END(o.order_time, INTERVAL '5' MINUTE)   AS window_end,
    p.category,
    COUNT(*)                                          AS order_count,
    SUM(o.amount)                                     AS total_revenue,
    AVG(o.amount)                                     AS avg_order_value
FROM orders AS o
INNER JOIN products AS p
    ON o.product_id = p.product_id
GROUP BY
    TUMBLE(o.order_time, INTERVAL '5' MINUTE),
    p.category;
