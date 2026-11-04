"""
PyFlink CDC Analytics Pipeline
===============================

A PyFlink application that reads Change Data Capture (CDC) events directly from
a MySQL database, computes real-time order analytics (revenue per hour, top
products by revenue), and writes the aggregated results to Kafka topics.

This demonstrates:
    - Using the Flink mysql-cdc connector from PyFlink
    - Creating CDC source tables that track INSERT, UPDATE, DELETE in real time
    - Tumbling window aggregations on CDC changelog streams
    - Writing aggregated results to Kafka via upsert-kafka connector
    - Configuring checkpointing for exactly-once guarantees

Architecture:
    MySQL (binlog) --> Flink CDC Source --> Aggregation --> Kafka Sink

Prerequisites:
    - MySQL container running with binlog enabled (debezium/example-mysql:2.4)
    - Kafka broker running at kafka:29092
    - The 'inventory' database with 'orders' and 'products' tables seeded
    - Flink CDC and Kafka connector JARs in the classpath
    - apache-flink Python package installed

Usage:
    python pyflink_cdc_analytics.py

    Or submit to a Flink cluster:
    flink run -py pyflink_cdc_analytics.py
"""

import os
import logging

from pyflink.table import EnvironmentSettings, TableEnvironment

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "debezium")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "inventory")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pyflink_cdc_analytics")


def create_mysql_orders_cdc_source() -> str:
    """
    DDL for the MySQL orders CDC source table.

    This table reads the MySQL binlog in real time, capturing all INSERT,
    UPDATE, and DELETE operations on the 'orders' table. The PRIMARY KEY
    is required for CDC sources to correctly handle updates and deletes.

    Returns:
        Flink SQL DDL string.
    """
    return f"""
        CREATE TABLE mysql_orders (
            order_id    INT,
            customer_id INT,
            product_id  INT,
            quantity    INT,
            amount      DECIMAL(10, 2),
            status      VARCHAR(50),
            created_at  TIMESTAMP(3),
            updated_at  TIMESTAMP(3),
            PRIMARY KEY (order_id) NOT ENFORCED
        ) WITH (
            'connector'       = 'mysql-cdc',
            'hostname'        = '{MYSQL_HOST}',
            'port'            = '{MYSQL_PORT}',
            'username'        = '{MYSQL_USER}',
            'password'        = '{MYSQL_PASSWORD}',
            'database-name'   = '{MYSQL_DATABASE}',
            'table-name'      = 'orders',
            'server-time-zone'= 'UTC'
        )
    """


def create_mysql_products_cdc_source() -> str:
    """
    DDL for the MySQL products CDC source table.

    Captures real-time changes to the products catalog in MySQL.

    Returns:
        Flink SQL DDL string.
    """
    return f"""
        CREATE TABLE mysql_products (
            product_id   INT,
            product_name VARCHAR(255),
            category     VARCHAR(100),
            price        DECIMAL(10, 2),
            brand        VARCHAR(100),
            updated_at   TIMESTAMP(3),
            PRIMARY KEY (product_id) NOT ENFORCED
        ) WITH (
            'connector'       = 'mysql-cdc',
            'hostname'        = '{MYSQL_HOST}',
            'port'            = '{MYSQL_PORT}',
            'username'        = '{MYSQL_USER}',
            'password'        = '{MYSQL_PASSWORD}',
            'database-name'   = '{MYSQL_DATABASE}',
            'table-name'      = 'products',
            'server-time-zone'= 'UTC'
        )
    """


def create_revenue_per_hour_sink() -> str:
    """
    DDL for the revenue-per-hour Kafka sink table.

    Uses upsert-kafka because windowed aggregations produce updates when
    late data arrives. The primary key is the window start time.

    Returns:
        Flink SQL DDL string.
    """
    return f"""
        CREATE TABLE revenue_per_hour_sink (
            window_start    TIMESTAMP(3),
            window_end      TIMESTAMP(3),
            order_count     BIGINT,
            total_revenue   DECIMAL(12, 2),
            avg_order_value DECIMAL(10, 2),
            PRIMARY KEY (window_start) NOT ENFORCED
        ) WITH (
            'connector'                       = 'upsert-kafka',
            'topic'                           = 'revenue-per-hour',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                      = 'json',
            'value.format'                    = 'json'
        )
    """


def create_top_products_sink() -> str:
    """
    DDL for the top-products-by-revenue Kafka sink table.

    Continuously updated running totals of revenue per product.

    Returns:
        Flink SQL DDL string.
    """
    return f"""
        CREATE TABLE top_products_sink (
            product_id      INT,
            product_name    VARCHAR(255),
            category        VARCHAR(100),
            total_revenue   DECIMAL(12, 2),
            total_quantity  BIGINT,
            order_count     BIGINT,
            PRIMARY KEY (product_id) NOT ENFORCED
        ) WITH (
            'connector'                       = 'upsert-kafka',
            'topic'                           = 'top-products',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                      = 'json',
            'value.format'                    = 'json'
        )
    """


def create_order_status_sink() -> str:
    """
    DDL for the order-status-summary Kafka sink table.

    Real-time count and revenue breakdown by order status.

    Returns:
        Flink SQL DDL string.
    """
    return f"""
        CREATE TABLE order_status_sink (
            status          VARCHAR(50),
            order_count     BIGINT,
            total_revenue   DECIMAL(12, 2),
            PRIMARY KEY (status) NOT ENFORCED
        ) WITH (
            'connector'                       = 'upsert-kafka',
            'topic'                           = 'order-status-summary',
            'properties.bootstrap.servers'    = '{KAFKA_BOOTSTRAP_SERVERS}',
            'key.format'                      = 'json',
            'value.format'                    = 'json'
        )
    """


def run_cdc_analytics() -> None:
    """
    Main entry point for the CDC analytics pipeline.

    This function:
        1. Creates a streaming TableEnvironment with checkpointing enabled.
        2. Registers MySQL CDC source tables (orders, products).
        3. Registers Kafka sink tables for analytics results.
        4. Submits three continuous analytics queries:
           a. Revenue per hour (tumbling window on created_at)
           b. Top products by total revenue (running aggregation)
           c. Order status summary (running aggregation)
        5. All queries run concurrently as separate Flink jobs.
    """
    logger.info("Starting PyFlink CDC Analytics Pipeline")

    # -----------------------------------------------------------------------
    # Step 1: Create the streaming table environment
    # -----------------------------------------------------------------------
    env_settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(env_settings)

    # Configure checkpointing for exactly-once CDC processing
    config = t_env.get_config()
    config.set("execution.checkpointing.interval", "60000")
    config.set("execution.checkpointing.mode", "EXACTLY_ONCE")
    config.set("execution.checkpointing.timeout", "600000")
    config.set("parallelism.default", "2")

    # -----------------------------------------------------------------------
    # Step 2: Create CDC source tables
    # -----------------------------------------------------------------------
    logger.info("Creating MySQL CDC source tables")
    t_env.execute_sql(create_mysql_orders_cdc_source())
    t_env.execute_sql(create_mysql_products_cdc_source())
    logger.info("CDC source tables created successfully")

    # -----------------------------------------------------------------------
    # Step 3: Create Kafka sink tables
    # -----------------------------------------------------------------------
    logger.info("Creating Kafka sink tables")
    t_env.execute_sql(create_revenue_per_hour_sink())
    t_env.execute_sql(create_top_products_sink())
    t_env.execute_sql(create_order_status_sink())
    logger.info("Kafka sink tables created successfully")

    # -----------------------------------------------------------------------
    # Step 4a: Revenue per hour (tumbling window)
    # -----------------------------------------------------------------------
    # Uses a 1-hour tumbling window based on the order's created_at timestamp.
    # Computes order count, total revenue, and average order value per window.
    # -----------------------------------------------------------------------
    logger.info("Submitting revenue-per-hour query")
    revenue_query = """
        INSERT INTO revenue_per_hour_sink
        SELECT
            TUMBLE_START(created_at, INTERVAL '1' HOUR)     AS window_start,
            TUMBLE_END(created_at, INTERVAL '1' HOUR)       AS window_end,
            COUNT(*)                                         AS order_count,
            SUM(amount)                                      AS total_revenue,
            CAST(AVG(amount) AS DECIMAL(10, 2))              AS avg_order_value
        FROM mysql_orders
        GROUP BY TUMBLE(created_at, INTERVAL '1' HOUR)
    """
    t_env.execute_sql(revenue_query)
    logger.info("Revenue-per-hour job submitted")

    # -----------------------------------------------------------------------
    # Step 4b: Top products by revenue (running aggregation with join)
    # -----------------------------------------------------------------------
    # Joins orders with products to get product details, then aggregates
    # total revenue and quantity per product. This is a non-windowed
    # (global) aggregation that continuously updates.
    # -----------------------------------------------------------------------
    logger.info("Submitting top-products query")
    top_products_query = """
        INSERT INTO top_products_sink
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            SUM(o.amount)                   AS total_revenue,
            CAST(SUM(o.quantity) AS BIGINT)  AS total_quantity,
            COUNT(*)                         AS order_count
        FROM mysql_orders o
        INNER JOIN mysql_products p
            ON o.product_id = p.product_id
        GROUP BY p.product_id, p.product_name, p.category
    """
    t_env.execute_sql(top_products_query)
    logger.info("Top-products job submitted")

    # -----------------------------------------------------------------------
    # Step 4c: Order status summary (running aggregation)
    # -----------------------------------------------------------------------
    # Counts orders and sums revenue grouped by order status.
    # Reflects real-time status changes from MySQL (e.g., 'pending' -> 'shipped').
    # -----------------------------------------------------------------------
    logger.info("Submitting order-status-summary query")
    status_query = """
        INSERT INTO order_status_sink
        SELECT
            status,
            COUNT(*)     AS order_count,
            SUM(amount)  AS total_revenue
        FROM mysql_orders
        GROUP BY status
    """
    result = t_env.execute_sql(status_query)
    logger.info("Order-status-summary job submitted")

    # Wait on the last job (all three run concurrently)
    logger.info("All CDC analytics jobs running. Waiting for completion (Ctrl+C to cancel)...")
    result.wait()


if __name__ == "__main__":
    run_cdc_analytics()
