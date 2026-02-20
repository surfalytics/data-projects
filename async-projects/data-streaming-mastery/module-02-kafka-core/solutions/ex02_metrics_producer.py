#!/usr/bin/env python3
"""
Solution: Exercise 1.2 -- Producer with Retry Metrics
======================================================

Produces 100 messages with idempotent delivery, gzip compression, and
tracks detailed delivery metrics including per-partition counts and
average latency.

Usage:
    python ex02_metrics_producer.py
"""

import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone

from confluent_kafka import Producer, KafkaException
from faker import Faker

BROKER = "localhost:9092"
TOPIC = "metric-events"
NUM_MESSAGES = 100

fake = Faker()


class DeliveryMetrics:
    """Tracks delivery metrics for produced messages.

    Attributes:
        successes: Count of successful deliveries.
        failures: Count of failed deliveries.
        latencies: List of delivery latencies in seconds.
        partition_counts: Dict mapping partition number to delivery count.
    """

    def __init__(self):
        """Initialize all metric counters to zero."""
        self.successes = 0
        self.failures = 0
        self.latencies = []
        self.partition_counts = defaultdict(int)

    def on_delivery(self, err, msg):
        """Delivery callback that updates metrics.

        Args:
            err: KafkaError on failure, None on success.
            msg: The produced Message object.
        """
        if err is not None:
            self.failures += 1
            print(f"  [FAIL] {err}")
        else:
            self.successes += 1
            self.partition_counts[msg.partition()] += 1
            latency = msg.latency()
            if latency is not None:
                self.latencies.append(latency)

    def report(self):
        """Print a summary of all collected metrics."""
        avg_latency = (
            sum(self.latencies) / len(self.latencies) if self.latencies else 0
        )
        min_latency = min(self.latencies) if self.latencies else 0
        max_latency = max(self.latencies) if self.latencies else 0

        print("\n" + "=" * 60)
        print("DELIVERY METRICS REPORT")
        print("=" * 60)
        print(f"  Successful deliveries: {self.successes}")
        print(f"  Failed deliveries:     {self.failures}")
        print(f"  Total:                 {self.successes + self.failures}")
        print()
        print("  Latency:")
        print(f"    Average: {avg_latency:.4f}s")
        print(f"    Min:     {min_latency:.4f}s")
        print(f"    Max:     {max_latency:.4f}s")
        print()
        print("  Per-Partition Counts:")
        for partition in sorted(self.partition_counts):
            count = self.partition_counts[partition]
            bar = "#" * (count // 2)
            print(f"    Partition {partition}: {count:4d} {bar}")
        print("=" * 60)


def generate_event(index):
    """Generate a fake metric event.

    Args:
        index: The message sequence number.

    Returns:
        tuple: (key_str, event_dict)
    """
    service = fake.random_element(["api-gateway", "auth-service", "order-service", "user-service"])
    event = {
        "event_id": f"evt-{index:05d}",
        "service": service,
        "metric": fake.random_element(["latency", "error_rate", "throughput", "cpu_usage"]),
        "value": round(fake.pyfloat(min_value=0.0, max_value=100.0), 2),
        "unit": fake.random_element(["ms", "percent", "req/s", "percent"]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return service, event


def main():
    """Produce metric events and report delivery statistics."""
    print(f"Metrics Producer -> topic '{TOPIC}' ({NUM_MESSAGES} messages)")
    print("-" * 60)

    metrics = DeliveryMetrics()

    producer = Producer({
        "bootstrap.servers": BROKER,
        "client.id": "metrics-producer",
        "acks": "all",
        "enable.idempotence": True,
        "compression.type": "gzip",
        "linger.ms": 100,
        "batch.size": 32768,
        "retries": 5,
        "delivery.timeout.ms": 30000,
    })

    try:
        for i in range(NUM_MESSAGES):
            key, event = generate_event(i)
            producer.produce(
                topic=TOPIC,
                key=key.encode("utf-8"),
                value=json.dumps(event).encode("utf-8"),
                callback=metrics.on_delivery,
            )
            producer.poll(0)

            if (i + 1) % 25 == 0:
                print(f"  Produced {i + 1}/{NUM_MESSAGES} messages...")

        print("Flushing...")
        producer.flush(timeout=15)
        metrics.report()

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted. Flushing...")
        producer.flush(timeout=5)
        metrics.report()


if __name__ == "__main__":
    main()
