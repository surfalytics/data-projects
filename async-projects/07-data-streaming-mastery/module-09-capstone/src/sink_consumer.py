#!/usr/bin/env python3
"""
Python Kafka Consumer that reads enriched data from Kafka and writes to PostgreSQL.

This is an alternative to the JDBC Sink Connector. It consumes from ksqlDB
output topics and writes to PostgreSQL analytics tables.

Topics consumed:
- ORDERS_ENRICHED -> orders_enriched
- REVENUE_PER_MINUTE -> revenue_per_minute
- REVENUE_PER_CATEGORY -> revenue_per_category
- TOP_CUSTOMERS -> top_customers
- ORDER_STATUS_COUNTS -> order_status_counts
"""

import json
import logging
import signal
import sys
import threading
import time
from datetime import datetime

import psycopg2
import psycopg2.extras
from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8081"
CONSUMER_GROUP = "python-sink-consumer"

PG_HOST = "localhost"
PG_PORT = 5432
PG_DB = "analytics"
PG_USER = "postgres"
PG_PASSWORD = "postgres"

TOPIC_TABLE_MAP = {
    "ORDERS_ENRICHED": "orders_enriched",
    "REVENUE_PER_MINUTE": "revenue_per_minute",
    "REVENUE_PER_CATEGORY": "revenue_per_category",
    "TOP_CUSTOMERS": "top_customers",
    "ORDER_STATUS_COUNTS": "order_status_counts",
}

BATCH_SIZE = 50
BATCH_TIMEOUT_SECONDS = 5

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sink-consumer")

# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------

shutdown_event = threading.Event()


def signal_handler(sig, frame):
    logger.info("Shutdown signal received.")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ---------------------------------------------------------------------------
# PostgreSQL Writer
# ---------------------------------------------------------------------------


class PostgresWriter:
    """Manages PostgreSQL connections and upsert operations."""

    def __init__(self):
        self.conn = None
        self._connect()

    def _connect(self):
        """Establish PostgreSQL connection."""
        self.conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD,
        )
        self.conn.autocommit = False
        logger.info("Connected to PostgreSQL.")

    def _ensure_connected(self):
        """Reconnect if connection is lost."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
        except Exception:
            logger.warning("PostgreSQL connection lost. Reconnecting...")
            self._connect()

    def upsert_orders_enriched(self, records):
        """Upsert enriched orders into PostgreSQL."""
        self._ensure_connected()
        sql = """
            INSERT INTO orders_enriched
                (order_id, customer_name, customer_email, status, total_amount, created_at, updated_at)
            VALUES (%(order_id)s, %(customer_name)s, %(customer_email)s, %(status)s,
                    %(total_amount)s, %(created_at)s, %(updated_at)s)
            ON CONFLICT (order_id) DO UPDATE SET
                customer_name = EXCLUDED.customer_name,
                customer_email = EXCLUDED.customer_email,
                status = EXCLUDED.status,
                total_amount = EXCLUDED.total_amount,
                updated_at = EXCLUDED.updated_at;
        """
        with self.conn.cursor() as cur:
            for r in records:
                params = {
                    "order_id": r.get("ORDER_ID") or r.get("order_id"),
                    "customer_name": r.get("CUSTOMER_NAME") or r.get("customer_name"),
                    "customer_email": r.get("CUSTOMER_EMAIL") or r.get("customer_email"),
                    "status": r.get("STATUS") or r.get("status"),
                    "total_amount": r.get("TOTAL_AMOUNT") or r.get("total_amount"),
                    "created_at": _to_timestamp(r.get("CREATED_AT") or r.get("created_at")),
                    "updated_at": _to_timestamp(r.get("UPDATED_AT") or r.get("updated_at")),
                }
                cur.execute(sql, params)
        self.conn.commit()

    def upsert_revenue_per_minute(self, records):
        """Upsert revenue per minute aggregation."""
        self._ensure_connected()
        sql = """
            INSERT INTO revenue_per_minute
                (window_start, window_end, total_revenue, order_count, avg_order_value)
            VALUES (%(window_start)s, %(window_end)s, %(total_revenue)s,
                    %(order_count)s, %(avg_order_value)s)
            ON CONFLICT (window_start, window_end) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                order_count = EXCLUDED.order_count,
                avg_order_value = EXCLUDED.avg_order_value;
        """
        with self.conn.cursor() as cur:
            for r in records:
                params = {
                    "window_start": _to_timestamp(r.get("WINDOW_START") or r.get("window_start")),
                    "window_end": _to_timestamp(r.get("WINDOW_END") or r.get("window_end")),
                    "total_revenue": r.get("TOTAL_REVENUE") or r.get("total_revenue"),
                    "order_count": r.get("ORDER_COUNT") or r.get("order_count"),
                    "avg_order_value": r.get("AVG_ORDER_VALUE") or r.get("avg_order_value"),
                }
                cur.execute(sql, params)
        self.conn.commit()

    def upsert_revenue_per_category(self, records):
        """Upsert revenue per category aggregation."""
        self._ensure_connected()
        sql = """
            INSERT INTO revenue_per_category
                (window_start, window_end, category, revenue, order_count)
            VALUES (%(window_start)s, %(window_end)s, %(category)s,
                    %(revenue)s, %(order_count)s)
            ON CONFLICT (window_start, window_end, category) DO UPDATE SET
                revenue = EXCLUDED.revenue,
                order_count = EXCLUDED.order_count;
        """
        with self.conn.cursor() as cur:
            for r in records:
                params = {
                    "window_start": _to_timestamp(r.get("WINDOW_START") or r.get("window_start")),
                    "window_end": _to_timestamp(r.get("WINDOW_END") or r.get("window_end")),
                    "category": r.get("CATEGORY") or r.get("category"),
                    "revenue": r.get("REVENUE") or r.get("revenue"),
                    "order_count": r.get("ORDER_COUNT") or r.get("order_count"),
                }
                cur.execute(sql, params)
        self.conn.commit()

    def upsert_top_customers(self, records):
        """Upsert top customers aggregation."""
        self._ensure_connected()
        sql = """
            INSERT INTO top_customers
                (window_start, window_end, customer_id, customer_name, total_spent, order_count)
            VALUES (%(window_start)s, %(window_end)s, %(customer_id)s,
                    %(customer_name)s, %(total_spent)s, %(order_count)s)
            ON CONFLICT (window_start, window_end, customer_id) DO UPDATE SET
                customer_name = EXCLUDED.customer_name,
                total_spent = EXCLUDED.total_spent,
                order_count = EXCLUDED.order_count;
        """
        with self.conn.cursor() as cur:
            for r in records:
                params = {
                    "window_start": _to_timestamp(r.get("WINDOW_START") or r.get("window_start")),
                    "window_end": _to_timestamp(r.get("WINDOW_END") or r.get("window_end")),
                    "customer_id": r.get("CUSTOMER_ID") or r.get("customer_id"),
                    "customer_name": r.get("CUSTOMER_NAME") or r.get("customer_name"),
                    "total_spent": r.get("TOTAL_SPENT") or r.get("total_spent"),
                    "order_count": r.get("ORDER_COUNT") or r.get("order_count"),
                }
                cur.execute(sql, params)
        self.conn.commit()

    def upsert_order_status_counts(self, records):
        """Upsert order status distribution."""
        self._ensure_connected()
        sql = """
            INSERT INTO order_status_counts (status, count, last_updated)
            VALUES (%(status)s, %(count)s, NOW())
            ON CONFLICT (status) DO UPDATE SET
                count = EXCLUDED.count,
                last_updated = NOW();
        """
        with self.conn.cursor() as cur:
            for r in records:
                params = {
                    "status": r.get("STATUS") or r.get("status"),
                    "count": r.get("COUNT") or r.get("count"),
                }
                cur.execute(sql, params)
        self.conn.commit()

    def close(self):
        """Close the PostgreSQL connection."""
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed.")


def _to_timestamp(val):
    """Convert epoch millis or various formats to datetime."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        # Assume epoch milliseconds
        return datetime.utcfromtimestamp(val / 1000.0)
    if isinstance(val, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(val, fmt)
            except ValueError:
                continue
    return val


# ---------------------------------------------------------------------------
# Kafka Consumer
# ---------------------------------------------------------------------------


def create_consumer():
    """Create Kafka consumer for all enriched topics."""
    conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
    }
    consumer = Consumer(conf)
    topics = list(TOPIC_TABLE_MAP.keys())
    consumer.subscribe(topics)
    logger.info(f"Subscribed to topics: {topics}")
    return consumer


def process_message(msg, writer):
    """Process a single Kafka message and write to PostgreSQL."""
    topic = msg.topic()

    try:
        value = json.loads(msg.value().decode("utf-8")) if msg.value() else None
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Try treating as raw bytes - might be Avro
        logger.warning(f"Could not decode message from {topic} as JSON. Skipping.")
        return

    if value is None:
        return

    try:
        if topic == "ORDERS_ENRICHED":
            writer.upsert_orders_enriched([value])
        elif topic == "REVENUE_PER_MINUTE":
            writer.upsert_revenue_per_minute([value])
        elif topic == "REVENUE_PER_CATEGORY":
            writer.upsert_revenue_per_category([value])
        elif topic == "TOP_CUSTOMERS":
            writer.upsert_top_customers([value])
        elif topic == "ORDER_STATUS_COUNTS":
            writer.upsert_order_status_counts([value])
    except Exception as e:
        logger.error(f"Error processing message from {topic}: {e}")


def main():
    logger.info("=" * 60)
    logger.info("Sink Consumer Starting")
    logger.info("=" * 60)

    # Wait for PostgreSQL
    writer = None
    for attempt in range(30):
        try:
            writer = PostgresWriter()
            break
        except Exception as e:
            logger.warning(f"PostgreSQL not ready (attempt {attempt + 1}/30): {e}")
            time.sleep(2)

    if writer is None:
        logger.error("Could not connect to PostgreSQL. Exiting.")
        sys.exit(1)

    # Wait for Kafka
    consumer = None
    for attempt in range(30):
        try:
            consumer = create_consumer()
            break
        except Exception as e:
            logger.warning(f"Kafka not ready (attempt {attempt + 1}/30): {e}")
            time.sleep(2)

    if consumer is None:
        logger.error("Could not connect to Kafka. Exiting.")
        sys.exit(1)

    message_count = 0

    try:
        while not shutdown_event.is_set():
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"Consumer error: {msg.error()}")
                continue

            process_message(msg, writer)
            message_count += 1

            if message_count % 100 == 0:
                logger.info(f"Processed {message_count} messages.")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    finally:
        logger.info(f"Total messages processed: {message_count}")
        if consumer:
            consumer.close()
        if writer:
            writer.close()

    logger.info("Sink consumer stopped.")


if __name__ == "__main__":
    main()
