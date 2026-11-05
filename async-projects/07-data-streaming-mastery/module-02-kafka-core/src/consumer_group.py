#!/usr/bin/env python3
"""
Consumer Group Example
=======================

Demonstrates Kafka consumer groups with:
  - Configurable group-id and consumer-id via CLI arguments
  - Rebalance callbacks that log partition assignments and revocations
  - Offset commit tracking
  - Cooperative incremental rebalancing

Run multiple instances of this script with the SAME group-id but
DIFFERENT consumer-ids to see partitions distributed among consumers.

Usage:
    # Terminal 1
    python consumer_group.py --group-id my-group --consumer-id consumer-1

    # Terminal 2
    python consumer_group.py --group-id my-group --consumer-id consumer-2

    # Terminal 3 (different group -- will get ALL partitions independently)
    python consumer_group.py --group-id another-group --consumer-id consumer-3

Prerequisites:
    - Kafka broker running on localhost:9092 (use docker-compose up)
    - Messages in the 'user-events' topic (run producer_advanced.py first)
    - pip install confluent-kafka
"""

import argparse
import signal
import sys
import json
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
    print("\n[SHUTDOWN] Signal received. Closing consumer...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ---------------------------------------------------------------------------
# Rebalance Callbacks
# ---------------------------------------------------------------------------
class RebalanceLogger:
    """Logs partition assignments and revocations during rebalancing.

    Attributes:
        consumer_id: A human-readable identifier for this consumer instance.
    """

    def __init__(self, consumer_id):
        """Initialize the rebalance logger.

        Args:
            consumer_id: Display name for this consumer.
        """
        self.consumer_id = consumer_id
        self.assignment_count = 0

    def on_assign(self, consumer, partitions):
        """Called when partitions are assigned to this consumer.

        This callback fires after a rebalance when the consumer receives
        its new set of partitions.

        Args:
            consumer: The Consumer instance.
            partitions: List of TopicPartition objects assigned.
        """
        self.assignment_count += 1
        partition_list = [f"{tp.topic}[{tp.partition}]" for tp in partitions]
        print(
            f"\n{'=' * 60}\n"
            f"[REBALANCE] {self.consumer_id} -- ASSIGNED partitions "
            f"(rebalance #{self.assignment_count}):\n"
            f"  {', '.join(partition_list)}\n"
            f"{'=' * 60}\n"
        )

    def on_revoke(self, consumer, partitions):
        """Called when partitions are about to be revoked from this consumer.

        This is the place to commit offsets or clean up state before
        partitions are reassigned to another consumer.

        Args:
            consumer: The Consumer instance.
            partitions: List of TopicPartition objects being revoked.
        """
        partition_list = [f"{tp.topic}[{tp.partition}]" for tp in partitions]
        print(
            f"\n{'=' * 60}\n"
            f"[REBALANCE] {self.consumer_id} -- REVOKED partitions:\n"
            f"  {', '.join(partition_list)}\n"
            f"  Committing offsets before revocation...\n"
            f"{'=' * 60}\n"
        )
        # Commit current offsets before partitions are taken away
        try:
            consumer.commit(asynchronous=False)
            print("  Offsets committed successfully.")
        except KafkaException as e:
            print(f"  [WARN] Failed to commit offsets: {e}")

    def on_lost(self, consumer, partitions):
        """Called when partitions are lost (broker-initiated revocation).

        Unlike on_revoke, this is called when the broker has already
        reassigned the partitions. Committing offsets here may fail.

        Args:
            consumer: The Consumer instance.
            partitions: List of TopicPartition objects that were lost.
        """
        partition_list = [f"{tp.topic}[{tp.partition}]" for tp in partitions]
        print(
            f"\n{'=' * 60}\n"
            f"[REBALANCE] {self.consumer_id} -- LOST partitions:\n"
            f"  {', '.join(partition_list)}\n"
            f"  (Partitions already reassigned by broker)\n"
            f"{'=' * 60}\n"
        )


# ---------------------------------------------------------------------------
# Consumer Factory
# ---------------------------------------------------------------------------
def create_consumer(group_id, consumer_id):
    """Create a Kafka consumer configured for consumer-group demonstration.

    Args:
        group_id: The consumer group ID.
        consumer_id: A human-readable name for this consumer instance.

    Returns:
        tuple: (Consumer, RebalanceLogger)
    """
    config = {
        "bootstrap.servers": BROKER,
        "group.id": group_id,
        "client.id": consumer_id,
        "auto.offset.reset": "earliest",
        # Use cooperative rebalancing to minimize stop-the-world pauses
        "partition.assignment.strategy": "cooperative-sticky",
        # Auto-commit every 5 seconds
        "enable.auto.commit": True,
        "auto.commit.interval.ms": 5000,
        # Session and heartbeat
        "session.timeout.ms": 15000,
        "heartbeat.interval.ms": 3000,
        # Max poll interval -- if processing takes longer, consumer is
        # considered dead and a rebalance is triggered
        "max.poll.interval.ms": 300000,
    }

    consumer = Consumer(config)
    rebalance_logger = RebalanceLogger(consumer_id)

    return consumer, rebalance_logger


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def parse_args():
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Kafka consumer group demo with rebalance callbacks"
    )
    parser.add_argument(
        "--group-id",
        required=True,
        help="Consumer group ID (e.g., my-group)",
    )
    parser.add_argument(
        "--consumer-id",
        required=True,
        help="Unique consumer ID within the group (e.g., consumer-1)",
    )
    parser.add_argument(
        "--topic",
        default=DEFAULT_TOPIC,
        help=f"Topic to consume (default: {DEFAULT_TOPIC})",
    )
    return parser.parse_args()


def main():
    """Run a consumer that demonstrates consumer group behavior."""
    args = parse_args()

    print("=" * 60)
    print("Consumer Group Demo")
    print("=" * 60)
    print(f"  Broker:      {BROKER}")
    print(f"  Topic:       {args.topic}")
    print(f"  Group ID:    {args.group_id}")
    print(f"  Consumer ID: {args.consumer_id}")
    print(f"  Strategy:    cooperative-sticky")
    print("=" * 60)
    print("Waiting for messages... (Ctrl+C to exit)\n")

    consumer, rebalance_logger = create_consumer(args.group_id, args.consumer_id)

    try:
        consumer.subscribe(
            [args.topic],
            on_assign=rebalance_logger.on_assign,
            on_revoke=rebalance_logger.on_revoke,
            on_lost=rebalance_logger.on_lost,
        )

        message_count = 0
        while running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    raise KafkaException(msg.error())

            message_count += 1
            key = msg.key().decode("utf-8") if msg.key() else None
            value = msg.value().decode("utf-8") if msg.value() else None

            # Try to parse JSON value for pretty display
            display_value = value
            try:
                parsed = json.loads(value)
                display_value = (
                    f"user={parsed.get('user_id', '?')} "
                    f"event={parsed.get('event_type', '?')}"
                )
            except (json.JSONDecodeError, TypeError):
                pass

            timestamp_type, timestamp = msg.timestamp()
            ts_str = (
                datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime(
                    "%H:%M:%S"
                )
                if timestamp > 0
                else "N/A"
            )

            print(
                f"  [{args.consumer_id}] msg #{message_count} | "
                f"partition={msg.partition()} offset={msg.offset()} "
                f"ts={ts_str} | {display_value}"
            )

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        print(f"\n[{args.consumer_id}] Consumed {message_count} messages.")
        print("Closing consumer (committing offsets, leaving group)...")
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
