#!/usr/bin/env python3
"""
Advanced CDC Event Processor -- filters, tracks schemas, handles tombstones,
and logs statistics.

This processor goes beyond the basic consumer by:
- Filtering events by operation type (e.g., only updates, only deletes).
- Tracking schema changes (new columns appearing / disappearing).
- Properly handling tombstone events.
- Maintaining and printing running statistics.

Usage:
    python src/cdc_event_processor.py
    python src/cdc_event_processor.py --filter-ops c,u
    python src/cdc_event_processor.py --filter-tables customers,orders
"""

import argparse
import json
import os
import signal
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set

from confluent_kafka import Consumer, KafkaError, KafkaException

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
CONSUMER_GROUP = "cdc-event-processor"
TOPIC_PREFIX = "ecommerce.ecommerce."

DEFAULT_TOPICS = [
    f"{TOPIC_PREFIX}customers",
    f"{TOPIC_PREFIX}addresses",
    f"{TOPIC_PREFIX}products",
    f"{TOPIC_PREFIX}orders",
    f"{TOPIC_PREFIX}order_items",
    f"{TOPIC_PREFIX}inventory",
]

OP_LABELS = {"c": "CREATE", "u": "UPDATE", "d": "DELETE", "r": "SNAPSHOT"}


class SchemaTracker:
    """Tracks the columns (fields) seen for each table and detects changes.

    Every time an event arrives, the tracker compares the set of columns in the
    'after' (or 'before' for deletes) against the previously known columns for
    that table.  If the set differs, it logs a schema change.
    """

    def __init__(self) -> None:
        """Initialize with empty schema tracking state."""
        self._schemas: Dict[str, Set[str]] = {}
        self._change_log: List[dict] = []

    def check(self, table: str, row: Optional[dict]) -> Optional[str]:
        """Check if the row's field set differs from the last known schema.

        Args:
            table: The table name.
            row: The 'after' or 'before' dict representing a row.

        Returns:
            A human-readable string describing the schema change, or None if
            the schema has not changed.
        """
        if row is None:
            return None

        current_fields = set(row.keys())

        if table not in self._schemas:
            self._schemas[table] = current_fields
            return None  # First time seeing this table -- no comparison.

        known_fields = self._schemas[table]
        if current_fields == known_fields:
            return None

        added = current_fields - known_fields
        removed = known_fields - current_fields

        parts = []
        if added:
            parts.append(f"new columns: {sorted(added)}")
        if removed:
            parts.append(f"removed columns: {sorted(removed)}")

        change_desc = f"SCHEMA CHANGE on '{table}': {', '.join(parts)}"
        self._change_log.append(
            {
                "table": table,
                "added": sorted(added),
                "removed": sorted(removed),
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Update tracked schema.
        self._schemas[table] = current_fields
        return change_desc

    @property
    def change_log(self) -> List[dict]:
        """Return the full list of detected schema changes."""
        return list(self._change_log)


class EventStatistics:
    """Maintains running counts of CDC events by table and operation."""

    def __init__(self) -> None:
        """Initialize counters."""
        self._counts: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self._tombstones: Dict[str, int] = defaultdict(int)
        self._start_time: float = time.time()
        self._total: int = 0

    def record(self, table: str, op: str) -> None:
        """Record a single CDC event.

        Args:
            table: The source table name.
            op: The operation code (c/u/d/r).
        """
        self._counts[table][op] += 1
        self._total += 1

    def record_tombstone(self, table: str) -> None:
        """Record a tombstone event.

        Args:
            table: The source table name.
        """
        self._tombstones[table] += 1

    @property
    def total(self) -> int:
        """Total number of non-tombstone events processed."""
        return self._total

    def summary(self) -> str:
        """Return a formatted summary of all statistics.

        Returns:
            Multi-line string with a breakdown by table and operation.
        """
        elapsed = time.time() - self._start_time
        lines = [
            "",
            "=" * 70,
            "CDC EVENT PROCESSING STATISTICS",
            "=" * 70,
            f"Total events processed: {self._total}",
            f"Total tombstones:       {sum(self._tombstones.values())}",
            f"Elapsed time:           {elapsed:.1f}s",
            f"Throughput:             {self._total / max(elapsed, 0.001):.1f} events/s",
            "",
            f"{'Table':<20} {'CREATE':>8} {'UPDATE':>8} {'DELETE':>8} {'SNAPSHOT':>10} {'TOMBSTONE':>10} {'Total':>8}",
            "-" * 70,
        ]

        all_tables = sorted(
            set(list(self._counts.keys()) + list(self._tombstones.keys()))
        )
        for table in all_tables:
            ops = self._counts.get(table, {})
            c = ops.get("c", 0)
            u = ops.get("u", 0)
            d = ops.get("d", 0)
            r = ops.get("r", 0)
            t = self._tombstones.get(table, 0)
            total = c + u + d + r
            lines.append(
                f"{table:<20} {c:>8} {u:>8} {d:>8} {r:>10} {t:>10} {total:>8}"
            )

        lines.append("-" * 70)
        lines.append("")
        return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed namespace with filter and display options.
    """
    parser = argparse.ArgumentParser(
        description="Advanced CDC event processor with filtering and statistics."
    )
    parser.add_argument(
        "--filter-ops",
        type=str,
        default="",
        help="Comma-separated operation codes to include (e.g. 'c,u'). Empty = all.",
    )
    parser.add_argument(
        "--filter-tables",
        type=str,
        default="",
        help="Comma-separated table names to include. Empty = all.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Seconds of silence before printing stats and exiting (0 = forever).",
    )
    parser.add_argument(
        "--stats-interval",
        type=int,
        default=50,
        help="Print interim stats every N events.",
    )
    return parser.parse_args()


def extract_table_name(topic: str) -> str:
    """Extract the table name from a Debezium topic.

    Args:
        topic: Full topic name like 'ecommerce.ecommerce.customers'.

    Returns:
        The table name, e.g. 'customers'.
    """
    parts = topic.split(".")
    return parts[-1] if parts else topic


def extract_payload(raw_value: bytes) -> Optional[dict]:
    """Parse a Debezium JSON message and return the payload.

    Args:
        raw_value: Raw Kafka message value bytes.

    Returns:
        The payload dict, or None for tombstones / unparseable messages.
    """
    if raw_value is None:
        return None
    try:
        msg = json.loads(raw_value.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    if "payload" in msg:
        return msg["payload"]
    if "op" in msg:
        return msg
    return None


def main() -> None:
    """Main processing loop."""
    args = parse_args()

    # Build filter sets.
    op_filter: Optional[Set[str]] = None
    if args.filter_ops:
        op_filter = {o.strip() for o in args.filter_ops.split(",")}

    table_filter: Optional[Set[str]] = None
    if args.filter_tables:
        table_filter = {t.strip() for t in args.filter_tables.split(",")}

    # Initialize tracker and stats.
    schema_tracker = SchemaTracker()
    stats = EventStatistics()

    # Set up consumer.
    consumer_config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": CONSUMER_GROUP,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe(DEFAULT_TOPICS)

    print(f"Subscribed to {len(DEFAULT_TOPICS)} topics.")
    if op_filter:
        print(f"Filtering operations: {op_filter}")
    if table_filter:
        print(f"Filtering tables: {table_filter}")
    print("Processing CDC events ...\n")

    # Graceful shutdown on SIGINT / SIGTERM.
    shutdown = False

    def handle_signal(signum, frame):
        nonlocal shutdown
        shutdown = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    empty_polls = 0
    max_empty = int(args.timeout) if args.timeout > 0 else 0

    try:
        while not shutdown:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                if max_empty > 0:
                    empty_polls += 1
                    if empty_polls >= max_empty:
                        print(f"\nNo messages for {args.timeout}s. Finishing up.")
                        break
                continue

            empty_polls = 0

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            topic = msg.topic()
            table = extract_table_name(topic)

            # Table filter.
            if table_filter and table not in table_filter:
                continue

            payload = extract_payload(msg.value())

            # Handle tombstone.
            if payload is None:
                stats.record_tombstone(table)
                key_data = json.loads(msg.key().decode("utf-8")) if msg.key() else {}
                key_payload = key_data.get("payload", key_data)
                print(f"  TOMBSTONE  {table} key={key_payload}")
                continue

            op = payload.get("op", "?")

            # Operation filter.
            if op_filter and op not in op_filter:
                continue

            stats.record(table, op)

            # Schema tracking.
            row = payload.get("after") or payload.get("before")
            schema_change = schema_tracker.check(table, row)
            if schema_change:
                print(f"\n  *** {schema_change} ***\n")

            # Print the event.
            label = OP_LABELS.get(op, f"UNKNOWN({op})")
            source = payload.get("source", {})
            snapshot = source.get("snapshot", "false")
            snap_tag = " [snapshot]" if snapshot not in ("false", False) else ""

            before = payload.get("before")
            after = payload.get("after")
            row_id = (after or before or {}).get("id", "?")

            print(
                f"  {label:<10} {table:<15} #{str(row_id):<6}{snap_tag}"
            )

            # Interim statistics.
            if args.stats_interval > 0 and stats.total % args.stats_interval == 0:
                print(stats.summary())

    finally:
        consumer.close()

    # Final statistics.
    print(stats.summary())

    # Schema change log.
    changes = schema_tracker.change_log
    if changes:
        print("SCHEMA CHANGES DETECTED:")
        for ch in changes:
            print(f"  Table: {ch['table']} | Added: {ch['added']} | "
                  f"Removed: {ch['removed']} | At: {ch['timestamp']}")
    else:
        print("No schema changes detected during this session.")


if __name__ == "__main__":
    main()
