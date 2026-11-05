#!/usr/bin/env python3
"""
IoT Sensor Data Generator — Produces simulated sensor telemetry to a Kafka topic.

This generator simulates a fleet of IoT devices sending periodic readings.
Each device maintains internal state so that readings evolve realistically
over time (gradual drift with occasional anomalies).

Supported device types:
  - thermostat  : temperature in Celsius (baseline ~22 C, drifts +/- 3 C)
  - humidity    : relative humidity in % (baseline ~45%, drifts +/- 10%)
  - pressure    : atmospheric pressure in hPa (baseline ~1013, drifts +/- 5)

Anomaly modes (~2% of readings by default, configurable):
  1. Sudden spike   — reading jumps far outside normal range
  2. Sensor dropout — reading is null (device sent a heartbeat but no data)
  3. Out-of-range   — a physically impossible value (e.g., -999)

Every message contains:
  device_id, device_type, reading (float | null), unit, battery_level,
  location (lat/lng + room/zone), firmware_version, timestamp

Kafka delivery:
  - confluent-kafka Producer with delivery callbacks
  - Messages keyed by device_id for partition affinity

Usage:
  python iot_sensor_generator.py \\
      --speed 10 --duration 600 \\
      --devices 20 --anomaly-rate 0.02 \\
      --kafka-bootstrap-servers localhost:9092 \\
      --topic iot-sensors

Requirements:
  pip install confluent-kafka faker
"""

import argparse
import json
import logging
import random
import signal
import threading
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import Producer
from faker import Faker

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("iot_sensor_generator")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
fake = Faker()
shutdown_event = threading.Event()

DEVICE_TYPES = {
    "thermostat": {"unit": "celsius", "baseline": 22.0, "drift": 3.0, "min": -40.0, "max": 60.0},
    "humidity": {"unit": "percent", "baseline": 45.0, "drift": 10.0, "min": 0.0, "max": 100.0},
    "pressure": {"unit": "hPa", "baseline": 1013.25, "drift": 5.0, "min": 870.0, "max": 1084.0},
}

LOCATIONS = [
    {"zone": "warehouse-A", "lat": 37.7749, "lng": -122.4194},
    {"zone": "warehouse-B", "lat": 37.7750, "lng": -122.4180},
    {"zone": "office-floor-1", "lat": 37.7848, "lng": -122.4294},
    {"zone": "office-floor-2", "lat": 37.7848, "lng": -122.4294},
    {"zone": "server-room", "lat": 37.7849, "lng": -122.4295},
    {"zone": "cold-storage", "lat": 37.7740, "lng": -122.4170},
    {"zone": "loading-dock", "lat": 37.7755, "lng": -122.4200},
    {"zone": "rooftop", "lat": 37.7850, "lng": -122.4290},
]

FIRMWARE_VERSIONS = ["1.0.0", "1.1.0", "1.2.3", "2.0.0-beta", "2.0.1"]


# ---------------------------------------------------------------------------
# Device model
# ---------------------------------------------------------------------------
class IoTDevice:
    """
    Represents a single IoT sensor device with stateful readings.

    The device maintains a current reading that drifts randomly around
    a baseline. Anomalies can override the normal reading.
    """

    def __init__(self, device_id, device_type, location):
        self.device_id = device_id
        self.device_type = device_type
        self.location = location
        self.firmware = random.choice(FIRMWARE_VERSIONS)
        self.battery = round(random.uniform(60.0, 100.0), 1)

        spec = DEVICE_TYPES[device_type]
        self.unit = spec["unit"]
        self.baseline = spec["baseline"]
        self.drift = spec["drift"]
        self.min_val = spec["min"]
        self.max_val = spec["max"]

        # Start near baseline with small random offset
        self.current = self.baseline + random.uniform(-self.drift, self.drift)

    def read(self, anomaly_rate):
        """
        Produce a single sensor reading.

        Returns a dict suitable for JSON serialization.
        """
        # Battery drain
        self.battery = max(0.0, round(self.battery - random.uniform(0.0, 0.02), 2))

        # Decide if this is an anomaly
        is_anomaly = random.random() < anomaly_rate
        reading = None
        anomaly_type = None

        if is_anomaly:
            anomaly_kind = random.choice(["spike", "dropout", "out_of_range"])
            anomaly_type = anomaly_kind
            if anomaly_kind == "spike":
                # Sudden spike: 5-10x normal drift
                spike = random.uniform(5, 10) * self.drift * random.choice([-1, 1])
                reading = round(self.current + spike, 2)
                logger.debug("Device %s ANOMALY spike: %.2f", self.device_id, reading)
            elif anomaly_kind == "dropout":
                reading = None
                logger.debug("Device %s ANOMALY dropout", self.device_id)
            elif anomaly_kind == "out_of_range":
                reading = round(random.choice([-999.0, 9999.0]), 2)
                logger.debug("Device %s ANOMALY out-of-range: %.2f", self.device_id, reading)
        else:
            # Normal drift: random walk bounded by baseline +/- drift
            step = random.gauss(0, self.drift * 0.1)
            self.current += step
            # Mean-revert gently toward baseline
            self.current += (self.baseline - self.current) * 0.05
            self.current = max(self.min_val, min(self.max_val, self.current))
            reading = round(self.current, 2)

        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "reading": reading,
            "unit": self.unit,
            "battery_level": self.battery,
            "anomaly": anomaly_type,
            "location": self.location,
            "firmware_version": self.firmware,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Device fleet factory
# ---------------------------------------------------------------------------
def create_fleet(num_devices):
    """
    Build a list of IoTDevice instances with randomized types and locations.
    """
    devices = []
    type_names = list(DEVICE_TYPES.keys())
    for i in range(num_devices):
        device_id = f"device-{i+1:04d}"
        device_type = random.choice(type_names)
        location = random.choice(LOCATIONS)
        devices.append(IoTDevice(device_id, device_type, location))
    logger.info(
        "Created fleet of %d devices: %s",
        num_devices,
        ", ".join(f"{d.device_id}({d.device_type})" for d in devices[:5])
        + ("..." if num_devices > 5 else ""),
    )
    return devices


# ---------------------------------------------------------------------------
# Kafka helpers
# ---------------------------------------------------------------------------
def delivery_callback(err, msg):
    """Called once per produced message to indicate delivery result."""
    if err is not None:
        logger.error("Delivery failed for key %s: %s", msg.key(), err)
    else:
        logger.debug(
            "Delivered to %s [%d] @ offset %d",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


def create_producer(bootstrap_servers):
    """Create a confluent-kafka Producer with retry logic."""
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "iot-sensor-generator",
        "acks": "all",
        "retries": 5,
        "retry.backoff.ms": 500,
        "linger.ms": 20,
        "batch.num.messages": 200,
    }
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            producer = Producer(conf)
            logger.info("Kafka producer created (bootstrap: %s)", bootstrap_servers)
            return producer
        except Exception as exc:
            if attempt == max_attempts:
                raise
            logger.warning("Producer creation attempt %d/%d failed: %s", attempt, max_attempts, exc)
            time.sleep(2 * attempt)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run(args):
    """Generate IoT telemetry until duration expires or SIGINT."""
    producer = create_producer(args.kafka_bootstrap_servers)
    topic = args.topic
    fleet = create_fleet(args.devices)
    anomaly_rate = args.anomaly_rate

    # Interval between full fleet rounds
    # speed = events/sec; fleet size = len(fleet); round_interval = fleet_size / speed
    round_interval = len(fleet) / max(args.speed, 0.1)
    end_time = time.time() + args.duration
    total_events = 0
    total_anomalies = 0

    logger.info(
        "Starting IoT generation: %d devices, speed=%.1f evt/s, duration=%ds, anomaly_rate=%.2f, topic=%s",
        args.devices,
        args.speed,
        args.duration,
        anomaly_rate,
        topic,
    )

    try:
        while time.time() < end_time and not shutdown_event.is_set():
            round_start = time.time()
            for device in fleet:
                if shutdown_event.is_set():
                    break
                reading = device.read(anomaly_rate)
                if reading["anomaly"] is not None:
                    total_anomalies += 1

                try:
                    producer.produce(
                        topic,
                        key=reading["device_id"],
                        value=json.dumps(reading).encode("utf-8"),
                        callback=delivery_callback,
                    )
                    total_events += 1
                except BufferError:
                    logger.warning("Producer queue full — flushing...")
                    producer.flush(timeout=10)
                    producer.produce(
                        topic,
                        key=reading["device_id"],
                        value=json.dumps(reading).encode("utf-8"),
                        callback=delivery_callback,
                    )
                    total_events += 1

                producer.poll(0)

            # Sleep for remainder of round interval to maintain target speed
            elapsed = time.time() - round_start
            sleep_time = max(0, round_interval - elapsed)
            if sleep_time > 0 and not shutdown_event.is_set():
                time.sleep(sleep_time)

            if total_events % (args.devices * 10) == 0 and total_events > 0:
                logger.info(
                    "Progress: %d events produced (%d anomalies)", total_events, total_anomalies
                )

    except KeyboardInterrupt:
        shutdown_event.set()
    finally:
        logger.info("Flushing remaining messages...")
        producer.flush(timeout=30)
        logger.info(
            "IoT generation complete: %d events produced (%d anomalies, %.1f%%).",
            total_events,
            total_anomalies,
            (total_anomalies / max(total_events, 1)) * 100,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="IoT sensor data generator — produces simulated telemetry to Kafka."
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=10,
        help="Target events per second across all devices (default: 10)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Generation duration in seconds (default: 300)",
    )
    parser.add_argument(
        "--devices",
        type=int,
        default=20,
        help="Number of IoT devices to simulate (default: 20)",
    )
    parser.add_argument(
        "--anomaly-rate",
        type=float,
        default=0.02,
        help="Fraction of readings that are anomalies (default: 0.02 = 2%%)",
    )
    parser.add_argument(
        "--kafka-bootstrap-servers",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default="iot-sensors",
        help="Kafka topic to produce to (default: iot-sensors)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def _handle_sigint(sig, frame):
    logger.info("SIGINT received — shutting down gracefully...")
    shutdown_event.set()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _handle_sigint)
    run(parse_args())
