"""
Seed Data Generator for Flink Module Exercises
===============================================

Produces sample data to Kafka topics (orders, customers, products) and inserts
corresponding records into MySQL for CDC exercises. This script populates the
data sources that all Flink SQL and PyFlink exercises depend on.

Data Generated:
    - 50 customers (Kafka + MySQL)
    - 20 products across 5 categories (Kafka + MySQL)
    - Continuous stream of orders (Kafka + MySQL, one per second)

Prerequisites:
    - Kafka broker running at localhost:9092 (or KAFKA_BOOTSTRAP_SERVERS)
    - MySQL running at localhost:3306 (or MYSQL_HOST)
    - Python packages: confluent-kafka, faker, mysql-connector-python

Usage:
    python seed_data.py

    The script runs continuously, producing one order per second.
    Press Ctrl+C to stop.

Environment Variables:
    KAFKA_BOOTSTRAP_SERVERS  -- Kafka broker (default: localhost:9092)
    MYSQL_HOST               -- MySQL host (default: localhost)
    MYSQL_PORT               -- MySQL port (default: 3306)
    MYSQL_USER               -- MySQL user (default: root)
    MYSQL_PASSWORD           -- MySQL password (default: debezium)
    MYSQL_DATABASE           -- MySQL database (default: inventory)
"""

import json
import os
import random
import sys
import time
import uuid
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from confluent_kafka import Producer
from faker import Faker
import mysql.connector

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "debezium")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "inventory")

# Data generation parameters
NUM_CUSTOMERS = 50
NUM_PRODUCTS = 20
ORDER_INTERVAL_SECONDS = 1  # Time between generated orders

# Product categories and sample data
CATEGORIES = ["Electronics", "Books", "Clothing", "Home & Garden", "Sports"]
BRANDS = {
    "Electronics": ["TechCo", "GadgetPro", "DigiMax", "SmartLife", "CircuitWave"],
    "Books": ["PageTurner", "LitPress", "ReadMore", "BookHouse", "InkWell"],
    "Clothing": ["StyleCraft", "ThreadLine", "FitWear", "UrbanEdge", "ComfortPlus"],
    "Home & Garden": ["GreenThumb", "HomeEase", "CozyNest", "DwellWell", "GardenPro"],
    "Sports": ["ActiveGear", "PeakForm", "TrailBlaze", "PowerPlay", "EndureFit"],
}
ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed_data")

# Faker instance for realistic data
fake = Faker()
Faker.seed(42)
random.seed(42)


# ---------------------------------------------------------------------------
# JSON serializer for Decimal and datetime
# ---------------------------------------------------------------------------


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Decimal and datetime objects."""

    def default(self, obj: Any) -> Any:
        """Convert Decimal to float and datetime to ISO string."""
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


# ---------------------------------------------------------------------------
# Kafka helpers
# ---------------------------------------------------------------------------


def create_kafka_producer() -> Producer:
    """
    Create and return a Confluent Kafka producer.

    Returns:
        A configured Producer instance.
    """
    config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "flink-seed-data-producer",
        "acks": "all",
    }
    return Producer(config)


def delivery_report(err: Any, msg: Any) -> None:
    """
    Callback for Kafka message delivery confirmation.

    Args:
        err: Error object if delivery failed, None if successful.
        msg: The delivered message.
    """
    if err is not None:
        logger.error("Delivery failed for topic %s: %s", msg.topic(), err)


def produce_to_kafka(producer: Producer, topic: str, key: str, value: dict) -> None:
    """
    Serialize and produce a message to a Kafka topic.

    Args:
        producer: The Kafka Producer instance.
        topic: Target Kafka topic.
        key: Message key (used for partitioning).
        value: Message value as a dictionary.
    """
    producer.produce(
        topic=topic,
        key=key.encode("utf-8"),
        value=json.dumps(value, cls=DecimalEncoder).encode("utf-8"),
        callback=delivery_report,
    )


# ---------------------------------------------------------------------------
# MySQL helpers
# ---------------------------------------------------------------------------


def get_mysql_connection() -> mysql.connector.MySQLConnection:
    """
    Create and return a MySQL database connection.

    Returns:
        A MySQL connection object.
    """
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )


def setup_mysql_tables(conn: mysql.connector.MySQLConnection) -> None:
    """
    Create the MySQL tables needed for CDC exercises if they don't exist.

    Creates: customers, products, orders.

    Args:
        conn: An active MySQL connection.
    """
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL,
            city VARCHAR(100),
            state VARCHAR(50),
            country VARCHAR(10) DEFAULT 'US',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INT AUTO_INCREMENT PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            category VARCHAR(100) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            brand VARCHAR(100),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT AUTO_INCREMENT PRIMARY KEY,
            customer_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL DEFAULT 1,
            amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (product_id) REFERENCES products(product_id)
        )
    """)

    conn.commit()
    cursor.close()
    logger.info("MySQL tables created/verified")


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------


def generate_customers(
    producer: Producer, conn: mysql.connector.MySQLConnection
) -> list[dict]:
    """
    Generate sample customer records and insert into Kafka + MySQL.

    Args:
        producer: Kafka producer.
        conn: MySQL connection.

    Returns:
        List of generated customer dictionaries.
    """
    customers = []
    cursor = conn.cursor()

    for i in range(1, NUM_CUSTOMERS + 1):
        customer = {
            "customer_id": str(i),
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "country": random.choice(["US", "CA", "UK", "DE", "FR"]),
            "created_at": datetime.utcnow().isoformat(),
        }
        customers.append(customer)

        # Produce to Kafka
        produce_to_kafka(producer, "customers", customer["customer_id"], customer)

        # Insert into MySQL
        cursor.execute(
            """
            INSERT INTO customers (first_name, last_name, email, city, state, country)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE first_name=VALUES(first_name)
            """,
            (
                customer["first_name"],
                customer["last_name"],
                customer["email"],
                customer["city"],
                customer["state"],
                customer["country"],
            ),
        )

    conn.commit()
    cursor.close()
    producer.flush()
    logger.info("Generated %d customers", len(customers))
    return customers


def generate_products(
    producer: Producer, conn: mysql.connector.MySQLConnection
) -> list[dict]:
    """
    Generate sample product records and insert into Kafka + MySQL.

    Args:
        producer: Kafka producer.
        conn: MySQL connection.

    Returns:
        List of generated product dictionaries.
    """
    products = []
    cursor = conn.cursor()

    product_names = {
        "Electronics": [
            "Wireless Headphones", "Smart Watch", "Bluetooth Speaker",
            "USB-C Hub",
        ],
        "Books": [
            "Python Cookbook", "Data Engineering Guide", "Streaming Systems",
            "Kafka Definitive Guide",
        ],
        "Clothing": [
            "Running Shoes", "Winter Jacket", "Cotton T-Shirt",
            "Hiking Boots",
        ],
        "Home & Garden": [
            "Garden Hose", "LED Desk Lamp", "Coffee Maker",
            "Plant Pot Set",
        ],
        "Sports": [
            "Yoga Mat", "Resistance Bands", "Water Bottle",
            "Fitness Tracker",
        ],
    }

    product_id = 0
    for category in CATEGORIES:
        for name in product_names[category]:
            product_id += 1
            product = {
                "product_id": str(product_id),
                "product_name": name,
                "category": category,
                "price": str(round(random.uniform(9.99, 299.99), 2)),
                "brand": random.choice(BRANDS[category]),
                "updated_at": datetime.utcnow().isoformat(),
            }
            products.append(product)

            # Produce to Kafka
            produce_to_kafka(producer, "products", product["product_id"], product)

            # Insert into MySQL
            cursor.execute(
                """
                INSERT INTO products (product_name, category, price, brand)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE product_name=VALUES(product_name)
                """,
                (
                    product["product_name"],
                    product["category"],
                    float(product["price"]),
                    product["brand"],
                ),
            )

    conn.commit()
    cursor.close()
    producer.flush()
    logger.info("Generated %d products", len(products))
    return products


def generate_order(
    producer: Producer,
    conn: mysql.connector.MySQLConnection,
    customers: list[dict],
    products: list[dict],
) -> dict:
    """
    Generate a single order record and insert into Kafka + MySQL.

    The order references random customer and product IDs from the
    previously generated data. The amount is calculated as
    price * quantity with some random variation.

    Args:
        producer: Kafka producer.
        conn: MySQL connection.
        customers: List of available customer records.
        products: List of available product records.

    Returns:
        The generated order dictionary.
    """
    customer = random.choice(customers)
    product = random.choice(products)
    quantity = random.randint(1, 5)
    unit_price = float(product["price"])
    amount = round(unit_price * quantity * random.uniform(0.9, 1.1), 2)

    # Simulate slight out-of-order events by occasionally backdating
    event_time = datetime.utcnow()
    if random.random() < 0.1:  # 10% of events are slightly late
        event_time -= timedelta(seconds=random.randint(1, 15))

    order = {
        "order_id": str(uuid.uuid4()),
        "customer_id": customer["customer_id"],
        "product_id": product["product_id"],
        "quantity": quantity,
        "amount": amount,
        "order_status": random.choice(ORDER_STATUSES),
        "order_time": event_time.isoformat(),
    }

    # Produce to Kafka
    produce_to_kafka(producer, "orders", order["order_id"], order)

    # Insert into MySQL
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO orders (customer_id, product_id, quantity, amount, status)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            int(customer["customer_id"]),
            int(product["product_id"]),
            quantity,
            amount,
            order["order_status"],
        ),
    )
    conn.commit()
    cursor.close()

    return order


def simulate_mysql_updates(conn: mysql.connector.MySQLConnection) -> None:
    """
    Simulate random updates to existing MySQL records to generate CDC events.

    This function randomly picks an action:
    - Update an order's status (e.g., pending -> shipped)
    - Update a product's price
    - Update a customer's city

    Args:
        conn: MySQL connection.
    """
    cursor = conn.cursor()
    action = random.choice(["update_order", "update_product", "update_customer"])

    try:
        if action == "update_order":
            new_status = random.choice(ORDER_STATUSES)
            cursor.execute(
                "UPDATE orders SET status = %s WHERE order_id = ("
                "SELECT order_id FROM (SELECT order_id FROM orders ORDER BY RAND() LIMIT 1) t"
                ")",
                (new_status,),
            )
            logger.debug("Updated random order status to '%s'", new_status)

        elif action == "update_product":
            price_change = round(random.uniform(-10, 20), 2)
            cursor.execute(
                "UPDATE products SET price = GREATEST(1.00, price + %s) "
                "WHERE product_id = ("
                "SELECT product_id FROM (SELECT product_id FROM products ORDER BY RAND() LIMIT 1) t"
                ")",
                (price_change,),
            )
            logger.debug("Updated random product price by %s", price_change)

        elif action == "update_customer":
            new_city = fake.city()
            cursor.execute(
                "UPDATE customers SET city = %s WHERE customer_id = ("
                "SELECT customer_id FROM ("
                "SELECT customer_id FROM customers ORDER BY RAND() LIMIT 1) t"
                ")",
                (new_city,),
            )
            logger.debug("Updated random customer city to '%s'", new_city)

        conn.commit()
    except Exception as e:
        logger.warning("MySQL update failed (non-fatal): %s", e)
        conn.rollback()
    finally:
        cursor.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """
    Main entry point for the seed data generator.

    1. Connects to Kafka and MySQL.
    2. Creates MySQL tables if they don't exist.
    3. Seeds customers and products (one-time).
    4. Continuously generates orders (one per second).
    5. Periodically simulates MySQL updates for CDC events.
    """
    logger.info("=== Flink Module Seed Data Generator ===")
    logger.info("Kafka: %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("MySQL: %s:%d/%s", MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE)

    # Create Kafka producer
    producer = create_kafka_producer()

    # Connect to MySQL
    try:
        conn = get_mysql_connection()
        logger.info("Connected to MySQL")
    except Exception as e:
        logger.error("Failed to connect to MySQL: %s", e)
        logger.info("Continuing with Kafka-only mode")
        conn = None

    # Setup MySQL tables
    if conn:
        setup_mysql_tables(conn)

    # Generate reference data (customers + products)
    logger.info("Generating reference data...")
    if conn:
        customers = generate_customers(producer, conn)
        products = generate_products(producer, conn)
    else:
        # Kafka-only fallback: generate without MySQL
        customers = []
        for i in range(1, NUM_CUSTOMERS + 1):
            customer = {
                "customer_id": str(i),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.email(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": random.choice(["US", "CA", "UK", "DE", "FR"]),
                "created_at": datetime.utcnow().isoformat(),
            }
            customers.append(customer)
            produce_to_kafka(producer, "customers", customer["customer_id"], customer)

        products = []
        pid = 0
        for cat in CATEGORIES:
            for _ in range(4):
                pid += 1
                product = {
                    "product_id": str(pid),
                    "product_name": fake.catch_phrase(),
                    "category": cat,
                    "price": str(round(random.uniform(9.99, 299.99), 2)),
                    "brand": random.choice(BRANDS[cat]),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                products.append(product)
                produce_to_kafka(producer, "products", product["product_id"], product)
        producer.flush()
        logger.info("Generated %d customers and %d products (Kafka only)", len(customers), len(products))

    # Continuously generate orders
    logger.info("Starting continuous order generation (1 order per %d second)...", ORDER_INTERVAL_SECONDS)
    logger.info("Press Ctrl+C to stop")

    order_count = 0
    try:
        while True:
            if conn:
                order = generate_order(producer, conn, customers, products)
            else:
                # Kafka-only order generation
                customer = random.choice(customers)
                product = random.choice(products)
                quantity = random.randint(1, 5)
                amount = round(float(product["price"]) * quantity * random.uniform(0.9, 1.1), 2)
                event_time = datetime.utcnow()
                if random.random() < 0.1:
                    event_time -= timedelta(seconds=random.randint(1, 15))
                order = {
                    "order_id": str(uuid.uuid4()),
                    "customer_id": customer["customer_id"],
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "amount": amount,
                    "order_status": random.choice(ORDER_STATUSES),
                    "order_time": event_time.isoformat(),
                }
                produce_to_kafka(producer, "orders", order["order_id"], order)

            order_count += 1
            producer.poll(0)  # Trigger delivery callbacks

            if order_count % 10 == 0:
                producer.flush()
                logger.info(
                    "Produced %d orders (latest: $%.2f, status=%s)",
                    order_count,
                    order["amount"],
                    order["order_status"],
                )

            # Every 5th order, simulate a MySQL update for CDC
            if conn and order_count % 5 == 0:
                simulate_mysql_updates(conn)

            time.sleep(ORDER_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("Stopping... Produced %d orders total", order_count)
    finally:
        producer.flush()
        if conn:
            conn.close()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    main()
