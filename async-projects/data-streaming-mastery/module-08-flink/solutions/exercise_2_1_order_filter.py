"""
Solution: Exercise 2.1 -- PyFlink Order Filter and Transform
=============================================================

Filters high-value orders (amount > 50), computes a value_tier classification,
and writes the transformed results to a Kafka topic.

Usage:
    python exercise_2_1_order_filter.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the order filter and transform pipeline."""
    logger.info("Starting Exercise 2.1: Order Filter and Transform")

    # Create streaming table environment
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # Configure checkpointing
    t_env.get_config().set("execution.checkpointing.interval", "60000")
    t_env.get_config().set("execution.checkpointing.mode", "EXACTLY_ONCE")
    t_env.get_config().set("parallelism.default", "2")

    # Create source table: orders from Kafka
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
            'properties.group.id' = 'pyflink-ex-2-1',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json',
            'json.ignore-parse-errors' = 'true'
        )
    """)

    # Create sink table: filtered orders to Kafka
    t_env.execute_sql(f"""
        CREATE TABLE filtered_orders_sink (
            order_id     STRING,
            amount       DECIMAL(10, 2),
            order_status STRING,
            order_time   TIMESTAMP(3),
            value_tier   STRING
        ) WITH (
            'connector' = 'kafka',
            'topic' = 'filtered-orders',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'format' = 'json'
        )
    """)

    # Filter and transform: orders > $50, with value_tier classification
    result = t_env.execute_sql("""
        INSERT INTO filtered_orders_sink
        SELECT
            order_id,
            amount,
            order_status,
            order_time,
            CASE
                WHEN amount > 200 THEN 'premium'
                WHEN amount > 100 THEN 'standard'
                ELSE 'basic'
            END AS value_tier
        FROM orders
        WHERE amount > 50.00
    """)

    logger.info("Pipeline submitted. Waiting for results (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    main()
