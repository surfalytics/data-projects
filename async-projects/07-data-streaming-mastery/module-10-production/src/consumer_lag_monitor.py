"""
Consumer Lag Monitor - Monitors consumer group lag using confluent-kafka AdminClient.

This script periodically checks the lag of all consumer groups and reports:
- Per-partition lag (difference between log end offset and committed offset)
- Total lag per consumer group
- Optionally exposes lag as Prometheus metrics

Usage:
    python src/consumer_lag_monitor.py

    # Custom configuration:
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
    POLL_INTERVAL=10 \
    EXPOSE_PROMETHEUS=true \
    PROMETHEUS_PORT=8001 \
    python src/consumer_lag_monitor.py
"""

import os
import sys
import time
import signal
import logging
from collections import defaultdict

from confluent_kafka import Consumer, TopicPartition
from confluent_kafka.admin import AdminClient
from prometheus_client import Gauge, start_http_server

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
EXPOSE_PROMETHEUS = os.getenv("EXPOSE_PROMETHEUS", "true").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "8001"))

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

CONSUMER_LAG = Gauge(
    "kafka_consumer_group_lag",
    "Consumer group lag per partition",
    ["group", "topic", "partition"],
)

CONSUMER_LAG_TOTAL = Gauge(
    "kafka_consumer_group_lag_total",
    "Total consumer group lag across all partitions",
    ["group"],
)

CONSUMER_GROUP_MEMBERS = Gauge(
    "kafka_consumer_group_members",
    "Number of members in a consumer group",
    ["group"],
)

# ---------------------------------------------------------------------------
# Shutdown handling
# ---------------------------------------------------------------------------

shutdown_requested = False


def handle_signal(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info("Shutdown signal received. Stopping...")
    shutdown_requested = True


signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)


# ---------------------------------------------------------------------------
# Lag calculation
# ---------------------------------------------------------------------------


def get_consumer_groups(admin_client):
    """
    List all consumer groups in the Kafka cluster.

    Args:
        admin_client: confluent_kafka AdminClient instance.

    Returns:
        List of consumer group IDs (strings).
    """
    future = admin_client.list_consumer_groups()
    result = future.result()

    groups = []
    for group in result.valid:
        groups.append(group.group_id)
    return groups


def get_consumer_group_lag(admin_client, group_id):
    """
    Calculate the lag for each partition in a consumer group.

    For each topic-partition the group has committed offsets for, this function
    computes: lag = log_end_offset - committed_offset.

    Args:
        admin_client: confluent_kafka AdminClient instance.
        group_id: The consumer group ID to check.

    Returns:
        Dictionary with structure:
        {
            "group_id": str,
            "total_lag": int,
            "partitions": [
                {
                    "topic": str,
                    "partition": int,
                    "committed_offset": int,
                    "log_end_offset": int,
                    "lag": int,
                }
            ]
        }
    """
    # Get committed offsets for the consumer group
    try:
        future = admin_client.list_consumer_group_offsets([group_id])
        offsets_result = future[group_id].result()
    except Exception as e:
        logger.warning("Failed to get offsets for group '%s': %s", group_id, e)
        return {"group_id": group_id, "total_lag": 0, "partitions": []}

    if not offsets_result.topic_partitions:
        return {"group_id": group_id, "total_lag": 0, "partitions": []}

    # Filter out partitions with no committed offset
    committed_partitions = [
        tp for tp in offsets_result.topic_partitions
        if tp.offset >= 0
    ]

    if not committed_partitions:
        return {"group_id": group_id, "total_lag": 0, "partitions": []}

    # Get log end offsets (watermark offsets) for each partition
    # We need a temporary consumer to call get_watermark_offsets
    temp_consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": f"_lag-monitor-{group_id}-temp",
        "enable.auto.commit": False,
        "auto.offset.reset": "latest",
    })

    partition_details = []
    total_lag = 0

    try:
        for tp in committed_partitions:
            try:
                low, high = temp_consumer.get_watermark_offsets(
                    TopicPartition(tp.topic, tp.partition),
                    timeout=5.0,
                )
                lag = max(0, high - tp.offset)
                partition_details.append({
                    "topic": tp.topic,
                    "partition": tp.partition,
                    "committed_offset": tp.offset,
                    "log_end_offset": high,
                    "lag": lag,
                })
                total_lag += lag
            except Exception as e:
                logger.warning(
                    "Failed to get watermark for %s-%d: %s",
                    tp.topic, tp.partition, e,
                )
    finally:
        temp_consumer.close()

    return {
        "group_id": group_id,
        "total_lag": total_lag,
        "partitions": partition_details,
    }


def format_lag_report(lag_data):
    """
    Format lag data into a human-readable report string.

    Args:
        lag_data: Dictionary returned by get_consumer_group_lag().

    Returns:
        Formatted string report.
    """
    lines = []
    lines.append(f"  Group: {lag_data['group_id']}")
    lines.append(f"  Total Lag: {lag_data['total_lag']:,} messages")

    if lag_data["partitions"]:
        # Group by topic
        by_topic = defaultdict(list)
        for p in lag_data["partitions"]:
            by_topic[p["topic"]].append(p)

        for topic, partitions in sorted(by_topic.items()):
            topic_lag = sum(p["lag"] for p in partitions)
            lines.append(f"    Topic: {topic} (total lag: {topic_lag:,})")
            for p in sorted(partitions, key=lambda x: x["partition"]):
                lag_indicator = ""
                if p["lag"] > 10000:
                    lag_indicator = " *** HIGH LAG ***"
                elif p["lag"] > 1000:
                    lag_indicator = " * elevated *"
                lines.append(
                    f"      Partition {p['partition']:3d}: "
                    f"committed={p['committed_offset']:>12,}  "
                    f"end={p['log_end_offset']:>12,}  "
                    f"lag={p['lag']:>10,}{lag_indicator}"
                )
    else:
        lines.append("    No committed offsets found")

    return "\n".join(lines)


def update_prometheus_metrics(lag_data):
    """
    Update Prometheus gauge metrics with the latest lag data.

    Args:
        lag_data: Dictionary returned by get_consumer_group_lag().
    """
    group_id = lag_data["group_id"]
    CONSUMER_LAG_TOTAL.labels(group=group_id).set(lag_data["total_lag"])

    for p in lag_data["partitions"]:
        CONSUMER_LAG.labels(
            group=group_id,
            topic=p["topic"],
            partition=str(p["partition"]),
        ).set(p["lag"])


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run_monitor():
    """
    Run the consumer lag monitor.

    Periodically queries all consumer groups, computes per-partition lag,
    prints a report, and optionally updates Prometheus metrics.
    """
    logger.info("Starting Consumer Lag Monitor")
    logger.info("  Bootstrap servers: %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("  Poll interval: %d seconds", POLL_INTERVAL)
    logger.info("  Prometheus export: %s", EXPOSE_PROMETHEUS)

    if EXPOSE_PROMETHEUS:
        start_http_server(PROMETHEUS_PORT)
        logger.info("Prometheus metrics at http://localhost:%d/metrics", PROMETHEUS_PORT)

    admin_client = AdminClient({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
    })

    logger.info("Monitoring consumer group lag (Ctrl+C to stop)...")
    logger.info("=" * 70)

    while not shutdown_requested:
        try:
            groups = get_consumer_groups(admin_client)

            if not groups:
                logger.info("No consumer groups found.")
            else:
                logger.info(
                    "Found %d consumer group(s) at %s",
                    len(groups),
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                )
                logger.info("-" * 70)

                for group_id in sorted(groups):
                    # Skip internal consumer groups
                    if group_id.startswith("_"):
                        continue

                    lag_data = get_consumer_group_lag(admin_client, group_id)
                    report = format_lag_report(lag_data)
                    logger.info("\n%s", report)

                    if EXPOSE_PROMETHEUS:
                        update_prometheus_metrics(lag_data)

                logger.info("=" * 70)

        except Exception as e:
            logger.error("Error during lag check: %s", e)

        # Wait for the next poll interval
        for _ in range(POLL_INTERVAL):
            if shutdown_requested:
                break
            time.sleep(1)

    logger.info("Consumer Lag Monitor stopped.")


if __name__ == "__main__":
    run_monitor()
