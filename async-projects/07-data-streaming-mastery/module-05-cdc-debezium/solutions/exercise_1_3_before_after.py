#!/usr/bin/env python3
"""
Solution 1.3: Before and After Comparison for the orders topic.

For each UPDATE event, prints a side-by-side diff of the before and after
states. For CREATE/SNAPSHOT events, prints a summary line.
"""

import json
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BOOTSTRAP = "localhost:9092"
CONSUMER_GROUP = "exercise-01-orders"
TOPIC = "ecommerce.ecommerce.orders"


def extract_payload(raw_value: bytes) -> Optional[dict]:
    """Parse Debezium JSON and return the payload."""
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


def diff_fields(before: dict, after: dict, exclude: set = None) -> list:
    """Return a list of (field, old_value, new_value) tuples for changed fields.

    Args:
        before: Row state before the change.
        after: Row state after the change.
        exclude: Field names to skip.

    Returns:
        List of tuples describing each changed field.
    """
    exclude = exclude or set()
    diffs = []
    for key in after:
        if key in exclude:
            continue
        old_val = before.get(key)
        new_val = after.get(key)
        if old_val != new_val:
            diffs.append((key, old_val, new_val))
    return diffs


def main() -> None:
    """Consume orders events and display before/after diffs for updates."""
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    consumer.subscribe([TOPIC])
    print(f"Subscribed to {TOPIC}. Reading events ...\n")

    empty_polls = 0
    max_empty = 15

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
                print("  [TOMBSTONE]")
                continue

            op = payload.get("op", "?")
            before = payload.get("before")
            after = payload.get("after")
            source = payload.get("source", {})
            snapshot = source.get("snapshot", "false")

            if op == "r" or (op == "c" and snapshot not in ("false", False)):
                # Snapshot event
                oid = after.get("id", "?")
                status = after.get("status", "?")
                amount = after.get("total_amount", 0)
                print(f"  [SNAPSHOT] Order #{oid}: {status}, total=${amount}")

            elif op == "c":
                # Live insert
                oid = after.get("id", "?")
                status = after.get("status", "?")
                amount = after.get("total_amount", 0)
                print(f"  [CREATE]   New order #{oid} created: "
                      f"{status}, total=${amount}")

            elif op == "u":
                # Update -- show diff
                oid = after.get("id", "?")
                changes = diff_fields(
                    before or {}, after or {}, exclude={"updated_at"}
                )
                if changes:
                    change_strs = [
                        f"{field} '{old}' -> '{new}'"
                        for field, old, new in changes
                    ]
                    print(f"  [UPDATE]   Order #{oid}: {', '.join(change_strs)}")
                else:
                    print(f"  [UPDATE]   Order #{oid}: (no visible field changes)")

            elif op == "d":
                oid = before.get("id", "?") if before else "?"
                print(f"  [DELETE]   Order #{oid} deleted")

            else:
                print(f"  [OP={op}]  (unknown operation)")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
