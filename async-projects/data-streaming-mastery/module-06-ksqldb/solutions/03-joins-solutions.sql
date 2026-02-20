-- =============================================================================
-- Solutions for Exercise 3: Joins
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Exercise 3.1: Stream-Table Join -- Enrich Orders
--
-- A LEFT JOIN between orders_stream and customers_table enriches each order
-- with customer details. The JOIN condition MUST use the table's PRIMARY KEY
-- (customer_id) because ksqlDB partitions and indexes tables by their key.
--
-- LEFT JOIN ensures that orders are emitted even when no matching customer
-- is found (customer fields will be NULL). INNER JOIN would drop orders
-- with missing customer records.
--
-- Important: stream-table joins are NOT retroactive. If a customer record
-- is updated after an order was enriched, the already-emitted enriched
-- order does NOT change. Only future orders use the updated customer data.
-- ---------------------------------------------------------------------------

-- Push query version:
SELECT
    o.order_id,
    o.customer_id,
    c.name                      AS customer_name,
    c.region                    AS customer_region,
    o.product_id,
    o.quantity,
    o.price,
    (o.price * o.quantity)      AS order_total
FROM orders_stream o
LEFT JOIN customers_table c
    ON o.customer_id = c.customer_id
EMIT CHANGES;

-- Persistent stream version:
CREATE STREAM IF NOT EXISTS enriched_orders_ex AS
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

-- Revenue by region (windowed aggregation on enriched stream):
SELECT
    customer_region,
    COUNT(*)                    AS order_count,
    SUM(order_total)            AS total_revenue
FROM enriched_orders_ex
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY customer_region
EMIT CHANGES;

-- ---------------------------------------------------------------------------
-- Exercise 3.2: Double Join -- Fully Enriched Orders
--
-- Join orders with both customers AND products in a single query.
-- ksqlDB processes the joins left to right. The order of JOINs does not
-- change the semantic result (both are stream-table joins), but it can
-- affect which columns are available for subsequent join conditions.
--
-- The underlying topic is auto-named based on the stream name
-- (e.g., FULLY_ENRICHED_ORDERS).
-- ---------------------------------------------------------------------------

-- Persistent stream: fully enriched orders
CREATE STREAM IF NOT EXISTS fully_enriched_orders AS
SELECT
    o.order_id                  AS order_id,
    c.name                      AS customer_name,
    c.region                    AS customer_region,
    p.name                      AS product_name,
    p.category                  AS product_category,
    o.quantity                  AS quantity,
    o.price                     AS price,
    (o.price * o.quantity)      AS order_total
FROM orders_stream o
LEFT JOIN customers_table c
    ON o.customer_id = c.customer_id
LEFT JOIN products_table p
    ON o.product_id = p.product_id
EMIT CHANGES;

-- Orders by product category (windowed):
SELECT
    product_category,
    COUNT(*)                    AS category_orders,
    SUM(order_total)            AS category_revenue
FROM fully_enriched_orders
WINDOW TUMBLING (SIZE 5 MINUTES)
GROUP BY product_category
EMIT CHANGES;

-- Materialized view for pull queries:
CREATE TABLE IF NOT EXISTS category_order_counts AS
SELECT
    product_category,
    COUNT(*)                    AS category_orders,
    SUM(order_total)            AS category_revenue
FROM fully_enriched_orders
GROUP BY product_category
EMIT CHANGES;

-- Pull query example:
-- SELECT * FROM category_order_counts WHERE product_category = 'Electronics';
