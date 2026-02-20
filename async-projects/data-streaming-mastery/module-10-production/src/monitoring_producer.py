"""
Monitoring Producer - Generates configurable load for Kafka monitoring demos.

This producer sends messages at a configurable rate to demonstrate Kafka monitoring
with Prometheus and Grafana. It exposes its own Prometheus metrics (messages sent,
send latency) on port 8000 for scraping.

Usage:
    python src/monitoring_producer.py

    # Custom configuration via environment variables:
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
    TOPIC=monitoring-demo \
    MESSAGES_PER_SECOND=100 \
    MESSAGE_SIZE_BYTES=1024 \
    DURATION_SECONDS=300 \
    python src/monitoring_producer.py

Prometheus metrics exposed on http://localhost:8000/metrics:
    - kafka_messages_sent_total: Counter of total messages sent
    - kafka_send_latency_seconds: Histogram of send latency
    - kafka_send_errors_total: Counter of send errors
"""

import json
import os
import sys
import time
import signal
import logging
from datetime import datetime, timezone

from confluent_kafka import Producer, KafkaError
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from faker import Faker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC = os.getenv("TOPIC", "monitoring-demo")
MESSAGES_PER_SECOND = int(os.getenv("MESSAGES_PER_SECOND", "50"))
MESSAGE_SIZE_BYTES = int(os.getenv("MESSAGE_SIZE_BYTES", "512"))
DURATION_SECONDS = int(os.getenv("DURATION_SECONDS", "600"))
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8000"))

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
# Prometheus Metrics
# ---------------------------------------------------------------------------

MESSAGES_SENT = Counter(
    "kafka_messages_sent_total",
    "Total number of messages successfully sent to Kafka",
    ["topic"],
)

SEND_LATENCY = Histogram(
    "kafka_send_latency_seconds",
    "Histogram of message send latency in seconds",
    ["topic"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

SEND_ERRORS = Counter(
    "kafka_send_errors_total",
    "Total number of message send errors",
    ["topic", "error_type"],
)

MESSAGES_IN_BUFFER = Gauge(
    "kafka_producer_messages_in_buffer",
    "Number of messages currently in the producer buffer",
)

# ---------------------------------------------------------------------------
# Shutdown handling
# ---------------------------------------------------------------------------

shutdown_requested = False


def handle_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info("Shutdown signal received (signal %d). Finishing current batch...", signum)
    shutdown_requested = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# ---------------------------------------------------------------------------
# Message generation
# ---------------------------------------------------------------------------

fake = Faker()


def generate_message(target_size_bytes):
    """
    Generate a JSON message of approximately the target size.

    The message contains realistic-looking event data with a timestamp,
    user information, and a payload field sized to reach the target bytes.

    Args:
        target_size_bytes: Approximate size of the serialized JSON message.

    Returns:
        Tuple of (key_bytes, value_bytes) ready for producing.
    """
    base_message = {
        "event_id": fake.uuid4(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": fake.uuid4()[:8],
        "user_name": fake.name(),
        "event_type": fake.random_element(["page_view", "click", "purchase", "signup", "logout"]),
        "source": fake.random_element(["web", "mobile_ios", "mobile_android", "api"]),
        "ip_address": fake.ipv4(),
        "user_agent": fake.user_agent()[:80],
    }

    # Calculate how much padding we need to reach the target size
    base_size = len(json.dumps(base_message).encode("utf-8"))
    padding_needed = max(0, target_size_bytes - base_size - 20)  # 20 bytes for the key overhead
    if padding_needed > 0:
        base_message["payload"] = "x" * padding_needed

    key = base_message["user_id"].encode("utf-8")
    value = json.dumps(base_message).encode("utf-8")
    return key, value


# ---------------------------------------------------------------------------
# Delivery callback
# ---------------------------------------------------------------------------


def delivery_callback(err, msg):
    """
    Called once for each message produced, to indicate delivery result.

    Args:
        err: Error object if delivery failed, None on success.
        msg: The message that was produced.
    """
    if err is not None:
        error_type = str(err.code()) if isinstance(err, KafkaError) else str(type(err).__name__)
        SEND_ERRORS.labels(topic=msg.topic(), error_type=error_type).inc()
        logger.error("Message delivery failed for topic %s: %s", msg.topic(), err)
    else:
        MESSAGES_SENT.labels(topic=msg.topic()).inc()


# ---------------------------------------------------------------------------
# Main producer loop
# ---------------------------------------------------------------------------


def run_producer():
    """
    Run the monitoring producer.

    Creates a Kafka producer, starts the Prometheus metrics server, and
    sends messages at the configured rate for the configured duration.
    Tracks send latency and error counts as Prometheus metrics.
    """
    logger.info("Starting Monitoring Producer")
    logger.info("  Bootstrap servers: %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("  Topic: %s", TOPIC)
    logger.info("  Messages/sec: %d", MESSAGES_PER_SECOND)
    logger.info("  Message size: %d bytes", MESSAGE_SIZE_BYTES)
    logger.info("  Duration: %d seconds", DURATION_SECONDS)
    logger.info("  Prometheus port: %d", PROMETHEUS_PORT)

    # Start Prometheus metrics HTTP server
    start_http_server(PROMETHEUS_PORT)
    logger.info("Prometheus metrics available at http://localhost:%d/metrics", PROMETHEUS_PORT)

    # Create the Kafka producer
    producer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "monitoring-producer",
        "acks": "all",
        "linger.ms": 10,
        "batch.size": 65536,
        "compression.type": "lz4",
        "retries": 3,
        "retry.backoff.ms": 100,
    }
    producer = Producer(producer_config)

    # Calculate sleep interval between messages
    interval = 1.0 / MESSAGES_PER_SECOND if MESSAGES_PER_SECOND > 0 else 0.01

    start_time = time.time()
    total_sent = 0
    total_errors = 0

    logger.info("Producing messages...")
    logger.info("-" * 60)

    try:
        while not shutdown_requested:
            elapsed = time.time() - start_time
            if elapsed >= DURATION_SECONDS:
                logger.info("Duration reached (%d seconds). Stopping.", DURATION_SECONDS)
                break

            # Generate and send a message
            key, value = generate_message(MESSAGE_SIZE_BYTES)

            send_start = time.time()
            try:
                producer.produce(
                    topic=TOPIC,
                    key=key,
                    value=value,
                    callback=delivery_callback,
                )
                send_duration = time.time() - send_start
                SEND_LATENCY.labels(topic=TOPIC).observe(send_duration)
                total_sent += 1
            except BufferError:
                # Producer buffer is full, poll to free space and retry
                logger.warning("Producer buffer full. Polling to free space...")
                producer.poll(1.0)
                SEND_ERRORS.labels(topic=TOPIC, error_type="BufferError").inc()
                total_errors += 1
                continue

            # Update buffer gauge
            MESSAGES_IN_BUFFER.set(len(producer))

            # Poll for delivery callbacks (non-blocking)
            producer.poll(0)

            # Log progress every 10 seconds
            if total_sent % (MESSAGES_PER_SECOND * 10) == 0 and total_sent > 0:
                rate = total_sent / elapsed if elapsed > 0 else 0
                logger.info(
                    "Progress: %d messages sent | %.1f msg/sec | %.0f seconds elapsed",
                    total_sent,
                    rate,
                    elapsed,
                )

            # Throttle to target rate
            time.sleep(interval)

    finally:
        # Flush remaining messages
        logger.info("Flushing remaining messages...")
        remaining = producer.flush(timeout=30)
        if remaining > 0:
            logger.warning("%d messages were not delivered", remaining)

        elapsed = time.time() - start_time
        rate = total_sent / elapsed if elapsed > 0 else 0

        logger.info("-" * 60)
        logger.info("Producer stopped.")
        logger.info("  Total messages sent: %d", total_sent)
        logger.info("  Total errors: %d", total_errors)
        logger.info("  Duration: %.1f seconds", elapsed)
        logger.info("  Average rate: %.1f messages/sec", rate)
        logger.info(
            "  Average throughput: %.2f KB/sec",
            (total_sent * MESSAGE_SIZE_BYTES) / elapsed / 1024 if elapsed > 0 else 0,
        )


if __name__ == "__main__":
    run_producer()
