#!/usr/bin/env python3
"""
Avro Producer for E-Commerce Order Events

Produces Avro-serialized order events to a Kafka topic using the Confluent
Schema Registry. Each message represents an e-commerce order with customer
details, line items, and metadata.

Usage:
    python avro_producer.py [--num-messages 10] [--topic orders-avro]

Prerequisites:
    - Kafka broker running on localhost:9092
    - Schema Registry running on localhost:8081
    - pip install confluent-kafka[avro] faker
"""

import argparse
import json
import time
import uuid
from datetime import datetime

from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringSerializer,
)
from faker import Faker

# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

ORDER_SCHEMA_STR = json.dumps({
    "type": "record",
    "name": "Order",
    "namespace": "com.ecommerce.events",
    "doc": "An e-commerce order event capturing a customer purchase.",
    "fields": [
        {
            "name": "order_id",
            "type": "string",
            "doc": "Unique identifier for the order (UUID)."
        },
        {
            "name": "customer_id",
            "type": "string",
            "doc": "Unique identifier for the customer."
        },
        {
            "name": "customer_email",
            "type": "string",
            "doc": "Customer email address."
        },
        {
            "name": "product_name",
            "type": "string",
            "doc": "Name of the product ordered."
        },
        {
            "name": "quantity",
            "type": "int",
            "doc": "Number of units ordered."
        },
        {
            "name": "unit_price",
            "type": "double",
            "doc": "Price per unit in USD."
        },
        {
            "name": "total_amount",
            "type": "double",
            "doc": "Total order amount in USD (quantity * unit_price)."
        },
        {
            "name": "order_status",
            "type": {
                "type": "enum",
                "name": "OrderStatus",
                "symbols": ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]
            },
            "doc": "Current status of the order."
        },
        {
            "name": "shipping_address",
            "type": {
                "type": "record",
                "name": "Address",
                "fields": [
                    {"name": "street", "type": "string"},
                    {"name": "city", "type": "string"},
                    {"name": "state", "type": "string"},
                    {"name": "zip_code", "type": "string"},
                    {"name": "country", "type": "string", "default": "US"}
                ]
            },
            "doc": "Shipping address for the order."
        },
        {
            "name": "created_at",
            "type": "long",
            "doc": "Order creation timestamp as Unix epoch milliseconds."
        },
        {
            "name": "notes",
            "type": ["null", "string"],
            "default": None,
            "doc": "Optional order notes from the customer."
        }
    ]
})

# ---------------------------------------------------------------------------
# Products catalog (for realistic fake data)
# ---------------------------------------------------------------------------

PRODUCTS = [
    ("Wireless Bluetooth Headphones", 49.99),
    ("Mechanical Keyboard RGB", 89.99),
    ("USB-C Hub 7-in-1", 34.99),
    ("27-inch 4K Monitor", 329.99),
    ("Ergonomic Mouse", 59.99),
    ("Laptop Stand Aluminum", 44.99),
    ("Webcam 1080p HD", 69.99),
    ("External SSD 1TB", 109.99),
    ("Desk LED Light Bar", 39.99),
    ("Noise Cancelling Earbuds", 79.99),
]

fake = Faker()


def generate_order() -> dict:
    """Generate a single fake e-commerce order event.

    Returns:
        dict: Order event payload matching the Avro schema.
    """
    product_name, unit_price = fake.random_element(PRODUCTS)
    quantity = fake.random_int(min=1, max=5)

    return {
        "order_id": str(uuid.uuid4()),
        "customer_id": f"CUST-{fake.random_int(min=1000, max=9999)}",
        "customer_email": fake.email(),
        "product_name": product_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": round(quantity * unit_price, 2),
        "order_status": fake.random_element(
            ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]
        ),
        "shipping_address": {
            "street": fake.street_address(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "zip_code": fake.zipcode(),
            "country": "US",
        },
        "created_at": int(datetime.utcnow().timestamp() * 1000),
        "notes": fake.sentence() if fake.boolean(chance_of_getting_true=30) else None,
    }


def order_to_dict(order: dict, ctx: SerializationContext) -> dict:
    """Convert an order dict to a dict for Avro serialization.

    The AvroSerializer calls this function to transform Python objects
    into dictionaries that match the Avro schema.

    Args:
        order: The order event dictionary.
        ctx: Serialization context (provided by confluent-kafka).

    Returns:
        dict: The order dictionary (already in the correct format).
    """
    return order


def delivery_report(err, msg):
    """Callback invoked once per message to indicate delivery result.

    Args:
        err: Delivery error (None if successful).
        msg: The message that was produced.
    """
    if err is not None:
        print(f"  [ERROR] Delivery failed: {err}")
    else:
        print(
            f"  [OK] Delivered to {msg.topic()} "
            f"[partition={msg.partition()}] "
            f"@ offset {msg.offset()}"
        )


def create_avro_producer(
    bootstrap_servers: str = "localhost:9092",
    schema_registry_url: str = "http://localhost:8081",
) -> tuple:
    """Create a Kafka producer configured with Avro serialization.

    Args:
        bootstrap_servers: Kafka broker address.
        schema_registry_url: Schema Registry URL.

    Returns:
        tuple: (Producer, AvroSerializer, StringSerializer)
    """
    schema_registry_conf = {"url": schema_registry_url}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    avro_serializer = AvroSerializer(
        schema_registry_client=schema_registry_client,
        schema_str=ORDER_SCHEMA_STR,
        to_dict=order_to_dict,
    )

    string_serializer = StringSerializer("utf_8")

    producer_conf = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "avro-order-producer",
    }

    producer = Producer(producer_conf)
    return producer, avro_serializer, string_serializer


def main():
    """Main entry point. Produces Avro-serialized order events to Kafka."""
    parser = argparse.ArgumentParser(
        description="Produce Avro-serialized e-commerce order events to Kafka."
    )
    parser.add_argument(
        "--num-messages",
        type=int,
        default=10,
        help="Number of order events to produce (default: 10).",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="orders-avro",
        help="Kafka topic to produce to (default: orders-avro).",
    )
    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default="localhost:9092",
        help="Kafka broker address (default: localhost:9092).",
    )
    parser.add_argument(
        "--schema-registry-url",
        type=str,
        default="http://localhost:8081",
        help="Schema Registry URL (default: http://localhost:8081).",
    )
    args = parser.parse_args()

    print(f"Creating Avro producer...")
    print(f"  Kafka: {args.bootstrap_servers}")
    print(f"  Schema Registry: {args.schema_registry_url}")
    print(f"  Topic: {args.topic}")
    print()

    producer, avro_serializer, string_serializer = create_avro_producer(
        bootstrap_servers=args.bootstrap_servers,
        schema_registry_url=args.schema_registry_url,
    )

    print(f"Producing {args.num_messages} order events...\n")

    for i in range(args.num_messages):
        order = generate_order()
        print(
            f"[{i + 1}/{args.num_messages}] Order {order['order_id'][:8]}... "
            f"| {order['product_name']} "
            f"| qty={order['quantity']} "
            f"| ${order['total_amount']:.2f} "
            f"| status={order['order_status']}"
        )

        producer.produce(
            topic=args.topic,
            key=string_serializer(
                order["order_id"],
                SerializationContext(args.topic, MessageField.KEY),
            ),
            value=avro_serializer(
                order,
                SerializationContext(args.topic, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )

        producer.poll(0)
        time.sleep(0.5)

    # Wait for all messages to be delivered
    remaining = producer.flush(timeout=10)
    print(f"\nDone. Messages remaining in queue: {remaining}")


if __name__ == "__main__":
    main()
