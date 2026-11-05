#!/usr/bin/env python3
"""
Solution: Exercise 1.3 -- Multi-Topic Event Router
====================================================

Produces fake events of three types (order, payment, notification) and
routes each to its own Kafka topic. Includes message headers with metadata.

Usage:
    python ex03_event_router.py
"""

import json
import random
import sys
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer, KafkaException
from faker import Faker

BROKER = "localhost:9092"
NUM_MESSAGES = 30

TOPIC_MAP = {
    "order": "orders-topic",
    "payment": "payments-topic",
    "notification": "notifications-topic",
}

fake = Faker()

stats = {"sent": 0, "delivered": 0, "failed": 0}


def delivery_callback(err, msg):
    """Track delivery results.

    Args:
        err: KafkaError on failure, None on success.
        msg: The produced Message object.
    """
    if err:
        stats["failed"] += 1
        print(f"  [FAIL] topic={msg.topic()} error={err}")
    else:
        stats["delivered"] += 1
        print(
            f"  [OK] topic={msg.topic()} partition={msg.partition()} "
            f"offset={msg.offset()}"
        )


def generate_order_event(correlation_id):
    """Generate a fake order event.

    Args:
        correlation_id: Shared correlation ID for tracing.

    Returns:
        dict: An order event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "order",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "order_id": f"ORD-{fake.random_int(min=10000, max=99999)}",
        "customer_id": f"CUST-{fake.random_int(min=1000, max=9999)}",
        "items": [
            {"product": fake.word(), "quantity": random.randint(1, 5), "price": round(random.uniform(5.0, 200.0), 2)}
            for _ in range(random.randint(1, 4))
        ],
        "total_amount": round(random.uniform(10.0, 500.0), 2),
    }


def generate_payment_event(correlation_id):
    """Generate a fake payment event.

    Args:
        correlation_id: Shared correlation ID for tracing.

    Returns:
        dict: A payment event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "payment",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "payment_id": f"PAY-{fake.random_int(min=10000, max=99999)}",
        "order_id": f"ORD-{fake.random_int(min=10000, max=99999)}",
        "amount": round(random.uniform(10.0, 500.0), 2),
        "method": fake.random_element(["credit_card", "debit_card", "paypal", "bank_transfer"]),
        "status": fake.random_element(["pending", "completed", "failed"]),
    }


def generate_notification_event(correlation_id):
    """Generate a fake notification event.

    Args:
        correlation_id: Shared correlation ID for tracing.

    Returns:
        dict: A notification event.
    """
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "notification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id,
        "notification_id": f"NOTIF-{fake.random_int(min=10000, max=99999)}",
        "user_id": f"USER-{fake.random_int(min=1000, max=9999)}",
        "channel": fake.random_element(["email", "sms", "push", "in_app"]),
        "message": fake.sentence(nb_words=10),
    }


EVENT_GENERATORS = {
    "order": generate_order_event,
    "payment": generate_payment_event,
    "notification": generate_notification_event,
}


def main():
    """Route events to different topics based on event type."""
    print("Multi-Topic Event Router")
    print(f"  Topics: {list(TOPIC_MAP.values())}")
    print(f"  Messages: {NUM_MESSAGES}")
    print("-" * 60)

    producer = Producer({
        "bootstrap.servers": BROKER,
        "client.id": "event-router",
        "acks": "all",
        "linger.ms": 50,
        "compression.type": "snappy",
    })

    event_types = list(TOPIC_MAP.keys())

    try:
        for i in range(NUM_MESSAGES):
            event_type = random.choice(event_types)
            correlation_id = str(uuid.uuid4())
            topic = TOPIC_MAP[event_type]

            event = EVENT_GENERATORS[event_type](correlation_id)
            value_bytes = json.dumps(event).encode("utf-8")

            print(
                f"[{i + 1}/{NUM_MESSAGES}] type={event_type} -> {topic} "
                f"correlation={correlation_id[:8]}..."
            )

            producer.produce(
                topic=topic,
                key=event.get("customer_id", event.get("user_id", event_type)).encode("utf-8"),
                value=value_bytes,
                headers={
                    "event_type": event_type.encode("utf-8"),
                    "source_service": b"event-router",
                    "correlation_id": correlation_id.encode("utf-8"),
                },
                callback=delivery_callback,
            )
            producer.poll(0)
            stats["sent"] += 1
            time.sleep(0.2)

        producer.flush(timeout=15)

        print("\n" + "=" * 60)
        print("Event Routing Summary")
        print(f"  Sent:      {stats['sent']}")
        print(f"  Delivered: {stats['delivered']}")
        print(f"  Failed:    {stats['failed']}")
        print("=" * 60)

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted. Flushing...")
        producer.flush(timeout=5)


if __name__ == "__main__":
    main()
