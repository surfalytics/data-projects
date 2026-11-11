-- =============================================================================
-- 04-joins-and-enrichment.sql
-- =============================================================================
-- Demonstrates Flink SQL joins for enriching streaming data.
-- Flink supports several join types for streams and changelog tables.
--
-- Join Types in Flink SQL:
-- 1. Regular Join      -- Joins two dynamic tables; both sides can change
-- 2. Temporal Join     -- Joins a stream with a versioned (temporal) table
-- 3. Lookup Join       -- Joins a stream with an external lookup source
-- 4. Interval Join     -- Joins two streams within a time interval
--
-- Prerequisites:
-- - Kafka tables from 01-create-kafka-tables.sql
-- - CDC tables from 03-cdc-source.sql
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
select
    o.order_id,
    o.amount,
    o.order_status,
    o.order_time,
    c.first_name,
    c.last_name,
    c.email,
    c.city,
    c.state
from orders as o
inner join customers as c on o.customer_id = c.customer_id
;


-- =============================================================================
-- Join 2: Enrich orders with product data (Regular Join)
-- =============================================================================
-- Adds product name, category, and brand to each order.
-- =============================================================================
select
    o.order_id,
    o.customer_id,
    o.quantity,
    o.amount,
    o.order_time,
    p.product_name,
    p.category,
    p.brand,
    p.price as unit_price
from orders as o
inner join products as p on o.product_id = p.product_id
;


-- =============================================================================
-- Join 3: Full order enrichment (three-way join)
-- =============================================================================
-- Combines orders with both customer and product dimensions.
-- This is the typical "enriched order" pattern in streaming pipelines.
-- =============================================================================
select
    o.order_id,
    o.order_time,
    o.quantity,
    o.amount,
    o.order_status,
    -- Customer details
    c.first_name || ' ' || c.last_name as customer_name,
    c.email as customer_email,
    c.city as customer_city,
    c.country as customer_country,
    -- Product details
    p.product_name,
    p.category as product_category,
    p.brand as product_brand,
    p.price as unit_price
from orders as o
inner join customers as c on o.customer_id = c.customer_id
inner join products as p on o.product_id = p.product_id
;


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
select
    o.order_id,
    o.amount,
    o.order_time,
    c.customer_id,
    c.first_name,
    c.created_at as customer_event_time
from orders as o
inner join
    customers as c
    on o.customer_id = c.customer_id
    and c.created_at between o.order_time - interval '1' hour and o.order_time
;


-- =============================================================================
-- Join 5: CDC-enriched orders (using MySQL CDC tables)
-- =============================================================================
-- Joins the Kafka orders stream with CDC dimension tables from MySQL.
-- The CDC tables act as continuously-updated dimension tables.
-- When a customer's address changes in MySQL, it is reflected here in real time.
-- =============================================================================
select
    o.order_id,
    o.amount,
    o.order_time,
    o.order_status,
    -- Customer info from MySQL CDC
    mc.first_name || ' ' || mc.last_name as customer_name,
    mc.email,
    mc.city,
    -- Product info from MySQL CDC
    mp.product_name,
    mp.category,
    mp.brand
from orders as o
left join mysql_customers as mc on o.customer_id = cast(mc.customer_id as string)
left join mysql_products as mp on o.product_id = cast(mp.product_id as string)
;


-- =============================================================================
-- Join 6: Aggregation after enrichment
-- =============================================================================
-- Compute revenue by product category per 5-minute window.
-- Pattern: window first, then join the dimension, then group by the dimension.
-- =============================================================================
-- A regular join drops the time attribute of order_time.
-- Window functions need a time attribute. So the window comes FIRST
-- (per product_id), and the join with products comes AFTER it.
select
    w.window_start,
    w.window_end,
    p.category,
    sum(w.order_count) as order_count,
    sum(w.total_revenue) as total_revenue
from
    (
        select
            window_start,
            window_end,
            product_id,
            count(*) as order_count,
            sum(amount) as total_revenue
        from table(tumble(table orders, descriptor(order_time), interval '5' minute))
        group by window_start, window_end, product_id
    ) as w
inner join products as p on w.product_id = p.product_id
group by w.window_start, w.window_end, p.category
;
