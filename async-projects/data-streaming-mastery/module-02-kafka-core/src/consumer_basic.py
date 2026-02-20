#!/usr/bin/env python3
"""
Basic Kafka Consumer Example
=============================

Demonstrates the simplest possible Kafka consumer that subscribes to a
topic and prints every message it receives. Uses auto-commit for offsets.

Usage:
    python consumer_basic.py
    python consumer_basic.py --topic my-topic --from-beginning

Prerequisites:
    - Kafka broker running on localhost:9092 (use docker-compose up)
    - Messages in the target topic (run producer_basic.py first)
    - pip install confluent-kafka
"""

import argparse
import signal
import sys

from confluent_kafka import Consumer, KafkaError, KafkaException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BROKER = "localhost:9092"
DEFAULT_TOPIC = "basic-messages"

# Graceful shutdown flag
running = True


def signal_handler(sig, frame):
    """Handle SIGINT/SIGTERM for graceful shutdown."""
    global running
    print("\nShutdown signal received. Closing consumer...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def create_consumer(group_id="basic-consumer-group", auto_offset_reset="earliest"):
    """Create and return a configured Kafka Consumer instance.

    Args:
        group_id: The consumer group ID.
        auto_offset_reset: Where to start reading if no committed offset
                           exists ('earliest' or 'latest').

    Returns:
        Consumer: A confluent_kafka.Consumer ready to subscribe and poll.
    """
    config = {
        "bootstrap.servers": BROKER,
        "group.id": group_id,
        "auto.offset.reset": auto_offset_reset,
        # Auto-commit offsets every 5 seconds (default behavior)
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
        # Heartbeat and session timeout
        "session.timeout.ms": 10000,
        "heartbeat.interval.ms": 3000,
    }
    return Consumer(config)


def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Basic Kafka consumer")
    parser.add_argument(
        "--topic", default=DEFAULT_TOPIC, help=f"Topic to consume (default: {DEFAULT_TOPIC})"
    )
    parser.add_argument(
        "--from-beginning",
        action="store_true",
        help="Read from the beginning of the topic",
    )
    return parser.parse_args()


def main():
    """Subscribe to a topic and print every message."""
    args = parse_args()
    offset_reset = "earliest" if args.from_beginning else "latest"

    print(f"Starting basic consumer")
    print(f"  Broker: {BROKER}")
    print(f"  Topic:  {args.topic}")
    print(f"  Offset: {offset_reset}")
    print("-" * 50)
    print("Waiting for messages... (Ctrl+C to exit)\n")

    consumer = create_consumer(auto_offset_reset=offset_reset)

    try:
        consumer.subscribe([args.topic])

        message_count = 0
        while running:
            # Poll for a message with a 1-second timeout
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                # No message received within the timeout
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # Reached end of partition -- not an error
                    print(
                        f"  [INFO] End of partition: {msg.topic()} "
                        f"[{msg.partition()}] @ offset {msg.offset()}"
                    )
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    print(f"  [WARN] Topic '{msg.topic()}' does not exist yet. Waiting...")
                else:
                    raise KafkaException(msg.error())
                continue

            # Successfully received a message
            message_count += 1
            key = msg.key().decode("utf-8") if msg.key() else None
            value = msg.value().decode("utf-8") if msg.value() else None

            print(
                f"  [{message_count}] "
                f"topic={msg.topic()} "
                f"partition={msg.partition()} "
                f"offset={msg.offset()} "
                f"key={key}"
            )
            print(f"         value={value}")
            print()

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        # Close the consumer to commit final offsets and leave the group
        print(f"\nConsumed {message_count} messages total.")
        print("Closing consumer and committing offsets...")
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
