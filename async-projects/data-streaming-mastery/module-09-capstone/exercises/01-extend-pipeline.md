# Exercise 1: Extend the Pipeline - Returns Rate Metric

## Objective

Add a new real-time metric to the pipeline: **Returns Rate** -- the percentage of delivered orders that have been returned, computed over a sliding window.

## Background

The current pipeline tracks order status counts, but does not compute derived ratios. A returns rate metric is critical for e-commerce operations teams to detect quality issues or fraud patterns in real time.

## Requirements

### 1. ksqlDB Query

Create a new ksqlDB table that computes the returns rate over a 15-minute tumbling window:

- Count orders with status `delivered`
- Count orders with status `returned`
- Compute `returns_rate = returned_count / (delivered_count + returned_count) * 100`
- Output topic: `RETURNS_RATE`

### 2. PostgreSQL Sink Table

Create a new table in PostgreSQL:

```sql
CREATE TABLE IF NOT EXISTS returns_rate (
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    delivered_count INT,
    returned_count INT,
    returns_rate_pct DECIMAL(5,2),
    PRIMARY KEY (window_start, window_end)
);
```

### 3. Sink the Data

Either:
- Add the new topic to the JDBC Sink Connector configuration, OR
- Extend `sink_consumer.py` to consume from the `RETURNS_RATE` topic

### 4. Grafana Panel

Add a new panel to the Grafana dashboard:
- **Type:** Gauge or Stat panel
- **Title:** "Returns Rate (%)"
- **Thresholds:** Green (0-5%), Yellow (5-10%), Red (>10%)
- **Query:** SELECT the latest returns rate from PostgreSQL

## Hints

- Use ksqlDB `CASE WHEN` expressions to count statuses conditionally within a single query.
- You can use `COUNT_DISTINCT` if you want unique order counts.
- The `HAVING` clause can filter windows with zero delivered orders (to avoid division by zero).

## Verification

1. Run the simulator for a few minutes to generate some returns.
2. Query the returns_rate table: `SELECT * FROM returns_rate ORDER BY window_start DESC LIMIT 5;`
3. Check the Grafana panel shows a percentage value updating in real time.

## Bonus Challenge

Add a Grafana alert rule that fires when the returns rate exceeds 15% in any 15-minute window. Configure it to send a notification (even if just to the Grafana alerting UI).
