#!/usr/bin/env python3
"""
Solution: Exercise 1.1 -- Sensor Data Producer
================================================

Produces simulated IoT sensor readings as JSON messages to the
'sensor-readings' topic. Uses sensor_id as the message key to ensure
all readings from the same sensor land in the same partition.

Usage:
    python ex01_sensor_producer.py
"""

import json
import random
import sys
import time
from datetime import datetime, timezone

from confluent_kafka import Producer, KafkaException

BROKER = "localhost:9092"
TOPIC = "sensor-readings"
NUM_MESSAGES = 30
NUM_SENSORS = 5
DELAY_SECONDS = 0.5

LOCATIONS = [
    "building-A-floor-1",
    "building-A-floor-2",
    "building-A-floor-3",
    "building-B-floor-1",
    "building-B-floor-2",
]

# Delivery stats
stats = {"delivered": 0, "failed": 0}


def delivery_callback(err, msg):
    """Log delivery result for each message.

    Args:
        err: KafkaError on failure, None on success.
        msg: The produced Message object.
    """
    if err is not None:
        stats["failed"] += 1
        print(f"  [FAIL] {err}")
    else:
        stats["delivered"] += 1
        print(
            f"  [OK] partition={msg.partition()} offset={msg.offset()} "
            f"key={msg.key().decode('utf-8')}"
        )


def generate_sensor_reading(sensor_id, location):
    """Generate a realistic sensor reading.

    Args:
        sensor_id: The sensor identifier string.
        location: The physical location of the sensor.

    Returns:
        dict: A sensor reading dictionary.
    """
    return {
        "sensor_id": sensor_id,
        "temperature": round(random.uniform(15.0, 35.0), 1),
        "humidity": round(random.uniform(30.0, 90.0), 1),
        "pressure": round(random.uniform(980.0, 1040.0), 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "location": location,
    }


def main():
    """Produce sensor reading messages to Kafka."""
    print(f"Sensor Data Producer -> topic '{TOPIC}'")
    print(f"  Sensors: {NUM_SENSORS}, Messages: {NUM_MESSAGES}")
    print("-" * 50)

    producer = Producer({
        "bootstrap.servers": BROKER,
        "client.id": "sensor-producer",
        "acks": "1",
        "linger.ms": 50,
    })

    # Map each sensor to a fixed location
    sensors = {
        f"sensor-{i:03d}": LOCATIONS[i % len(LOCATIONS)]
        for i in range(NUM_SENSORS)
    }

    try:
        for i in range(NUM_MESSAGES):
            sensor_id = f"sensor-{i % NUM_SENSORS:03d}"
            location = sensors[sensor_id]
            reading = generate_sensor_reading(sensor_id, location)

            print(
                f"[{i + 1}/{NUM_MESSAGES}] sensor={sensor_id} "
                f"temp={reading['temperature']} humidity={reading['humidity']}"
            )

            producer.produce(
                topic=TOPIC,
                key=sensor_id.encode("utf-8"),
                value=json.dumps(reading).encode("utf-8"),
                callback=delivery_callback,
            )
            producer.poll(0)
            time.sleep(DELAY_SECONDS)

        remaining = producer.flush(timeout=10)

        print("\n" + "=" * 50)
        print(f"Delivered: {stats['delivered']}")
        print(f"Failed:    {stats['failed']}")
        if remaining > 0:
            print(f"Unflushed: {remaining}")

    except BufferError:
        print("ERROR: Producer buffer full.", file=sys.stderr)
        producer.flush(timeout=5)
        sys.exit(1)
    except KafkaException as e:
        print(f"Kafka error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted. Flushing...")
        producer.flush(timeout=5)


if __name__ == "__main__":
    main()
