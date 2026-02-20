"""
Shared Faust Record models for the streaming applications.

This module defines all typed models used across the Faust agents in this project.
Faust Records handle automatic JSON serialization and deserialization, providing
type safety for Kafka message payloads.

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime
from typing import Optional


class Transaction(faust.Record):
    """A financial transaction event.

    Attributes:
        transaction_id: Unique identifier for the transaction.
        user_id: Identifier of the user who made the transaction.
        amount: Transaction amount in USD.
        merchant: Name of the merchant.
        country: Two-letter country code where the transaction occurred.
        timestamp: When the transaction was created.
    """

    transaction_id: str
    user_id: str
    amount: float
    merchant: str
    country: str
    timestamp: datetime


class FraudAlert(faust.Record):
    """An alert generated when suspicious activity is detected.

    Attributes:
        transaction_id: The transaction that triggered the alert.
        user_id: The user involved in the suspicious activity.
        reason: Human-readable explanation of why this was flagged.
        risk_score: Numeric risk score from 0.0 (safe) to 1.0 (definite fraud).
        flagged_at: Timestamp when the alert was created.
    """

    transaction_id: str
    user_id: str
    reason: str
    risk_score: float
    flagged_at: datetime


class Order(faust.Record):
    """An order event from the e-commerce system.

    Attributes:
        order_id: Unique identifier for the order.
        customer_id: Identifier of the customer who placed the order.
        product_id: Identifier of the product ordered.
        quantity: Number of items ordered.
        amount: Total order amount in USD.
        category: Product category (e.g., 'electronics', 'clothing').
        timestamp: When the order was placed.
    """

    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    amount: float
    category: str
    timestamp: datetime


class Customer(faust.Record):
    """Customer reference data used for stream enrichment.

    Attributes:
        customer_id: Unique identifier for the customer.
        name: Full name of the customer.
        email: Email address.
        tier: Customer tier (e.g., 'gold', 'silver', 'bronze').
        country: Two-letter country code.
    """

    customer_id: str
    name: str
    email: str
    tier: str = "bronze"
    country: str = "US"


class Product(faust.Record):
    """Product reference data used for stream enrichment.

    Attributes:
        product_id: Unique identifier for the product.
        name: Product name.
        category: Product category.
        price: Unit price in USD.
        in_stock: Whether the product is currently in stock.
    """

    product_id: str
    name: str
    category: str
    price: float
    in_stock: bool = True


class EnrichedOrder(faust.Record):
    """An order event enriched with customer and product details.

    Attributes:
        order_id: Unique identifier for the order.
        customer_id: Identifier of the customer.
        customer_name: Full name of the customer (from lookup).
        customer_tier: Customer tier (from lookup).
        product_id: Identifier of the product.
        product_name: Name of the product (from lookup).
        product_category: Category of the product (from lookup).
        quantity: Number of items ordered.
        unit_price: Price per unit (from product lookup).
        total_amount: Total order amount.
        timestamp: When the order was placed.
    """

    order_id: str
    customer_id: str
    customer_name: str
    customer_tier: str
    product_id: str
    product_name: str
    product_category: str
    quantity: int
    unit_price: float
    total_amount: float
    timestamp: datetime


class TransformedMessage(faust.Record):
    """Output of the basic app transformation pipeline.

    Attributes:
        original_id: Original message identifier.
        content: Transformed message content.
        word_count: Number of words in the content.
        processed_at: When the transformation was applied.
    """

    original_id: str
    content: str
    word_count: int
    processed_at: datetime


class RawMessage(faust.Record):
    """Input message for the basic app transformation pipeline.

    Attributes:
        message_id: Unique identifier for the message.
        content: Raw message text content.
        source: Source system that produced the message.
        timestamp: When the message was created.
    """

    message_id: str
    content: str
    source: str
    timestamp: datetime
