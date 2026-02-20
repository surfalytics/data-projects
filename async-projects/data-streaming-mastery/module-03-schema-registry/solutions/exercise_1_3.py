#!/usr/bin/env python3
"""
Solution: Exercise 1.3 - Clickstream Event Avro Schema

Defines a Clickstream Event schema with nested nullable records, maps,
enums, and comprehensive documentation. Registers and produces 5 samples.

Usage:
    python exercise_1_3.py

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
# Clickstream Event Avro Schema
# ---------------------------------------------------------------------------

CLICKSTREAM_SCHEMA = {
    "type": "record",
    "name": "ClickstreamEvent",
    "namespace": "com.analytics.clickstream",
    "doc": "Captures user interaction events on a website for behavioral analytics.",
    "fields": [
        {
            "name": "event_id",
            "type": "string",
            "doc": "Unique event identifier in UUID format."
        },
        {
            "name": "session_id",
            "type": "string",
            "doc": "Browser session identifier linking events in a single visit."
        },
        {
            "name": "user_id",
            "type": ["null", "string"],
            "default": None,
            "doc": "Authenticated user ID. Null for anonymous visitors."
        },
        {
            "name": "event_type",
            "type": {
                "type": "enum",
                "name": "EventType",
                "symbols": [
                    "PAGE_VIEW", "CLICK", "SCROLL",
                    "FORM_SUBMIT", "ADD_TO_CART", "PURCHASE"
                ]
            },
            "doc": "The type of user interaction event."
        },
        {
            "name": "page_url",
            "type": "string",
            "doc": "Full URL of the page where the event occurred."
        },
        {
            "name": "referrer_url",
            "type": ["null", "string"],
            "default": None,
            "doc": "URL of the referring page (null for direct traffic)."
        },
        {
            "name": "user_agent",
            "type": "string",
            "doc": "Browser user-agent string for device/browser identification."
        },
        {
            "name": "ip_address",
            "type": "string",
            "doc": "Client IP address (IPv4 or IPv6)."
        },
        {
            "name": "geo_location",
            "type": [
                "null",
                {
                    "type": "record",
                    "name": "GeoLocation",
                    "doc": "Geographic location derived from IP address.",
                    "fields": [
                        {"name": "latitude", "type": "double"},
                        {"name": "longitude", "type": "double"},
                        {"name": "country", "type": "string"},
                        {
                            "name": "city",
                            "type": ["null", "string"],
                            "default": None,
                            "doc": "City name (may be unavailable for some IPs)."
                        }
                    ]
                }
            ],
            "default": None,
            "doc": "Geo-location data (null if IP lookup fails)."
        },
        {
            "name": "custom_properties",
            "type": {"type": "map", "values": "string"},
            "doc": "Arbitrary key-value metadata for event-specific context."
        },
        {
            "name": "timestamp",
            "type": {"type": "long", "logicalType": "timestamp-millis"},
            "doc": "Event timestamp in milliseconds since Unix epoch."
        }
    ]
}

SCHEMA_STR = json.dumps(CLICKSTREAM_SCHEMA)

PAGES = [
    "/", "/products", "/products/123", "/cart",
    "/checkout", "/account", "/search?q=keyboard"
]


def generate_clickstream_event() -> dict:
    """Generate a fake clickstream event matching the Avro schema.

    Returns:
        dict: Clickstream event record.
    """
    is_authenticated = fake.boolean(chance_of_getting_true=60)
    has_referrer = fake.boolean(chance_of_getting_true=50)
    has_geo = fake.boolean(chance_of_getting_true=80)
    has_city = fake.boolean(chance_of_getting_true=70)

    event_type = fake.random_element([
        "PAGE_VIEW", "CLICK", "SCROLL",
        "FORM_SUBMIT", "ADD_TO_CART", "PURCHASE"
    ])

    # Build custom properties based on event type
    custom_props = {"browser": fake.random_element(["Chrome", "Firefox", "Safari", "Edge"])}
    if event_type == "CLICK":
        custom_props["element_id"] = fake.random_element(["btn-buy", "nav-home", "link-details"])
    elif event_type == "ADD_TO_CART":
        custom_props["product_id"] = f"PROD-{fake.random_int(min=100, max=999)}"
    elif event_type == "PURCHASE":
        custom_props["order_total"] = str(round(fake.pyfloat(min_value=10, max_value=500, right_digits=2), 2))

    return {
        "event_id": str(uuid.uuid4()),
        "session_id": str(uuid.uuid4()),
        "user_id": f"user-{fake.random_int(min=1000, max=9999)}" if is_authenticated else None,
        "event_type": event_type,
        "page_url": f"https://shop.example.com{fake.random_element(PAGES)}",
        "referrer_url": fake.url() if has_referrer else None,
        "user_agent": fake.user_agent(),
        "ip_address": fake.ipv4(),
        "geo_location": {
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude()),
            "country": fake.country_code(),
            "city": fake.city() if has_city else None,
        } if has_geo else None,
        "custom_properties": custom_props,
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
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
    """Register the Clickstream schema and produce 5 sample events."""
    topic = "clickstream-events"
    bootstrap_servers = "localhost:9092"
    schema_registry_url = "http://localhost:8081"

    print("Exercise 1.3: Clickstream Event Schema")
    print(f"Schema fields: {[f['name'] for f in CLICKSTREAM_SCHEMA['fields']]}")
    print()

    sr_client = SchemaRegistryClient({"url": schema_registry_url})
    avro_serializer = AvroSerializer(
        schema_registry_client=sr_client,
        schema_str=SCHEMA_STR,
        to_dict=to_dict,
    )
    string_serializer = StringSerializer("utf_8")
    producer = Producer({"bootstrap.servers": bootstrap_servers})

    print("Producing 5 clickstream events...\n")

    for i in range(5):
        event = generate_clickstream_event()
        user_label = event["user_id"] or "anonymous"
        geo_label = event["geo_location"]["country"] if event["geo_location"] else "unknown"
        print(
            f"[{i + 1}/5] {event['event_type']:15s} "
            f"| user={user_label:15s} "
            f"| page={event['page_url'].split('.com')[1]:25s} "
            f"| geo={geo_label}"
        )

        producer.produce(
            topic=topic,
            key=string_serializer(
                event["event_id"],
                SerializationContext(topic, MessageField.KEY),
            ),
            value=avro_serializer(
                event,
                SerializationContext(topic, MessageField.VALUE),
            ),
            on_delivery=delivery_report,
        )
        producer.poll(0)
        time.sleep(0.3)

    producer.flush(timeout=10)
    print("\nDone. Schema registered and 5 clickstream events produced.")


if __name__ == "__main__":
    main()
