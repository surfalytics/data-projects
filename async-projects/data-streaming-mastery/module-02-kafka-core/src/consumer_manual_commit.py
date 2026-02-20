#!/usr/bin/env python3
"""
Manual Offset Commit Consumer
===============================

Demonstrates manual (synchronous) offset commit to achieve at-least-once
processing semantics. The consumer:

  1. Polls a batch of messages
  2. Processes each message (simulated work)
  3. Commits the offsets ONLY after successful processing

If the consumer crashes between processing and committing, the messages
will be re-delivered on restart -- hence "at-least-once."

Usage:
    python consumer_manual_commit.py
    python consumer_manual_commit.py --topic user-events --batch-size 5

Prerequisites:
    - Kafka broker running on localhost:9092 (use docker-compose up)
    - Messages in the target topic (run a producer first)
    - pip install confluent-kafka
"""

import argparse
import json
import signal
import sys
import time
from datetime import datetime, timezone

from confluent_kafka import Consumer, KafkaError, KafkaException, TopicPartition

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BROKER = "localhost:9092"
DEFAULT_TOPIC = "user-events"

# Graceful shutdown flag
running = True


def signal_handler(sig, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global running
    print("\n[SHUTDOWN] Signal received. Will finish current batch then exit...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ---------------------------------------------------------------------------
# Message Processor
# ---------------------------------------------------------------------------
def process_message(msg):
    """Process a single Kafka message.

    In a real application this might write to a database, call an API,
    update a cache, etc. Here we simulate work with a small sleep and
    print the message content.

    Args:
        msg: A confluent_kafka.Message object.

    Returns:
        bool: True if processing succeeded, False otherwise.
    """
    try:
        key = msg.key().decode("utf-8") if msg.key() else None
        value = msg.value().decode("utf-8") if msg.value() else None

        # Attempt JSON parsing
        parsed = None
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass

        if parsed:
            display = (
                f"user={parsed.get('user_id', '?')} "
                f"event={parsed.get('event_type', '?')}"
            )
        else:
            display = f"value={value}"

        print(
            f"    Processing: partition={msg.partition()} "
            f"offset={msg.offset()} key={key} | {display}"
        )

        # Simulate processing work (e.g., database write)
        time.sleep(0.05)

        return True

    except Exception as e:
        print(f"    [ERROR] Failed to process message: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Consumer Factory
# ---------------------------------------------------------------------------
def create_consumer(group_id="manual-commit-group"):
    """Create a Kafka consumer with auto-commit DISABLED.

    Args:
        group_id: The consumer group ID.

    Returns:
        Consumer: A confluent_kafka.Consumer with manual commit enabled.
    """
    config = {
        "bootstrap.servers": BROKER,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        # CRITICAL: disable auto-commit for manual control
        "enable.auto.commit": False,
        # Session and heartbeat
        "session.timeout.ms": 15000,
        "heartbeat.interval.ms": 3000,
        "max.poll.interval.ms": 300000,
    }
    return Consumer(config)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Kafka consumer with manual offset commit (at-least-once)"
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help=f"Topic to consume (default: {DEFAULT_TOPIC})",
    )
    parser.add_argument(
        "--group-id",
        default="manual-commit-group",
        help="Consumer group ID (default: manual-commit-group)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of messages to process before committing (default: 10)",
    )
    return parser.parse_args()


def main():
    """Consume messages with manual offset commits for at-least-once guarantees."""
    args = parse_args()

    print("=" * 60)
    print("Manual Offset Commit Consumer")
    print("=" * 60)
    print(f"  Broker:     {BROKER}")
    print(f"  Topic:      {args.topic}")
    print(f"  Group ID:   {args.group_id}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Auto-commit: DISABLED")
    print(f"  Guarantee:  at-least-once")
    print("=" * 60)
    print("Waiting for messages... (Ctrl+C to exit)\n")

    consumer = create_consumer(group_id=args.group_id)

    total_processed = 0
    total_committed = 0
    batch_messages = []

    try:
        consumer.subscribe([args.topic])

        while running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                # No message available; commit any pending batch on idle
                if batch_messages:
                    print(
                        f"\n  [COMMIT] Idle timeout -- committing batch of "
                        f"{len(batch_messages)} messages..."
                    )
                    try:
                        consumer.commit(asynchronous=False)
                        total_committed += len(batch_messages)
                        print(f"  [COMMIT] Success. Total committed: {total_committed}")
                    except KafkaException as e:
                        print(f"  [COMMIT ERROR] {e}")
                    batch_messages = []
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # Commit any pending batch at end of partition
                    if batch_messages:
                        print(
                            f"\n  [COMMIT] End of partition -- committing batch of "
                            f"{len(batch_messages)} messages..."
                        )
                        try:
                            consumer.commit(asynchronous=False)
                            total_committed += len(batch_messages)
                        except KafkaException as e:
                            print(f"  [COMMIT ERROR] {e}")
                        batch_messages = []
                    continue
                else:
                    raise KafkaException(msg.error())

            # Process the message
            success = process_message(msg)

            if success:
                total_processed += 1
                batch_messages.append(msg)

                # Commit after batch_size messages
                if len(batch_messages) >= args.batch_size:
                    print(
                        f"\n  [COMMIT] Batch of {len(batch_messages)} processed. "
                        f"Committing offsets synchronously..."
                    )
                    try:
                        # commitSync blocks until the broker confirms
                        consumer.commit(asynchronous=False)
                        total_committed += len(batch_messages)
                        print(
                            f"  [COMMIT] Success. Total committed: {total_committed}"
                        )
                    except KafkaException as e:
                        print(
                            f"  [COMMIT ERROR] Failed to commit offsets: {e}. "
                            f"Messages will be re-delivered on restart."
                        )
                    batch_messages = []
            else:
                # On processing failure, do NOT commit.
                # The message will be re-delivered on next poll or restart.
                print(
                    f"  [WARN] Processing failed for offset {msg.offset()}. "
                    f"Will NOT commit -- message will be retried."
                )

    except KafkaException as e:
        print(f"\nKafka error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        # Commit any remaining messages in the batch before shutting down
        if batch_messages:
            print(f"\n  [COMMIT] Final batch of {len(batch_messages)} messages...")
            try:
                consumer.commit(asynchronous=False)
                total_committed += len(batch_messages)
            except KafkaException as e:
                print(f"  [COMMIT ERROR] {e}")

        print(f"\nSummary:")
        print(f"  Total processed: {total_processed}")
        print(f"  Total committed: {total_committed}")
        print("Closing consumer...")
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
