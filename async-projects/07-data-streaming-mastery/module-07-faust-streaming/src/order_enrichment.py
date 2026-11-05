"""
Stream Enrichment Agent -- Order Enrichment Pipeline.

This Faust application demonstrates the stream-table join pattern. It reads
order events from a Kafka topic, looks up customer and product reference data
from Faust Tables, and produces enriched order events that combine all three
data sources into a single denormalized record.

The enrichment pattern is extremely common in real-time data pipelines:
- Raw events carry only identifiers (customer_id, product_id)
- Reference data is maintained in compacted Kafka topics backed by Tables
- The agent joins the stream with the tables to produce enriched output

Usage:
    faust -A src.order_enrichment worker -l info

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime

from .models import Order, Customer, Product, EnrichedOrder

# ---------------------------------------------------------------------------
# Faust App
# ---------------------------------------------------------------------------

app = faust.App(
    "order-enrichment-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

orders_topic = app.topic(
    "orders",
    value_type=Order,
    partitions=4,
)

customers_topic = app.topic(
    "customers",
    value_type=Customer,
    partitions=4,
)

products_topic = app.topic(
    "products",
    value_type=Product,
    partitions=4,
)

enriched_orders_topic = app.topic(
    "enriched-orders",
    value_type=EnrichedOrder,
    partitions=4,
)

# ---------------------------------------------------------------------------
# Reference Data Tables
# ---------------------------------------------------------------------------

# Customer lookup table -- keyed by customer_id
customer_table = app.Table(
    "customer-table",
    default=dict,
)

# Product lookup table -- keyed by product_id
product_table = app.Table(
    "product-table",
    default=dict,
)

# ---------------------------------------------------------------------------
# Reference Data Agents (populate tables from compacted topics)
# ---------------------------------------------------------------------------


@app.agent(customers_topic)
async def update_customers(stream):
    """Maintain the customer reference table from the customers topic.

    Each message is expected to be keyed by customer_id. The agent stores
    the latest customer record so that the enrichment agent can look it up.
    """
    async for customer in stream:
        customer_table[customer.customer_id] = {
            "name": customer.name,
            "email": customer.email,
            "tier": customer.tier,
            "country": customer.country,
        }
        print(f"[customers] Updated customer {customer.customer_id}: {customer.name}")


@app.agent(products_topic)
async def update_products(stream):
    """Maintain the product reference table from the products topic.

    Each message is expected to be keyed by product_id. The agent stores
    the latest product record for enrichment lookups.
    """
    async for product in stream:
        product_table[product.product_id] = {
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "in_stock": product.in_stock,
        }
        print(f"[products] Updated product {product.product_id}: {product.name}")


# ---------------------------------------------------------------------------
# Enrichment Agent
# ---------------------------------------------------------------------------


@app.agent(orders_topic)
async def enrich_orders(stream):
    """Enrich order events with customer and product details.

    For each incoming order:
    1. Look up the customer by customer_id in the customer table.
    2. Look up the product by product_id in the product table.
    3. Combine the data into an EnrichedOrder and send to the output topic.

    If reference data is not found, sensible defaults are used.
    """
    async for order in stream:
        # Customer lookup
        customer_data = customer_table.get(order.customer_id, {})
        customer_name = customer_data.get("name", "Unknown Customer")
        customer_tier = customer_data.get("tier", "unknown")

        # Product lookup
        product_data = product_table.get(order.product_id, {})
        product_name = product_data.get("name", "Unknown Product")
        product_category = product_data.get("category", "unknown")
        unit_price = product_data.get("price", 0.0)

        # Build enriched order
        enriched = EnrichedOrder(
            order_id=order.order_id,
            customer_id=order.customer_id,
            customer_name=customer_name,
            customer_tier=customer_tier,
            product_id=order.product_id,
            product_name=product_name,
            product_category=product_category,
            quantity=order.quantity,
            unit_price=unit_price,
            total_amount=order.amount,
            timestamp=order.timestamp,
        )

        await enriched_orders_topic.send(value=enriched)

        print(
            f"[enrich] Order {order.order_id}: "
            f"customer={customer_name} ({customer_tier}), "
            f"product={product_name} ({product_category}), "
            f"total=${order.amount:,.2f}"
        )


# ---------------------------------------------------------------------------
# Enriched Order Sink (logging)
# ---------------------------------------------------------------------------


@app.agent(enriched_orders_topic)
async def log_enriched_orders(stream):
    """Log enriched orders for verification."""
    async for enriched in stream:
        print(
            f"[enriched] {enriched.order_id} | "
            f"{enriched.customer_name} ({enriched.customer_tier}) | "
            f"{enriched.product_name} x{enriched.quantity} | "
            f"${enriched.total_amount:,.2f}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/customers/")
async def list_customers(web, request):
    """Expose the customer reference table via HTTP."""
    customers = {k: v for k, v in customer_table.items()}
    return web.json({"customer_count": len(customers), "customers": customers})


@app.page("/products/")
async def list_products(web, request):
    """Expose the product reference table via HTTP."""
    products = {k: v for k, v in product_table.items()}
    return web.json({"product_count": len(products), "products": products})


if __name__ == "__main__":
    app.main()
