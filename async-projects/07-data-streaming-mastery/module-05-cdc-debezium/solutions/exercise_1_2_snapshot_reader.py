#!/usr/bin/env python3
"""
Solution 1.2: Read and Parse Snapshot Events from the customers topic.

Reads all events from ecommerce.ecommerce.customers, parses the Debezium
envelope, and prints each customer with a label indicating whether the event
is from the initial snapshot or a live change.
"""

import json
import sys
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BOOTSTRAP = "localhost:9092"
CONSUMER_GROUP = "exercise-01"
TOPIC = "ecommerce.ecommerce.customers"


def extract_payload(raw_value: bytes) -> Optional[dict]:
    """Parse the Debezium JSON message and return the payload.

    Args:
        raw_value: Raw bytes from the Kafka message value.

    Returns:
        The payload dict, or None for tombstones.
    """
    if raw_value is None:
        return None
    try:
        message = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    if "payload" in message:
        return message["payload"]
    if "op" in message:
        return message
    return None


def main() -> None:
    """Consume and display customer snapshot events."""
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    consumer.subscribe([TOPIC])
    print(f"Subscribed to {TOPIC}. Reading events ...\n")

    empty_polls = 0
    max_empty = 10  # Stop after 10 seconds of no messages.

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                empty_polls += 1
                if empty_polls >= max_empty:
                    print(f"\nNo messages for {max_empty}s. Done.")
                    break
                continue

            empty_polls = 0

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            payload = extract_payload(msg.value())

            if payload is None:
                # Tombstone
                print("  [TOMBSTONE] (null value)")
                continue

            op = payload.get("op", "?")
            source = payload.get("source", {})
            snapshot = source.get("snapshot", "false")
            after = payload.get("after")
            before = payload.get("before")

            # Determine event label.
            if snapshot not in ("false", False):
                label = "SNAPSHOT"
            elif op == "c":
                label = "CREATE"
            elif op == "u":
                label = "UPDATE"
            elif op == "d":
                label = "DELETE"
            else:
                label = f"OP={op}"

            # Extract customer details.
            row = after if after else before
            if row:
                cid = row.get("id", "?")
                first = row.get("first_name", "?")
                last = row.get("last_name", "?")
                email = row.get("email", "?")
                print(f"  [{label}] Customer #{cid}: {first} {last} ({email})")
            else:
                print(f"  [{label}] (no row data)")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
