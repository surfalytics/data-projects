#!/usr/bin/env python3
"""
Clickstream Generator — Produces realistic web-analytics events to a Kafka topic.

This generator simulates website visitor sessions with realistic navigation
patterns modelled after a typical e-commerce storefront:

  home -> category -> product -> (add_to_cart | back to category) -> cart -> checkout

Event types produced:
  - page_view   : user lands on or navigates to a page
  - click       : user clicks a link or button
  - search      : user performs a site search
  - add_to_cart : user adds a product to their cart
  - checkout    : user initiates checkout

Every event contains:
  session_id, user_id, event_type, page_url, referrer, user_agent,
  ip_address, geo (city + country), device_type, timestamp

Sessions:
  - A new session is created with a unique session_id (UUID4).
  - Each session has a random number of events (3-15).
  - Navigation follows weighted transition probabilities so the funnel
    narrows naturally (not every session reaches checkout).

Kafka delivery:
  - Uses confluent-kafka Producer with delivery-report callbacks.
  - Messages are JSON-serialized and keyed by session_id for partition affinity.

Usage:
  python clickstream_generator.py \\
      --speed 5 --duration 600 \\
      --kafka-bootstrap-servers localhost:9092 \\
      --topic clickstream

Requirements:
  pip install confluent-kafka faker
"""

import argparse
import json
import logging
import random
import signal
import sys
import threading
import time
import uuid
from datetime import datetime, timezone

from confluent_kafka import KafkaError, Producer
from faker import Faker

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("clickstream_generator")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
fake = Faker()
shutdown_event = threading.Event()

CATEGORIES = [
    "electronics",
    "clothing",
    "kitchen",
    "outdoors",
    "fitness",
    "office",
    "footwear",
    "groceries",
]

PRODUCTS = {
    "electronics": ["wireless-headphones", "usb-c-hub", "mechanical-keyboard", "smart-watch", "portable-charger"],
    "clothing": ["cotton-tshirt", "denim-jeans", "winter-jacket", "hoodie", "polo-shirt"],
    "kitchen": ["french-press", "cast-iron-skillet", "blender", "knife-set", "water-bottle"],
    "outdoors": ["hiking-backpack", "camping-tent", "sleeping-bag", "trekking-poles", "headlamp"],
    "fitness": ["yoga-mat", "resistance-bands", "dumbbells", "jump-rope", "foam-roller"],
    "office": ["desk-lamp", "monitor-stand", "ergonomic-chair", "notebook", "pen-set"],
    "footwear": ["running-shoes", "hiking-boots", "sandals", "sneakers", "loafers"],
    "groceries": ["green-tea", "coffee-beans", "protein-bars", "olive-oil", "honey"],
}

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
DEVICE_WEIGHTS = [0.45, 0.45, 0.10]

SEARCH_TERMS = [
    "wireless headphones",
    "running shoes",
    "yoga mat",
    "coffee maker",
    "backpack",
    "usb hub",
    "water bottle",
    "desk lamp",
    "smart watch",
    "kitchen knife",
]

# Navigation state machine transitions (from -> [(to, weight), ...])
TRANSITIONS = {
    "home": [("category", 0.50), ("search", 0.30), ("home", 0.20)],
    "category": [("product", 0.55), ("category", 0.15), ("search", 0.15), ("home", 0.15)],
    "product": [("add_to_cart", 0.30), ("category", 0.25), ("product", 0.20), ("search", 0.15), ("home", 0.10)],
    "add_to_cart": [("cart", 0.60), ("product", 0.25), ("category", 0.15)],
    "cart": [("checkout", 0.50), ("product", 0.25), ("home", 0.25)],
    "search": [("product", 0.50), ("category", 0.30), ("home", 0.20)],
    "checkout": [],  # terminal
}

BASE_URL = "https://shop.example.com"


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
    """Create a confluent-kafka Producer with sensible defaults and retry."""
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "clickstream-generator",
        "acks": "all",
        "retries": 5,
        "retry.backoff.ms": 500,
        "linger.ms": 50,
        "batch.num.messages": 100,
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
# Event generation
# ---------------------------------------------------------------------------
def _build_url(state, category=None, product=None):
    """Build a realistic page URL for a given navigation state."""
    if state == "home":
        return f"{BASE_URL}/"
    if state == "category":
        return f"{BASE_URL}/c/{category or random.choice(CATEGORIES)}"
    if state == "product":
        cat = category or random.choice(CATEGORIES)
        prod = product or random.choice(PRODUCTS[cat])
        return f"{BASE_URL}/p/{cat}/{prod}"
    if state == "search":
        term = random.choice(SEARCH_TERMS).replace(" ", "+")
        return f"{BASE_URL}/search?q={term}"
    if state in ("add_to_cart", "cart"):
        return f"{BASE_URL}/cart"
    if state == "checkout":
        return f"{BASE_URL}/checkout"
    return f"{BASE_URL}/"


def _pick_next_state(current):
    """Weighted random next state from the transition table."""
    options = TRANSITIONS.get(current, [])
    if not options:
        return None
    states, weights = zip(*options)
    return random.choices(states, weights=weights, k=1)[0]


def _map_event_type(state):
    """Map a navigation state to the event_type field."""
    mapping = {
        "home": "page_view",
        "category": "page_view",
        "product": "page_view",
        "search": "search",
        "add_to_cart": "add_to_cart",
        "cart": "page_view",
        "checkout": "checkout",
    }
    return mapping.get(state, "click")


def generate_session_events():
    """
    Generate a list of events for a single user session.

    Returns a list of dicts ready for JSON serialization.
    """
    session_id = str(uuid.uuid4())
    user_id = f"user_{random.randint(1000, 99999)}"
    user_agent = fake.user_agent()
    ip_address = fake.ipv4_public()
    city = fake.city()
    country = fake.country_code(representation="alpha-2")
    device_type = random.choices(DEVICE_TYPES, weights=DEVICE_WEIGHTS, k=1)[0]

    num_events = random.randint(3, 15)
    events = []
    state = "home"
    category = random.choice(CATEGORIES)
    product = random.choice(PRODUCTS[category])
    referrer = random.choice(
        [
            "https://www.google.com/",
            "https://www.facebook.com/",
            "https://twitter.com/",
            f"{BASE_URL}/",
            "",
        ]
    )

    for _ in range(num_events):
        url = _build_url(state, category=category, product=product)
        event = {
            "session_id": session_id,
            "user_id": user_id,
            "event_type": _map_event_type(state),
            "page_url": url,
            "referrer": referrer,
            "user_agent": user_agent,
            "ip_address": ip_address,
            "geo": {"city": city, "country": country},
            "device_type": device_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        events.append(event)

        # Advance referrer
        referrer = url

        # Pick next navigation state
        next_state = _pick_next_state(state)
        if next_state is None:
            break
        # Possibly switch category/product
        if next_state == "category":
            category = random.choice(CATEGORIES)
        if next_state == "product":
            product = random.choice(PRODUCTS[category])
        state = next_state

    return events


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run(args):
    """Produce clickstream events to Kafka until duration expires or SIGINT."""
    producer = create_producer(args.kafka_bootstrap_servers)
    topic = args.topic
    delay = 1.0 / max(args.speed, 0.1)
    end_time = time.time() + args.duration
    total_events = 0
    total_sessions = 0

    logger.info(
        "Starting clickstream generation: speed=%s evt/s, duration=%ds, topic=%s",
        args.speed,
        args.duration,
        topic,
    )

    try:
        while time.time() < end_time and not shutdown_event.is_set():
            events = generate_session_events()
            total_sessions += 1
            for ev in events:
                if shutdown_event.is_set():
                    break
                try:
                    producer.produce(
                        topic,
                        key=ev["session_id"],
                        value=json.dumps(ev).encode("utf-8"),
                        callback=delivery_callback,
                    )
                    total_events += 1
                except BufferError:
                    logger.warning("Producer queue full — flushing...")
                    producer.flush(timeout=10)
                    producer.produce(
                        topic,
                        key=ev["session_id"],
                        value=json.dumps(ev).encode("utf-8"),
                        callback=delivery_callback,
                    )
                    total_events += 1

                # Trigger delivery callbacks periodically
                producer.poll(0)
                time.sleep(delay)

    except KeyboardInterrupt:
        shutdown_event.set()
    finally:
        logger.info("Flushing remaining messages...")
        producer.flush(timeout=30)
        logger.info(
            "Clickstream generation complete: %d sessions, %d events produced.",
            total_sessions,
            total_events,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Clickstream generator — produces session-based web events to Kafka."
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=5,
        help="Target events per second (default: 5)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Generation duration in seconds (default: 300)",
    )
    parser.add_argument(
        "--kafka-bootstrap-servers",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)",
    )
    parser.add_argument(
        "--topic",
        default="clickstream",
        help="Kafka topic to produce to (default: clickstream)",
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
