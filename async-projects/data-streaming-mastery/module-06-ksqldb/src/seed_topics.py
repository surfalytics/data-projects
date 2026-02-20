#!/usr/bin/env python3
"""
Seed Kafka topics with sample data for ksqlDB exercises.

Produces records to four topics:
  - orders:      Order events (order_id, customer_id, product_id, quantity, price, timestamp)
  - customers:   Customer records (customer_id, name, email, region)
  - products:    Product records (product_id, name, category, price)
  - clickstream: Page view events (user_id, page, referrer, timestamp)

Uses confluent-kafka Producer and Faker for realistic data generation.
Runs continuously until interrupted with Ctrl+C.
"""

import json
import random
import signal
import sys
import time
from datetime import datetime, timezone

from confluent_kafka import Producer
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
ORDERS_TOPIC = "orders"
CUSTOMERS_TOPIC = "customers"
PRODUCTS_TOPIC = "products"
CLICKSTREAM_TOPIC = "clickstream"

NUM_CUSTOMERS = 50
NUM_PRODUCTS = 20
ORDERS_PER_SECOND = 2
CLICKS_PER_SECOND = 5

fake = Faker()
Faker.seed(42)
random.seed(42)

# ---------------------------------------------------------------------------
# Data Generators
# ---------------------------------------------------------------------------

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America"]
CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
PAGES = ["/home", "/products", "/cart", "/checkout", "/about", "/contact",
         "/products/electronics", "/products/clothing", "/products/sports",
         "/search", "/account", "/deals"]
REFERRERS = ["google.com", "facebook.com", "twitter.com", "direct",
             "email", "bing.com", "reddit.com"]


def generate_customers(num: int) -> list[dict]:
    """Generate a fixed set of customer records."""
    customers = []
    for i in range(1, num + 1):
        customers.append({
            "customer_id": f"C{i:04d}",
            "name": fake.name(),
            "email": fake.email(),
            "region": random.choice(REGIONS),
        })
    return customers


def generate_products(num: int) -> list[dict]:
    """Generate a fixed set of product records."""
    products = []
    for i in range(1, num + 1):
        products.append({
            "product_id": f"P{i:04d}",
            "name": fake.catch_phrase(),
            "category": random.choice(CATEGORIES),
            "price": round(random.uniform(5.0, 500.0), 2),
        })
    return products


def generate_order(customers: list[dict], products: list[dict]) -> dict:
    """Generate a single order event."""
    customer = random.choice(customers)
    product = random.choice(products)
    return {
        "order_id": f"O{random.randint(100000, 999999)}",
        "customer_id": customer["customer_id"],
        "product_id": product["product_id"],
        "quantity": random.randint(1, 10),
        "price": product["price"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def generate_click(customers: list[dict]) -> dict:
    """Generate a single clickstream event."""
    customer = random.choice(customers)
    return {
        "user_id": customer["customer_id"],
        "page": random.choice(PAGES),
        "referrer": random.choice(REFERRERS),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Kafka Producer Helpers
# ---------------------------------------------------------------------------

def delivery_report(err, msg):
    """Callback for Kafka message delivery reports."""
    if err is not None:
        print(f"  [ERROR] Delivery failed for {msg.topic()}: {err}")


def create_producer() -> Producer:
    """Create and return a confluent-kafka Producer."""
    conf = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "ksqldb-seed-producer",
        "acks": "all",
    }
    return Producer(conf)


def produce_json(producer: Producer, topic: str, key: str, value: dict):
    """Serialize a dict to JSON and produce to a Kafka topic."""
    producer.produce(
        topic=topic,
        key=key,
        value=json.dumps(value).encode("utf-8"),
        callback=delivery_report,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """Seed Kafka topics with continuous sample data."""
    print("=" * 60)
    print("ksqlDB Module 6 -- Kafka Topic Seeder")
    print("=" * 60)

    producer = create_producer()

    # Generate reference data
    customers = generate_customers(NUM_CUSTOMERS)
    products = generate_products(NUM_PRODUCTS)

    # Produce customers (reference / lookup data)
    print(f"\n[1/4] Producing {len(customers)} customer records to '{CUSTOMERS_TOPIC}'...")
    for c in customers:
        produce_json(producer, CUSTOMERS_TOPIC, c["customer_id"], c)
    producer.flush()
    print(f"  Done. {len(customers)} customers produced.")

    # Produce products (reference / lookup data)
    print(f"\n[2/4] Producing {len(products)} product records to '{PRODUCTS_TOPIC}'...")
    for p in products:
        produce_json(producer, PRODUCTS_TOPIC, p["product_id"], p)
    producer.flush()
    print(f"  Done. {len(products)} products produced.")

    # Continuous order and clickstream generation
    print(f"\n[3/4] Starting continuous order generation (~{ORDERS_PER_SECOND}/sec)...")
    print(f"[4/4] Starting continuous clickstream generation (~{CLICKS_PER_SECOND}/sec)...")
    print("\nPress Ctrl+C to stop.\n")

    order_count = 0
    click_count = 0

    # Graceful shutdown
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        running = False
        print("\n\nShutting down...")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while running:
            # Produce orders
            for _ in range(ORDERS_PER_SECOND):
                order = generate_order(customers, products)
                produce_json(producer, ORDERS_TOPIC, order["order_id"], order)
                order_count += 1

            # Produce clicks
            for _ in range(CLICKS_PER_SECOND):
                click = generate_click(customers)
                produce_json(producer, CLICKSTREAM_TOPIC, click["user_id"], click)
                click_count += 1

            producer.flush()

            if order_count % 20 == 0:
                print(f"  Orders: {order_count:,} | Clicks: {click_count:,}", end="\r")

            time.sleep(1.0)

    except KeyboardInterrupt:
        pass
    finally:
        producer.flush()
        print(f"\n\nFinal counts -- Orders: {order_count:,} | Clicks: {click_count:,}")
        print("Seeder stopped.")


if __name__ == "__main__":
    main()
