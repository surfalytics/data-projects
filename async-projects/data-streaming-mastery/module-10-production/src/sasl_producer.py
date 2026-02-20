"""
SASL Producer - Example Kafka producer configured with SASL_PLAINTEXT authentication.

This script demonstrates how to configure a Kafka producer with SASL/PLAIN
authentication. SASL/PLAIN sends credentials as username/password. In production,
always combine SASL with SSL (use SASL_SSL instead of SASL_PLAINTEXT) to encrypt
the credentials in transit.

Prerequisites:
    Configure Kafka broker with SASL_PLAINTEXT listener and create user credentials.
    See README.md for broker configuration details.

Usage:
    python src/sasl_producer.py

    # Custom configuration:
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \
    SASL_USERNAME=producer \
    SASL_PASSWORD=producer-secret \
    TOPIC=sasl-demo \
    python src/sasl_producer.py
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
TOPIC = os.getenv("TOPIC", "sasl-demo")
NUM_MESSAGES = int(os.getenv("NUM_MESSAGES", "20"))

# SASL configuration
SASL_MECHANISM = os.getenv("SASL_MECHANISM", "PLAIN")
SASL_USERNAME = os.getenv("SASL_USERNAME", "producer")
SASL_PASSWORD = os.getenv("SASL_PASSWORD", "producer-secret")
SECURITY_PROTOCOL = os.getenv("SECURITY_PROTOCOL", "SASL_PLAINTEXT")

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
# Delivery callback
# ---------------------------------------------------------------------------


def delivery_callback(err, msg):
    """
    Called when a message is delivered or delivery fails.

    Args:
        err: Error if delivery failed, None on success.
        msg: The delivered (or failed) message.
    """
    if err is not None:
        logger.error(
            "Delivery failed for %s [%d]: %s",
            msg.topic(), msg.partition(), err,
        )
    else:
        logger.info(
            "Delivered to %s [%d] @ offset %d (authenticated as '%s')",
            msg.topic(), msg.partition(), msg.offset(), SASL_USERNAME,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_sasl_producer():
    """
    Run the SASL-configured Kafka producer.

    Creates a producer with SASL authentication, demonstrating the
    security.protocol, sasl.mechanism, sasl.username, and sasl.password
    configuration options.
    """
    logger.info("=" * 60)
    logger.info("SASL Producer Example")
    logger.info("=" * 60)
    logger.info("Configuration:")
    logger.info("  Bootstrap servers: %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("  Topic: %s", TOPIC)
    logger.info("  Messages to send: %d", NUM_MESSAGES)
    logger.info("")
    logger.info("SASL Configuration:")
    logger.info("  Security protocol: %s", SECURITY_PROTOCOL)
    logger.info("  SASL mechanism: %s", SASL_MECHANISM)
    logger.info("  Username: %s", SASL_USERNAME)
    logger.info("  Password: %s", "*" * len(SASL_PASSWORD))

    # Build the producer configuration with SASL settings
    producer_config = {
        # Kafka connection
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "client.id": "sasl-producer-demo",

        # Security protocol: SASL_PLAINTEXT means SASL authentication without SSL.
        # In production, use SASL_SSL to encrypt credentials in transit.
        # Options: PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL
        "security.protocol": SECURITY_PROTOCOL,

        # SASL mechanism: PLAIN sends username/password.
        # Other options: SCRAM-SHA-256, SCRAM-SHA-512, GSSAPI (Kerberos), OAUTHBEARER
        "sasl.mechanism": SASL_MECHANISM,

        # SASL credentials
        # sasl.username: The username for PLAIN or SCRAM authentication
        "sasl.username": SASL_USERNAME,

        # sasl.password: The password for PLAIN or SCRAM authentication
        "sasl.password": SASL_PASSWORD,

        # Producer settings
        "acks": "all",
        "retries": 3,
    }

    # For SASL_SSL, you would also need these SSL settings:
    # producer_config.update({
    #     "ssl.ca.location": "/path/to/ca-cert.pem",
    #     # Optional for mutual TLS + SASL:
    #     # "ssl.certificate.location": "/path/to/client-cert.pem",
    #     # "ssl.key.location": "/path/to/client-key.pem",
    # })

    logger.info("")
    logger.info("Creating SASL-configured producer...")

    try:
        producer = Producer(producer_config)
        logger.info("Producer created successfully with SASL authentication.")
    except Exception as e:
        logger.error("Failed to create producer: %s", e)
        logger.error("")
        logger.error("Common SASL issues:")
        logger.error("  1. Broker is not configured with SASL listener")
        logger.error("  2. Username/password is incorrect")
        logger.error("  3. SASL mechanism mismatch between client and broker")
        logger.error("  4. For SCRAM: user credentials not created in ZooKeeper")
        sys.exit(1)

    logger.info("")
    logger.info("Sending %d messages with SASL authentication...", NUM_MESSAGES)
    logger.info("-" * 60)

    for i in range(NUM_MESSAGES):
        message = {
            "message_id": i + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "authentication": f"SASL/{SASL_MECHANISM}",
            "authenticated_user": SASL_USERNAME,
            "content": f"Authenticated message #{i + 1}",
            "producer": "sasl-producer-demo",
        }

        key = f"key-{i % 5}".encode("utf-8")
        value = json.dumps(message).encode("utf-8")

        try:
            producer.produce(
                topic=TOPIC,
                key=key,
                value=value,
                callback=delivery_callback,
            )
        except BufferError:
            logger.warning("Buffer full, waiting...")
            producer.poll(1.0)
            producer.produce(
                topic=TOPIC,
                key=key,
                value=value,
                callback=delivery_callback,
            )

        producer.poll(0)
        time.sleep(0.1)

    # Flush remaining messages
    logger.info("")
    logger.info("Flushing remaining messages...")
    remaining = producer.flush(timeout=10)

    if remaining > 0:
        logger.warning("%d messages were not delivered", remaining)
    else:
        logger.info("All messages delivered successfully with SASL authentication.")

    logger.info("")
    logger.info("=" * 60)
    logger.info("SASL Producer Example Complete")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Security Notes:")
    logger.info("  - SASL_PLAINTEXT sends credentials in cleartext over the network.")
    logger.info("  - In production, ALWAYS use SASL_SSL to encrypt credentials in transit.")
    logger.info("  - SCRAM-SHA-512 is preferred over PLAIN as the password is never sent.")
    logger.info("  - Combine SASL with ACLs to control what authenticated users can do.")


if __name__ == "__main__":
    run_sasl_producer()
