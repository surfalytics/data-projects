"""
Real-Time Analytics Agent with Web Views.

This Faust application tracks live analytics on an order stream:
- Orders per minute using a tumbling window
- Revenue per product category using a tumbling window
- HTTP endpoints to query current analytics state

This demonstrates Faust's ability to compute real-time aggregations and
expose them through its built-in web server.

Usage:
    faust -A src.realtime_analytics worker -l info --web-port 6066

    # Then query the endpoints:
    curl http://localhost:6066/analytics/orders-per-minute/
    curl http://localhost:6066/analytics/revenue-by-category/
    curl http://localhost:6066/analytics/dashboard/

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime, timedelta

from .models import Order

# ---------------------------------------------------------------------------
# Faust App
# ---------------------------------------------------------------------------

app = faust.App(
    "realtime-analytics-app",
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

# ---------------------------------------------------------------------------
# Windowed Tables
# ---------------------------------------------------------------------------

# Orders per minute -- tumbling window of 60 seconds
orders_per_minute = app.Table(
    "orders-per-minute",
    default=int,
).tumbling(
    timedelta(minutes=1),
    expires=timedelta(hours=1),
)

# Revenue per product category -- tumbling window of 60 seconds
revenue_by_category = app.Table(
    "revenue-by-category",
    default=float,
).tumbling(
    timedelta(minutes=1),
    expires=timedelta(hours=1),
)

# Non-windowed running totals for the dashboard
total_orders = app.Table("total-orders", default=int)
total_revenue = app.Table("total-revenue", default=float)
category_totals = app.Table("category-totals", default=float)

# ---------------------------------------------------------------------------
# Analytics Agent
# ---------------------------------------------------------------------------


@app.agent(orders_topic)
async def track_analytics(stream):
    """Track real-time order analytics.

    For each incoming order event:
    1. Increment the orders-per-minute windowed counter.
    2. Add the order amount to the revenue-by-category windowed sum.
    3. Update running totals for the overall dashboard.
    """
    async for order in stream:
        # Windowed aggregations
        orders_per_minute["all"] += 1
        revenue_by_category[order.category] += order.amount

        # Running totals (non-windowed)
        total_orders["count"] += 1
        total_revenue["sum"] += order.amount
        category_totals[order.category] += order.amount

        current_opm = orders_per_minute["all"].current()
        current_rev = revenue_by_category[order.category].current()

        print(
            f"[analytics] Order {order.order_id} | "
            f"category={order.category} | "
            f"amount=${order.amount:,.2f} | "
            f"orders_this_min={current_opm} | "
            f"category_rev_this_min=${current_rev:,.2f}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/analytics/orders-per-minute/")
async def orders_per_minute_view(web, request):
    """Return the current orders-per-minute count.

    This queries the tumbling window table to get the count for the
    current 1-minute window.
    """
    try:
        current = orders_per_minute["all"].current()
    except Exception:
        current = 0

    return web.json(
        {
            "metric": "orders_per_minute",
            "current_window_count": current,
            "window_size_seconds": 60,
            "queried_at": datetime.utcnow().isoformat(),
        }
    )


@app.page("/analytics/revenue-by-category/")
async def revenue_by_category_view(web, request):
    """Return revenue per category for the current 1-minute window."""
    categories = {}
    for key, value in category_totals.items():
        try:
            current_window = revenue_by_category[key].current()
        except Exception:
            current_window = 0.0
        categories[key] = {
            "current_window_revenue": round(current_window, 2),
            "all_time_revenue": round(value, 2),
        }

    return web.json(
        {
            "metric": "revenue_by_category",
            "window_size_seconds": 60,
            "categories": categories,
            "queried_at": datetime.utcnow().isoformat(),
        }
    )


@app.page("/analytics/dashboard/")
async def dashboard_view(web, request):
    """Return a combined analytics dashboard.

    Includes orders per minute, revenue by category, and running totals.
    """
    try:
        current_opm = orders_per_minute["all"].current()
    except Exception:
        current_opm = 0

    categories = {}
    for key, value in category_totals.items():
        try:
            current_window = revenue_by_category[key].current()
        except Exception:
            current_window = 0.0
        categories[key] = {
            "current_minute_revenue": round(current_window, 2),
            "all_time_revenue": round(value, 2),
        }

    return web.json(
        {
            "dashboard": {
                "orders_per_minute": current_opm,
                "total_orders": total_orders.get("count", 0),
                "total_revenue": round(total_revenue.get("sum", 0.0), 2),
                "categories": categories,
            },
            "queried_at": datetime.utcnow().isoformat(),
        }
    )


@app.page("/health/")
async def health(web, request):
    """Health check endpoint."""
    return web.json({"status": "ok", "app": "realtime-analytics-app"})


if __name__ == "__main__":
    app.main()
