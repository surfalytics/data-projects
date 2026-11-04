"""
Solution: Exercise 2.3 -- PyFlink Multi-Sink Pipeline
======================================================

A single PyFlink application that reads orders and writes to three sinks
simultaneously: print (debug), orders-per-minute (Kafka), and
orders-by-status (Kafka).

Usage:
    python exercise_2_3_multi_sink.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the multi-sink pipeline."""
    logger.info("Starting Exercise 2.3: Multi-Sink Pipeline")

    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    t_env.get_config().set("execution.checkpointing.interval", "60000")
    t_env.get_config().set("execution.checkpointing.mode", "EXACTLY_ONCE")
    t_env.get_config().set("parallelism.default", "2")

    # -----------------------------------------------------------------------
    # Source: orders from Kafka
    # -----------------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE orders (
            order_id     STRING,
            customer_id  STRING,
            product_id   STRING,
            quantity     INT,
            amount       DECIMAL(10, 2),
            order_status STRING,
            order_time   TIMESTAMP(3),
            WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'orders',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'properties.group.id' = 'pyflink-ex-2-3',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json',
            'json.ignore-parse-errors' = 'true'
        )
    """)

    # -----------------------------------------------------------------------
    # Sink 1: Print sink (all orders, for debugging)
    # -----------------------------------------------------------------------
    t_env.execute_sql("""
        CREATE TABLE print_sink (
            order_id     STRING,
            amount       DECIMAL(10, 2),
            order_status STRING,
            order_time   TIMESTAMP(3)
        ) WITH (
            'connector' = 'print'
        )
    """)

    logger.info("Submitting Job 1: All orders to print sink")
    t_env.execute_sql("""
        INSERT INTO print_sink
        SELECT order_id, amount, order_status, order_time
        FROM orders
    """)

    # -----------------------------------------------------------------------
    # Sink 2: Orders per minute (upsert-kafka)
    # -----------------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE orders_per_minute_sink (
            window_start  TIMESTAMP(3),
            window_end    TIMESTAMP(3),
            order_count   BIGINT,
            total_revenue DECIMAL(12, 2),
            PRIMARY KEY (window_start) NOT ENFORCED
        ) WITH (
            'connector' = 'upsert-kafka',
            'topic' = 'orders-per-minute',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format' = 'json',
            'value.format' = 'json'
        )
    """)

    logger.info("Submitting Job 2: Orders per minute to Kafka")
    t_env.execute_sql("""
        INSERT INTO orders_per_minute_sink
        SELECT
            TUMBLE_START(order_time, INTERVAL '1' MINUTE) AS window_start,
            TUMBLE_END(order_time, INTERVAL '1' MINUTE)   AS window_end,
            COUNT(*)                                       AS order_count,
            SUM(amount)                                    AS total_revenue
        FROM orders
        GROUP BY TUMBLE(order_time, INTERVAL '1' MINUTE)
    """)

    # -----------------------------------------------------------------------
    # Sink 3: Orders by status (upsert-kafka)
    # -----------------------------------------------------------------------
    t_env.execute_sql(f"""
        CREATE TABLE orders_by_status_sink (
            order_status  STRING,
            order_count   BIGINT,
            total_revenue DECIMAL(12, 2),
            PRIMARY KEY (order_status) NOT ENFORCED
        ) WITH (
            'connector' = 'upsert-kafka',
            'topic' = 'orders-by-status',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format' = 'json',
            'value.format' = 'json'
        )
    """)

    logger.info("Submitting Job 3: Orders by status to Kafka")
    result = t_env.execute_sql("""
        INSERT INTO orders_by_status_sink
        SELECT
            order_status,
            COUNT(*)    AS order_count,
            SUM(amount) AS total_revenue
        FROM orders
        GROUP BY order_status
    """)

    logger.info("All three jobs submitted. Waiting (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    main()
