#!/usr/bin/env python3
"""
Advanced Kafka Producer Example
================================

Demonstrates production-grade Kafka producer patterns:
  - Custom partitioner based on message key
  - Delivery callbacks with detailed logging
  - Configurable acknowledgment levels (acks)
  - Error handling and graceful shutdown
  - Sending fake user-event JSON payloads via Faker

Usage:
    python producer_advanced.py
    python producer_advanced.py --acks all --num-messages 50
    python producer_advanced.py --topic custom-topic --linger-ms 200

Prerequisites:
    - Kafka broker running on localhost:9092 (use docker-compose up)
    - pip install confluent-kafka faker
"""

import argparse
import json
import sys
import time
import hashlib
from datetime import datetime, timezone

from confluent_kafka import Producer, KafkaError, KafkaException
from faker import Faker

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
fake = Faker()

# Counters for delivery stats
stats = {
    "sent": 0,
    "delivered": 0,
    "failed": 0,
}

EVENT_TYPES = [
    "page_view",
    "button_click",
    "sign_up",
    "purchase",
    "logout",
    "search",
    "add_to_cart",
    "remove_from_cart",
]


# ---------------------------------------------------------------------------
# Custom Partitioner
# ---------------------------------------------------------------------------
def custom_partitioner(key, num_partitions):
    """Partition messages deterministically by a stable hash of the key.

    This partitioner uses SHA-256 instead of the default murmur2 hash to
    demonstrate how you can implement your own partitioning logic. The key
    is expected to be a user_id string.

    Args:
        key: The message key (bytes or str).
        num_partitions: Total number of partitions for the topic.

    Returns:
        int: The partition number (0-indexed).
    """
    if key is None:
        # Fall back to round-robin for null keys
        return hash(time.time()) % num_partitions

    key_str = key if isinstance(key, str) else key.decode("utf-8")
    digest = hashlib.sha256(key_str.encode("utf-8")).hexdigest()
    return int(digest, 16) % num_partitions


# ---------------------------------------------------------------------------
# Delivery Callback
# ---------------------------------------------------------------------------
def on_delivery(err, msg):
    """Detailed delivery callback with stats tracking.

    Args:
        err: KafkaError instance on failure, None on success.
        msg: The Message object that was produced.
    """
    if err is not None:
        stats["failed"] += 1
        print(
            f"  [FAIL] topic={msg.topic()} partition={msg.partition()} "
            f"key={msg.key()} error={err}"
        )
    else:
        stats["delivered"] += 1
        print(
            f"  [OK]   topic={msg.topic()} partition={msg.partition()} "
            f"offset={msg.offset()} "
            f"key={msg.key().decode('utf-8') if msg.key() else None} "
            f"latency={msg.latency():.3f}s"
        )


# ---------------------------------------------------------------------------
# Event Generator
# ---------------------------------------------------------------------------
def generate_user_event():
    """Generate a realistic fake user event using Faker.

    Returns:
        tuple: (user_id, event_dict) where user_id is a string and
               event_dict is a JSON-serializable dictionary.
    """
    user_id = f"user-{fake.random_int(min=1000, max=1099)}"
    event = {
        "user_id": user_id,
        "event_type": fake.random_element(EVENT_TYPES),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": fake.uuid4(),
        "ip_address": fake.ipv4(),
        "user_agent": fake.user_agent(),
        "page": fake.uri_path(),
        "metadata": {
            "country": fake.country_code(),
            "city": fake.city(),
            "device": fake.random_element(["mobile", "desktop", "tablet"]),
            "browser": fake.random_element(["Chrome", "Firefox", "Safari", "Edge"]),
        },
    }
    return user_id, event


# ---------------------------------------------------------------------------
# Producer Factory
# ---------------------------------------------------------------------------
def create_producer(acks="all", linger_ms=50):
    """Create a production-grade Kafka Producer.

    Args:
        acks: Acknowledgment level ('0', '1', or 'all').
        linger_ms: Milliseconds to wait for batching.

    Returns:
        Producer: A configured confluent_kafka.Producer.
    """
    config = {
        "bootstrap.servers": "localhost:9092",
        "client.id": "advanced-producer",
        # Durability
        "acks": str(acks),
        # Idempotence ensures exactly-once delivery per partition
        "enable.idempotence": acks == "all",
        # Batching
        "linger.ms": linger_ms,
        "batch.size": 65536,  # 64 KB
        # Retries
        "retries": 5,
        "retry.backoff.ms": 200,
        "delivery.timeout.ms": 30000,
        # Compression
        "compression.type": "snappy",
        # Buffer
        "queue.buffering.max.messages": 100000,
        "queue.buffering.max.kbytes": 1048576,  # 1 GB
    }
    return Producer(config)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Advanced Kafka producer with fake user events"
    )
    parser.add_argument(
        "--topic", default="user-events", help="Kafka topic (default: user-events)"
    )
    parser.add_argument(
        "--num-messages",
        type=int,
        default=20,
        help="Number of messages to produce (default: 20)",
    )
    parser.add_argument(
        "--acks",
        choices=["0", "1", "all"],
        default="all",
        help="Acknowledgment level (default: all)",
    )
    parser.add_argument(
        "--linger-ms",
        type=int,
        default=50,
        help="Linger time in ms for batching (default: 50)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between messages in seconds (default: 0.2)",
    )
    return parser.parse_args()


def main():
    """Produce fake user events to Kafka with advanced configuration."""
    args = parse_args()

    print("=" * 60)
    print("Advanced Kafka Producer")
    print("=" * 60)
    print(f"  Topic:        {args.topic}")
    print(f"  Messages:     {args.num_messages}")
    print(f"  Acks:         {args.acks}")
    print(f"  Linger (ms):  {args.linger_ms}")
    print(f"  Idempotent:   {args.acks == 'all'}")
    print("=" * 60)

    producer = create_producer(acks=args.acks, linger_ms=args.linger_ms)

    try:
        for i in range(args.num_messages):
            user_id, event = generate_user_event()
            value_bytes = json.dumps(event).encode("utf-8")

            # Determine partition using custom partitioner.
            # Note: confluent-kafka does not support passing a Python callable
            # as the partitioner in config, so we compute the partition
            # manually and pass it to produce().
            # In a real app you might let Kafka handle this or use a
            # different client that supports pluggable partitioners natively.
            partition = custom_partitioner(user_id, num_partitions=3)

            print(
                f"[{i + 1}/{args.num_messages}] "
                f"Producing event: user={user_id} type={event['event_type']} "
                f"-> partition {partition}"
            )

            producer.produce(
                topic=args.topic,
                key=user_id.encode("utf-8"),
                value=value_bytes,
                partition=partition,
                headers={
                    "event_type": event["event_type"].encode("utf-8"),
                    "source": b"advanced-producer",
                    "produced_at": datetime.now(timezone.utc).isoformat().encode("utf-8"),
                },
                callback=on_delivery,
            )

            # Trigger delivery callbacks without blocking
            producer.poll(0)
            stats["sent"] += 1

            time.sleep(args.delay)

        # Flush remaining messages
        print("\nFlushing remaining messages...")
        remaining = producer.flush(timeout=15)

        print("\n" + "=" * 60)
        print("Production Summary")
        print("=" * 60)
        print(f"  Sent:      {stats['sent']}")
        print(f"  Delivered: {stats['delivered']}")
        print(f"  Failed:    {stats['failed']}")
        if remaining > 0:
            print(f"  Unflushed: {remaining}")
        print("=" * 60)

    except BufferError:
        print(
            "ERROR: Producer buffer is full. "
            "Try increasing queue.buffering.max.messages or slowing down.",
            file=sys.stderr,
        )
        producer.flush(timeout=10)
        sys.exit(1)

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        producer.flush(timeout=5)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\nInterrupted by user. Flushing...")
        producer.flush(timeout=5)
        print(f"Delivered {stats['delivered']} of {stats['sent']} messages.")
        sys.exit(0)


if __name__ == "__main__":
    main()
