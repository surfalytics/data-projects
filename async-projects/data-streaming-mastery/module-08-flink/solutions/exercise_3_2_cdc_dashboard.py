"""
Solution: Exercise 3.2 -- CDC-Powered Real-Time Dashboard
==========================================================

Reads CDC data from MySQL (orders, customers, products) and computes three
real-time analytics views:
    A. Revenue by city
    B. Category performance
    C. Hourly order trend

Each view is written to a separate Kafka topic.

Usage:
    python exercise_3_2_cdc_dashboard.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "debezium")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "inventory")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def create_cdc_source(t_env: TableEnvironment, table_name: str, mysql_table: str, schema: str, pk: str) -> None:
    """
    Create a MySQL CDC source table in the Flink catalog.

    Args:
        t_env: The Flink TableEnvironment.
        table_name: Name of the Flink table to create.
        mysql_table: Name of the MySQL table to read from.
        schema: Column definitions as SQL string.
        pk: Primary key column name.
    """
    t_env.execute_sql(f"""
        CREATE TABLE {table_name} (
            {schema},
            PRIMARY KEY ({pk}) NOT ENFORCED
        ) WITH (
            'connector'        = 'mysql-cdc',
            'hostname'         = '{MYSQL_HOST}',
            'port'             = '{MYSQL_PORT}',
            'username'         = '{MYSQL_USER}',
            'password'         = '{MYSQL_PASSWORD}',
            'database-name'    = '{MYSQL_DATABASE}',
            'table-name'       = '{mysql_table}',
            'server-time-zone' = 'UTC'
        )
    """)


def main() -> None:
    """Run the CDC-powered dashboard pipeline."""
    logger.info("Starting Exercise 3.2: CDC-Powered Real-Time Dashboard")

    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    t_env.get_config().set("execution.checkpointing.interval", "60000")
    t_env.get_config().set("execution.checkpointing.mode", "EXACTLY_ONCE")
    t_env.get_config().set("parallelism.default", "2")

    # -----------------------------------------------------------------------
    # CDC Sources
    # -----------------------------------------------------------------------
    logger.info("Creating CDC source tables")

    create_cdc_source(
        t_env, "cdc_orders", "orders",
        """
            order_id    INT,
            customer_id INT,
            product_id  INT,
            quantity    INT,
            amount      DECIMAL(10, 2),
            status      VARCHAR(50),
            created_at  TIMESTAMP(3),
            updated_at  TIMESTAMP(3)
        """,
        "order_id",
    )

    create_cdc_source(
        t_env, "cdc_customers", "customers",
        """
            customer_id INT,
            first_name  VARCHAR(100),
            last_name   VARCHAR(100),
            email       VARCHAR(255),
            city        VARCHAR(100),
            state       VARCHAR(50),
            country     VARCHAR(10),
            created_at  TIMESTAMP(3)
        """,
        "customer_id",
    )

    create_cdc_source(
        t_env, "cdc_products", "products",
        """
            product_id   INT,
            product_name VARCHAR(255),
            category     VARCHAR(100),
            price        DECIMAL(10, 2),
            brand        VARCHAR(100),
            updated_at   TIMESTAMP(3)
        """,
        "product_id",
    )

    # -----------------------------------------------------------------------
    # View A: Revenue by City
    # -----------------------------------------------------------------------
    logger.info("Creating View A: Revenue by City")

    t_env.execute_sql(f"""
        CREATE TABLE revenue_by_city_sink (
            city          VARCHAR(100),
            total_revenue DECIMAL(12, 2),
            order_count   BIGINT,
            PRIMARY KEY (city) NOT ENFORCED
        ) WITH (
            'connector'                    = 'upsert-kafka',
            'topic'                        = 'revenue-by-city',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                   = 'json',
            'value.format'                 = 'json'
        )
    """)

    t_env.execute_sql("""
        INSERT INTO revenue_by_city_sink
        SELECT
            c.city,
            SUM(o.amount) AS total_revenue,
            COUNT(*)      AS order_count
        FROM cdc_orders o
        INNER JOIN cdc_customers c
            ON o.customer_id = c.customer_id
        GROUP BY c.city
    """)

    # -----------------------------------------------------------------------
    # View B: Category Performance
    # -----------------------------------------------------------------------
    logger.info("Creating View B: Category Performance")

    t_env.execute_sql(f"""
        CREATE TABLE category_performance_sink (
            category        VARCHAR(100),
            total_revenue   DECIMAL(12, 2),
            avg_order_value DECIMAL(10, 2),
            total_quantity  BIGINT,
            order_count     BIGINT,
            PRIMARY KEY (category) NOT ENFORCED
        ) WITH (
            'connector'                    = 'upsert-kafka',
            'topic'                        = 'category-performance',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                   = 'json',
            'value.format'                 = 'json'
        )
    """)

    t_env.execute_sql("""
        INSERT INTO category_performance_sink
        SELECT
            p.category,
            SUM(o.amount)                        AS total_revenue,
            CAST(AVG(o.amount) AS DECIMAL(10, 2)) AS avg_order_value,
            CAST(SUM(o.quantity) AS BIGINT)        AS total_quantity,
            COUNT(*)                              AS order_count
        FROM cdc_orders o
        INNER JOIN cdc_products p
            ON o.product_id = p.product_id
        GROUP BY p.category
    """)

    # -----------------------------------------------------------------------
    # View C: Hourly Order Trend
    # -----------------------------------------------------------------------
    logger.info("Creating View C: Hourly Order Trend")

    t_env.execute_sql(f"""
        CREATE TABLE hourly_order_trend_sink (
            window_start  TIMESTAMP(3),
            window_end    TIMESTAMP(3),
            order_count   BIGINT,
            total_revenue DECIMAL(12, 2),
            PRIMARY KEY (window_start) NOT ENFORCED
        ) WITH (
            'connector'                    = 'upsert-kafka',
            'topic'                        = 'hourly-order-trend',
            'properties.bootstrap.servers' = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                   = 'json',
            'value.format'                 = 'json'
        )
    """)

    result = t_env.execute_sql("""
        INSERT INTO hourly_order_trend_sink
        SELECT
            TUMBLE_START(created_at, INTERVAL '1' HOUR) AS window_start,
            TUMBLE_END(created_at, INTERVAL '1' HOUR)   AS window_end,
            COUNT(*)                                     AS order_count,
            SUM(amount)                                  AS total_revenue
        FROM cdc_orders
        GROUP BY TUMBLE(created_at, INTERVAL '1' HOUR)
    """)

    logger.info("All three dashboard views running. Waiting (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    main()
