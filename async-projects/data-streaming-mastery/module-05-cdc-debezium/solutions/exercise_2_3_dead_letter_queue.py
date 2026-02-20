#!/usr/bin/env python3
"""
Solution 2.3: Dead Letter Queue and Error Handling.

This script demonstrates robust CDC event processing with:
- Event structure validation.
- Routing malformed messages to a DLQ topic.
- Injecting a bad message to test error handling.
- Counting successes and failures.

Usage:
    python solutions/exercise_2_3_dead_letter_queue.py
"""

import json
import time
from typing import Optional

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

KAFKA_BOOTSTRAP = "localhost:9092"
CONSUMER_GROUP = "exercise-02-dlq"
SOURCE_TOPIC = "ecommerce.ecommerce.orders"
DLQ_TOPIC = "cdc-dlq"


def ensure_dlq_topic_exists() -> None:
    """Create the DLQ topic if it does not exist."""
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP})
    metadata = admin.list_topics(timeout=10)

    if DLQ_TOPIC not in metadata.topics:
        print(f"Creating DLQ topic '{DLQ_TOPIC}' ...")
        new_topic = NewTopic(DLQ_TOPIC, num_partitions=1, replication_factor=1)
        futures = admin.create_topics([new_topic])
        for topic, future in futures.items():
            try:
                future.result()
                print(f"  Topic '{topic}' created.")
            except Exception as e:
                print(f"  Warning: {e}")
    else:
        print(f"DLQ topic '{DLQ_TOPIC}' already exists.")


def inject_bad_message() -> None:
    """Produce a malformed message to the source topic to test DLQ handling."""
    print(f"\nInjecting a malformed message into '{SOURCE_TOPIC}' ...")
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})

    # This message is valid JSON but does not conform to Debezium envelope format.
    bad_msg = json.dumps({"garbage": "this is not a valid CDC event"}).encode("utf-8")
    producer.produce(
        topic=SOURCE_TOPIC,
        key=json.dumps({"id": -999}).encode("utf-8"),
        value=bad_msg,
    )
    producer.flush()
    print("  Malformed message injected.")


def validate_event(raw_value: bytes) -> tuple:
    """Validate a message conforms to the Debezium envelope structure.

    Args:
        raw_value: Raw Kafka message value.

    Returns:
        Tuple of (is_valid: bool, payload_or_error: dict|str).
        If valid, payload_or_error is the payload dict.
        If invalid, payload_or_error is an error description string.
    """
    if raw_value is None:
        # Tombstones are valid but have no payload.
        return True, None

    try:
        message = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return False, f"JSON parse error: {e}"

    # Extract payload.
    payload = message.get("payload") if "payload" in message else message

    if "op" not in payload:
        return False, "Missing 'op' field"

    op = payload["op"]
    if op not in ("c", "u", "d", "r"):
        return False, f"Invalid 'op' value: '{op}'"

    # For creates and snapshots, 'after' must be present.
    if op in ("c", "r") and payload.get("after") is None:
        return False, f"'after' is null for op='{op}'"

    # For deletes, 'before' must be present.
    if op == "d" and payload.get("before") is None:
        return False, f"'before' is null for op='d'"

    return True, payload


def send_to_dlq(
    producer: Producer,
    msg,
    error_reason: str,
) -> None:
    """Produce a failed message to the DLQ topic with error metadata.

    Args:
        producer: Kafka producer instance.
        msg: Original Kafka consumer message.
        error_reason: Description of why the message failed validation.
    """
    headers = [
        ("error_reason", error_reason.encode("utf-8")),
        ("original_topic", msg.topic().encode("utf-8")),
        ("original_partition", str(msg.partition()).encode("utf-8")),
        ("original_offset", str(msg.offset()).encode("utf-8")),
    ]

    producer.produce(
        topic=DLQ_TOPIC,
        key=msg.key(),
        value=msg.value(),
        headers=headers,
    )
    producer.flush()


def main() -> None:
    """Run the DLQ-enabled CDC consumer."""
    print("=" * 60)
    print("Exercise 2.3: Dead Letter Queue and Error Handling")
    print("=" * 60)

    ensure_dlq_topic_exists()
    inject_bad_message()

    time.sleep(2)  # Let the injected message propagate.

    # Set up consumer and producer (for DLQ writes).
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([SOURCE_TOPIC])

    dlq_producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP})

    total = 0
    success = 0
    dlq_count = 0
    tombstones = 0

    print(f"\nConsuming from '{SOURCE_TOPIC}' with validation ...\n")

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

            total += 1

            is_valid, result = validate_event(msg.value())

            if not is_valid:
                # Send to DLQ.
                dlq_count += 1
                send_to_dlq(dlq_producer, msg, result)
                print(
                    f"  [DLQ] offset={msg.offset()} error=\"{result}\""
                )
                continue

            if result is None:
                # Tombstone.
                tombstones += 1
                continue

            # Valid event -- process normally.
            success += 1
            op = result.get("op", "?")
            after = result.get("after") or {}
            before = result.get("before") or {}
            row = after or before
            row_id = row.get("id", "?")
            op_label = {"c": "CREATE", "u": "UPDATE", "d": "DELETE", "r": "SNAPSHOT"}.get(op, op)
            print(f"  [OK] {op_label} order #{row_id}")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        consumer.close()

    # Print summary.
    print()
    print("=" * 60)
    print(f"Processed: {total} | Success: {success} | "
          f"Tombstones: {tombstones} | DLQ: {dlq_count}")
    print("=" * 60)

    # Read DLQ to verify.
    if dlq_count > 0:
        print(f"\nReading DLQ topic '{DLQ_TOPIC}' ...")
        dlq_consumer = Consumer({
            "bootstrap.servers": KAFKA_BOOTSTRAP,
            "group.id": "dlq-reader",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        })
        dlq_consumer.subscribe([DLQ_TOPIC])

        dlq_empty = 0
        try:
            while dlq_empty < 5:
                msg = dlq_consumer.poll(timeout=1.0)
                if msg is None:
                    dlq_empty += 1
                    continue
                if msg.error():
                    continue
                headers = dict(msg.headers()) if msg.headers() else {}
                error = headers.get("error_reason", b"unknown").decode("utf-8")
                orig_topic = headers.get("original_topic", b"?").decode("utf-8")
                orig_offset = headers.get("original_offset", b"?").decode("utf-8")
                print(
                    f"  DLQ entry: topic={orig_topic}, offset={orig_offset}, "
                    f"error=\"{error}\""
                )
        finally:
            dlq_consumer.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
