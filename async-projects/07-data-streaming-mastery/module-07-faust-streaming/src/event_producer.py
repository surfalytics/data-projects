"""
Event Producer -- Generate Fake Transactions, Orders, Customers, and Products.

This script uses the confluent-kafka Python client and Faker to generate
realistic test events for the Faust streaming applications in this module.

It produces events to the following Kafka topics:
- transactions  : Financial transaction events (for fraud_detection.py)
- orders        : E-commerce order events (for order_enrichment.py, realtime_analytics.py)
- customers     : Customer reference data (for order_enrichment.py table)
- products      : Product reference data (for order_enrichment.py table)

Usage:
    # Make sure Kafka is running (docker-compose up -d), then:
    python -m src.event_producer

    # Or with options:
    python -m src.event_producer --transactions 100 --orders 100 --bootstrap-server localhost:9092

Uses confluent-kafka for producing (Faust is for consuming/processing).
"""

import argparse
import json
import random
import time
import uuid
from datetime import datetime, timedelta

from confluent_kafka import Producer
from faker import Faker

fake = Faker()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"

COUNTRIES = ["US", "GB", "DE", "FR", "JP", "BR", "AU", "CA", "IN", "MX"]

PRODUCT_CATEGORIES = [
    "electronics",
    "clothing",
    "home_garden",
    "sports",
    "books",
    "toys",
    "food",
    "automotive",
]

MERCHANTS = [
    "Amazon",
    "Walmart",
    "Target",
    "BestBuy",
    "Costco",
    "HomeDepot",
    "Macys",
    "Nike",
    "Apple",
    "Starbucks",
    "GasStation",
    "AirlineTickets",
    "HotelBooking",
    "OnlineGaming",
    "Jewelry",
]

# Pre-defined set of customer and product IDs for consistent reference data
CUSTOMER_IDS = [f"cust-{i:04d}" for i in range(1, 51)]
PRODUCT_IDS = [f"prod-{i:04d}" for i in range(1, 31)]
USER_IDS = [f"user-{i:04d}" for i in range(1, 21)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def delivery_report(err, msg):
    """Callback for Kafka produce confirmations."""
    if err is not None:
        print(f"  [ERROR] Delivery failed for {msg.topic()}: {err}")
    else:
        print(
            f"  [OK] {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}"
        )


def create_producer(bootstrap_servers: str) -> Producer:
    """Create a confluent-kafka Producer instance."""
    return Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "faust-event-producer",
            "acks": "all",
        }
    )


# ---------------------------------------------------------------------------
# Data Generators
# ---------------------------------------------------------------------------


def generate_transaction() -> dict:
    """Generate a single fake transaction event."""
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": random.choice(USER_IDS),
        "amount": round(random.uniform(1.0, 8000.0), 2),
        "merchant": random.choice(MERCHANTS),
        "country": random.choice(COUNTRIES),
        "timestamp": datetime.utcnow().isoformat(),
    }


def generate_order() -> dict:
    """Generate a single fake order event."""
    product_id = random.choice(PRODUCT_IDS)
    quantity = random.randint(1, 5)
    unit_price = round(random.uniform(9.99, 299.99), 2)
    return {
        "order_id": str(uuid.uuid4()),
        "customer_id": random.choice(CUSTOMER_IDS),
        "product_id": product_id,
        "quantity": quantity,
        "amount": round(unit_price * quantity, 2),
        "category": random.choice(PRODUCT_CATEGORIES),
        "timestamp": datetime.utcnow().isoformat(),
    }


def generate_customer(customer_id: str) -> dict:
    """Generate a fake customer reference record."""
    return {
        "customer_id": customer_id,
        "name": fake.name(),
        "email": fake.email(),
        "tier": random.choice(["bronze", "silver", "gold", "platinum"]),
        "country": random.choice(COUNTRIES),
    }


def generate_product(product_id: str) -> dict:
    """Generate a fake product reference record."""
    category = random.choice(PRODUCT_CATEGORIES)
    return {
        "product_id": product_id,
        "name": fake.catch_phrase(),
        "category": category,
        "price": round(random.uniform(9.99, 499.99), 2),
        "in_stock": random.random() > 0.1,
    }


# ---------------------------------------------------------------------------
# Produce Functions
# ---------------------------------------------------------------------------


def produce_reference_data(producer: Producer):
    """Produce customer and product reference data to their topics.

    This populates the lookup tables used by the order enrichment agent.
    """
    print("\n--- Producing Customer Reference Data ---")
    for cid in CUSTOMER_IDS:
        customer = generate_customer(cid)
        producer.produce(
            topic="customers",
            key=cid.encode("utf-8"),
            value=json.dumps(customer).encode("utf-8"),
            callback=delivery_report,
        )
    producer.flush()
    print(f"Produced {len(CUSTOMER_IDS)} customer records.")

    print("\n--- Producing Product Reference Data ---")
    for pid in PRODUCT_IDS:
        product = generate_product(pid)
        producer.produce(
            topic="products",
            key=pid.encode("utf-8"),
            value=json.dumps(product).encode("utf-8"),
            callback=delivery_report,
        )
    producer.flush()
    print(f"Produced {len(PRODUCT_IDS)} product records.")


def produce_transactions(producer: Producer, count: int, delay: float = 0.2):
    """Produce transaction events for the fraud detection agent.

    Args:
        producer: Kafka producer instance.
        count: Number of transactions to generate.
        delay: Seconds to wait between messages (simulates real-time flow).
    """
    print(f"\n--- Producing {count} Transactions ---")
    for i in range(count):
        txn = generate_transaction()
        producer.produce(
            topic="transactions",
            key=txn["user_id"].encode("utf-8"),
            value=json.dumps(txn).encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 10 == 0:
            producer.flush()
            print(f"  Produced {i + 1}/{count} transactions")

        time.sleep(delay)

    producer.flush()
    print(f"Produced {count} transactions.")


def produce_orders(producer: Producer, count: int, delay: float = 0.3):
    """Produce order events for the enrichment and analytics agents.

    Args:
        producer: Kafka producer instance.
        count: Number of orders to generate.
        delay: Seconds to wait between messages (simulates real-time flow).
    """
    print(f"\n--- Producing {count} Orders ---")
    for i in range(count):
        order = generate_order()
        producer.produce(
            topic="orders",
            key=order["customer_id"].encode("utf-8"),
            value=json.dumps(order).encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 10 == 0:
            producer.flush()
            print(f"  Produced {i + 1}/{count} orders")

        time.sleep(delay)

    producer.flush()
    print(f"Produced {count} orders.")


def produce_raw_messages(producer: Producer, count: int, delay: float = 0.2):
    """Produce raw messages for the basic transform app.

    Args:
        producer: Kafka producer instance.
        count: Number of raw messages to generate.
        delay: Seconds to wait between messages.
    """
    print(f"\n--- Producing {count} Raw Messages ---")
    for i in range(count):
        msg = {
            "message_id": str(uuid.uuid4()),
            "content": fake.sentence(nb_words=random.randint(5, 20)),
            "source": random.choice(["web", "mobile", "api", "batch"]),
            "timestamp": datetime.utcnow().isoformat(),
        }
        producer.produce(
            topic="raw-messages",
            key=msg["message_id"].encode("utf-8"),
            value=json.dumps(msg).encode("utf-8"),
            callback=delivery_report,
        )

        if (i + 1) % 10 == 0:
            producer.flush()
            print(f"  Produced {i + 1}/{count} raw messages")

        time.sleep(delay)

    producer.flush()
    print(f"Produced {count} raw messages.")


# ---------------------------------------------------------------------------
# Burst Producer (for triggering fraud alerts)
# ---------------------------------------------------------------------------


def produce_fraud_burst(producer: Producer, user_id: str, count: int = 10):
    """Produce a burst of transactions from a single user to trigger fraud rules.

    This intentionally creates a high-frequency pattern from one user,
    with some high-value transactions mixed in, to exercise the fraud
    detection logic.

    Args:
        producer: Kafka producer instance.
        user_id: The user ID to use for all burst transactions.
        count: Number of rapid-fire transactions.
    """
    print(f"\n--- Producing Fraud Burst: {count} txns for {user_id} ---")
    countries = random.sample(COUNTRIES, min(3, len(COUNTRIES)))

    for i in range(count):
        txn = {
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "amount": round(random.uniform(100.0, 7000.0), 2),
            "merchant": random.choice(MERCHANTS),
            "country": countries[i % len(countries)],  # Rotate countries
            "timestamp": datetime.utcnow().isoformat(),
        }
        producer.produce(
            topic="transactions",
            key=user_id.encode("utf-8"),
            value=json.dumps(txn).encode("utf-8"),
            callback=delivery_report,
        )
        time.sleep(0.05)  # Very fast -- triggers high-frequency rule

    producer.flush()
    print(f"Fraud burst complete for {user_id}.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    """Parse arguments and run the event producer."""
    parser = argparse.ArgumentParser(
        description="Generate fake events for Faust streaming apps"
    )
    parser.add_argument(
        "--bootstrap-server",
        default=KAFKA_BOOTSTRAP_SERVERS,
        help="Kafka bootstrap server (default: localhost:9092)",
    )
    parser.add_argument(
        "--transactions",
        type=int,
        default=50,
        help="Number of transaction events to produce (default: 50)",
    )
    parser.add_argument(
        "--orders",
        type=int,
        default=50,
        help="Number of order events to produce (default: 50)",
    )
    parser.add_argument(
        "--raw-messages",
        type=int,
        default=20,
        help="Number of raw messages to produce (default: 20)",
    )
    parser.add_argument(
        "--fraud-burst",
        action="store_true",
        help="Also produce a burst of transactions to trigger fraud detection",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay in seconds between messages (default: 0.2)",
    )

    args = parser.parse_args()

    producer = create_producer(args.bootstrap_server)

    # Step 1: Produce reference data (customers and products)
    produce_reference_data(producer)

    # Step 2: Produce raw messages for the basic app
    produce_raw_messages(producer, args.raw_messages, args.delay)

    # Step 3: Produce transaction events
    produce_transactions(producer, args.transactions, args.delay)

    # Step 4: Produce order events
    produce_orders(producer, args.orders, args.delay)

    # Step 5: Optionally produce a fraud burst
    if args.fraud_burst:
        produce_fraud_burst(producer, random.choice(USER_IDS), count=12)

    print("\n=== All events produced successfully ===")


if __name__ == "__main__":
    main()
