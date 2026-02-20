-- =============================================================================
-- 01-create-streams.sql
-- Create ksqlDB STREAMS from Kafka topics.
--
-- Streams are append-only collections of events. Every message on the
-- underlying Kafka topic becomes a new row in the stream.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Stream: orders_stream
-- Source topic: "orders"
-- Each message represents a single order event.
-- The KEY column (order_id) maps to the Kafka message key.
-- VALUE_FORMAT = JSON means the message value is a JSON object.
-- ---------------------------------------------------------------------------
CREATE STREAM IF NOT EXISTS orders_stream (
    order_id VARCHAR KEY,
    customer_id VARCHAR,
    product_id VARCHAR,
    quantity INT,
    price DOUBLE,
    `timestamp` VARCHAR
) WITH (
    KAFKA_TOPIC = 'orders',
    VALUE_FORMAT = 'JSON'
);

-- ---------------------------------------------------------------------------
-- Stream: clickstream_stream
-- Source topic: "clickstream"
-- Each message represents a page-view event from a user.
-- We use user_id as the KEY so downstream GROUP BY operations can partition
-- correctly by user.
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

-- ---------------------------------------------------------------------------
-- Verify: list all streams to confirm creation.
-- ---------------------------------------------------------------------------
-- SHOW STREAMS;
