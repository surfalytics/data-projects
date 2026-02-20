#!/usr/bin/env python3
"""
CDC Consumer -- reads Debezium change events and prints human-readable descriptions.

This consumer subscribes to all Debezium topics for the ecommerce database,
parses the envelope format (before/after/source/op), and prints a friendly
description of each change.

Examples of output:
    INSERT into customers: John Doe (john@example.com)
    UPDATE orders #3: status changed from 'pending' to 'shipped'
    DELETE from customers: #6 Alice Wonder

Usage:
    python src/cdc_consumer.py [--topics TOPIC1,TOPIC2] [--from-beginning]
"""

import argparse
import json
import os
import sys
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CONSUMER_GROUP = "cdc-consumer-demo"
TOPIC_PREFIX = "ecommerce.ecommerce."

DEFAULT_TOPICS = [
    f"{TOPIC_PREFIX}customers",
    f"{TOPIC_PREFIX}addresses",
    f"{TOPIC_PREFIX}products",
    f"{TOPIC_PREFIX}orders",
    f"{TOPIC_PREFIX}order_items",
    f"{TOPIC_PREFIX}inventory",
]

# Map single-char operation codes to human-readable labels.
OP_LABELS = {
    "c": "INSERT",
    "u": "UPDATE",
    "d": "DELETE",
    "r": "SNAPSHOT",
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Consume and display Debezium CDC events."
    )
    parser.add_argument(
        "--topics",
        type=str,
        default=",".join(DEFAULT_TOPICS),
        help="Comma-separated list of Kafka topics to subscribe to.",
    )
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        default=True,
        help="Read from the beginning of each topic (default: True).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for messages before exiting (0 = run forever).",
    )
    return parser.parse_args()


def extract_payload(raw_value: bytes) -> Optional[dict]:
    """Parse a Debezium message value and return the payload dict.

    Debezium JSON messages have a top-level 'schema' and 'payload'.
    This function extracts the 'payload' portion.

    Args:
        raw_value: Raw bytes from the Kafka message value.

    Returns:
        The payload dictionary, or None if the message is a tombstone or
        cannot be parsed.
    """
    if raw_value is None:
        return None  # Tombstone event
    try:
        message = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None

    # Debezium envelope: message may have 'payload' at the top level,
    # or the message itself may be the payload (depends on converter config).
    if "payload" in message:
        return message["payload"]
    if "op" in message:
        return message  # Already the payload
    return None


def describe_change(table: str, payload: dict) -> str:
    """Build a human-readable description of a CDC event.

    Args:
        table: The source table name (e.g., 'customers').
        payload: The Debezium event payload containing before/after/op.

    Returns:
        A formatted string describing the change.
    """
    op = payload.get("op", "?")
    label = OP_LABELS.get(op, f"UNKNOWN({op})")
    before = payload.get("before")
    after = payload.get("after")
    source = payload.get("source", {})
    ts_ms = source.get("ts_ms", 0)

    # Determine the primary key value.
    row = after if after else before
    row_id = row.get("id", "?") if row else "?"

    if table == "customers":
        return _describe_customer_change(label, op, row_id, before, after)
    elif table == "orders":
        return _describe_order_change(label, op, row_id, before, after)
    elif table == "products":
        return _describe_product_change(label, op, row_id, before, after)
    elif table == "order_items":
        return _describe_order_item_change(label, op, row_id, before, after)
    elif table == "inventory":
        return _describe_inventory_change(label, op, row_id, before, after)
    elif table == "addresses":
        return _describe_address_change(label, op, row_id, before, after)
    else:
        return f"{label} {table} #{row_id}"


def _describe_customer_change(
    label: str, op: str, row_id, before: Optional[dict], after: Optional[dict]
) -> str:
    """Describe a change to the customers table."""
    if op in ("c", "r"):
        name = f"{after.get('first_name', '')} {after.get('last_name', '')}"
        email = after.get("email", "")
        return f"{label} into customers: {name} ({email})"
    elif op == "u":
        name = f"{after.get('first_name', '')} {after.get('last_name', '')}"
        changes = _diff_fields(before, after, exclude={"updated_at"})
        return f"{label} customers #{row_id} ({name}): {changes}"
    elif op == "d":
        name = f"{before.get('first_name', '')} {before.get('last_name', '')}"
        return f"{label} from customers: #{row_id} {name}"
    return f"{label} customers #{row_id}"


def _describe_order_change(
    label: str, op: str, row_id, before: Optional[dict], after: Optional[dict]
) -> str:
    """Describe a change to the orders table."""
    if op in ("c", "r"):
        status = after.get("status", "?")
        amount = after.get("total_amount", 0)
        cust_id = after.get("customer_id", "?")
        return (
            f"{label} into orders: #{row_id} for customer #{cust_id} "
            f"status='{status}' total=${amount}"
        )
    elif op == "u":
        old_status = before.get("status", "?") if before else "?"
        new_status = after.get("status", "?") if after else "?"
        if old_status != new_status:
            return (
                f"{label} orders #{row_id}: "
                f"status changed from '{old_status}' to '{new_status}'"
            )
        changes = _diff_fields(before, after, exclude={"updated_at"})
        return f"{label} orders #{row_id}: {changes}"
    elif op == "d":
        return f"{label} from orders: #{row_id}"
    return f"{label} orders #{row_id}"


def _describe_product_change(
    label: str, op: str, row_id, before: Optional[dict], after: Optional[dict]
) -> str:
    """Describe a change to the products table."""
    if op in ("c", "r"):
        name = after.get("name", "?")
        price = after.get("price", 0)
        return f"{label} into products: #{row_id} '{name}' ${price}"
    elif op == "u":
        name = after.get("name", "?")
        changes = _diff_fields(before, after)
        return f"{label} products #{row_id} ('{name}'): {changes}"
    elif op == "d":
        name = before.get("name", "?")
        return f"{label} from products: #{row_id} '{name}'"
    return f"{label} products #{row_id}"


def _describe_order_item_change(
    label: str, op: str, row_id, before: Optional[dict], after: Optional[dict]
) -> str:
    """Describe a change to the order_items table."""
    if op in ("c", "r"):
        order_id = after.get("order_id", "?")
        product_id = after.get("product_id", "?")
        qty = after.get("quantity", 0)
        return (
            f"{label} into order_items: #{row_id} "
            f"order #{order_id} product #{product_id} qty={qty}"
        )
    elif op == "d":
        order_id = before.get("order_id", "?")
        return f"{label} from order_items: #{row_id} (order #{order_id})"
    changes = _diff_fields(before, after)
    return f"{label} order_items #{row_id}: {changes}"


def _describe_inventory_change(
    label: str, op: str, row_id, before: Optional[dict], after: Optional[dict]
) -> str:
    """Describe a change to the inventory table."""
    if op in ("c", "r"):
        product_id = after.get("product_id", "?")
        warehouse = after.get("warehouse", "?")
        qty = after.get("quantity", 0)
        return (
            f"{label} into inventory: #{row_id} "
            f"product #{product_id} @ {warehouse} qty={qty}"
        )
    elif op == "u":
        old_qty = before.get("quantity", "?") if before else "?"
        new_qty = after.get("quantity", "?") if after else "?"
        warehouse = after.get("warehouse", "?") if after else "?"
        return (
            f"{label} inventory #{row_id} @ {warehouse}: "
            f"quantity {old_qty} -> {new_qty}"
        )
    elif op == "d":
        return f"{label} from inventory: #{row_id}"
    return f"{label} inventory #{row_id}"


def _describe_address_change(
    label: str, op: str, row_id, before: Optional[dict], after: Optional[dict]
) -> str:
    """Describe a change to the addresses table."""
    if op in ("c", "r"):
        city = after.get("city", "?")
        state = after.get("state", "?")
        cust_id = after.get("customer_id", "?")
        return (
            f"{label} into addresses: #{row_id} "
            f"for customer #{cust_id} ({city}, {state})"
        )
    elif op == "d":
        return f"{label} from addresses: #{row_id}"
    changes = _diff_fields(before, after)
    return f"{label} addresses #{row_id}: {changes}"


def _diff_fields(
    before: Optional[dict], after: Optional[dict], exclude: Optional[set] = None
) -> str:
    """Return a summary of which fields changed between before and after.

    Args:
        before: Row state before the change.
        after: Row state after the change.
        exclude: Set of field names to skip (e.g. auto-updated timestamps).

    Returns:
        A string like "email: 'old' -> 'new', phone: '111' -> '222'".
    """
    if not before or not after:
        return "(no diff available)"
    exclude = exclude or set()
    diffs = []
    for key in after:
        if key in exclude:
            continue
        old_val = before.get(key)
        new_val = after.get(key)
        if old_val != new_val:
            diffs.append(f"{key}: '{old_val}' -> '{new_val}'")
    return ", ".join(diffs) if diffs else "(no field changes detected)"


def extract_table_name(topic: str) -> str:
    """Extract the table name from a Debezium topic name.

    Debezium topics follow the pattern: {prefix}.{database}.{table}

    Args:
        topic: Full Kafka topic name.

    Returns:
        The table name portion.
    """
    parts = topic.split(".")
    return parts[-1] if parts else topic


def main() -> None:
    """Main consumer loop: subscribe, poll, describe, print."""
    args = parse_args()
    topics = [t.strip() for t in args.topics.split(",")]

    consumer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest" if args.from_beginning else "latest",
        "enable.auto.commit": True,
    }

    consumer = Consumer(consumer_config)
    consumer.subscribe(topics)

    print(f"\nSubscribed to topics: {topics}")
    print("Waiting for CDC events ...\n")
    print("=" * 80)

    empty_polls = 0
    max_empty = int(args.timeout / 1.0) if args.timeout > 0 else 0

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                if max_empty > 0:
                    empty_polls += 1
                    if empty_polls >= max_empty:
                        print(
                            f"\nNo messages for {args.timeout}s. Exiting."
                        )
                        break
                continue

            empty_polls = 0  # Reset on any message.

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            topic = msg.topic()
            table = extract_table_name(topic)
            payload = extract_payload(msg.value())

            if payload is None:
                # Tombstone event.
                key_data = json.loads(msg.key().decode("utf-8")) if msg.key() else {}
                key_payload = key_data.get("payload", key_data)
                print(f"  TOMBSTONE  {table} key={key_payload}")
                continue

            description = describe_change(table, payload)
            op = payload.get("op", "?")
            source = payload.get("source", {})
            binlog_file = source.get("file", "?")
            binlog_pos = source.get("pos", "?")
            snapshot = source.get("snapshot", "false")

            snap_tag = " [snapshot]" if snapshot not in ("false", False) else ""
            print(
                f"  [{binlog_file}:{binlog_pos}]{snap_tag} {description}"
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
