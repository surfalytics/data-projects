"""
PyFlink Windowed Aggregation with Watermarks
=============================================

Demonstrates event-time windowed aggregation in PyFlink, including:
    - Kafka source with embedded event timestamps
    - Watermark strategy for handling out-of-order events
    - Tumbling, sliding (hopping), and session window aggregations
    - Writing results to both print sink and Kafka

This is a more advanced example that shows how Flink handles the real-world
challenge of events arriving out of order. Watermarks tell Flink when it is
safe to close a window and emit results.

Architecture:
    Kafka (orders topic) --> Flink (watermarks + windows) --> Kafka (results)

Prerequisites:
    - Kafka broker running at kafka:29092
    - The 'orders' topic populated with JSON order events
    - apache-flink Python package installed
    - Flink Kafka connector JAR in the classpath

Usage:
    python pyflink_windowed_aggregation.py

    Or submit to a Flink cluster:
    flink run -py pyflink_windowed_aggregation.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
INPUT_TOPIC = os.environ.get("INPUT_TOPIC", "orders")
CONSUMER_GROUP = "pyflink-windowed-agg"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pyflink_windowed_aggregation")


def create_orders_source_ddl() -> str:
    """
    DDL for the orders Kafka source table with event-time watermarks.

    The WATERMARK clause declares that:
    - 'order_time' is the event-time column
    - Events may arrive up to 10 seconds late (out of order)
    - Flink will wait up to 10 seconds before closing a window

    Returns:
        Flink SQL CREATE TABLE statement.
    """
    return f"""
        CREATE TABLE orders_source (
            order_id     STRING,
            customer_id  STRING,
            product_id   STRING,
            quantity     INT,
            amount       DECIMAL(10, 2),
            order_status STRING,
            order_time   TIMESTAMP(3),
            -- Watermark: tolerate up to 10 seconds of out-of-order events
            WATERMARK FOR order_time AS order_time - INTERVAL '10' SECOND
        ) WITH (
            'connector'                       = 'kafka',
            'topic'                           = '{INPUT_TOPIC}',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id'             = '{CONSUMER_GROUP}',
            'scan.startup.mode'               = 'earliest-offset',
            'format'                          = 'json',
            'json.fail-on-missing-field'      = 'false',
            'json.ignore-parse-errors'        = 'true'
        )
    """


def create_tumbling_sink_ddl() -> str:
    """
    DDL for the tumbling window results sink (Kafka upsert).

    Results are keyed by window_start for upsert semantics.

    Returns:
        Flink SQL CREATE TABLE statement.
    """
    return f"""
        CREATE TABLE tumbling_results (
            window_start     TIMESTAMP(3),
            window_end       TIMESTAMP(3),
            order_count      BIGINT,
            total_revenue    DECIMAL(12, 2),
            avg_order_value  DECIMAL(10, 2),
            max_order_value  DECIMAL(10, 2),
            min_order_value  DECIMAL(10, 2),
            PRIMARY KEY (window_start) NOT ENFORCED
        ) WITH (
            'connector'                       = 'upsert-kafka',
            'topic'                           = 'tumbling-order-stats',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                      = 'json',
            'value.format'                    = 'json'
        )
    """


def create_sliding_sink_ddl() -> str:
    """
    DDL for the sliding (hopping) window results sink.

    Uses a 10-minute window sliding every 1 minute.

    Returns:
        Flink SQL CREATE TABLE statement.
    """
    return f"""
        CREATE TABLE sliding_results (
            window_start     TIMESTAMP(3),
            window_end       TIMESTAMP(3),
            order_count      BIGINT,
            total_revenue    DECIMAL(12, 2),
            PRIMARY KEY (window_start) NOT ENFORCED
        ) WITH (
            'connector'                       = 'upsert-kafka',
            'topic'                           = 'sliding-order-stats',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                      = 'json',
            'value.format'                    = 'json'
        )
    """


def create_session_sink_ddl() -> str:
    """
    DDL for the session window results sink.

    Sessions are grouped by customer_id with a 5-minute gap.

    Returns:
        Flink SQL CREATE TABLE statement.
    """
    return f"""
        CREATE TABLE session_results (
            customer_id      STRING,
            session_start    TIMESTAMP(3),
            session_end      TIMESTAMP(3),
            order_count      BIGINT,
            session_revenue  DECIMAL(12, 2),
            PRIMARY KEY (customer_id, session_start) NOT ENFORCED
        ) WITH (
            'connector'                       = 'upsert-kafka',
            'topic'                           = 'session-order-stats',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                      = 'json',
            'value.format'                    = 'json'
        )
    """


def create_print_sink_ddl() -> str:
    """
    DDL for a print sink (stdout) for development debugging.

    Returns:
        Flink SQL CREATE TABLE statement.
    """
    return """
        CREATE TABLE print_sink (
            window_type      STRING,
            window_start     TIMESTAMP(3),
            window_end       TIMESTAMP(3),
            group_key        STRING,
            order_count      BIGINT,
            total_revenue    DECIMAL(12, 2)
        ) WITH (
            'connector' = 'print'
        )
    """


def run_windowed_aggregation() -> None:
    """
    Main entry point for the windowed aggregation pipeline.

    Submits three concurrent Flink SQL jobs:
        1. Tumbling window (1-minute): Order count, revenue, and value stats.
        2. Sliding window (10-min window, 1-min slide): Rolling order metrics.
        3. Session window (5-min gap): Per-customer session analytics.

    All three jobs read from the same Kafka source and write to separate
    Kafka output topics.
    """
    logger.info("Starting PyFlink Windowed Aggregation Pipeline")

    # -----------------------------------------------------------------------
    # Step 1: Create the streaming table environment
    # -----------------------------------------------------------------------
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # Configure checkpointing and parallelism
    config = t_env.get_config()
    config.set("execution.checkpointing.interval", "60000")
    config.set("execution.checkpointing.mode", "EXACTLY_ONCE")
    config.set("parallelism.default", "2")

    # -----------------------------------------------------------------------
    # Step 2: Create source and sink tables
    # -----------------------------------------------------------------------
    logger.info("Creating source and sink tables")
    t_env.execute_sql(create_orders_source_ddl())
    t_env.execute_sql(create_tumbling_sink_ddl())
    t_env.execute_sql(create_sliding_sink_ddl())
    t_env.execute_sql(create_session_sink_ddl())
    t_env.execute_sql(create_print_sink_ddl())
    logger.info("All tables created")

    # -----------------------------------------------------------------------
    # Step 3a: Tumbling window aggregation (1-minute windows)
    # -----------------------------------------------------------------------
    # Non-overlapping 1-minute windows. Each order falls into exactly one window.
    # The watermark (10 seconds) means the window at [10:00, 10:01) will fire
    # when the watermark passes 10:01:00, i.e., when Flink receives an event
    # with timestamp >= 10:01:10.
    # -----------------------------------------------------------------------
    logger.info("Submitting tumbling window query (1-minute windows)")
    tumbling_query = """
        INSERT INTO tumbling_results
        SELECT
            TUMBLE_START(order_time, INTERVAL '1' MINUTE)       AS window_start,
            TUMBLE_END(order_time, INTERVAL '1' MINUTE)         AS window_end,
            COUNT(*)                                             AS order_count,
            SUM(amount)                                          AS total_revenue,
            CAST(AVG(amount) AS DECIMAL(10, 2))                  AS avg_order_value,
            MAX(amount)                                          AS max_order_value,
            MIN(amount)                                          AS min_order_value
        FROM orders_source
        GROUP BY TUMBLE(order_time, INTERVAL '1' MINUTE)
    """
    t_env.execute_sql(tumbling_query)
    logger.info("Tumbling window job submitted")

    # -----------------------------------------------------------------------
    # Step 3b: Sliding window aggregation (10-min window, 1-min slide)
    # -----------------------------------------------------------------------
    # Overlapping windows that provide a rolling 10-minute view, updated
    # every minute. Each order can appear in up to 10 windows.
    # -----------------------------------------------------------------------
    logger.info("Submitting sliding window query (10-min window, 1-min slide)")
    sliding_query = """
        INSERT INTO sliding_results
        SELECT
            HOP_START(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)  AS window_start,
            HOP_END(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)    AS window_end,
            COUNT(*)                                                           AS order_count,
            SUM(amount)                                                        AS total_revenue
        FROM orders_source
        GROUP BY HOP(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)
    """
    t_env.execute_sql(sliding_query)
    logger.info("Sliding window job submitted")

    # -----------------------------------------------------------------------
    # Step 3c: Session window aggregation (5-min gap per customer)
    # -----------------------------------------------------------------------
    # Session windows are dynamic: they open when a customer places an order
    # and close after 5 minutes of inactivity. Each customer has independent
    # sessions. Great for analyzing buying sessions or user engagement.
    # -----------------------------------------------------------------------
    logger.info("Submitting session window query (5-min gap per customer)")
    session_query = """
        INSERT INTO session_results
        SELECT
            customer_id,
            SESSION_START(order_time, INTERVAL '5' MINUTE)      AS session_start,
            SESSION_END(order_time, INTERVAL '5' MINUTE)        AS session_end,
            COUNT(*)                                             AS order_count,
            SUM(amount)                                          AS session_revenue
        FROM orders_source
        GROUP BY SESSION(order_time, INTERVAL '5' MINUTE), customer_id
    """
    result = t_env.execute_sql(session_query)
    logger.info("Session window job submitted")

    # Wait for the last job (all three run concurrently as separate Flink jobs)
    logger.info("All windowed aggregation jobs running. Waiting (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    run_windowed_aggregation()
