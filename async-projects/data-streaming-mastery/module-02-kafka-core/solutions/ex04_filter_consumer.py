#!/usr/bin/env python3
"""
Solution: Exercise 2.1 -- JSON Message Consumer with Filtering
===============================================================

Consumes sensor readings and filters for high temperature alerts
(temperature > 30.0). Tracks total messages read vs alerts triggered.

Usage:
    python ex04_filter_consumer.py
"""

import json
import signal
import sys

from confluent_kafka import Consumer, KafkaError, KafkaException

BROKER = "localhost:9092"
TOPIC = "sensor-readings"
GROUP_ID = "sensor-alert-group"
TEMP_THRESHOLD = 30.0

running = True


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global running
    print("\nShutting down...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def process_reading(value_str):
    """Parse and evaluate a sensor reading for alerts.

    Args:
        value_str: JSON string of the sensor reading.

    Returns:
        tuple: (is_alert: bool, reading: dict or None, error: str or None)
    """
    try:
        reading = json.loads(value_str)
    except (json.JSONDecodeError, TypeError) as e:
        return False, None, f"Malformed JSON: {e}"

    required_fields = ["sensor_id", "temperature", "location", "timestamp"]
    for field in required_fields:
        if field not in reading:
            return False, reading, f"Missing field: {field}"

    try:
        temp = float(reading["temperature"])
    except (ValueError, TypeError):
        return False, reading, f"Invalid temperature: {reading['temperature']}"

    is_alert = temp > TEMP_THRESHOLD
    return is_alert, reading, None


def main():
    """Consume sensor readings and filter for high-temperature alerts."""
    print(f"Sensor Alert Consumer")
    print(f"  Topic: {TOPIC}, Group: {GROUP_ID}")
    print(f"  Alert threshold: temperature > {TEMP_THRESHOLD}")
    print("-" * 60)
    print("Waiting for messages... (Ctrl+C to exit)\n")

    consumer = Consumer({
        "bootstrap.servers": BROKER,
        "group.id": GROUP_ID,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    total_read = 0
    alerts = 0
    errors = 0

    try:
        consumer.subscribe([TOPIC])

        while running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            total_read += 1
            value_str = msg.value().decode("utf-8") if msg.value() else None

            is_alert, reading, error = process_reading(value_str)

            if error:
                errors += 1
                print(f"  [ERROR] offset={msg.offset()} -- {error}")
                continue

            if is_alert:
                alerts += 1
                print(
                    f"  [ALERT] sensor={reading['sensor_id']} "
                    f"temp={reading['temperature']} "
                    f"location={reading['location']} "
                    f"time={reading['timestamp']}"
                )

    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        print(f"\nSummary:")
        print(f"  Total read:  {total_read}")
        print(f"  Alerts:      {alerts}")
        print(f"  Errors:      {errors}")
        print(f"  Normal:      {total_read - alerts - errors}")
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
