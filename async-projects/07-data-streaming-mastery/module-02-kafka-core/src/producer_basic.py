#!/usr/bin/env python3
"""
Basic Kafka Producer Example
=============================

Demonstrates the simplest possible Kafka producer using the confluent-kafka
Python client. Sends a series of string messages to a topic and handles
delivery confirmations via callbacks.

Usage:
    python producer_basic.py

Prerequisites:
    - Kafka broker running on localhost:9092 (use docker-compose up)
    - pip install confluent-kafka
"""

import sys
import time
from confluent_kafka import Producer, KafkaError, KafkaException


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BROKER = "localhost:9092"
TOPIC = "basic-messages"
NUM_MESSAGES = 10


def delivery_callback(err, msg):
    """Called once for each message produced to indicate delivery result.

    This callback is triggered by poll() or flush() and reports whether the
    message was successfully delivered to the broker or if an error occurred.

    Args:
        err: KafkaError instance on failure, None on success.
        msg: The Message object that was produced.
    """
    if err is not None:
        print(f"  [ERROR] Delivery failed for message [{msg.key()}]: {err}")
    else:
        print(
            f"  [OK] Delivered to {msg.topic()} "
            f"[partition={msg.partition()}] "
            f"@ offset {msg.offset()}"
        )


def create_producer():
    """Create and return a configured Kafka Producer instance.

    Returns:
        Producer: A confluent_kafka.Producer ready to send messages.
    """
    config = {
        "bootstrap.servers": BROKER,
        "client.id": "basic-producer",
        # Wait up to 500ms to accumulate messages into a batch
        "linger.ms": 100,
        # Acknowledgment: wait for the leader to confirm the write
        "acks": "1",
    }
    return Producer(config)


def main():
    """Entry point: produce NUM_MESSAGES simple text messages to TOPIC."""
    print(f"Starting basic producer -> topic '{TOPIC}'")
    print(f"Broker: {BROKER}")
    print("-" * 50)

    producer = create_producer()

    try:
        for i in range(NUM_MESSAGES):
            message_value = f"Hello Kafka! Message #{i + 1} at {time.strftime('%H:%M:%S')}"
            message_key = f"key-{i % 3}"  # rotate among 3 keys

            print(f"Producing: key={message_key}, value={message_value}")

            # produce() is asynchronous -- the message is queued in an
            # internal buffer and sent in the background by the librdkafka
            # sender thread.
            producer.produce(
                topic=TOPIC,
                key=message_key,
                value=message_value,
                callback=delivery_callback,
            )

            # Serve delivery callbacks from previous produce() calls.
            # This is non-blocking when events=0 (default); it just triggers
            # any pending callbacks.
            producer.poll(0)

            time.sleep(0.3)

        # Wait for all outstanding messages to be delivered.
        remaining = producer.flush(timeout=10)
        if remaining > 0:
            print(f"WARNING: {remaining} message(s) were not delivered.")
        else:
            print("\nAll messages delivered successfully!")

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user. Flushing remaining messages...")
        producer.flush(timeout=5)
        sys.exit(0)


if __name__ == "__main__":
    main()
