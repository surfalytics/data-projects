#!/usr/bin/env python3
"""
E-Commerce Activity Simulator — Writes realistic e-commerce events to MySQL.

This simulator models a complete e-commerce lifecycle:
  1. Customer registration (new users created with Faker-generated profiles)
  2. Product browsing (page views on random products)
  3. Add to cart (items placed in shopping cart)
  4. Purchase (cart converted to an order, inventory decremented)
  5. Order status transitions (pending -> confirmed -> shipped -> delivered)
  6. Occasional cancellations (~5%) and returns (~3%)

Architecture:
  - Uses SQLAlchemy ORM with connection pooling (pool_size=5, max_overflow=10)
  - Concurrent simulated users via ThreadPoolExecutor
  - Each user thread independently walks through the lifecycle at random intervals
  - Order status transitions happen over configurable time windows
  - Graceful shutdown on SIGINT with thread draining

Database schema (auto-created on startup):
  - customers: id, name, email, address, created_at
  - products: id, name, category, price, inventory_qty
  - orders: id, customer_id, status, total, created_at, updated_at
  - order_items: id, order_id, product_id, quantity, unit_price
  - cart_items: id, customer_id, product_id, quantity, added_at

Usage:
  python ecommerce_simulator.py \\
      --speed 2 --duration 300 \\
      --mysql-host localhost --mysql-port 3306 \\
      --mysql-user root --mysql-password debezium \\
      --mysql-database ecommerce

Requirements:
  pip install sqlalchemy pymysql faker
"""

import argparse
import logging
import random
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ecommerce_simulator")

# ---------------------------------------------------------------------------
# SQLAlchemy models
# ---------------------------------------------------------------------------
Base = declarative_base()


class Customer(Base):
    """A registered customer."""

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")
    cart_items = relationship("CartItem", back_populates="customer")


class Product(Base):
    """A product available for sale."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    price = Column(Float, nullable=False)
    inventory_qty = Column(Integer, nullable=False, default=100)


class Order(Base):
    """A customer order with lifecycle statuses."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Line item within an order."""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")


class CartItem(Base):
    """An item currently in a customer's shopping cart."""

    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="cart_items")


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = [
    ("Wireless Bluetooth Headphones", "Electronics", 79.99),
    ("Organic Green Tea (100 bags)", "Groceries", 12.49),
    ("Running Shoes — Men's", "Footwear", 124.95),
    ("Stainless Steel Water Bottle", "Kitchen", 24.99),
    ("USB-C Hub 7-in-1", "Electronics", 39.99),
    ("Yoga Mat — Non-Slip", "Fitness", 34.99),
    ("Mechanical Keyboard RGB", "Electronics", 89.99),
    ("French Press Coffee Maker", "Kitchen", 29.99),
    ("Hiking Backpack 40L", "Outdoors", 74.99),
    ("Noise Cancelling Earbuds", "Electronics", 149.99),
    ("Cast Iron Skillet 12-inch", "Kitchen", 44.99),
    ("LED Desk Lamp", "Office", 32.99),
    ("Portable Charger 20000mAh", "Electronics", 29.99),
    ("Cotton T-Shirt — Unisex", "Clothing", 19.99),
    ("Smart Watch Fitness Tracker", "Electronics", 199.99),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
fake = Faker()
shutdown_event = threading.Event()

# Retry decorator for database operations
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds


def with_retry(func):
    """Decorator that retries a function on OperationalError."""

    def wrapper(*args, **kwargs):
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return func(*args, **kwargs)
            except OperationalError as exc:
                if attempt == MAX_RETRIES:
                    logger.error("Max retries reached for %s: %s", func.__name__, exc)
                    raise
                logger.warning(
                    "Retry %d/%d for %s: %s",
                    attempt,
                    MAX_RETRIES,
                    func.__name__,
                    exc,
                )
                time.sleep(RETRY_DELAY * attempt)

    return wrapper


# ---------------------------------------------------------------------------
# Database bootstrap
# ---------------------------------------------------------------------------
def create_db_engine(host, port, user, password, database):
    """Create a SQLAlchemy engine with connection pooling and retry logic."""
    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            engine = create_engine(
                url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            # Verify connectivity
            with engine.connect() as conn:
                conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            logger.info("Connected to MySQL at %s:%s/%s", host, port, database)
            return engine
        except OperationalError as exc:
            if attempt == MAX_RETRIES:
                logger.error("Failed to connect to MySQL after %d attempts", MAX_RETRIES)
                raise
            logger.warning(
                "Connection attempt %d/%d failed: %s — retrying in %ds",
                attempt,
                MAX_RETRIES,
                exc,
                RETRY_DELAY * attempt,
            )
            time.sleep(RETRY_DELAY * attempt)


def seed_products(session):
    """Insert seed products if the table is empty."""
    if session.query(Product).count() == 0:
        for name, category, price in PRODUCT_CATALOG:
            session.add(
                Product(
                    name=name,
                    category=category,
                    price=price,
                    inventory_qty=random.randint(50, 200),
                )
            )
        session.commit()
        logger.info("Seeded %d products", len(PRODUCT_CATALOG))


# ---------------------------------------------------------------------------
# Simulation actions
# ---------------------------------------------------------------------------
@with_retry
def register_customer(Session):
    """Create a new customer with a Faker-generated profile."""
    session = Session()
    try:
        customer = Customer(
            name=fake.name(),
            email=fake.unique.email(),
            address=fake.address().replace("\n", ", "),
        )
        session.add(customer)
        session.commit()
        logger.info("Registered customer id=%d name=%s", customer.id, customer.name)
        return customer.id
    finally:
        session.close()


@with_retry
def browse_products(Session, customer_id):
    """Simulate a customer viewing random products (logged only)."""
    session = Session()
    try:
        products = session.query(Product).order_by(__import__("sqlalchemy").func.rand()).limit(random.randint(1, 5)).all()
        product_names = [p.name for p in products]
        logger.info(
            "Customer %d browsed %d products: %s",
            customer_id,
            len(product_names),
            ", ".join(product_names[:3]) + ("..." if len(product_names) > 3 else ""),
        )
        return [p.id for p in products]
    finally:
        session.close()


@with_retry
def add_to_cart(Session, customer_id, product_ids):
    """Add one or more products to the customer's cart."""
    session = Session()
    try:
        added = []
        for pid in product_ids:
            item = CartItem(
                customer_id=customer_id,
                product_id=pid,
                quantity=random.randint(1, 3),
            )
            session.add(item)
            added.append(pid)
        session.commit()
        logger.info(
            "Customer %d added %d item(s) to cart", customer_id, len(added)
        )
        return added
    finally:
        session.close()


@with_retry
def purchase(Session, customer_id):
    """Convert the customer's cart into an order and decrement inventory."""
    session = Session()
    try:
        cart = (
            session.query(CartItem)
            .filter(CartItem.customer_id == customer_id)
            .all()
        )
        if not cart:
            logger.debug("Customer %d has an empty cart — skipping purchase", customer_id)
            return None

        order = Order(customer_id=customer_id, status="pending", total=0.0)
        session.add(order)
        session.flush()

        total = 0.0
        for ci in cart:
            product = session.query(Product).get(ci.product_id)
            if product is None or product.inventory_qty < ci.quantity:
                continue
            unit_price = product.price
            oi = OrderItem(
                order_id=order.id,
                product_id=ci.product_id,
                quantity=ci.quantity,
                unit_price=unit_price,
            )
            session.add(oi)
            total += unit_price * ci.quantity
            product.inventory_qty -= ci.quantity

        order.total = round(total, 2)

        # Clear cart
        for ci in cart:
            session.delete(ci)

        session.commit()
        logger.info(
            "Customer %d placed order #%d — total=$%.2f",
            customer_id,
            order.id,
            order.total,
        )
        return order.id
    finally:
        session.close()


@with_retry
def transition_order(Session, order_id, new_status):
    """Move an order to the next status."""
    session = Session()
    try:
        order = session.query(Order).get(order_id)
        if order is None:
            return
        old = order.status
        order.status = new_status
        order.updated_at = datetime.utcnow()
        session.commit()
        logger.info("Order #%d status: %s -> %s", order_id, old, new_status)
    finally:
        session.close()


# ---------------------------------------------------------------------------
# User lifecycle thread
# ---------------------------------------------------------------------------
def simulate_user(Session, speed, transition_delay):
    """
    Simulate a single user's lifecycle:
      register -> browse -> add to cart -> purchase -> order transitions.
    """
    if shutdown_event.is_set():
        return

    delay = 1.0 / max(speed, 0.1)

    try:
        # 1. Register
        customer_id = register_customer(Session)
        if shutdown_event.is_set():
            return
        time.sleep(delay)

        # 2. Browse
        product_ids = browse_products(Session, customer_id)
        if shutdown_event.is_set() or not product_ids:
            return
        time.sleep(delay)

        # 3. Add to cart (pick 1-3 of browsed products)
        to_add = random.sample(product_ids, min(len(product_ids), random.randint(1, 3)))
        add_to_cart(Session, customer_id, to_add)
        if shutdown_event.is_set():
            return
        time.sleep(delay)

        # 4. Purchase
        order_id = purchase(Session, customer_id)
        if order_id is None or shutdown_event.is_set():
            return
        time.sleep(delay)

        # 5. Order transitions
        roll = random.random()
        if roll < 0.05:
            # ~5% cancellation
            time.sleep(transition_delay)
            if not shutdown_event.is_set():
                transition_order(Session, order_id, "cancelled")
            return

        # confirmed
        time.sleep(transition_delay)
        if shutdown_event.is_set():
            return
        transition_order(Session, order_id, "confirmed")

        # shipped
        time.sleep(transition_delay)
        if shutdown_event.is_set():
            return
        transition_order(Session, order_id, "shipped")

        # delivered
        time.sleep(transition_delay)
        if shutdown_event.is_set():
            return
        transition_order(Session, order_id, "delivered")

        # ~3% return after delivery
        if random.random() < 0.03:
            time.sleep(transition_delay)
            if not shutdown_event.is_set():
                transition_order(Session, order_id, "returned")

    except Exception:
        logger.exception("Error in user simulation for customer")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def run(args):
    """Entry-point: set up DB, seed data, and launch user threads."""
    engine = create_db_engine(
        args.mysql_host,
        args.mysql_port,
        args.mysql_user,
        args.mysql_password,
        args.mysql_database,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    # Seed
    session = Session()
    try:
        seed_products(session)
    finally:
        session.close()

    transition_delay = max(0.5, 1.0 / args.speed)
    end_time = time.time() + args.duration

    logger.info(
        "Starting e-commerce simulation: speed=%d evt/s, duration=%ds",
        args.speed,
        args.duration,
    )

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = []
        try:
            while time.time() < end_time and not shutdown_event.is_set():
                fut = pool.submit(simulate_user, Session, args.speed, transition_delay)
                futures.append(fut)
                # Stagger new user creation
                time.sleep(1.0 / max(args.speed, 0.1))
        except KeyboardInterrupt:
            shutdown_event.set()

        # Drain
        for f in as_completed(futures, timeout=30):
            try:
                f.result()
            except Exception:
                pass

    logger.info("Simulation finished.")
    engine.dispose()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="E-commerce activity simulator — writes realistic events to MySQL."
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=2,
        help="Target events per second (default: 2)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=300,
        help="Simulation duration in seconds (default: 300)",
    )
    parser.add_argument("--mysql-host", default="localhost", help="MySQL host (default: localhost)")
    parser.add_argument("--mysql-port", type=int, default=3306, help="MySQL port (default: 3306)")
    parser.add_argument("--mysql-user", default="root", help="MySQL user (default: root)")
    parser.add_argument("--mysql-password", default="debezium", help="MySQL password (default: debezium)")
    parser.add_argument("--mysql-database", default="ecommerce", help="MySQL database (default: ecommerce)")
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
