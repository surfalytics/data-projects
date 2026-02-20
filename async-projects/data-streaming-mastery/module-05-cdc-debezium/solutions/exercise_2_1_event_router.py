#!/usr/bin/env python3
"""
Solution 2.1: Filtered Event Router.

Reads from all Debezium topics and routes events to specific handlers based
on operation type and table name. Tracks routing counts.
"""

import json
from collections import defaultdict
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

KAFKA_BOOTSTRAP = "localhost:9092"
CONSUMER_GROUP = "exercise-02-router"
TOPIC_PREFIX = "ecommerce.ecommerce."
TOPICS = [
    f"{TOPIC_PREFIX}customers",
    f"{TOPIC_PREFIX}addresses",
    f"{TOPIC_PREFIX}products",
    f"{TOPIC_PREFIX}orders",
    f"{TOPIC_PREFIX}order_items",
    f"{TOPIC_PREFIX}inventory",
]


def extract_payload(raw_value: bytes) -> Optional[dict]:
    """Parse Debezium JSON and return the payload."""
    if raw_value is None:
        return None
    try:
        msg = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if "payload" in msg:
        return msg["payload"]
    if "op" in msg:
        return msg
    return None


def extract_table(topic: str) -> str:
    """Get the table name from a Debezium topic."""
    return topic.split(".")[-1]


class EventRouter:
    """Routes CDC events to handlers and tracks counts."""

    def __init__(self) -> None:
        """Initialize routing counters."""
        self.counts = defaultdict(int)

    def route(self, table: str, payload: dict) -> None:
        """Route an event to the appropriate handler.

        Args:
            table: Source table name.
            payload: Debezium event payload.
        """
        op = payload.get("op", "?")
        before = payload.get("before")
        after = payload.get("after")
        row = after or before or {}
        row_id = row.get("id", "?")

        # Route: INSERT on customers -> new customer alert.
        if op == "c" and table == "customers":
            name = f"{row.get('first_name', '')} {row.get('last_name', '')}"
            print(f"  ** NEW CUSTOMER ALERT: {name} (#{row_id}) **")
            self.counts["new_customer_alert"] += 1
            return

        # Route: UPDATE on orders where status -> shipped.
        if op == "u" and table == "orders":
            new_status = (after or {}).get("status")
            if new_status == "shipped":
                print(f"  ** SHIPPING NOTIFICATION: Order #{row_id} **")
                self.counts["shipping_notification"] += 1
                return

        # Route: DELETE on any table -> deletion warning.
        if op == "d":
            print(f"  ** DELETION WARNING: {table} #{row_id} **")
            self.counts["deletion_warning"] += 1
            return

        # Default: summary line.
        op_label = {"c": "CREATE", "u": "UPDATE", "r": "SNAPSHOT"}.get(op, op)
        print(f"  {op_label} {table} #{row_id}")
        self.counts["default"] += 1

    def handle_tombstone(self, table: str, key_data: dict) -> None:
        """Handle a tombstone event.

        Args:
            table: Source table name.
            key_data: Parsed key data (primary key).
        """
        print(f"  [TOMBSTONE] {table} key={key_data}")
        self.counts["tombstone"] += 1

    def print_summary(self) -> None:
        """Print routing statistics."""
        print("\n" + "=" * 50)
        print("ROUTING SUMMARY")
        print("=" * 50)
        total = sum(self.counts.values())
        for handler, count in sorted(self.counts.items()):
            print(f"  {handler:<25} {count:>5}")
        print(f"  {'TOTAL':<25} {total:>5}")
        print("=" * 50)


def main() -> None:
    """Main consumer loop with event routing."""
    router = EventRouter()

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe(TOPICS)

    print(f"Subscribed to {len(TOPICS)} topics. Routing events ...\n")

    empty_polls = 0
    max_empty = 20

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                empty_polls += 1
                if empty_polls >= max_empty:
                    break
                continue

            empty_polls = 0

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            table = extract_table(msg.topic())
            payload = extract_payload(msg.value())

            if payload is None:
                key_data = {}
                if msg.key():
                    try:
                        kd = json.loads(msg.key().decode("utf-8"))
                        key_data = kd.get("payload", kd)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass
                router.handle_tombstone(table, key_data)
                continue

            router.route(table, payload)

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        consumer.close()

    router.print_summary()


if __name__ == "__main__":
    main()
