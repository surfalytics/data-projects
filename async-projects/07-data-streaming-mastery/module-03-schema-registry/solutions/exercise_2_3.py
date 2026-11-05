#!/usr/bin/env python3
"""
Solution: Exercise 2.3 - Multi-Version Consumer

Demonstrates registering three schema versions (V1, V2, V3) for inventory
updates, producing messages with each version, and consuming all messages
with a single consumer that handles all versions.

Usage:
    python exercise_2_3.py

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
TOPIC = "inventory-updates-exercise"

HEADERS = {"Content-Type": "application/vnd.schemaregistry.v1+json"}

# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------

INVENTORY_V1 = {
    "type": "record",
    "name": "InventoryUpdate",
    "namespace": "com.warehouse.inventory",
    "fields": [
        {"name": "product_id", "type": "string"},
        {"name": "warehouse_id", "type": "string"},
        {"name": "quantity", "type": "int"},
        {"name": "timestamp", "type": "long"},
    ],
}

INVENTORY_V2 = {
    "type": "record",
    "name": "InventoryUpdate",
    "namespace": "com.warehouse.inventory",
    "fields": [
        {"name": "product_id", "type": "string"},
        {"name": "warehouse_id", "type": "string"},
        {"name": "quantity", "type": "int"},
        {"name": "timestamp", "type": "long"},
        {"name": "update_type", "type": "string", "default": "ADJUSTMENT"},
        {"name": "location_aisle", "type": ["null", "string"], "default": None},
    ],
}

INVENTORY_V3 = {
    "type": "record",
    "name": "InventoryUpdate",
    "namespace": "com.warehouse.inventory",
    "fields": [
        {"name": "product_id", "type": "string"},
        {"name": "warehouse_id", "type": "string"},
        {"name": "quantity", "type": "int"},
        {"name": "timestamp", "type": "long"},
        {"name": "update_type", "type": "string", "default": "ADJUSTMENT"},
        {"name": "location_aisle", "type": ["null", "string"], "default": None},
        {"name": "batch_id", "type": ["null", "string"], "default": None},
        {"name": "expiry_date", "type": ["null", "long"], "default": None},
    ],
}

SCHEMAS = [
    ("V1", INVENTORY_V1),
    ("V2", INVENTORY_V2),
    ("V3", INVENTORY_V3),
]


def identity(obj, ctx):
    """Pass-through function for serialization/deserialization.

    Args:
        obj: The object.
        ctx: Serialization context.

    Returns:
        The object unchanged.
    """
    return obj


def delivery_report(err, msg):
    """Delivery callback.

    Args:
        err: Error or None.
        msg: Delivered message.
    """
    if err:
        print(f"      [ERROR] {err}")
    else:
        print(f"      [OK] partition={msg.partition()} offset={msg.offset()}")


def check_compatibility(schema_dict: dict, subject: str, mode: str = "BACKWARD_TRANSITIVE") -> bool:
    """Check schema compatibility.

    Args:
        schema_dict: Schema to check.
        subject: Subject name.
        mode: Compatibility mode.

    Returns:
        bool: True if compatible.
    """
    # Set compatibility mode
    requests.put(
        f"{SCHEMA_REGISTRY_URL}/config/{subject}",
        json={"compatibility": mode},
        headers=HEADERS,
    )

    url = f"{SCHEMA_REGISTRY_URL}/compatibility/subjects/{subject}/versions/latest"
    payload = {"schema": json.dumps(schema_dict)}
    resp = requests.post(url, json=payload, headers=HEADERS)
    if resp.status_code == 200:
        return resp.json().get("is_compatible", False)
    elif resp.status_code == 404:
        return True
    return False


def generate_v1_event() -> dict:
    """Generate a V1 inventory update.

    Returns:
        dict: V1 inventory event.
    """
    return {
        "product_id": f"PROD-{fake.random_int(100, 999)}",
        "warehouse_id": f"WH-{fake.random_element(['EAST', 'WEST', 'CENTRAL'])}",
        "quantity": fake.random_int(min=-50, max=200),
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
    }


def generate_v2_event() -> dict:
    """Generate a V2 inventory update.

    Returns:
        dict: V2 inventory event with update_type and location.
    """
    event = generate_v1_event()
    event["update_type"] = fake.random_element(["RECEIVING", "SHIPPING", "ADJUSTMENT", "RETURN"])
    event["location_aisle"] = f"Aisle-{fake.random_element(['A', 'B', 'C'])}{fake.random_int(1, 20)}"
    return event


def generate_v3_event() -> dict:
    """Generate a V3 inventory update.

    Returns:
        dict: V3 inventory event with batch tracking.
    """
    event = generate_v2_event()
    event["batch_id"] = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
    event["expiry_date"] = int(
        (datetime.utcnow().timestamp() + fake.random_int(30, 365) * 86400) * 1000
    )
    return event


def produce_events(schema_str: str, events: list, label: str):
    """Produce events using the given schema.

    Args:
        schema_str: Avro schema JSON string.
        events: List of event dicts.
        label: Schema version label.
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
        print(
            f"      [{label}] product={event['product_id']} "
            f"warehouse={event['warehouse_id']} qty={event['quantity']}"
        )
        producer.produce(
            topic=TOPIC,
            key=string_serializer(
                event["product_id"],
                SerializationContext(TOPIC, MessageField.KEY),
            ),
            value=serializer(
                event,
                SerializationContext(TOPIC, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        time.sleep(0.2)

    producer.flush(timeout=10)


def determine_version(event: dict) -> str:
    """Determine which schema version produced the event based on field presence.

    Args:
        event: Deserialized event dictionary.

    Returns:
        str: Version label (V1, V2, or V3).
    """
    if event.get("batch_id") is not None:
        return "V3"
    elif event.get("update_type") is not None and event.get("update_type") != "ADJUSTMENT":
        return "V2"
    elif event.get("location_aisle") is not None:
        return "V2"
    else:
        return "V1 (or V2/V3 with defaults)"


def main():
    """Run the multi-version consumer exercise."""
    print("=" * 70)
    print("  Exercise 2.3: Multi-Version Consumer")
    print("=" * 70)

    subject = f"{TOPIC}-value"

    # Step 1: Register and produce for each version
    generators = [generate_v1_event, generate_v2_event, generate_v3_event]

    for i, (label, schema) in enumerate(SCHEMAS):
        print(f"\n[{i + 1}] Registering {label} and producing 3 messages...")
        field_names = [f["name"] for f in schema["fields"]]
        print(f"    Fields: {field_names}")

        if i > 0:
            is_compat = check_compatibility(schema, subject, "BACKWARD_TRANSITIVE")
            print(f"    BACKWARD_TRANSITIVE compatible: {is_compat}")
            if not is_compat:
                print(f"    ERROR: {label} is not compatible! Aborting.")
                return

        events = [generators[i]() for _ in range(3)]
        produce_events(json.dumps(schema), events, label)

    # Step 2: Consume all 9 messages
    print(f"\n[4] Consuming all 9 messages with a single consumer...")
    sr_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    deserializer = AvroDeserializer(
        schema_registry_client=sr_client,
        from_dict=identity,
    )
    string_deserializer = StringDeserializer("utf_8")

    consumer = Consumer({
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": f"ex23-{uuid.uuid4().hex[:8]}",
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

            event = deserializer(
                msg.value(),
                SerializationContext(TOPIC, MessageField.VALUE),
            )
            version = determine_version(event)

            print(
                f"    [{count}] [{version:25s}] "
                f"product={event['product_id']} "
                f"qty={event['quantity']:4d} "
                f"type={str(event.get('update_type', '-')):12s} "
                f"aisle={str(event.get('location_aisle', '-')):10s} "
                f"batch={str(event.get('batch_id', '-'))}"
            )
    finally:
        consumer.close()

    print(f"\n    Total messages consumed: {count}")

    # Step 3: Verify transitive compatibility
    print("\n[5] BACKWARD_TRANSITIVE compatibility verification:")
    print("    V1 -> V2: V2 adds update_type (default='ADJUSTMENT') and location_aisle (default=null)")
    print("              New consumer reading V1 data gets defaults. Compatible.")
    print("    V2 -> V3: V3 adds batch_id (default=null) and expiry_date (default=null)")
    print("              New consumer reading V2 data gets defaults. Compatible.")
    print("    V1 -> V3: V3 consumer reading V1 data gets defaults for ALL 4 new fields.")
    print("              This is BACKWARD_TRANSITIVE -- V3 can read ALL previous versions.")

    # Step 4: Could V1 consumer read V3 data?
    print("\n[6] Could a V1 consumer read V3 data?")
    print("    NO, not in general. A V1 consumer:")
    print("    - Would encounter extra fields (update_type, location_aisle, batch_id, expiry_date)")
    print("    - In Avro, the V1 reader schema would skip those extra fields")
    print("    - However, this only works with Avro's schema resolution, not raw deserialization")
    print("    - With Schema Registry, the V1 consumer uses the WRITER schema (V3) to read")
    print("      the data and the READER schema (V1) to project fields -- so it CAN read V3")
    print("      data, but only gets the 4 original fields. This is FORWARD compatibility.")
    print("    - IMPORTANT: This works because we never REMOVED fields from V1.")
    print()


if __name__ == "__main__":
    main()
