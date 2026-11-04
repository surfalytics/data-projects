#!/usr/bin/env python3
"""
Solution: Exercise 2.2 -- Multi-Consumer Group Demo
=====================================================

Demonstrates consumer groups with rebalance callbacks and manual offset
commit every N messages. Run multiple instances with the same group-id
to see partition sharing, or different group-ids for independent consumption.

Usage:
    python ex05_multi_group_consumer.py --group-id group-A --consumer-id A1
    python ex05_multi_group_consumer.py --group-id group-A --consumer-id A2
    python ex05_multi_group_consumer.py --group-id group-B --consumer-id B1
"""

import argparse
import json
import signal
import sys

from confluent_kafka import Consumer, KafkaError, KafkaException

BROKER = "localhost:9092"
TOPIC = "user-events"
COMMIT_EVERY_N = 10

running = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    print("\nShutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def on_assign(consumer, partitions):
    """Log partition assignments during rebalance.

    Args:
        consumer: The Consumer instance.
        partitions: List of assigned TopicPartition objects.
    """
    parts = [f"{tp.topic}[{tp.partition}]" for tp in partitions]
    print(f"\n  >> ASSIGNED: {', '.join(parts)}\n")


def on_revoke(consumer, partitions):
    """Log partition revocations and commit offsets.

    Args:
        consumer: The Consumer instance.
        partitions: List of revoked TopicPartition objects.
    """
    parts = [f"{tp.topic}[{tp.partition}]" for tp in partitions]
    print(f"\n  >> REVOKED: {', '.join(parts)}")
    try:
        consumer.commit(asynchronous=False)
        print("  >> Offsets committed before revocation.\n")
    except KafkaException as e:
        print(f"  >> Commit failed: {e}\n")


def parse_args():
    """Parse CLI arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Multi-consumer group demo")
    parser.add_argument("--group-id", required=True, help="Consumer group ID")
    parser.add_argument("--consumer-id", required=True, help="Unique consumer ID")
    parser.add_argument("--topic", default=TOPIC, help=f"Topic (default: {TOPIC})")
    return parser.parse_args()


def main():
    """Run a consumer with rebalance callbacks and manual commit."""
    args = parse_args()

    print(f"Consumer: {args.consumer_id} | Group: {args.group_id} | Topic: {args.topic}")
    print(f"Commit every {COMMIT_EVERY_N} messages")
    print("-" * 60)

    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": args.group_id,
        "client.id": args.consumer_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
        "partition.assignment.strategy": "cooperative-sticky",
        "session.timeout.ms": 15000,
        "heartbeat.interval.ms": 3000,
    })

    count = 0
    uncommitted = 0

    try:
        consumer.subscribe(
            [args.topic],
            on_assign=on_assign,
            on_revoke=on_revoke,
        )

        while running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            count += 1
            uncommitted += 1

            key = msg.key().decode("utf-8") if msg.key() else None
            value = msg.value().decode("utf-8") if msg.value() else None

            summary = value[:80] if value else "None"
            try:
                parsed = json.loads(value)
                summary = f"user={parsed.get('user_id', '?')} event={parsed.get('event_type', '?')}"
            except (json.JSONDecodeError, TypeError):
                pass

            print(
                f"  [{args.consumer_id}] #{count} | "
                f"group={args.group_id} p={msg.partition()} "
                f"off={msg.offset()} | {summary}"
            )

            if uncommitted >= COMMIT_EVERY_N:
                try:
                    consumer.commit(asynchronous=False)
                    print(f"  [{args.consumer_id}] -- committed offsets ({uncommitted} msgs)")
                    uncommitted = 0
                except KafkaException as e:
                    print(f"  [COMMIT ERROR] {e}")

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        if uncommitted > 0:
            try:
                consumer.commit(asynchronous=False)
            except KafkaException:
                pass
        print(f"\n[{args.consumer_id}] Total consumed: {count}")
        consumer.close()
        print("Closed.")


if __name__ == "__main__":
    main()
