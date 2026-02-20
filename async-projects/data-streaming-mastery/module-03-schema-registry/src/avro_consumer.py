#!/usr/bin/env python3
"""
Avro Consumer for E-Commerce Order Events

Consumes Avro-serialized order events from a Kafka topic, deserializing them
using the Confluent Schema Registry. Prints each order with formatted output.

Usage:
    python avro_consumer.py [--topic orders-avro] [--group-id order-consumers]

Prerequisites:
    - Kafka broker running on localhost:9092
    - Schema Registry running on localhost:8081
    - Messages produced by avro_producer.py
    - pip install confluent-kafka[avro]
"""

import argparse
import signal
import sys
from datetime import datetime

from confluent_kafka import Consumer, KafkaError, KafkaException
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringDeserializer,
)

# ---------------------------------------------------------------------------
# Global flag for graceful shutdown
# ---------------------------------------------------------------------------

running = True


def signal_handler(sig, frame):
    """Handle SIGINT (Ctrl+C) for graceful shutdown.

    Args:
        sig: Signal number.
        frame: Current stack frame.
    """
    global running
    print("\nShutting down consumer...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


def dict_to_order(obj: dict, ctx: SerializationContext) -> dict:
    """Convert a deserialized dictionary to an order object.

    The AvroDeserializer calls this function to transform the raw
    deserialized data into a Python object. Here we simply return
    the dict, but you could create a dataclass or named tuple.

    Args:
        obj: The deserialized Avro record as a dictionary.
        ctx: Serialization context (provided by confluent-kafka).

    Returns:
        dict: The order event dictionary.
    """
    return obj


def format_order(order: dict) -> str:
    """Format an order event for human-readable display.

    Args:
        order: The deserialized order event dictionary.

    Returns:
        str: Formatted multi-line string representation of the order.
    """
    created_at = datetime.utcfromtimestamp(
        order["created_at"] / 1000
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    address = order["shipping_address"]
    address_str = (
        f"{address['street']}, {address['city']}, "
        f"{address['state']} {address['zip_code']}, {address['country']}"
    )

    lines = [
        f"  Order ID:     {order['order_id']}",
        f"  Customer:     {order['customer_id']} ({order['customer_email']})",
        f"  Product:      {order['product_name']}",
        f"  Quantity:     {order['quantity']}",
        f"  Unit Price:   ${order['unit_price']:.2f}",
        f"  Total:        ${order['total_amount']:.2f}",
        f"  Status:       {order['order_status']}",
        f"  Ship To:      {address_str}",
        f"  Created At:   {created_at}",
    ]

    if order.get("notes"):
        lines.append(f"  Notes:        {order['notes']}")

    return "\n".join(lines)


def create_avro_consumer(
    bootstrap_servers: str = "localhost:9092",
    schema_registry_url: str = "http://localhost:8081",
    group_id: str = "order-consumers",
) -> tuple:
    """Create a Kafka consumer configured with Avro deserialization.

    Args:
        bootstrap_servers: Kafka broker address.
        schema_registry_url: Schema Registry URL.
        group_id: Consumer group ID.

    Returns:
        tuple: (Consumer, AvroDeserializer, StringDeserializer)
    """
    schema_registry_conf = {"url": schema_registry_url}
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)

    avro_deserializer = AvroDeserializer(
        schema_registry_client=schema_registry_client,
        from_dict=dict_to_order,
    )

    string_deserializer = StringDeserializer("utf_8")

    consumer_conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }

    consumer = Consumer(consumer_conf)
    return consumer, avro_deserializer, string_deserializer


def main():
    """Main entry point. Consumes and displays Avro-serialized order events."""
    parser = argparse.ArgumentParser(
        description="Consume Avro-serialized e-commerce order events from Kafka."
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="orders-avro",
        help="Kafka topic to consume from (default: orders-avro).",
    )
    parser.add_argument(
        "--group-id",
        type=str,
        default="order-consumers",
        help="Consumer group ID (default: order-consumers).",
    )
    parser.add_argument(
        "--bootstrap-servers",
        type=str,
        default="localhost:9092",
        help="Kafka broker address (default: localhost:9092).",
    )
    parser.add_argument(
        "--schema-registry-url",
        type=str,
        default="http://localhost:8081",
        help="Schema Registry URL (default: http://localhost:8081).",
    )
    args = parser.parse_args()

    print(f"Creating Avro consumer...")
    print(f"  Kafka: {args.bootstrap_servers}")
    print(f"  Schema Registry: {args.schema_registry_url}")
    print(f"  Topic: {args.topic}")
    print(f"  Group: {args.group_id}")
    print()

    consumer, avro_deserializer, string_deserializer = create_avro_consumer(
        bootstrap_servers=args.bootstrap_servers,
        schema_registry_url=args.schema_registry_url,
        group_id=args.group_id,
    )

    consumer.subscribe([args.topic])
    print(f"Subscribed to '{args.topic}'. Waiting for messages (Ctrl+C to quit)...\n")

    message_count = 0

    try:
        while running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(
                        f"  Reached end of partition {msg.partition()} "
                        f"at offset {msg.offset()}"
                    )
                else:
                    raise KafkaException(msg.error())
                continue

            # Deserialize key and value
            key = string_deserializer(
                msg.key(),
                SerializationContext(args.topic, MessageField.KEY),
            )
            order = avro_deserializer(
                msg.value(),
                SerializationContext(args.topic, MessageField.VALUE),
            )

            message_count += 1
            print(f"--- Message #{message_count} ---")
            print(f"  Key:          {key}")
            print(f"  Partition:    {msg.partition()}")
            print(f"  Offset:       {msg.offset()}")
            print(format_order(order))
            print()

    except KeyboardInterrupt:
        pass
    finally:
        print(f"\nConsumed {message_count} messages total.")
        consumer.close()
        print("Consumer closed.")


if __name__ == "__main__":
    main()
