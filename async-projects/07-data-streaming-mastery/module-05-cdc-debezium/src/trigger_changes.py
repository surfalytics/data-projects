#!/usr/bin/env python3
"""
Trigger database changes to generate CDC events.

This script connects to the MySQL ecommerce database and performs a series of
INSERT, UPDATE, and DELETE operations. When Debezium is running, each of these
operations produces a corresponding CDC event in Kafka.

Operations performed:
1. Insert new customers.
2. Insert addresses for new customers.
3. Create new orders with order items.
4. Update order statuses (pending -> confirmed -> shipped -> delivered).
5. Update product stock quantities.
6. Update inventory levels.
7. Delete test records.

Usage:
    python src/trigger_changes.py
"""

import os
import sys
import time
from decimal import Decimal

from sqlalchemy import (
    create_engine,
    text,
)
from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "debezium")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "ecommerce")

DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
)

# Brief pause between groups of changes so CDC events are visually distinct.
CHANGE_DELAY = 1.0


def wait_for_mysql(engine, timeout: int = 60) -> None:
    """Wait until MySQL is accepting connections.

    Args:
        engine: SQLAlchemy engine instance.
        timeout: Maximum seconds to wait.

    Raises:
        SystemExit: If MySQL is not reachable within the timeout.
    """
    print(f"Waiting for MySQL at {MYSQL_HOST}:{MYSQL_PORT} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("MySQL is ready.")
            return
        except Exception:
            time.sleep(2)
    print(f"ERROR: MySQL not available after {timeout}s.")
    sys.exit(1)


def insert_customers(session: Session) -> list:
    """Insert new customers and return their IDs.

    Args:
        session: Active SQLAlchemy session.

    Returns:
        List of newly inserted customer IDs.
    """
    print("\n--- Inserting new customers ---")
    new_customers = [
        {
            "email": "emma.watson@example.com",
            "first_name": "Emma",
            "last_name": "Watson",
            "phone": "555-0201",
        },
        {
            "email": "liam.johnson@example.com",
            "first_name": "Liam",
            "last_name": "Johnson",
            "phone": "555-0202",
        },
        {
            "email": "olivia.martinez@example.com",
            "first_name": "Olivia",
            "last_name": "Martinez",
            "phone": "555-0203",
        },
    ]

    customer_ids = []
    for cust in new_customers:
        result = session.execute(
            text(
                "INSERT INTO customers (email, first_name, last_name, phone) "
                "VALUES (:email, :first_name, :last_name, :phone)"
            ),
            cust,
        )
        customer_ids.append(result.lastrowid)
        print(f"  Inserted customer: {cust['first_name']} {cust['last_name']} "
              f"(ID: {result.lastrowid})")

    session.commit()
    return customer_ids


def insert_addresses(session: Session, customer_ids: list) -> list:
    """Insert addresses for the given customers.

    Args:
        session: Active SQLAlchemy session.
        customer_ids: List of customer IDs to create addresses for.

    Returns:
        List of newly inserted address IDs.
    """
    print("\n--- Inserting addresses ---")
    addresses = [
        {
            "customer_id": customer_ids[0],
            "street": "100 Tech Blvd",
            "city": "San Francisco",
            "state": "CA",
            "zip_code": "94105",
            "country": "US",
            "is_default": True,
        },
        {
            "customer_id": customer_ids[1],
            "street": "200 Innovation Way",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "US",
            "is_default": True,
        },
        {
            "customer_id": customer_ids[2],
            "street": "300 Data Drive",
            "city": "Chicago",
            "state": "IL",
            "zip_code": "60601",
            "country": "US",
            "is_default": True,
        },
    ]

    address_ids = []
    for addr in addresses:
        result = session.execute(
            text(
                "INSERT INTO addresses "
                "(customer_id, street, city, state, zip_code, country, is_default) "
                "VALUES (:customer_id, :street, :city, :state, :zip_code, :country, :is_default)"
            ),
            addr,
        )
        address_ids.append(result.lastrowid)
        print(f"  Inserted address: {addr['city']}, {addr['state']} "
              f"for customer #{addr['customer_id']} (ID: {result.lastrowid})")

    session.commit()
    return address_ids


def create_orders(session: Session, customer_ids: list, address_ids: list) -> list:
    """Create orders with order items.

    Args:
        session: Active SQLAlchemy session.
        customer_ids: Customer IDs to place orders for.
        address_ids: Shipping address IDs.

    Returns:
        List of newly created order IDs.
    """
    print("\n--- Creating orders ---")
    orders_data = [
        {
            "customer_id": customer_ids[0],
            "address_id": address_ids[0],
            "items": [
                {"product_id": 1, "quantity": 2, "unit_price": 29.99},
                {"product_id": 3, "quantity": 1, "unit_price": 49.99},
            ],
        },
        {
            "customer_id": customer_ids[1],
            "address_id": address_ids[1],
            "items": [
                {"product_id": 6, "quantity": 1, "unit_price": 199.99},
                {"product_id": 8, "quantity": 2, "unit_price": 24.99},
            ],
        },
        {
            "customer_id": customer_ids[2],
            "address_id": address_ids[2],
            "items": [
                {"product_id": 7, "quantity": 1, "unit_price": 349.99},
                {"product_id": 10, "quantity": 1, "unit_price": 99.99},
                {"product_id": 4, "quantity": 1, "unit_price": 39.99},
            ],
        },
    ]

    order_ids = []
    for order in orders_data:
        total = sum(
            item["unit_price"] * item["quantity"] for item in order["items"]
        )
        result = session.execute(
            text(
                "INSERT INTO orders (customer_id, shipping_address_id, status, total_amount) "
                "VALUES (:cid, :aid, 'pending', :total)"
            ),
            {"cid": order["customer_id"], "aid": order["address_id"], "total": total},
        )
        order_id = result.lastrowid
        order_ids.append(order_id)
        print(f"  Created order #{order_id} for customer #{order['customer_id']} "
              f"total=${total:.2f}")

        for item in order["items"]:
            subtotal = item["unit_price"] * item["quantity"]
            session.execute(
                text(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal) "
                    "VALUES (:oid, :pid, :qty, :price, :subtotal)"
                ),
                {
                    "oid": order_id,
                    "pid": item["product_id"],
                    "qty": item["quantity"],
                    "price": item["unit_price"],
                    "subtotal": subtotal,
                },
            )
            print(f"    Added item: product #{item['product_id']} "
                  f"x{item['quantity']} = ${subtotal:.2f}")

    session.commit()
    return order_ids


def update_order_statuses(session: Session, order_ids: list) -> None:
    """Walk orders through status transitions to generate UPDATE events.

    Args:
        session: Active SQLAlchemy session.
        order_ids: Order IDs to update.
    """
    print("\n--- Updating order statuses ---")
    transitions = [
        ("pending", "confirmed"),
        ("confirmed", "shipped"),
    ]

    for from_status, to_status in transitions:
        time.sleep(CHANGE_DELAY)
        for oid in order_ids:
            session.execute(
                text(
                    "UPDATE orders SET status = :new_status "
                    "WHERE id = :oid AND status = :old_status"
                ),
                {"new_status": to_status, "old_status": from_status, "oid": oid},
            )
            print(f"  Order #{oid}: '{from_status}' -> '{to_status}'")
        session.commit()

    # Deliver the first order.
    time.sleep(CHANGE_DELAY)
    session.execute(
        text(
            "UPDATE orders SET status = 'delivered' "
            "WHERE id = :oid AND status = 'shipped'"
        ),
        {"oid": order_ids[0]},
    )
    session.commit()
    print(f"  Order #{order_ids[0]}: 'shipped' -> 'delivered'")


def update_inventory(session: Session) -> None:
    """Update inventory quantities to generate UPDATE events.

    Args:
        session: Active SQLAlchemy session.
    """
    print("\n--- Updating inventory ---")
    updates = [
        {"product_id": 1, "warehouse": "warehouse-east", "qty_delta": -2},
        {"product_id": 3, "warehouse": "warehouse-east", "qty_delta": -1},
        {"product_id": 6, "warehouse": "warehouse-east", "qty_delta": -1},
        {"product_id": 7, "warehouse": "warehouse-west", "qty_delta": -1},
    ]
    for upd in updates:
        session.execute(
            text(
                "UPDATE inventory SET quantity = quantity + :delta "
                "WHERE product_id = :pid AND warehouse = :wh"
            ),
            {"delta": upd["qty_delta"], "pid": upd["product_id"], "wh": upd["warehouse"]},
        )
        print(f"  Inventory product #{upd['product_id']} @ {upd['warehouse']}: "
              f"delta={upd['qty_delta']}")
    session.commit()


def update_customer_email(session: Session) -> None:
    """Update a customer's email to demonstrate field-level change detection.

    Args:
        session: Active SQLAlchemy session.
    """
    print("\n--- Updating customer email ---")
    session.execute(
        text(
            "UPDATE customers SET email = :new_email WHERE email = :old_email"
        ),
        {"new_email": "emma.w.updated@example.com", "old_email": "emma.watson@example.com"},
    )
    session.commit()
    print("  Updated emma.watson@example.com -> emma.w.updated@example.com")


def delete_test_records(session: Session) -> None:
    """Delete a customer (and cascade) to generate DELETE events.

    This also demonstrates cascading deletes: removing a customer deletes their
    addresses, orders, and order items through foreign key constraints.

    Args:
        session: Active SQLAlchemy session.
    """
    print("\n--- Deleting test record (cascade) ---")

    # First, insert a throwaway customer to delete.
    result = session.execute(
        text(
            "INSERT INTO customers (email, first_name, last_name, phone) "
            "VALUES ('temp.delete@example.com', 'Temp', 'Delete', '555-9999')"
        )
    )
    temp_id = result.lastrowid
    session.commit()
    print(f"  Inserted temporary customer #{temp_id}")

    time.sleep(CHANGE_DELAY)

    # Now delete the temporary customer.
    session.execute(
        text("DELETE FROM customers WHERE id = :cid"),
        {"cid": temp_id},
    )
    session.commit()
    print(f"  Deleted customer #{temp_id} (triggers DELETE CDC event)")


def main() -> None:
    """Run all database changes in sequence."""
    print("=" * 60)
    print("CDC Change Trigger Script")
    print("=" * 60)

    engine = create_engine(DATABASE_URL, echo=False)
    wait_for_mysql(engine)

    with Session(engine) as session:
        # 1. Insert customers.
        customer_ids = insert_customers(session)
        time.sleep(CHANGE_DELAY)

        # 2. Insert addresses.
        address_ids = insert_addresses(session, customer_ids)
        time.sleep(CHANGE_DELAY)

        # 3. Create orders with items.
        order_ids = create_orders(session, customer_ids, address_ids)
        time.sleep(CHANGE_DELAY)

        # 4. Update order statuses.
        update_order_statuses(session, order_ids)
        time.sleep(CHANGE_DELAY)

        # 5. Update inventory.
        update_inventory(session)
        time.sleep(CHANGE_DELAY)

        # 6. Update a customer email.
        update_customer_email(session)
        time.sleep(CHANGE_DELAY)

        # 7. Delete test records.
        delete_test_records(session)

    print("\n" + "=" * 60)
    print("All changes triggered successfully.")
    print("Run cdc_consumer.py or cdc_event_processor.py to see the events.")
    print("=" * 60)


if __name__ == "__main__":
    main()
