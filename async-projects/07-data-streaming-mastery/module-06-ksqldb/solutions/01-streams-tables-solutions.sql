-- =============================================================================
-- Solutions for Exercise 1: Streams and Tables
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Exercise 1.1: Create a Stream from the Clickstream Topic
--
-- We use CREATE STREAM to define an append-only collection over the
-- "clickstream" Kafka topic. user_id is the KEY (maps to the Kafka message
-- key). VALUE_FORMAT = JSON tells ksqlDB how to deserialize the value.
-- ---------------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS clickstream_stream (
    user_id VARCHAR KEY,
    page VARCHAR,
    referrer VARCHAR,
    `timestamp` VARCHAR
) WITH (
    KAFKA_TOPIC = 'clickstream',
    VALUE_FORMAT = 'JSON'
);

-- Verify:
-- DESCRIBE clickstream_stream;

-- ---------------------------------------------------------------------------
-- Exercise 1.2: Create a Table from the Products Topic
--
-- Tables use PRIMARY KEY instead of KEY. This tells ksqlDB to treat the
-- topic as a changelog: when two messages share the same product_id, the
-- later message replaces the earlier one (upsert semantics).
--
-- Answer to bonus question:
--   Streams use KEY because every row is independent (append-only).
--   Tables use PRIMARY KEY because rows are deduplicated by key.
--   When two messages with the same product_id arrive, the table keeps
--   only the latest value.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products_table (
    product_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    category VARCHAR,
    price DOUBLE
) WITH (
    KAFKA_TOPIC = 'products',
    VALUE_FORMAT = 'JSON'
);

-- Verify:
-- DESCRIBE products_table;

-- ---------------------------------------------------------------------------
-- Exercise 1.3: Create a Derived Stream (Filtered)
--
-- CREATE STREAM ... AS SELECT creates a persistent query that:
--   1. Reads from clickstream_stream continuously.
--   2. Filters to only rows where page starts with '/products/electronics'.
--   3. Writes matching rows to a new Kafka topic (ELECTRONICS_CLICKS).
--
-- The LIKE operator with '%' wildcard matches any suffix.
-- ---------------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS electronics_clicks AS
SELECT
    user_id,
    page,
    referrer,
    `timestamp`
FROM clickstream_stream
WHERE page LIKE '/products/electronics%'
EMIT CHANGES;

-- Verify:
-- SHOW STREAMS;
-- SELECT * FROM electronics_clicks EMIT CHANGES;
-- PRINT 'ELECTRONICS_CLICKS' FROM BEGINNING LIMIT 5;
