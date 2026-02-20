# Exercise 03: Extending the Fraud Detection System

## Prerequisites

- Kafka running locally (`docker-compose up -d` from the module root)
- `faust-streaming` installed (`pip install -r requirements.txt`)
- Review `src/fraud_detection.py` to understand the existing fraud detection agent

---

## Exercise 3.1: Velocity-Based Fraud Detection

**Objective:** Extend the fraud detection system with a velocity check that flags users whose spending velocity (total amount in a time window) exceeds a threshold.

**Requirements:**

1. Start from the existing `src/fraud_detection.py` as a reference (or build fresh).
2. Add a new windowed table `"spending-velocity"` (tumbling, 10-minute window, default=float) that tracks total spending per user.
3. Add a new fraud rule: **Spending Velocity**
   - If a user spends more than $10,000 total in a 10-minute window, flag it.
   - The risk score should scale from 0.6 (just over $10,000) to 1.0 ($20,000+).
4. Add a new windowed table `"merchant-diversity"` (tumbling, 5-minute window) that tracks the set of unique merchants per user (store as a string of comma-separated merchant names).
5. Add another fraud rule: **Merchant Diversity**
   - If a user transacts at more than 4 unique merchants in 5 minutes, flag it.
   - Risk score: 0.5.
6. Ensure all alerts are sent to the `"fraud-alerts"` topic with proper `FraudAlert` records.
7. Add a web view at `/fraud/velocity/{user_id}/` that returns the current spending velocity for a given user.

**Hints:**
- For the merchant set, you cannot store a Python `set` directly in a Faust table. Store a comma-separated string and split it to count unique merchants.
- Calculate risk_score for velocity: `min(0.6 + (total - 10000) / 25000, 1.0)`.

**File:** Save your solution as `solutions/exercise_03_1_velocity_fraud.py`

---

## Exercise 3.2: Fraud Alert Aggregator and Reporter

**Objective:** Build a downstream agent that consumes the `fraud-alerts` topic, aggregates alerts by user, and produces a summary report.

**Requirements:**

1. Create a Faust app named `"fraud-reporter-app"`.
2. Define a `FraudSummary` Record with: `user_id` (str), `alert_count` (int), `total_risk_score` (float), `avg_risk_score` (float), `reasons` (str), `last_alert_at` (datetime).
3. Create a table `"fraud-summaries"` (default=dict) to accumulate per-user fraud data.
4. Create an output topic `"fraud-summaries"` with `value_type=FraudSummary`.
5. Write an agent that:
   - Reads from `"fraud-alerts"`.
   - For each alert, updates the user's summary in the table: increment alert_count, add to total_risk_score, append the reason (keep last 5 reasons), update last_alert_at.
   - Every time a user's alert count crosses a multiple of 3 (3, 6, 9, ...), publishes a `FraudSummary` to the output topic.
6. Add a web view at `/fraud/report/` that returns all user summaries sorted by alert_count descending.
7. Add a web view at `/fraud/report/{user_id}/` that returns the summary for a specific user.

**Hints:**
- Store reasons as a comma-separated string. Split, append, keep last 5, rejoin.
- Check `alert_count % 3 == 0` to decide when to publish a summary.
- Compute `avg_risk_score = total_risk_score / alert_count`.

**File:** Save your solution as `solutions/exercise_03_2_fraud_reporter.py`
