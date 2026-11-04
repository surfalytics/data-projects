"""
Solution: Exercise 2.2 -- PyFlink Custom Aggregation
=====================================================

Computes per-customer order statistics using 2-minute tumbling windows
with event-time watermarks, and writes results to Kafka.

Usage:
    python exercise_2_2_customer_stats.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the per-customer aggregation pipeline."""
    logger.info("Starting Exercise 2.2: Customer Order Statistics")

    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    t_env.get_config().set("execution.checkpointing.interval", "60000")
    t_env.get_config().set("execution.checkpointing.mode", "EXACTLY_ONCE")
    t_env.get_config().set("parallelism.default", "2")

    # Source: orders with event-time watermark (5-second tolerance)
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
            'properties.group.id' = 'pyflink-ex-2-2',
            'scan.startup.mode' = 'earliest-offset',
            'format' = 'json',
            'json.ignore-parse-errors' = 'true'
        )
    """)

    # Sink: per-customer stats with composite primary key
    t_env.execute_sql(f"""
        CREATE TABLE customer_order_stats_sink (
            customer_id     STRING,
            window_start    TIMESTAMP(3),
            window_end      TIMESTAMP(3),
            order_count     BIGINT,
            total_amount    DECIMAL(12, 2),
            avg_order_value DECIMAL(10, 2),
            max_order_value DECIMAL(10, 2),
            PRIMARY KEY (customer_id, window_start) NOT ENFORCED
        ) WITH (
            'connector' = 'upsert-kafka',
            'topic' = 'customer-order-stats',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format' = 'json',
            'value.format' = 'json'
        )
    """)

    # Aggregate: per-customer stats in 2-minute tumbling windows
    result = t_env.execute_sql("""
        INSERT INTO customer_order_stats_sink
        SELECT
            customer_id,
            TUMBLE_START(order_time, INTERVAL '2' MINUTE)     AS window_start,
            TUMBLE_END(order_time, INTERVAL '2' MINUTE)       AS window_end,
            COUNT(*)                                           AS order_count,
            SUM(amount)                                        AS total_amount,
            CAST(AVG(amount) AS DECIMAL(10, 2))                AS avg_order_value,
            MAX(amount)                                        AS max_order_value
        FROM orders
        GROUP BY
            TUMBLE(order_time, INTERVAL '2' MINUTE),
            customer_id
    """)

    logger.info("Pipeline submitted. Waiting for results (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    main()
