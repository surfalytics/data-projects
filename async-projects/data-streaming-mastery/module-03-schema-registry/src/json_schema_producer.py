#!/usr/bin/env python3
"""
JSON Schema Producer

Produces messages to Kafka using JSON Schema serialization via the Confluent
Schema Registry. This provides a comparison point against Avro serialization
from avro_producer.py.

JSON Schema is human-readable and easy to debug, but produces larger messages
because field names are included in every record.

Usage:
    python json_schema_producer.py [--num-messages 10] [--topic orders-json]

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
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringSerializer,
)
from faker import Faker

fake = Faker()

# ---------------------------------------------------------------------------
# JSON Schema definition
# ---------------------------------------------------------------------------

ORDER_JSON_SCHEMA_STR = json.dumps({
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Order",
    "description": "An e-commerce order event using JSON Schema serialization.",
    "type": "object",
    "properties": {
        "order_id": {
            "type": "string",
            "description": "Unique order identifier (UUID)."
        },
        "customer_id": {
            "type": "string",
            "description": "Customer identifier."
        },
        "customer_email": {
            "type": "string",
            "format": "email",
            "description": "Customer email address."
        },
        "product_name": {
            "type": "string",
            "description": "Name of the ordered product."
        },
        "quantity": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of units ordered."
        },
        "unit_price": {
            "type": "number",
            "minimum": 0,
            "description": "Price per unit in USD."
        },
        "total_amount": {
            "type": "number",
            "minimum": 0,
            "description": "Total order amount in USD."
        },
        "order_status": {
            "type": "string",
            "enum": ["PENDING", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"],
            "description": "Current order status."
        },
        "shipping_address": {
            "type": "object",
            "properties": {
                "street": {"type": "string"},
                "city": {"type": "string"},
                "state": {"type": "string"},
                "zip_code": {"type": "string"},
                "country": {"type": "string", "default": "US"}
            },
            "required": ["street", "city", "state", "zip_code"],
            "description": "Shipping address."
        },
        "created_at": {
            "type": "string",
            "format": "date-time",
            "description": "ISO 8601 order creation timestamp."
        },
        "notes": {
            "type": ["string", "null"],
            "description": "Optional order notes."
        }
    },
    "required": [
        "order_id", "customer_id", "customer_email",
        "product_name", "quantity", "unit_price",
        "total_amount", "order_status", "shipping_address", "created_at"
    ]
})

# ---------------------------------------------------------------------------
# Product catalog
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


def generate_order() -> dict:
    """Generate a fake e-commerce order event matching the JSON Schema.

    Returns:
        dict: Order event payload.
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
        "created_at": datetime.utcnow().isoformat() + "Z",
        "notes": fake.sentence() if fake.boolean(chance_of_getting_true=30) else None,
    }


def order_to_dict(order: dict, ctx: SerializationContext) -> dict:
    """Convert an order dictionary for JSON Schema serialization.

    Args:
        order: The order event dictionary.
        ctx: Serialization context.

    Returns:
        dict: The order dictionary (already in correct format).
    """
    return order


def delivery_report(err, msg):
    """Callback for message delivery confirmation.

    Args:
        err: Delivery error (None if successful).
        msg: The delivered message.
    """
    if err is not None:
        print(f"  [ERROR] Delivery failed: {err}")
    else:
        size = len(msg.value()) if msg.value() else 0
        print(
            f"  [OK] Delivered to {msg.topic()} "
            f"[partition={msg.partition()}] "
            f"@ offset {msg.offset()} "
            f"(size={size} bytes)"
        )


def main():
    """Main entry point. Produces JSON Schema-serialized order events."""
    parser = argparse.ArgumentParser(
        description="Produce JSON Schema-serialized order events to Kafka."
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
        default="orders-json",
        help="Kafka topic to produce to (default: orders-json).",
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

    print("JSON Schema Producer")
    print(f"  Kafka: {args.bootstrap_servers}")
    print(f"  Schema Registry: {args.schema_registry_url}")
    print(f"  Topic: {args.topic}")
    print()

    # Set up Schema Registry and serializer
    sr_client = SchemaRegistryClient({"url": args.schema_registry_url})

    json_serializer = JSONSerializer(
        schema_str=ORDER_JSON_SCHEMA_STR,
        schema_registry_client=sr_client,
        to_dict=order_to_dict,
    )

    string_serializer = StringSerializer("utf_8")

    producer = Producer({
        "bootstrap.servers": args.bootstrap_servers,
        "client.id": "json-schema-order-producer",
    })

    print(f"Producing {args.num_messages} order events with JSON Schema...\n")

    for i in range(args.num_messages):
        order = generate_order()
        print(
            f"[{i + 1}/{args.num_messages}] Order {order['order_id'][:8]}... "
            f"| {order['product_name']} "
            f"| qty={order['quantity']} "
            f"| ${order['total_amount']:.2f}"
        )

        producer.produce(
            topic=args.topic,
            key=string_serializer(
                order["order_id"],
                SerializationContext(args.topic, MessageField.KEY),
            ),
            value=json_serializer(
                order,
                SerializationContext(args.topic, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )

        producer.poll(0)
        time.sleep(0.5)

    remaining = producer.flush(timeout=10)
    print(f"\nDone. Messages remaining in queue: {remaining}")
    print(
        "\nNote: Compare the message sizes here (JSON Schema) with those from "
        "avro_producer.py (Avro). JSON Schema messages are typically larger because "
        "field names are included in every record."
    )


if __name__ == "__main__":
    main()
