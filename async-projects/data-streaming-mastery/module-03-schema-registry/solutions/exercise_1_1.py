#!/usr/bin/env python3
"""
Solution: Exercise 1.1 - Customer Profile Avro Schema

Defines a Customer Profile Avro schema with nullable fields, logical types,
enums, and arrays. Registers the schema and produces 5 sample messages.

Usage:
    python exercise_1_1.py

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
# Customer Profile Avro Schema
# ---------------------------------------------------------------------------

CUSTOMER_PROFILE_SCHEMA = {
    "type": "record",
    "name": "CustomerProfile",
    "namespace": "com.ecommerce.customers",
    "doc": "A customer profile capturing personal details, membership tier, and interests.",
    "fields": [
        {
            "name": "customer_id",
            "type": "string",
            "doc": "Unique customer identifier in UUID format."
        },
        {
            "name": "first_name",
            "type": "string",
            "doc": "Customer first name."
        },
        {
            "name": "last_name",
            "type": "string"
        },
        {
            "name": "email",
            "type": "string",
            "doc": "Customer email address."
        },
        {
            "name": "phone",
            "type": ["null", "string"],
            "default": None,
            "doc": "Customer phone number (optional)."
        },
        {
            "name": "date_of_birth",
            "type": ["null", {"type": "int", "logicalType": "date"}],
            "default": None,
            "doc": "Date of birth as days since Unix epoch (optional)."
        },
        {
            "name": "membership_tier",
            "type": {
                "type": "enum",
                "name": "MembershipTier",
                "symbols": ["BRONZE", "SILVER", "GOLD", "PLATINUM"]
            },
            "doc": "Customer membership tier."
        },
        {
            "name": "interests",
            "type": {
                "type": "array",
                "items": "string"
            },
            "doc": "List of customer interests (can be empty)."
        },
        {
            "name": "created_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
            "doc": "Profile creation timestamp in milliseconds since epoch."
        },
        {
            "name": "updated_at",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
            "doc": "Profile last updated timestamp in milliseconds since epoch."
        }
    ]
}

SCHEMA_STR = json.dumps(CUSTOMER_PROFILE_SCHEMA)

INTEREST_OPTIONS = [
    "electronics", "fashion", "sports", "cooking", "travel",
    "gaming", "music", "photography", "fitness", "reading"
]


def generate_customer() -> dict:
    """Generate a fake customer profile matching the Avro schema.

    Returns:
        dict: Customer profile event.
    """
    now_ms = int(datetime.utcnow().timestamp() * 1000)
    has_phone = fake.boolean(chance_of_getting_true=70)
    has_dob = fake.boolean(chance_of_getting_true=60)

    # date_of_birth as days since epoch
    dob_days = None
    if has_dob:
        dob = fake.date_of_birth(minimum_age=18, maximum_age=80)
        from datetime import date
        epoch = date(1970, 1, 1)
        dob_days = (dob - epoch).days

    return {
        "customer_id": str(uuid.uuid4()),
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.email(),
        "phone": fake.phone_number() if has_phone else None,
        "date_of_birth": dob_days,
        "membership_tier": fake.random_element(["BRONZE", "SILVER", "GOLD", "PLATINUM"]),
        "interests": fake.random_elements(
            elements=INTEREST_OPTIONS,
            length=fake.random_int(min=0, max=4),
            unique=True,
        ),
        "created_at": now_ms,
        "updated_at": now_ms,
    }


def to_dict(obj, ctx):
    """Pass-through serialization function.

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
    """Register the Customer Profile schema and produce 5 sample messages."""
    topic = "customer-profiles"
    bootstrap_servers = "localhost:9092"
    schema_registry_url = "http://localhost:8081"

    print("Exercise 1.1: Customer Profile Schema")
    print(f"Schema fields: {[f['name'] for f in CUSTOMER_PROFILE_SCHEMA['fields']]}")
    print()

    sr_client = SchemaRegistryClient({"url": schema_registry_url})
    avro_serializer = AvroSerializer(
        schema_registry_client=sr_client,
        schema_str=SCHEMA_STR,
        to_dict=to_dict,
    )
    string_serializer = StringSerializer("utf_8")
    producer = Producer({"bootstrap.servers": bootstrap_servers})

    print("Producing 5 customer profile events...\n")

    for i in range(5):
        customer = generate_customer()
        print(
            f"[{i + 1}/5] {customer['first_name']} {customer['last_name']} "
            f"| {customer['email']} "
            f"| tier={customer['membership_tier']} "
            f"| interests={customer['interests']}"
        )

        producer.produce(
            topic=topic,
            key=string_serializer(
                customer["customer_id"],
                SerializationContext(topic, MessageField.KEY),
            ),
            value=avro_serializer(
                customer,
                SerializationContext(topic, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        time.sleep(0.3)

    producer.flush(timeout=10)
    print("\nDone. Schema registered and 5 messages produced.")


if __name__ == "__main__":
    main()
