# Exercise 2: Add Grafana Alerts for Anomalies

## Objective

Configure Grafana alerting to detect anomalies in the e-commerce streaming pipeline and notify operators when action is required.

## Background

A real-time dashboard is useful for at-a-glance monitoring, but production systems need proactive alerting. In this exercise, you will create alert rules that fire when key metrics deviate from normal patterns.

## Requirements

### Alert 1: Revenue Drop

Create an alert that fires when the **total revenue per minute drops below $10** for 3 consecutive minutes.

**Setup steps:**
1. In Grafana, navigate to Alerting > Alert rules > New alert rule.
2. Use the PostgreSQL datasource.
3. Query:
   ```sql
   SELECT
     window_start AS "time",
     total_revenue AS "value"
   FROM revenue_per_minute
   WHERE window_start >= NOW() - INTERVAL '5 minutes'
   ORDER BY window_start DESC
   LIMIT 3;
   ```
4. Condition: `WHEN avg() OF query IS BELOW 10`
5. Evaluate every 1 minute, for 3 minutes.

### Alert 2: High Cancellation Rate

Create an alert when the **cancellation count exceeds 20% of total orders** in the status distribution.

**Setup steps:**
1. Query:
   ```sql
   SELECT
     COALESCE(
       (SELECT count FROM order_status_counts WHERE status = 'cancelled'),
       0
     )::float /
     NULLIF(
       (SELECT SUM(count) FROM order_status_counts),
       0
     ) * 100 AS cancellation_rate;
   ```
2. Condition: `WHEN last() OF query IS ABOVE 20`
3. Evaluate every 2 minutes, for 5 minutes.

### Alert 3: No New Orders

Create an alert when **no new orders arrive for 5 consecutive minutes** (pipeline stall detection).

**Setup steps:**
1. Query:
   ```sql
   SELECT
     COUNT(*) AS recent_orders
   FROM revenue_per_minute
   WHERE window_start >= NOW() - INTERVAL '5 minutes';
   ```
2. Condition: `WHEN last() OF query IS BELOW 1`
3. Evaluate every 1 minute, for 5 minutes.

### Configure a Contact Point

1. Go to Alerting > Contact points.
2. Create a new contact point using the **Email** or **Webhook** type.
3. For testing, you can use Grafana's built-in Alertmanager.
4. Assign the contact point to a Notification Policy.

### Configure Notification Policy

1. Go to Alerting > Notification policies.
2. Edit the default policy to route alerts to your contact point.
3. Set grouping by `alertname`.
4. Set group wait to 30s, group interval to 1m, repeat interval to 5m.

## Verification

1. Start the full pipeline with `./setup.sh`.
2. Let it run for a few minutes until alerts evaluate.
3. Stop the simulator to trigger the "No New Orders" alert.
4. Check Alerting > Alert rules to see alert states (Normal, Pending, Firing).
5. Verify notifications appear in the contact point history.

## Hints

- Grafana alert rules require queries that return a single numeric value or time series.
- Use the "Classic condition" evaluation type for simple threshold alerts.
- The `for` duration prevents flapping -- the condition must persist for that long before firing.
- You can add labels to alerts (e.g., `severity: critical`) to route them differently.

## Bonus Challenge

1. Add a **Slack webhook** contact point and send alert notifications to a Slack channel.
2. Create a **dashboard annotation** that marks when alerts fire, so you can correlate alert events with dashboard data.
3. Implement an alert for **inventory running low** (any product with stock_quantity < 10).
