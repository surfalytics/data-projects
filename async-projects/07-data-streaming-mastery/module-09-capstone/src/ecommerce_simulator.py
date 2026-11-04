#!/usr/bin/env python3
"""
E-Commerce Simulator for Module 9 Capstone.

Generates realistic e-commerce activity by writing directly to MySQL:
- Customer registrations
- Product purchases (orders with multiple items)
- Order status transitions (pending -> confirmed -> shipped -> delivered)
- Occasional cancellations and returns
- Inventory adjustments

Usage:
    python ecommerce_simulator.py --speed 2 --duration 600
"""

import argparse
import logging
import random
import signal
import sys
import threading
import time
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "debezium"
MYSQL_DATABASE = "ecommerce"

FIRST_NAMES = [
    "Liam", "Olivia", "Noah", "Emma", "Aiden", "Sophia", "Jackson", "Ava",
    "Lucas", "Isabella", "Ethan", "Mia", "Mason", "Charlotte", "Logan",
    "Amelia", "Alexander", "Harper", "Sebastian", "Evelyn", "Mateo", "Luna",
    "Daniel", "Ella", "Owen", "Scarlett", "James", "Grace", "Benjamin", "Chloe",
]

LAST_NAMES = [
    "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee",
    "Walker", "Hall", "Allen", "Young", "King", "Wright", "Lopez", "Hill",
    "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
    "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker",
    "Evans",
]

STATUS_TRANSITIONS = {
    "pending": "confirmed",
    "confirmed": "shipped",
    "shipped": "delivered",
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ecommerce-simulator")

# ---------------------------------------------------------------------------
# Global shutdown flag
# ---------------------------------------------------------------------------

shutdown_event = threading.Event()


def signal_handler(sig, frame):
    logger.info("Shutdown signal received. Stopping simulator...")
    shutdown_event.set()


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def create_db_engine():
    """Create a SQLAlchemy engine with connection pooling."""
    url = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    engine = create_engine(
        url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    return engine


@contextmanager
def get_connection(engine):
    """Context manager for database connections."""
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Simulator actions
# ---------------------------------------------------------------------------


def register_customer(engine):
    """Register a new customer with random name and email."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    unique_id = random.randint(1000, 99999)
    email = f"{first.lower()}.{last.lower()}.{unique_id}@example.com"
    phone = f"+1-555-{random.randint(1000, 9999)}"

    with get_connection(engine) as conn:
        result = conn.execute(
            text(
                "INSERT INTO customers (email, first_name, last_name, phone) "
                "VALUES (:email, :first_name, :last_name, :phone)"
            ),
            {"email": email, "first_name": first, "last_name": last, "phone": phone},
        )
        customer_id = result.lastrowid
        logger.info(f"New customer registered: {first} {last} (ID: {customer_id})")
        return customer_id


def create_order(engine):
    """Create a new order with 1-5 random items."""
    with get_connection(engine) as conn:
        # Pick a random existing customer
        customers = conn.execute(text("SELECT id FROM customers")).fetchall()
        if not customers:
            logger.warning("No customers found. Registering one first.")
            return None

        customer_id = random.choice(customers)[0]

        # Pick 1-5 random products
        products = conn.execute(
            text("SELECT id, price, stock_quantity FROM products WHERE stock_quantity > 0")
        ).fetchall()
        if not products:
            logger.warning("No products in stock.")
            return None

        num_items = random.randint(1, min(5, len(products)))
        selected_products = random.sample(products, num_items)

        # Create order
        result = conn.execute(
            text(
                "INSERT INTO orders (customer_id, status, total_amount) "
                "VALUES (:customer_id, 'pending', 0.00)"
            ),
            {"customer_id": customer_id},
        )
        order_id = result.lastrowid

        total = 0.0
        for prod_id, price, stock in selected_products:
            quantity = random.randint(1, min(3, stock))
            subtotal = round(float(price) * quantity, 2)
            total += subtotal

            conn.execute(
                text(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) "
                    "VALUES (:order_id, :product_id, :quantity, :unit_price, :subtotal)"
                ),
                {
                    "order_id": order_id,
                    "product_id": prod_id,
                    "quantity": quantity,
                    "unit_price": float(price),
                    "subtotal": subtotal,
                },
            )

            # Decrement stock
            conn.execute(
                text(
                    "UPDATE products SET stock_quantity = stock_quantity - :qty "
                    "WHERE id = :pid AND stock_quantity >= :qty"
                ),
                {"qty": quantity, "pid": prod_id},
            )

            # Log inventory change
            conn.execute(
                text(
                    "INSERT INTO inventory_log (product_id, change_quantity, reason) "
                    "VALUES (:pid, :qty, :reason)"
                ),
                {"pid": prod_id, "qty": -quantity, "reason": f"Sold in order #{order_id}"},
            )

        # Update order total
        conn.execute(
            text("UPDATE orders SET total_amount = :total WHERE id = :oid"),
            {"total": round(total, 2), "oid": order_id},
        )

        logger.info(
            f"Order #{order_id} created for customer #{customer_id}: "
            f"{num_items} items, total ${total:.2f}"
        )
        return order_id


def advance_order_status(engine):
    """Move a random pending/confirmed/shipped order to the next status."""
    with get_connection(engine) as conn:
        orders = conn.execute(
            text(
                "SELECT id, status FROM orders "
                "WHERE status IN ('pending', 'confirmed', 'shipped') "
                "ORDER BY RAND() LIMIT 1"
            )
        ).fetchone()

        if not orders:
            return None

        order_id, current_status = orders
        new_status = STATUS_TRANSITIONS.get(current_status)
        if not new_status:
            return None

        conn.execute(
            text("UPDATE orders SET status = :status WHERE id = :oid"),
            {"status": new_status, "oid": order_id},
        )
        logger.info(f"Order #{order_id}: {current_status} -> {new_status}")
        return order_id


def cancel_order(engine):
    """Cancel a random pending or confirmed order."""
    with get_connection(engine) as conn:
        order = conn.execute(
            text(
                "SELECT id, status FROM orders "
                "WHERE status IN ('pending', 'confirmed') "
                "ORDER BY RAND() LIMIT 1"
            )
        ).fetchone()

        if not order:
            return None

        order_id = order[0]
        conn.execute(
            text("UPDATE orders SET status = 'cancelled' WHERE id = :oid"),
            {"oid": order_id},
        )

        # Restore inventory for cancelled items
        items = conn.execute(
            text("SELECT product_id, quantity FROM order_items WHERE order_id = :oid"),
            {"oid": order_id},
        ).fetchall()

        for prod_id, qty in items:
            conn.execute(
                text(
                    "UPDATE products SET stock_quantity = stock_quantity + :qty "
                    "WHERE id = :pid"
                ),
                {"qty": qty, "pid": prod_id},
            )
            conn.execute(
                text(
                    "INSERT INTO inventory_log (product_id, change_quantity, reason) "
                    "VALUES (:pid, :qty, :reason)"
                ),
                {"pid": prod_id, "qty": qty, "reason": f"Cancelled order #{order_id}"},
            )

        logger.info(f"Order #{order_id} cancelled. Inventory restored.")
        return order_id


def return_order(engine):
    """Return a random delivered order."""
    with get_connection(engine) as conn:
        order = conn.execute(
            text(
                "SELECT id FROM orders WHERE status = 'delivered' "
                "ORDER BY RAND() LIMIT 1"
            )
        ).fetchone()

        if not order:
            return None

        order_id = order[0]
        conn.execute(
            text("UPDATE orders SET status = 'returned' WHERE id = :oid"),
            {"oid": order_id},
        )

        # Restore inventory for returned items
        items = conn.execute(
            text("SELECT product_id, quantity FROM order_items WHERE order_id = :oid"),
            {"oid": order_id},
        ).fetchall()

        for prod_id, qty in items:
            conn.execute(
                text(
                    "UPDATE products SET stock_quantity = stock_quantity + :qty "
                    "WHERE id = :pid"
                ),
                {"qty": qty, "pid": prod_id},
            )
            conn.execute(
                text(
                    "INSERT INTO inventory_log (product_id, change_quantity, reason) "
                    "VALUES (:pid, :qty, :reason)"
                ),
                {"pid": prod_id, "qty": qty, "reason": f"Returned order #{order_id}"},
            )

        logger.info(f"Order #{order_id} returned. Inventory restored.")
        return order_id


# ---------------------------------------------------------------------------
# Simulator thread
# ---------------------------------------------------------------------------


def simulate_user(engine, speed, user_id):
    """Simulate a single concurrent user performing random actions."""
    logger.info(f"User thread {user_id} started.")

    while not shutdown_event.is_set():
        try:
            # Weighted random action selection
            action = random.choices(
                population=[
                    "register",
                    "order",
                    "advance",
                    "advance",
                    "advance",
                    "cancel",
                    "return",
                ],
                weights=[10, 30, 25, 20, 10, 3, 2],
                k=1,
            )[0]

            if action == "register":
                register_customer(engine)
            elif action == "order":
                create_order(engine)
            elif action == "advance":
                advance_order_status(engine)
            elif action == "cancel":
                cancel_order(engine)
            elif action == "return":
                return_order(engine)

            # Realistic delay between actions, scaled by speed
            delay = random.uniform(0.5, 3.0) / speed
            shutdown_event.wait(delay)

        except Exception as e:
            logger.error(f"User {user_id} error: {e}")
            shutdown_event.wait(2.0)

    logger.info(f"User thread {user_id} stopped.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="E-Commerce Simulator for Streaming Capstone"
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=2.0,
        help="Speed multiplier for event generation (default: 2.0)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Duration to run in seconds (default: 600 = 10 minutes)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=3,
        help="Number of concurrent simulated users (default: 3)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("E-Commerce Simulator Starting")
    logger.info(f"  Speed:    {args.speed}x")
    logger.info(f"  Duration: {args.duration}s")
    logger.info(f"  Threads:  {args.threads}")
    logger.info("=" * 60)

    # Wait for MySQL to be available
    engine = None
    for attempt in range(30):
        try:
            engine = create_db_engine()
            with get_connection(engine) as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to MySQL successfully.")
            break
        except Exception as e:
            logger.warning(f"MySQL not ready (attempt {attempt + 1}/30): {e}")
            time.sleep(2)
    else:
        logger.error("Could not connect to MySQL after 30 attempts. Exiting.")
        sys.exit(1)

    # Start user simulation threads
    threads = []
    for i in range(args.threads):
        t = threading.Thread(
            target=simulate_user,
            args=(engine, args.speed, i + 1),
            daemon=True,
        )
        t.start()
        threads.append(t)

    # Run for the specified duration or until interrupted
    start_time = time.time()
    try:
        while not shutdown_event.is_set():
            elapsed = time.time() - start_time
            if elapsed >= args.duration:
                logger.info(f"Duration of {args.duration}s reached. Stopping.")
                shutdown_event.set()
                break
            shutdown_event.wait(1.0)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt. Stopping.")
        shutdown_event.set()

    # Wait for threads to finish
    for t in threads:
        t.join(timeout=5)

    if engine:
        engine.dispose()

    logger.info("Simulator stopped. Goodbye.")


if __name__ == "__main__":
    main()
