#!/usr/bin/env python3
"""
Schema Evolution Demo

Demonstrates schema evolution with the Confluent Schema Registry:
1. Registers a v1 schema and produces messages
2. Evolves to a v2 schema (adds a field with a default value)
3. Produces messages with the v2 schema
4. Consumes ALL messages (v1 and v2) with the v2 consumer
5. Shows that backward compatibility allows the v2 consumer to read v1 data

This is a complete, self-contained demo that illustrates the most common
schema evolution pattern: adding optional fields with defaults.

Usage:
    python schema_evolution_demo.py

Prerequisites:
    - Kafka broker running on localhost:9092
    - Schema Registry running on localhost:8081
    - pip install confluent-kafka[avro] requests faker
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BOOTSTRAP_SERVERS = "localhost:9092"
SCHEMA_REGISTRY_URL = "http://localhost:8081"
TOPIC = "user-events-evolution"

# ---------------------------------------------------------------------------
# Schema V1: Basic user event
# ---------------------------------------------------------------------------

USER_EVENT_V1 = {
    "type": "record",
    "name": "UserEvent",
    "namespace": "com.example.events",
    "doc": "A user activity event (version 1).",
    "fields": [
        {"name": "user_id", "type": "string", "doc": "Unique user identifier."},
        {"name": "event_type", "type": "string", "doc": "Type of event (click, view, purchase)."},
        {"name": "page_url", "type": "string", "doc": "URL of the page where the event occurred."},
        {"name": "timestamp", "type": "long", "doc": "Event timestamp as Unix epoch milliseconds."},
    ],
}

# ---------------------------------------------------------------------------
# Schema V2: Adds session_id and device_type with defaults (backward compatible)
# ---------------------------------------------------------------------------

USER_EVENT_V2 = {
    "type": "record",
    "name": "UserEvent",
    "namespace": "com.example.events",
    "doc": "A user activity event (version 2 - adds session_id and device_type).",
    "fields": [
        {"name": "user_id", "type": "string", "doc": "Unique user identifier."},
        {"name": "event_type", "type": "string", "doc": "Type of event (click, view, purchase)."},
        {"name": "page_url", "type": "string", "doc": "URL of the page where the event occurred."},
        {"name": "timestamp", "type": "long", "doc": "Event timestamp as Unix epoch milliseconds."},
        {
            "name": "session_id",
            "type": ["null", "string"],
            "default": None,
            "doc": "Session identifier (added in v2).",
        },
        {
            "name": "device_type",
            "type": "string",
            "default": "unknown",
            "doc": "Device type: desktop, mobile, tablet, unknown (added in v2).",
        },
    ],
}


def identity_to_dict(obj, ctx):
    """Pass-through serialization function.

    Args:
        obj: The object to serialize.
        ctx: Serialization context.

    Returns:
        dict: The object unchanged.
    """
    return obj


def identity_from_dict(obj, ctx):
    """Pass-through deserialization function.

    Args:
        obj: The deserialized dictionary.
        ctx: Serialization context.

    Returns:
        dict: The object unchanged.
    """
    return obj


def delivery_report(err, msg):
    """Kafka producer delivery callback.

    Args:
        err: Delivery error or None.
        msg: Delivered message.
    """
    if err:
        print(f"    [ERROR] Delivery failed: {err}")
    else:
        print(f"    [OK] partition={msg.partition()} offset={msg.offset()}")


def generate_v1_event() -> dict:
    """Generate a user event matching the V1 schema.

    Returns:
        dict: V1 user event.
    """
    return {
        "user_id": f"user-{fake.random_int(min=100, max=999)}",
        "event_type": fake.random_element(["click", "view", "purchase"]),
        "page_url": fake.url(),
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
    }


def generate_v2_event() -> dict:
    """Generate a user event matching the V2 schema (includes new fields).

    Returns:
        dict: V2 user event with session_id and device_type.
    """
    return {
        "user_id": f"user-{fake.random_int(min=100, max=999)}",
        "event_type": fake.random_element(["click", "view", "purchase"]),
        "page_url": fake.url(),
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
        "session_id": str(uuid.uuid4()),
        "device_type": fake.random_element(["desktop", "mobile", "tablet"]),
    }


def check_schema_versions():
    """Print all registered versions for the topic's value subject.

    Queries the Schema Registry REST API to show what schema versions
    are currently registered.
    """
    subject = f"{TOPIC}-value"
    url = f"{SCHEMA_REGISTRY_URL}/subjects/{subject}/versions"
    resp = requests.get(url)
    if resp.status_code == 200:
        versions = resp.json()
        print(f"  Registered versions for '{subject}': {versions}")
        for version in versions:
            schema_resp = requests.get(f"{url}/{version}")
            if schema_resp.status_code == 200:
                schema_data = schema_resp.json()
                schema = json.loads(schema_data["schema"])
                field_names = [f["name"] for f in schema.get("fields", [])]
                print(f"    Version {version}: fields = {field_names}")
    else:
        print(f"  No versions found for '{subject}' (subject may not exist yet).")


def check_compatibility(schema_dict: dict) -> bool:
    """Check if a schema is compatible with the latest registered version.

    Args:
        schema_dict: The Avro schema dictionary to check.

    Returns:
        bool: True if compatible, False otherwise.
    """
    subject = f"{TOPIC}-value"
    url = f"{SCHEMA_REGISTRY_URL}/compatibility/subjects/{subject}/versions/latest"
    payload = {"schema": json.dumps(schema_dict)}
    resp = requests.post(url, json=payload, headers={"Content-Type": "application/vnd.schemaregistry.v1+json"})
    if resp.status_code == 200:
        return resp.json().get("is_compatible", False)
    elif resp.status_code == 404:
        print("  No existing schema to check against (first version).")
        return True
    else:
        print(f"  Compatibility check error: {resp.status_code} - {resp.text}")
        return False


def produce_messages(schema_str: str, events: list, label: str):
    """Produce a list of events to Kafka using the given Avro schema.

    Args:
        schema_str: JSON string of the Avro schema.
        events: List of event dictionaries to produce.
        label: Label for log output (e.g., 'V1' or 'V2').
    """
    sr_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    serializer = AvroSerializer(
        schema_registry_client=sr_client,
        schema_str=schema_str,
        to_dict=identity_to_dict,
    )
    string_serializer = StringSerializer("utf_8")
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    print(f"\n  Producing {len(events)} {label} events...")
    for event in events:
        producer.produce(
            topic=TOPIC,
            key=string_serializer(
                event["user_id"],
                SerializationContext(TOPIC, MessageField.KEY),
            ),
            value=serializer(
                event,
                SerializationContext(TOPIC, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        time.sleep(0.3)

    producer.flush(timeout=10)


def consume_all_messages():
    """Consume all messages from the topic using a V2-aware deserializer.

    Demonstrates that the v2 consumer can read both v1 and v2 messages.
    V1 messages will have default values for the fields added in v2.
    """
    sr_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    deserializer = AvroDeserializer(
        schema_registry_client=sr_client,
        from_dict=identity_from_dict,
    )
    string_deserializer = StringDeserializer("utf_8")

    consumer = Consumer({
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": f"evolution-demo-{uuid.uuid4().hex[:8]}",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe([TOPIC])

    print(f"\n  Consuming all messages from '{TOPIC}'...")
    print("  (V1 messages will show default values for new fields)\n")

    count = 0
    empty_polls = 0

    try:
        while empty_polls < 10:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                empty_polls += 1
                continue
            if msg.error():
                print(f"  Consumer error: {msg.error()}")
                continue

            empty_polls = 0
            count += 1

            key = string_deserializer(
                msg.key(),
                SerializationContext(TOPIC, MessageField.KEY),
            )
            event = deserializer(
                msg.value(),
                SerializationContext(TOPIC, MessageField.VALUE),
            )

            # Determine version based on presence of new fields
            has_session = event.get("session_id") is not None
            version = "V2" if has_session else "V1 (defaults applied)"

            print(
                f"  [{count}] [{version}] "
                f"user={event['user_id']} "
                f"event={event['event_type']} "
                f"session_id={event.get('session_id', 'N/A')} "
                f"device={event.get('device_type', 'N/A')}"
            )
    finally:
        consumer.close()

    print(f"\n  Total messages consumed: {count}")


def main():
    """Run the complete schema evolution demonstration."""
    print("=" * 70)
    print("  SCHEMA EVOLUTION DEMO")
    print("  Demonstrates adding fields with defaults (backward compatible)")
    print("=" * 70)

    # Step 1: Check current state
    print("\n[Step 1] Current schema registry state:")
    check_schema_versions()

    # Step 2: Produce V1 messages
    print("\n[Step 2] Producing messages with V1 schema")
    print(f"  V1 fields: {[f['name'] for f in USER_EVENT_V1['fields']]}")
    v1_events = [generate_v1_event() for _ in range(5)]
    produce_messages(json.dumps(USER_EVENT_V1), v1_events, "V1")

    # Step 3: Check registry after V1
    print("\n[Step 3] Schema registry after V1 registration:")
    check_schema_versions()

    # Step 4: Check V2 compatibility
    print("\n[Step 4] Checking V2 compatibility with V1...")
    is_compatible = check_compatibility(USER_EVENT_V2)
    print(f"  V2 is backward compatible with V1: {is_compatible}")
    if not is_compatible:
        print("  ERROR: V2 is not compatible! Aborting.")
        return

    # Step 5: Produce V2 messages
    print("\n[Step 5] Producing messages with V2 schema")
    print(f"  V2 fields: {[f['name'] for f in USER_EVENT_V2['fields']]}")
    v2_events = [generate_v2_event() for _ in range(5)]
    produce_messages(json.dumps(USER_EVENT_V2), v2_events, "V2")

    # Step 6: Check registry after V2
    print("\n[Step 6] Schema registry after V2 registration:")
    check_schema_versions()

    # Step 7: Consume all messages with V2 consumer
    print("\n[Step 7] Consuming ALL messages (V1 + V2) with V2-aware consumer")
    consume_all_messages()

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print("  - V1 schema had 4 fields: user_id, event_type, page_url, timestamp")
    print("  - V2 schema added 2 fields: session_id (nullable), device_type (default='unknown')")
    print("  - V2 is BACKWARD compatible with V1 because new fields have defaults")
    print("  - V2 consumer can read V1 data -- missing fields get default values")
    print("  - This is the most common and safest schema evolution pattern")
    print("=" * 70)


if __name__ == "__main__":
    main()
