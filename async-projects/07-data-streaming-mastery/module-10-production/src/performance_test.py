"""
Performance Test - Benchmarks Kafka producer throughput under different configurations.

This script produces N messages of configurable size and measures throughput
(messages/sec, MB/sec) with different producer configurations:
  1. acks=0 (fire-and-forget) vs acks=all (full durability)
  2. With and without compression (none, lz4, zstd, snappy, gzip)
  3. Different batch sizes (16KB, 64KB, 128KB)

Results are printed in a formatted table for easy comparison.

Usage:
    python src/performance_test.py

    # Custom configuration:
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
    NUM_MESSAGES=50000 \
    MESSAGE_SIZE_BYTES=1024 \
    python src/performance_test.py
"""

import json
import os
import sys
import time
import logging
from datetime import datetime, timezone

from confluent_kafka import Producer

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC_PREFIX = os.getenv("TOPIC_PREFIX", "perf-test")
NUM_MESSAGES = int(os.getenv("NUM_MESSAGES", "10000"))
MESSAGE_SIZE_BYTES = int(os.getenv("MESSAGE_SIZE_BYTES", "1024"))

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Message generation
# ---------------------------------------------------------------------------


def generate_message(size_bytes):
    """
    Generate a single message of approximately the specified size.

    Creates a JSON message with a fixed structure and pads it to reach
    the target size. The same message is reused for all sends in a test
    to isolate Kafka performance from message generation overhead.

    Args:
        size_bytes: Target size of the serialized message in bytes.

    Returns:
        Bytes of the serialized JSON message.
    """
    base = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "id": 0,
        "src": "perf-test",
    }
    base_size = len(json.dumps(base).encode("utf-8"))
    padding = max(0, size_bytes - base_size - 20)
    base["data"] = "P" * padding
    return json.dumps(base).encode("utf-8")


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def run_benchmark(config_name, producer_config, topic, num_messages, message_bytes):
    """
    Run a single benchmark with the given producer configuration.

    Produces num_messages messages and measures wall-clock time, then
    computes throughput metrics.

    Args:
        config_name: Human-readable name for this configuration.
        producer_config: Dictionary of confluent-kafka Producer configuration.
        topic: Kafka topic to produce to.
        num_messages: Number of messages to send.
        message_bytes: Pre-serialized message bytes to send.

    Returns:
        Dictionary with benchmark results:
        {
            "config": str,
            "messages": int,
            "duration_sec": float,
            "messages_per_sec": float,
            "mb_per_sec": float,
            "errors": int,
        }
    """
    errors = 0
    delivered = 0

    def delivery_cb(err, msg):
        """Track delivery success/failure."""
        nonlocal errors, delivered
        if err is not None:
            errors += 1
        else:
            delivered += 1

    producer = Producer(producer_config)
    message_size = len(message_bytes)
    key = b"perf-key"

    # Warm up: send a few messages to establish connections
    for _ in range(10):
        producer.produce(topic=topic, key=key, value=message_bytes)
    producer.flush(timeout=10)

    # Run the benchmark
    start_time = time.time()

    for i in range(num_messages):
        try:
            producer.produce(
                topic=topic,
                key=key,
                value=message_bytes,
                callback=delivery_cb,
            )
        except BufferError:
            # Buffer full -- poll to make room and retry
            producer.poll(1.0)
            producer.produce(
                topic=topic,
                key=key,
                value=message_bytes,
                callback=delivery_cb,
            )

        # Periodically poll for delivery callbacks to prevent buffer overflow
        if i % 1000 == 0:
            producer.poll(0)

    # Flush all remaining messages and wait for delivery
    producer.flush(timeout=60)

    end_time = time.time()
    duration = end_time - start_time

    messages_per_sec = num_messages / duration if duration > 0 else 0
    total_bytes = num_messages * message_size
    mb_per_sec = (total_bytes / (1024 * 1024)) / duration if duration > 0 else 0

    return {
        "config": config_name,
        "messages": num_messages,
        "duration_sec": duration,
        "messages_per_sec": messages_per_sec,
        "mb_per_sec": mb_per_sec,
        "errors": errors,
    }


def print_results_table(results):
    """
    Print benchmark results in a formatted table.

    Args:
        results: List of result dictionaries from run_benchmark().
    """
    # Header
    header = (
        f"{'Configuration':<40} "
        f"{'Messages':>10} "
        f"{'Duration':>10} "
        f"{'msg/sec':>12} "
        f"{'MB/sec':>10} "
        f"{'Errors':>8}"
    )
    separator = "-" * len(header)

    print()
    print(separator)
    print(header)
    print(separator)

    for r in results:
        print(
            f"{r['config']:<40} "
            f"{r['messages']:>10,} "
            f"{r['duration_sec']:>9.2f}s "
            f"{r['messages_per_sec']:>12,.0f} "
            f"{r['mb_per_sec']:>9.2f} "
            f"{r['errors']:>8,}"
        )

    print(separator)
    print()


# ---------------------------------------------------------------------------
# Test configurations
# ---------------------------------------------------------------------------


def get_test_configurations():
    """
    Define the set of producer configurations to benchmark.

    Returns a list of (name, config_overrides) tuples. Each config_overrides
    dict is merged with the base configuration.

    Returns:
        List of (config_name, config_dict) tuples.
    """
    base_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "perf-test",
        "linger.ms": 5,
        "batch.size": 65536,
    }

    configs = []

    # Test 1: acks comparison
    for acks in ["0", "1", "all"]:
        name = f"acks={acks}, no compression"
        config = {**base_config, "acks": acks, "compression.type": "none"}
        configs.append((name, config))

    # Test 2: Compression comparison (with acks=all)
    for compression in ["none", "lz4", "zstd", "snappy", "gzip"]:
        name = f"acks=all, compression={compression}"
        config = {**base_config, "acks": "all", "compression.type": compression}
        configs.append((name, config))

    # Test 3: Batch size comparison (with acks=all, lz4)
    for batch_size in [16384, 65536, 131072, 262144]:
        batch_kb = batch_size // 1024
        name = f"acks=all, lz4, batch={batch_kb}KB"
        config = {
            **base_config,
            "acks": "all",
            "compression.type": "lz4",
            "batch.size": batch_size,
        }
        configs.append((name, config))

    # Test 4: Linger.ms comparison (with acks=all, lz4, 64KB batch)
    for linger in [0, 5, 20, 50, 100]:
        name = f"acks=all, lz4, linger={linger}ms"
        config = {
            **base_config,
            "acks": "all",
            "compression.type": "lz4",
            "batch.size": 65536,
            "linger.ms": linger,
        }
        configs.append((name, config))

    return configs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_performance_tests():
    """
    Run all performance benchmarks and print results.

    Iterates through different producer configurations, runs each benchmark,
    collects results, and prints a comparison table.
    """
    logger.info("=" * 70)
    logger.info("Kafka Producer Performance Benchmark")
    logger.info("=" * 70)
    logger.info("Configuration:")
    logger.info("  Bootstrap servers: %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("  Messages per test: %d", NUM_MESSAGES)
    logger.info("  Message size: %d bytes", MESSAGE_SIZE_BYTES)
    logger.info("  Total data per test: %.2f MB", NUM_MESSAGES * MESSAGE_SIZE_BYTES / (1024 * 1024))
    logger.info("")

    # Pre-generate the message to avoid measuring serialization time
    message_bytes = generate_message(MESSAGE_SIZE_BYTES)
    actual_size = len(message_bytes)
    logger.info("Actual message size: %d bytes", actual_size)

    configurations = get_test_configurations()
    logger.info("Running %d benchmark configurations...", len(configurations))
    logger.info("")

    results = []

    for i, (config_name, config) in enumerate(configurations, 1):
        topic = f"{TOPIC_PREFIX}-{i}"
        logger.info("[%d/%d] Running: %s", i, len(configurations), config_name)

        try:
            result = run_benchmark(config_name, config, topic, NUM_MESSAGES, message_bytes)
            results.append(result)
            logger.info(
                "  -> %.0f msg/sec, %.2f MB/sec (%.2fs)",
                result["messages_per_sec"],
                result["mb_per_sec"],
                result["duration_sec"],
            )
        except Exception as e:
            logger.error("  -> FAILED: %s", e)
            results.append({
                "config": config_name,
                "messages": NUM_MESSAGES,
                "duration_sec": 0,
                "messages_per_sec": 0,
                "mb_per_sec": 0,
                "errors": NUM_MESSAGES,
            })

        # Brief pause between tests to let the broker stabilize
        time.sleep(1)

    # Print final results
    logger.info("")
    logger.info("=" * 70)
    logger.info("RESULTS")
    logger.info("=" * 70)
    print_results_table(results)

    # Find the best configuration
    if results:
        best = max(results, key=lambda r: r["messages_per_sec"])
        logger.info("Best throughput: %s", best["config"])
        logger.info(
            "  %.0f messages/sec, %.2f MB/sec",
            best["messages_per_sec"],
            best["mb_per_sec"],
        )

    logger.info("")
    logger.info("Performance Test Complete")


if __name__ == "__main__":
    run_performance_tests()
