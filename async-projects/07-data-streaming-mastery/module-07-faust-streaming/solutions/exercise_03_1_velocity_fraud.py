"""
Solution: Exercise 3.1 -- Velocity-Based Fraud Detection.

Extends the base fraud detection system with two additional rules:
1. Spending Velocity: flags users spending >$10,000 in a 10-minute window.
2. Merchant Diversity: flags users transacting at >4 unique merchants in 5 minutes.

Usage:
    faust -A solutions.exercise_03_1_velocity_fraud worker -l info --web-port 6066

    curl http://localhost:6066/fraud/velocity/user-0001/

Uses faust-streaming (the maintained community fork), NOT robinhood/faust.
"""

import faust
from datetime import datetime, timedelta
from typing import List

# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


class Transaction(faust.Record):
    """A financial transaction event.

    Attributes:
        transaction_id: Unique identifier for the transaction.
        user_id: Identifier of the user who made the transaction.
        amount: Transaction amount in USD.
        merchant: Name of the merchant.
        country: Two-letter country code.
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
        user_id: The user involved.
        reason: Explanation of why this was flagged.
        risk_score: Numeric risk score from 0.0 to 1.0.
        flagged_at: Timestamp when the alert was created.
    """

    transaction_id: str
    user_id: str
    reason: str
    risk_score: float
    flagged_at: datetime


# ---------------------------------------------------------------------------
# App, Topics, Tables
# ---------------------------------------------------------------------------

app = faust.App(
    "velocity-fraud-app",
    broker="kafka://localhost:9092",
    store="memory://",
    topic_partitions=4,
    value_serializer="json",
)

transactions_topic = app.topic("transactions", value_type=Transaction, partitions=4)
fraud_alerts_topic = app.topic("fraud-alerts", value_type=FraudAlert, partitions=4)

# --- Original rules tables ---

# Transaction count per user in 5-minute window
transaction_counts = app.Table(
    "txn-counts-velocity",
    default=int,
).tumbling(timedelta(minutes=5), expires=timedelta(hours=1))

# Last known country per user
last_country = app.Table("last-country-velocity", default=str)

# --- New rule tables ---

# Spending velocity: total amount per user in 10-minute window
spending_velocity = app.Table(
    "spending-velocity",
    default=float,
).tumbling(timedelta(minutes=10), expires=timedelta(hours=1))

# Merchant diversity: comma-separated unique merchants per user in 5-minute window
# Faust tables cannot store sets, so we use a comma-separated string.
merchant_diversity = app.Table(
    "merchant-diversity",
    default=str,
).tumbling(timedelta(minutes=5), expires=timedelta(hours=1))

# ---------------------------------------------------------------------------
# Fraud Detection Agent
# ---------------------------------------------------------------------------

VELOCITY_THRESHOLD = 10000.0
MERCHANT_DIVERSITY_THRESHOLD = 4
HIGH_FREQ_THRESHOLD = 5
HIGH_VALUE_THRESHOLD = 5000.0


@app.agent(transactions_topic)
async def detect_fraud(stream):
    """Process transactions and apply all fraud detection rules.

    Rules:
    1. High frequency: >5 transactions in 5 minutes.
    2. High value: single transaction > $5,000.
    3. Country hop: different country than last transaction.
    4. Spending velocity: >$10,000 total in 10 minutes.
    5. Merchant diversity: >4 unique merchants in 5 minutes.
    """
    async for txn in stream.group_by(Transaction.user_id):
        alerts: List[FraudAlert] = []
        now = datetime.utcnow()

        # --- Rule 1: High frequency ---
        transaction_counts[txn.user_id] += 1
        freq_count = transaction_counts[txn.user_id].current()

        if freq_count > HIGH_FREQ_THRESHOLD:
            alerts.append(
                FraudAlert(
                    transaction_id=txn.transaction_id,
                    user_id=txn.user_id,
                    reason=f"High frequency: {freq_count} txns in 5 min",
                    risk_score=min(0.5 + (freq_count - 5) * 0.1, 1.0),
                    flagged_at=now,
                )
            )

        # --- Rule 2: High value ---
        if txn.amount > HIGH_VALUE_THRESHOLD:
            alerts.append(
                FraudAlert(
                    transaction_id=txn.transaction_id,
                    user_id=txn.user_id,
                    reason=f"High-value transaction: ${txn.amount:,.2f}",
                    risk_score=min(txn.amount / 10000, 1.0),
                    flagged_at=now,
                )
            )

        # --- Rule 3: Country hop ---
        prev_country = last_country.get(txn.user_id)
        if prev_country and prev_country != txn.country:
            alerts.append(
                FraudAlert(
                    transaction_id=txn.transaction_id,
                    user_id=txn.user_id,
                    reason=f"Country hop: {prev_country} -> {txn.country}",
                    risk_score=0.7,
                    flagged_at=now,
                )
            )
        last_country[txn.user_id] = txn.country

        # --- Rule 4: Spending velocity ---
        spending_velocity[txn.user_id] += txn.amount
        total_spent = spending_velocity[txn.user_id].current()

        if total_spent > VELOCITY_THRESHOLD:
            risk = min(0.6 + (total_spent - VELOCITY_THRESHOLD) / 25000, 1.0)
            alerts.append(
                FraudAlert(
                    transaction_id=txn.transaction_id,
                    user_id=txn.user_id,
                    reason=f"Spending velocity: ${total_spent:,.2f} in 10 min",
                    risk_score=risk,
                    flagged_at=now,
                )
            )

        # --- Rule 5: Merchant diversity ---
        current_merchants_str = merchant_diversity[txn.user_id].current()
        if current_merchants_str:
            merchants_set = set(current_merchants_str.split(","))
        else:
            merchants_set = set()

        merchants_set.add(txn.merchant)
        merchant_diversity[txn.user_id] = ",".join(merchants_set)

        if len(merchants_set) > MERCHANT_DIVERSITY_THRESHOLD:
            alerts.append(
                FraudAlert(
                    transaction_id=txn.transaction_id,
                    user_id=txn.user_id,
                    reason=(
                        f"Merchant diversity: {len(merchants_set)} unique "
                        f"merchants in 5 min"
                    ),
                    risk_score=0.5,
                    flagged_at=now,
                )
            )

        # --- Publish alerts ---
        for alert in alerts:
            await fraud_alerts_topic.send(value=alert)
            print(
                f"[FRAUD] {alert.user_id} | {alert.reason} | "
                f"risk={alert.risk_score:.2f}"
            )

        if not alerts:
            print(
                f"[OK] {txn.user_id} txn={txn.transaction_id} "
                f"${txn.amount:,.2f} at {txn.merchant}"
            )


# ---------------------------------------------------------------------------
# Web Views
# ---------------------------------------------------------------------------


@app.page("/fraud/velocity/{user_id}/")
async def velocity_view(web, request, user_id):
    """Return the current spending velocity for a user."""
    try:
        current_spend = spending_velocity[user_id].current()
    except Exception:
        current_spend = 0.0

    try:
        txn_count = transaction_counts[user_id].current()
    except Exception:
        txn_count = 0

    try:
        merchants_str = merchant_diversity[user_id].current()
        unique_merchants = len(set(merchants_str.split(","))) if merchants_str else 0
    except Exception:
        unique_merchants = 0

    return web.json(
        {
            "user_id": user_id,
            "spending_velocity_10min": round(current_spend, 2),
            "transaction_count_5min": txn_count,
            "unique_merchants_5min": unique_merchants,
            "last_country": last_country.get(user_id, "unknown"),
            "thresholds": {
                "velocity": VELOCITY_THRESHOLD,
                "frequency": HIGH_FREQ_THRESHOLD,
                "high_value": HIGH_VALUE_THRESHOLD,
                "merchant_diversity": MERCHANT_DIVERSITY_THRESHOLD,
            },
        }
    )


@app.page("/fraud/stats/")
async def fraud_stats(web, request):
    """Return overview of tracked users."""
    countries = {k: v for k, v in last_country.items()}
    return web.json({"tracked_users": len(countries), "countries": countries})


if __name__ == "__main__":
    app.main()
