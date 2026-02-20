#!/usr/bin/env python3
"""
Solution: Exercise 3.1 -- Key-Based Partitioning Analysis
==========================================================

Produces 200 messages with 10 different keys to a 3-partition topic, then
consumes all messages and reports on partition distribution and key consistency.

Usage:
    python ex07_partition_analysis.py

This script runs BOTH the producer and consumer phases sequentially.
"""

import json
import signal
import sys
import time
from collections import defaultdict

from confluent_kafka import Producer, Consumer, KafkaError, KafkaException

BROKER = "localhost:9092"
TOPIC = "partition-test"
NUM_MESSAGES = 200
NUM_KEYS = 10
GROUP_ID = "partition-analysis-group"

running = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    print("\nShutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ---------------------------------------------------------------------------
# Phase 1: Produce
# ---------------------------------------------------------------------------
def produce_messages():
    """Produce 200 messages with 10 rotating keys.

    Returns:
        bool: True if production succeeded.
    """
    print("=" * 50)
    print("Phase 1: Producing Messages")
    print("=" * 50)

    delivered = 0

    def on_delivery(err, msg):
        nonlocal delivered
        if err:
            print(f"  [FAIL] {err}")
        else:
            delivered += 1

    producer = Producer({
        "bootstrap.servers": BROKER,
        "client.id": "partition-analysis-producer",
        "acks": "all",
        "linger.ms": 10,
    })

    try:
        for i in range(NUM_MESSAGES):
            key = f"user-{i % NUM_KEYS}"
            value = json.dumps({"index": i, "key": key, "data": f"message-{i}"})

            producer.produce(
                topic=TOPIC,
                key=key.encode("utf-8"),
                value=value.encode("utf-8"),
                callback=on_delivery,
            )
            producer.poll(0)

        producer.flush(timeout=15)
        print(f"  Delivered {delivered}/{NUM_MESSAGES} messages.\n")
        return delivered == NUM_MESSAGES

    except KafkaException as e:
        print(f"  Producer error: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Phase 2: Consume and Analyze
# ---------------------------------------------------------------------------
def consume_and_analyze():
    """Consume all messages and analyze partition distribution.

    Returns:
        None
    """
    print("=" * 50)
    print("Phase 2: Consuming and Analyzing")
    print("=" * 50)

    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    # Tracking data structures
    partition_counts = defaultdict(int)       # partition -> message count
    partition_keys = defaultdict(set)         # partition -> set of keys
    key_partitions = defaultdict(set)         # key -> set of partitions

    consumed = 0
    empty_polls = 0
    max_empty_polls = 10  # Stop after 10 consecutive empty polls

    try:
        consumer.subscribe([TOPIC])

        while running and consumed < NUM_MESSAGES and empty_polls < max_empty_polls:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                empty_polls += 1
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    empty_polls += 1
                    continue
                raise KafkaException(msg.error())

            empty_polls = 0
            consumed += 1

            key = msg.key().decode("utf-8") if msg.key() else "null"
            partition = msg.partition()

            partition_counts[partition] += 1
            partition_keys[partition].add(key)
            key_partitions[key].add(partition)

        # Generate report
        print(f"\n  Consumed {consumed} messages.\n")
        print("=" * 50)
        print("Partition Distribution Report")
        print("=" * 50)

        for partition in sorted(partition_counts):
            count = partition_counts[partition]
            keys = sorted(partition_keys[partition])
            bar = "#" * (count // 4)
            print(f"  Partition {partition}: {count} messages {bar}")
            print(f"    Keys: {', '.join(keys)}")

        # Consistency check
        print()
        inconsistent_keys = []
        for key in sorted(key_partitions):
            if len(key_partitions[key]) > 1:
                inconsistent_keys.append(key)

        if inconsistent_keys:
            print("  Key Consistency Check: FAILED")
            for key in inconsistent_keys:
                parts = sorted(key_partitions[key])
                print(f"    WARNING: '{key}' appears in partitions: {parts}")
        else:
            print("  Key Consistency Check: PASSED")
            print("    All messages with the same key landed in the same partition.")

        print("=" * 50)

    except KafkaException as e:
        print(f"  Consumer error: {e}", file=sys.stderr)

    finally:
        consumer.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Run the partition analysis: produce then consume."""
    print(f"Partition Analysis: {NUM_MESSAGES} messages, {NUM_KEYS} keys, topic={TOPIC}")
    print("-" * 50)

    success = produce_messages()
    if not success:
        print("Production failed. Aborting analysis.")
        sys.exit(1)

    # Small delay to ensure messages are committed
    time.sleep(1)

    consume_and_analyze()


if __name__ == "__main__":
    main()
