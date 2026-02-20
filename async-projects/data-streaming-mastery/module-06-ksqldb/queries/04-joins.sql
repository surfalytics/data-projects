-- =============================================================================
-- 04-joins.sql
-- Stream-Table and Stream-Stream joins.
--
-- Key concepts:
--   - Stream-Table joins enrich events with lookup data.
--   - The stream drives the join; the table provides the latest state.
--   - JOIN condition must use the table's PRIMARY KEY.
--   - Stream-Stream joins require a WITHIN clause to bound the time window.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. Enrich orders with customer details (Stream-Table JOIN)
--
-- For every order that arrives, look up the customer name and region from
-- the customers_table. LEFT JOIN ensures orders are emitted even if the
-- customer record is missing.
-- ---------------------------------------------------------------------------
SELECT
    o.order_id,
    o.customer_id,
    c.name           AS customer_name,
    c.email          AS customer_email,
    c.region         AS customer_region,
    o.product_id,
    o.quantity,
    o.price,
    (o.price * o.quantity) AS order_total
FROM orders_stream o
LEFT JOIN customers_table c
    ON o.customer_id = c.customer_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 2. Enrich orders with product details (Stream-Table JOIN)
--
-- Look up the product name and category for each order.
-- ---------------------------------------------------------------------------
SELECT
    o.order_id,
    o.customer_id,
    o.product_id,
    p.name           AS product_name,
    p.category       AS product_category,
    o.quantity,
    o.price,
    (o.price * o.quantity) AS order_total
FROM orders_stream o
LEFT JOIN products_table p
    ON o.product_id = p.product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 3. Fully enriched orders (double Stream-Table JOIN)
--
-- Join orders with BOTH customers and products in a single query.
-- This gives a complete picture: who bought what, how much, from where.
-- ---------------------------------------------------------------------------
SELECT
    o.order_id,
    c.name           AS customer_name,
    c.region         AS customer_region,
    p.name           AS product_name,
    p.category       AS product_category,
    o.quantity,
    o.price,
    (o.price * o.quantity) AS order_total
FROM orders_stream o
LEFT JOIN customers_table c
    ON o.customer_id = c.customer_id
LEFT JOIN products_table p
    ON o.product_id = p.product_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- 4. Revenue by region (aggregation on enriched stream)
--
-- First we need to create a persistent enriched stream, then aggregate.
-- Step A: Create the enriched stream.
-- ---------------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS enriched_orders AS
SELECT
    o.order_id                  AS order_id,
    o.customer_id               AS customer_id,
    c.name                      AS customer_name,
    c.region                    AS customer_region,
    o.product_id                AS product_id,
    o.quantity                  AS quantity,
    o.price                     AS price,
    (o.price * o.quantity)      AS order_total
FROM orders_stream o
LEFT JOIN customers_table c
    ON o.customer_id = c.customer_id
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- Step B: Aggregate revenue by region using the enriched stream.
-- This is now possible because customer_region is part of the stream.
-- ---------------------------------------------------------------------------
SELECT
    customer_region,
    COUNT(*)                    AS order_count,
    SUM(order_total)            AS total_revenue,
    AVG(order_total)            AS avg_order_value
FROM enriched_orders
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY customer_region
EMIT CHANGES;
