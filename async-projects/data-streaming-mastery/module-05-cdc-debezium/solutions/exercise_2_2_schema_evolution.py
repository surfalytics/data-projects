#!/usr/bin/env python3
"""
Solution 2.2: Schema Evolution Detector.

This script:
1. Alters the customers table to add a loyalty_tier column.
2. Inserts and updates rows using the new column.
3. Consumes CDC events and detects when the new field first appears.
4. Cleans up by dropping the added column.

Usage:
    python solutions/exercise_2_2_schema_evolution.py
"""

import json
import time
from typing import Optional, Set

import pymysql
from confluent_kafka import Consumer, KafkaError, KafkaException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP = "localhost:9092"
CONSUMER_GROUP = "exercise-02-schema-evo"
TOPIC = "ecommerce.ecommerce.customers"

MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "debezium",
    "database": "ecommerce",
}


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


def perform_schema_changes() -> None:
    """Connect to MySQL and make schema + data changes.

    1. ALTER TABLE to add loyalty_tier column.
    2. INSERT a new customer with loyalty_tier = 'gold'.
    3. UPDATE an existing customer's loyalty_tier to 'silver'.
    """
    print("Connecting to MySQL ...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    try:
        # Step 1: Add column.
        print("  ALTER TABLE customers ADD COLUMN loyalty_tier ...")
        cursor.execute(
            "ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(20) DEFAULT 'bronze'"
        )
        conn.commit()
        print("  Column added.")

        time.sleep(2)  # Let Debezium process the DDL.

        # Step 2: Insert a new customer with loyalty_tier.
        print("  INSERT new customer with loyalty_tier = 'gold' ...")
        cursor.execute(
            "INSERT INTO customers (email, first_name, last_name, phone, loyalty_tier) "
            "VALUES ('gold.member@example.com', 'Gold', 'Member', '555-0301', 'gold')"
        )
        conn.commit()

        # Step 3: Update existing customer.
        print("  UPDATE customer #1 loyalty_tier = 'silver' ...")
        cursor.execute(
            "UPDATE customers SET loyalty_tier = 'silver' WHERE id = 1"
        )
        conn.commit()

        print("  Schema changes and data modifications complete.\n")

    finally:
        cursor.close()
        conn.close()


def cleanup_schema_changes() -> None:
    """Drop the loyalty_tier column to restore original schema."""
    print("\nCleaning up: dropping loyalty_tier column ...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE customers DROP COLUMN loyalty_tier")
        conn.commit()
        # Also delete the test customer.
        cursor.execute("DELETE FROM customers WHERE email = 'gold.member@example.com'")
        conn.commit()
        print("  Cleanup complete.")
    finally:
        cursor.close()
        conn.close()


def consume_and_detect_schema_changes() -> None:
    """Consume events from the customers topic and detect new fields."""
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([TOPIC])

    print(f"Consuming from {TOPIC} to detect schema changes ...\n")

    known_fields: Set[str] = set()
    first_event = True
    empty_polls = 0
    max_empty = 15

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

            payload = extract_payload(msg.value())
            if payload is None:
                continue

            op = payload.get("op", "?")
            after = payload.get("after")
            before = payload.get("before")
            row = after or before
            if not row:
                continue

            current_fields = set(row.keys())

            # On the first event, establish the baseline schema.
            if first_event:
                known_fields = current_fields
                first_event = False
            else:
                new_fields = current_fields - known_fields
                removed_fields = known_fields - current_fields

                if new_fields:
                    print(f"\n  *** SCHEMA CHANGE DETECTED: 'customers' table "
                          f"now includes {sorted(new_fields)} ***\n")
                    known_fields = current_fields

                if removed_fields:
                    print(f"\n  *** SCHEMA CHANGE DETECTED: 'customers' table "
                          f"no longer includes {sorted(removed_fields)} ***\n")
                    known_fields = current_fields

            # Print customer info.
            op_label = {"c": "CREATE", "u": "UPDATE", "d": "DELETE", "r": "SNAPSHOT"}.get(op, op)
            cid = row.get("id", "?")
            name = f"{row.get('first_name', '')} {row.get('last_name', '')}"
            loyalty = row.get("loyalty_tier", "(not present)")

            print(f"  [{op_label}] Customer #{cid}: {name} | loyalty_tier={loyalty}")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        consumer.close()


def main() -> None:
    """Run the full schema evolution exercise."""
    print("=" * 60)
    print("Exercise 2.2: Schema Evolution Detector")
    print("=" * 60)
    print()

    # Step 1: Make schema changes in MySQL.
    perform_schema_changes()

    # Step 2: Consume events and detect the new column.
    time.sleep(3)  # Give Debezium time to produce events.
    consume_and_detect_schema_changes()

    # Step 3: Cleanup.
    cleanup_schema_changes()

    print("\nAnswers to exercise questions:")
    print("  - Events for customers that existed BEFORE the ALTER will include")
    print("    loyalty_tier with the DEFAULT value ('bronze') when they are next")
    print("    modified, or 'null' / absent in snapshot events produced before the ALTER.")
    print("  - The schema history topic (schema-changes.ecommerce) contains the DDL")
    print("    statement for the ALTER TABLE along with the binlog position.")
    print()


if __name__ == "__main__":
    main()
