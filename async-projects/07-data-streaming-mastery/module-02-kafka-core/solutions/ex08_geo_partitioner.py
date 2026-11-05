#!/usr/bin/env python3
"""
Solution: Exercise 3.2 -- Custom Partitioner: Geographic Routing
=================================================================

Implements a geographic partitioner that routes messages to specific
partitions based on country code. Includes both a producer that uses
the partitioner and a consumer that verifies correct routing.

Usage:
    python ex08_geo_partitioner.py

Partition Mapping:
    - Partition 0: Americas (US, CA, BR, MX, AR)
    - Partition 1: Europe (GB, DE, FR, ES, IT)
    - Partition 2: Asia-Pacific (JP, AU, IN, KR, SG)
"""

import hashlib
import json
import signal
import sys
import time
from collections import defaultdict

from confluent_kafka import Producer, Consumer, KafkaError, KafkaException
from faker import Faker

BROKER = "localhost:9092"
TOPIC = "geo-events"
NUM_MESSAGES = 100
NUM_PARTITIONS = 3
GROUP_ID = "geo-analysis-group"

fake = Faker()
running = True

# Geographic region to partition mapping
REGION_MAP = {
    # Americas -> Partition 0
    "US": 0, "CA": 0, "BR": 0, "MX": 0, "AR": 0,
    # Europe -> Partition 1
    "GB": 1, "DE": 1, "FR": 1, "ES": 1, "IT": 1,
    # Asia-Pacific -> Partition 2
    "JP": 2, "AU": 2, "IN": 2, "KR": 2, "SG": 2,
}

REGION_NAMES = {
    0: "Americas",
    1: "Europe",
    2: "Asia-Pacific",
}


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def geo_partitioner(country_code, num_partitions):
    """Route a message to a partition based on country code.

    Known countries are mapped to their region's partition. Unknown
    countries use a hash-based fallback.

    Args:
        country_code: Two-letter ISO country code (e.g., 'US').
        num_partitions: Total number of partitions.

    Returns:
        int: Target partition number.
    """
    if country_code in REGION_MAP:
        return REGION_MAP[country_code]

    # Hash-based fallback for unknown countries
    digest = hashlib.md5(country_code.encode("utf-8")).hexdigest()
    return int(digest, 16) % num_partitions


def generate_geo_event(index):
    """Generate a fake event with a country code.

    Args:
        index: Event sequence number.

    Returns:
        tuple: (country_code, event_dict)
    """
    country_code = fake.country_code()
    event = {
        "event_id": f"geo-{index:04d}",
        "country_code": country_code,
        "city": fake.city(),
        "user_id": f"user-{fake.random_int(min=100, max=999)}",
        "action": fake.random_element(["login", "purchase", "browse", "logout"]),
        "amount": round(fake.pyfloat(min_value=1.0, max_value=500.0), 2),
    }
    return country_code, event


# ---------------------------------------------------------------------------
# Phase 1: Produce
# ---------------------------------------------------------------------------
def produce_messages():
    """Produce geo-tagged events using the geographic partitioner.

    Returns:
        dict: Mapping of country_code -> expected_partition for verification.
    """
    print("=" * 50)
    print("Phase 1: Producing Geo-Tagged Events")
    print("=" * 50)

    expected_routing = {}  # country_code -> partition
    delivered = 0

    def on_delivery(err, msg):
        nonlocal delivered
        if err:
            print(f"  [FAIL] {err}")
        else:
            delivered += 1

    producer = Producer({
        "bootstrap.servers": BROKER,
        "client.id": "geo-producer",
        "acks": "all",
    })

    try:
        for i in range(NUM_MESSAGES):
            country_code, event = generate_geo_event(i)
            partition = geo_partitioner(country_code, NUM_PARTITIONS)
            expected_routing[country_code] = partition

            region = REGION_NAMES.get(partition, f"unknown(p{partition})")
            if REGION_MAP.get(country_code) is not None:
                routing_type = "mapped"
            else:
                routing_type = "hashed"

            producer.produce(
                topic=TOPIC,
                key=country_code.encode("utf-8"),
                value=json.dumps(event).encode("utf-8"),
                partition=partition,
                callback=on_delivery,
            )
            producer.poll(0)

        producer.flush(timeout=15)
        print(f"  Delivered {delivered}/{NUM_MESSAGES} messages.\n")
        return expected_routing

    except KafkaException as e:
        print(f"  Error: {e}", file=sys.stderr)
        return expected_routing


# ---------------------------------------------------------------------------
# Phase 2: Consume and Verify
# ---------------------------------------------------------------------------
def consume_and_verify(expected_routing):
    """Consume all messages and verify geographic routing.

    Args:
        expected_routing: Dict of country_code -> expected partition.
    """
    print("=" * 50)
    print("Phase 2: Consuming and Verifying Routing")
    print("=" * 50)

    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    partition_counts = defaultdict(int)
    partition_countries = defaultdict(set)
    misrouted = []
    consumed = 0
    empty_polls = 0

    try:
        consumer.subscribe([TOPIC])

        while running and consumed < NUM_MESSAGES and empty_polls < 10:
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

            partition = msg.partition()
            value = json.loads(msg.value().decode("utf-8"))
            country = value.get("country_code", "??")

            partition_counts[partition] += 1
            partition_countries[partition].add(country)

            expected = expected_routing.get(country)
            if expected is not None and expected != partition:
                misrouted.append({
                    "country": country,
                    "expected": expected,
                    "actual": partition,
                    "offset": msg.offset(),
                })

        # Report
        print(f"\n  Consumed {consumed} messages.\n")
        print("=" * 50)
        print("Geographic Routing Report")
        print("=" * 50)

        for p in sorted(partition_counts):
            region = REGION_NAMES.get(p, "Unknown")
            countries = sorted(partition_countries[p])
            known = [c for c in countries if c in REGION_MAP]
            unknown = [c for c in countries if c not in REGION_MAP]

            print(f"\n  Partition {p} ({region}): {partition_counts[p]} messages")
            if known:
                print(f"    Known countries:   {', '.join(known)}")
            if unknown:
                print(f"    Hashed countries:  {', '.join(unknown)}")

        print(f"\n  Routing Verification:")
        if misrouted:
            print(f"    FAILED -- {len(misrouted)} misrouted messages:")
            for m in misrouted[:5]:
                print(
                    f"      country={m['country']} expected=p{m['expected']} "
                    f"actual=p{m['actual']}"
                )
        else:
            print("    PASSED -- All messages routed correctly.")

        print("=" * 50)

    except KafkaException as e:
        print(f"  Error: {e}", file=sys.stderr)

    finally:
        consumer.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    """Run geographic partitioning demo: produce then verify."""
    print(f"Geographic Partitioner Demo: {NUM_MESSAGES} events -> {TOPIC}")
    print("-" * 50)

    expected_routing = produce_messages()
    time.sleep(1)
    consume_and_verify(expected_routing)


if __name__ == "__main__":
    main()
