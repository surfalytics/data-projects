#!/usr/bin/env python3
"""
Solution: Exercise 2.1 - Backward-Compatible Schema Evolution

Demonstrates adding four new fields to a UserProfile schema while maintaining
backward compatibility. Produces V1 and V2 messages, then consumes all with
a V2-aware consumer.

Usage:
    python exercise_2_1.py

Prerequisites:
    - Kafka broker running on localhost:9092
    - Schema Registry running on localhost:8081
"""

import json
import time
import uuid
from datetime import datetime

import requests
from confluent_kafka import Consumer, Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer, AvroSerializer
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringDeserializer,
    StringSerializer,
)
from faker import Faker

fake = Faker()

BOOTSTRAP_SERVERS = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8081"
TOPIC = "user-profiles-exercise"

# ---------------------------------------------------------------------------
# V1 Schema: Basic user profile
# ---------------------------------------------------------------------------

USER_PROFILE_V1 = {
    "type": "record",
    "name": "UserProfile",
    "namespace": "com.example.users",
    "fields": [
        {"name": "user_id", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "signup_date", "type": "long"},
    ],
}

# ---------------------------------------------------------------------------
# V2 Schema: Adds phone_number, account_status, last_login, preferences
#
# All new fields are backward compatible because:
# - phone_number: nullable with null default -> V1 data gets null
# - account_status: enum with default "ACTIVE" -> V1 data gets "ACTIVE"
# - last_login: nullable with null default -> V1 data gets null
# - preferences: nullable map with null default -> V1 data gets null
# ---------------------------------------------------------------------------

USER_PROFILE_V2 = {
    "type": "record",
    "name": "UserProfile",
    "namespace": "com.example.users",
    "fields": [
        {"name": "user_id", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "signup_date", "type": "long"},
        {
            "name": "phone_number",
            "type": ["null", "string"],
            "default": None,
            "doc": "Added in V2. Nullable -- V1 data defaults to null."
        },
        {
            "name": "account_status",
            "type": {
                "type": "enum",
                "name": "AccountStatus",
                "symbols": ["ACTIVE", "SUSPENDED", "DELETED"]
            },
            "default": "ACTIVE",
            "doc": "Added in V2. V1 data defaults to ACTIVE."
        },
        {
            "name": "last_login",
            "type": ["null", "long"],
            "default": None,
            "doc": "Added in V2. Nullable timestamp -- V1 data defaults to null."
        },
        {
            "name": "preferences",
            "type": ["null", {"type": "map", "values": "string"}],
            "default": None,
            "doc": "Added in V2. Nullable map -- V1 data defaults to null."
        },
    ],
}


def identity(obj, ctx):
    """Pass-through serialization/deserialization.

    Args:
        obj: The object.
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
        print(f"    [ERROR] {err}")
    else:
        print(f"    [OK] partition={msg.partition()} offset={msg.offset()}")


def check_compatibility(schema_dict: dict, subject: str) -> bool:
    """Check schema compatibility against the latest version.

    Args:
        schema_dict: The schema to check.
        subject: The subject name.

    Returns:
        bool: True if compatible.
    """
    url = f"{SCHEMA_REGISTRY_URL}/compatibility/subjects/{subject}/versions/latest"
    payload = {"schema": json.dumps(schema_dict)}
    resp = requests.post(
        url, json=payload,
        headers={"Content-Type": "application/vnd.schemaregistry.v1+json"},
    )
    if resp.status_code == 200:
        return resp.json().get("is_compatible", False)
    elif resp.status_code == 404:
        return True  # No existing schema
    return False


def produce_messages(schema_str: str, events: list, label: str):
    """Produce events using the given schema.

    Args:
        schema_str: Avro schema JSON string.
        events: List of event dicts.
        label: Label for logging (V1 or V2).
    """
    sr_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    serializer = AvroSerializer(
        schema_registry_client=sr_client,
        schema_str=schema_str,
        to_dict=identity,
    )
    string_serializer = StringSerializer("utf_8")
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    for event in events:
        print(f"    [{label}] user={event['user_id']} email={event['email']}")
        producer.produce(
            topic=TOPIC,
            key=string_serializer(event["user_id"], SerializationContext(TOPIC, MessageField.KEY)),
            value=serializer(event, SerializationContext(TOPIC, MessageField.VALUE)),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        time.sleep(0.2)

    producer.flush(timeout=10)


def main():
    """Run the backward-compatible evolution exercise."""
    print("=" * 60)
    print("  Exercise 2.1: Backward-Compatible Schema Evolution")
    print("=" * 60)

    # Step 1: Produce V1 messages
    print("\n[1] Producing 3 messages with V1 schema...")
    v1_events = [
        {
            "user_id": f"user-{fake.random_int(100, 999)}",
            "email": fake.email(),
            "name": fake.name(),
            "signup_date": int(datetime.utcnow().timestamp() * 1000),
        }
        for _ in range(3)
    ]
    produce_messages(json.dumps(USER_PROFILE_V1), v1_events, "V1")

    # Step 2: Check V2 compatibility
    subject = f"{TOPIC}-value"
    print(f"\n[2] Checking V2 compatibility with V1 (subject: {subject})...")
    is_compat = check_compatibility(USER_PROFILE_V2, subject)
    print(f"    V2 backward compatible: {is_compat}")

    if not is_compat:
        print("    ERROR: V2 is not compatible. Aborting.")
        return

    # Step 3: Produce V2 messages
    print("\n[3] Producing 3 messages with V2 schema...")
    v2_events = [
        {
            "user_id": f"user-{fake.random_int(100, 999)}",
            "email": fake.email(),
            "name": fake.name(),
            "signup_date": int(datetime.utcnow().timestamp() * 1000),
            "phone_number": fake.phone_number(),
            "account_status": fake.random_element(["ACTIVE", "SUSPENDED"]),
            "last_login": int(datetime.utcnow().timestamp() * 1000),
            "preferences": {"theme": "dark", "language": "en"},
        }
        for _ in range(3)
    ]
    produce_messages(json.dumps(USER_PROFILE_V2), v2_events, "V2")

    # Step 4: Consume all messages with V2 consumer
    print(f"\n[4] Consuming all 6 messages with V2-aware consumer...")
    sr_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    deserializer = AvroDeserializer(
        schema_registry_client=sr_client,
        from_dict=identity,
    )
    string_deserializer = StringDeserializer("utf_8")

    consumer = Consumer({
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": f"ex21-{uuid.uuid4().hex[:8]}",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([TOPIC])

    count = 0
    empty = 0
    try:
        while empty < 10:
            msg = consumer.poll(1.0)
            if msg is None:
                empty += 1
                continue
            if msg.error():
                continue
            empty = 0
            count += 1

            event = deserializer(msg.value(), SerializationContext(TOPIC, MessageField.VALUE))
            has_v2 = event.get("phone_number") is not None or event.get("account_status") is not None

            print(
                f"    [{count}] {'V2' if has_v2 else 'V1->defaults'} "
                f"| user={event['user_id']} "
                f"| phone={event.get('phone_number', 'N/A')} "
                f"| status={event.get('account_status', 'N/A')} "
                f"| prefs={event.get('preferences', 'N/A')}"
            )
    finally:
        consumer.close()

    # Step 5: Explanation
    print(f"\n    Total consumed: {count}")
    print("\n[5] Why each V2 field is backward compatible:")
    print("    - phone_number: union ['null','string'] with default null")
    print("      -> When reading V1 data, consumer gets null (no phone)")
    print("    - account_status: enum with default 'ACTIVE'")
    print("      -> When reading V1 data, consumer gets ACTIVE")
    print("    - last_login: union ['null','long'] with default null")
    print("      -> When reading V1 data, consumer gets null (never logged in)")
    print("    - preferences: union ['null',map] with default null")
    print("      -> When reading V1 data, consumer gets null (no prefs)")
    print()


if __name__ == "__main__":
    main()
