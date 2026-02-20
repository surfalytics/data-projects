#!/usr/bin/env python3
"""
Solution: Exercise 1.2 - Product Catalog Avro Schema

Defines a Product Catalog Avro schema with nested records, nullable fields,
enums, arrays, and default values. Registers the schema and produces 5 samples.

Usage:
    python exercise_1_2.py

Prerequisites:
    - Kafka broker running on localhost:9092
    - Schema Registry running on localhost:8081
"""

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

fake = Faker()

# ---------------------------------------------------------------------------
# Product Catalog Avro Schema
# ---------------------------------------------------------------------------

PRODUCT_SCHEMA = {
    "type": "record",
    "name": "Product",
    "namespace": "com.ecommerce.catalog",
    "doc": "A product in the e-commerce catalog with pricing, dimensions, and stock info.",
    "fields": [
        {
            "name": "product_id",
            "type": "string",
            "doc": "Unique product identifier."
        },
        {
            "name": "name",
            "type": "string",
            "doc": "Product display name."
        },
        {
            "name": "description",
            "type": ["null", "string"],
            "default": None,
            "doc": "Product description (optional)."
        },
        {
            "name": "category",
            "type": {
                "type": "enum",
                "name": "ProductCategory",
                "symbols": ["ELECTRONICS", "CLOTHING", "HOME", "FOOD", "SPORTS", "OTHER"]
            },
            "doc": "Product category."
        },
        {
            "name": "price_cents",
            "type": "int",
            "doc": "Price in cents to avoid floating-point precision issues."
        },
        {
            "name": "currency",
            "type": "string",
            "default": "USD",
            "doc": "ISO 4217 currency code."
        },
        {
            "name": "tags",
            "type": {"type": "array", "items": "string"},
            "doc": "Searchable tags for the product."
        },
        {
            "name": "dimensions",
            "type": [
                "null",
                {
                    "type": "record",
                    "name": "Dimensions",
                    "fields": [
                        {"name": "length_cm", "type": "double"},
                        {"name": "width_cm", "type": "double"},
                        {"name": "height_cm", "type": "double"}
                    ]
                }
            ],
            "default": None,
            "doc": "Product dimensions in centimeters (optional)."
        },
        {
            "name": "weight_grams",
            "type": ["null", "int"],
            "default": None,
            "doc": "Product weight in grams (optional)."
        },
        {
            "name": "in_stock",
            "type": "boolean",
            "default": True,
            "doc": "Whether the product is currently in stock."
        },
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
            "doc": "Timestamp when the product was added to the catalog."
        }
    ]
}

SCHEMA_STR = json.dumps(PRODUCT_SCHEMA)

SAMPLE_PRODUCTS = [
    ("Wireless Bluetooth Speaker", "ELECTRONICS", 4999, ["audio", "bluetooth", "portable"]),
    ("Organic Cotton T-Shirt", "CLOTHING", 2499, ["organic", "cotton", "casual"]),
    ("Stainless Steel Water Bottle", "HOME", 1899, ["kitchen", "eco-friendly"]),
    ("Protein Energy Bars (12-pack)", "FOOD", 2999, ["protein", "snack", "healthy"]),
    ("Yoga Mat Premium", "SPORTS", 3999, ["yoga", "fitness", "non-slip"]),
]


def generate_product(name: str, category: str, price_cents: int, tags: list) -> dict:
    """Generate a product record matching the Avro schema.

    Args:
        name: Product name.
        category: Product category enum value.
        price_cents: Price in cents.
        tags: List of tag strings.

    Returns:
        dict: Product record.
    """
    has_dimensions = fake.boolean(chance_of_getting_true=60)
    has_weight = fake.boolean(chance_of_getting_true=70)

    return {
        "product_id": f"PROD-{uuid.uuid4().hex[:8].upper()}",
        "name": name,
        "description": fake.sentence(nb_words=10) if fake.boolean(chance_of_getting_true=80) else None,
        "category": category,
        "price_cents": price_cents,
        "currency": "USD",
        "tags": tags,
        "dimensions": {
            "length_cm": round(fake.pyfloat(min_value=5, max_value=100, right_digits=1), 1),
            "width_cm": round(fake.pyfloat(min_value=5, max_value=80, right_digits=1), 1),
            "height_cm": round(fake.pyfloat(min_value=2, max_value=60, right_digits=1), 1),
        } if has_dimensions else None,
        "weight_grams": fake.random_int(min=50, max=5000) if has_weight else None,
        "in_stock": fake.boolean(chance_of_getting_true=85),
        "created_at": int(datetime.utcnow().timestamp() * 1000),
    }


def to_dict(obj, ctx):
    """Pass-through serialization.

    Args:
        obj: Object to serialize.
        ctx: Serialization context.

    Returns:
        dict: The object unchanged.
    """
    return obj


def delivery_report(err, msg):
    """Delivery callback.

    Args:
        err: Error or None.
        msg: Delivered message.
    """
    if err:
        print(f"  [ERROR] {err}")
    else:
        print(f"  [OK] partition={msg.partition()} offset={msg.offset()}")


def main():
    """Register the Product schema and produce 5 sample products."""
    topic = "product-catalog"
    bootstrap_servers = "localhost:9092"
    schema_registry_url = "http://localhost:8081"

    print("Exercise 1.2: Product Catalog Schema")
    print(f"Schema fields: {[f['name'] for f in PRODUCT_SCHEMA['fields']]}")
    print()

    sr_client = SchemaRegistryClient({"url": schema_registry_url})
    avro_serializer = AvroSerializer(
        schema_registry_client=sr_client,
        schema_str=SCHEMA_STR,
        to_dict=to_dict,
    )
    string_serializer = StringSerializer("utf_8")
    producer = Producer({"bootstrap.servers": bootstrap_servers})

    print("Producing 5 product records...\n")

    for i, (name, category, price, tags) in enumerate(SAMPLE_PRODUCTS):
        product = generate_product(name, category, price, tags)
        print(
            f"[{i + 1}/5] {product['product_id']} | {product['name']} "
            f"| ${product['price_cents'] / 100:.2f} "
            f"| stock={product['in_stock']} "
            f"| dims={'yes' if product['dimensions'] else 'no'}"
        )

        producer.produce(
            topic=topic,
            key=string_serializer(
                product["product_id"],
                SerializationContext(topic, MessageField.KEY),
            ),
            value=avro_serializer(
                product,
                SerializationContext(topic, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        time.sleep(0.3)

    producer.flush(timeout=10)
    print("\nDone. Schema registered and 5 products produced.")


if __name__ == "__main__":
    main()
