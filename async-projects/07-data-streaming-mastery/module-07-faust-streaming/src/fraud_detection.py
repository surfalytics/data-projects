"""
Real-Time Fraud Detection Agent.

This Faust application monitors a stream of financial transactions and flags
suspicious activity in real time. It demonstrates:
- Windowed tables for tracking transaction frequency per user
- Multi-rule fraud detection logic
- Stateful processing with country-tracking tables
- Writing alerts to a dedicated output topic

Fraud rules implemented:
1. High frequency -- more than 5 transactions in a 5-minute window
2. High value -- a single transaction exceeding $5,000
3. Country hop -- transaction from a different country than the user's last known country

Usage:
    faust -A src.fraud_detection worker -l info

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime, timedelta
from typing import List

from .models import Transaction, FraudAlert

# ---------------------------------------------------------------------------
# Faust App
# ---------------------------------------------------------------------------

app = faust.App(
    "fraud-detection-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

transactions_topic = app.topic(
    "transactions",
    value_type=Transaction,
    partitions=4,
)

fraud_alerts_topic = app.topic(
    "fraud-alerts",
    value_type=FraudAlert,
    partitions=4,
)

# ---------------------------------------------------------------------------
# State Tables
# ---------------------------------------------------------------------------

# Windowed table: count of transactions per user in last 5 minutes
transaction_counts = app.Table(
    "transaction-counts",
    default=int,
).tumbling(
    timedelta(minutes=5),
    expires=timedelta(hours=1),
)

# Table: last known country per user (for country-hop detection)
last_country = app.Table(
    "last-country",
    default=str,
)

# ---------------------------------------------------------------------------
# Fraud Detection Agent
# ---------------------------------------------------------------------------


@app.agent(transactions_topic)
async def detect_fraud(stream):
    """Process transactions and flag suspicious ones.

    For each incoming transaction, the agent runs three fraud-detection rules
    and publishes a FraudAlert for every rule violation.
    """
    async for transaction in stream.group_by(Transaction.user_id):
        alerts: List[FraudAlert] = []

        # ----- Rule 1: High frequency (>5 txns in 5 min) -----
        transaction_counts[transaction.user_id] += 1
        current_count = transaction_counts[transaction.user_id].current()

        if current_count > 5:
            alerts.append(
                FraudAlert(
                    transaction_id=transaction.transaction_id,
                    user_id=transaction.user_id,
                    reason=(
                        f"High frequency: {current_count} transactions "
                        f"in the last 5 minutes"
                    ),
                    risk_score=min(0.5 + (current_count - 5) * 0.1, 1.0),
                    flagged_at=datetime.utcnow(),
                )
            )

        # ----- Rule 2: High value (single txn > $5,000) -----
        if transaction.amount > 5000:
            risk = min(transaction.amount / 10000, 1.0)
            alerts.append(
                FraudAlert(
                    transaction_id=transaction.transaction_id,
                    user_id=transaction.user_id,
                    reason=(
                        f"High-value transaction: ${transaction.amount:,.2f} "
                        f"at {transaction.merchant}"
                    ),
                    risk_score=risk,
                    flagged_at=datetime.utcnow(),
                )
            )

        # ----- Rule 3: Country hop -----
        previous_country = last_country.get(transaction.user_id)
        if previous_country and previous_country != transaction.country:
            alerts.append(
                FraudAlert(
                    transaction_id=transaction.transaction_id,
                    user_id=transaction.user_id,
                    reason=(
                        f"Country hop detected: {previous_country} -> "
                        f"{transaction.country}"
                    ),
                    risk_score=0.7,
                    flagged_at=datetime.utcnow(),
                )
            )

        # Update last known country
        last_country[transaction.user_id] = transaction.country

        # ----- Publish alerts -----
        for alert in alerts:
            await fraud_alerts_topic.send(value=alert)
            print(
                f"[FRAUD ALERT] user={alert.user_id} "
                f"txn={alert.transaction_id} "
                f"reason={alert.reason} "
                f"risk={alert.risk_score:.2f}"
            )

        if not alerts:
            print(
                f"[OK] user={transaction.user_id} "
                f"txn={transaction.transaction_id} "
                f"amount=${transaction.amount:,.2f} "
                f"country={transaction.country}"
            )


# ---------------------------------------------------------------------------
# Alert Sink Agent (logging)
# ---------------------------------------------------------------------------


@app.agent(fraud_alerts_topic)
async def log_alerts(stream):
    """Log all fraud alerts for monitoring and audit."""
    async for alert in stream:
        print(
            f"[ALERT LOGGED] txn={alert.transaction_id} "
            f"user={alert.user_id} "
            f"risk={alert.risk_score:.2f} "
            f"reason={alert.reason}"
        )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/fraud/stats/")
async def fraud_stats(web, request):
    """Expose current fraud detection state via HTTP."""
    countries = {k: v for k, v in last_country.items()}
    return web.json(
        {
            "status": "running",
            "tracked_users_countries": countries,
        }
    )


if __name__ == "__main__":
    app.main()
