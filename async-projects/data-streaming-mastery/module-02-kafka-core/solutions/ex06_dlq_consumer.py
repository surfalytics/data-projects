#!/usr/bin/env python3
"""
Solution: Exercise 2.3 -- Dead Letter Queue Consumer
======================================================

Consumes from 'user-events', validates messages, and routes failures
to a dead letter queue topic ('user-events-dlq') with error metadata
in message headers.

Usage:
    python ex06_dlq_consumer.py
"""

import json
import random
import signal
import sys
from datetime import datetime, timezone

from confluent_kafka import Consumer, Producer, KafkaError, KafkaException

BROKER = "localhost:9092"
SOURCE_TOPIC = "user-events"
DLQ_TOPIC = "user-events-dlq"
GROUP_ID = "dlq-consumer-group"
REQUIRED_FIELDS = ["user_id", "event_type", "timestamp"]
SIMULATED_FAILURE_RATE = 0.1  # 10% random failures

running = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    print("\nShutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class DeadLetterQueue:
    """Manages sending failed messages to a DLQ topic.

    Attributes:
        producer: Kafka producer for the DLQ topic.
        dlq_topic: Name of the DLQ topic.
        sent_count: Number of messages sent to DLQ.
    """

    def __init__(self, broker, dlq_topic):
        """Initialize the DLQ producer.

        Args:
            broker: Kafka bootstrap servers.
            dlq_topic: Name of the dead letter queue topic.
        """
        self.producer = Producer({
            "bootstrap.servers": broker,
            "client.id": "dlq-producer",
            "acks": "all",
        })
        self.dlq_topic = dlq_topic
        self.sent_count = 0

    def send(self, original_msg, error_reason, retry_count=0):
        """Send a failed message to the DLQ with error metadata.

        Args:
            original_msg: The original confluent_kafka.Message object.
            error_reason: Human-readable description of the failure.
            retry_count: Number of times this message has been retried.
        """
        headers = {
            "original_topic": (original_msg.topic() or "unknown").encode("utf-8"),
            "original_partition": str(original_msg.partition()).encode("utf-8"),
            "original_offset": str(original_msg.offset()).encode("utf-8"),
            "error_reason": error_reason.encode("utf-8"),
            "retry_count": str(retry_count).encode("utf-8"),
            "failed_at": datetime.now(timezone.utc).isoformat().encode("utf-8"),
        }

        self.producer.produce(
            topic=self.dlq_topic,
            key=original_msg.key(),
            value=original_msg.value(),
            headers=headers,
        )
        self.producer.poll(0)
        self.sent_count += 1

    def flush(self):
        """Flush any pending DLQ messages."""
        self.producer.flush(timeout=10)


def validate_and_process(value_str):
    """Validate and process a message.

    Args:
        value_str: The raw string value of the message.

    Returns:
        tuple: (success: bool, error_reason: str or None)
    """
    # Parse JSON
    try:
        data = json.loads(value_str)
    except (json.JSONDecodeError, TypeError) as e:
        return False, f"Malformed JSON: {e}"

    # Validate required fields
    for field in REQUIRED_FIELDS:
        if field not in data:
            return False, f"Missing required field: {field}"
        if not data[field]:
            return False, f"Empty required field: {field}"

    # Simulate random processing failure
    if random.random() < SIMULATED_FAILURE_RATE:
        return False, "Simulated processing failure (random)"

    return True, None


def main():
    """Consume messages with DLQ routing for failures."""
    print("Dead Letter Queue Consumer")
    print(f"  Source: {SOURCE_TOPIC} -> DLQ: {DLQ_TOPIC}")
    print(f"  Simulated failure rate: {SIMULATED_FAILURE_RATE * 100}%")
    print("-" * 60)

    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })

    dlq = DeadLetterQueue(BROKER, DLQ_TOPIC)

    processed = 0
    failed = 0

    try:
        consumer.subscribe([SOURCE_TOPIC])

        while running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            value_str = msg.value().decode("utf-8") if msg.value() else None
            success, error_reason = validate_and_process(value_str)

            if success:
                processed += 1
                if processed % 20 == 0:
                    print(f"  Processed {processed} messages successfully...")
            else:
                failed += 1
                print(
                    f"  [DLQ] p={msg.partition()} off={msg.offset()} "
                    f"reason={error_reason}"
                )
                dlq.send(msg, error_reason)

            # Commit after each message for at-least-once
            try:
                consumer.commit(asynchronous=False)
            except KafkaException as e:
                print(f"  [COMMIT ERROR] {e}")

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        dlq.flush()
        total = processed + failed
        print(f"\nSummary:")
        print(f"  Total:     {total}")
        print(f"  Processed: {processed}")
        print(f"  Failed:    {failed} (sent to DLQ)")
        if total > 0:
            print(f"  Fail rate: {failed / total * 100:.1f}%")
        consumer.close()
        print("Closed.")


if __name__ == "__main__":
    main()
