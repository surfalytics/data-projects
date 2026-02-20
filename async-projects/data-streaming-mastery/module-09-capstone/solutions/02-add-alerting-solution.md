# Solution: Exercise 2 - Add Grafana Alerts for Anomalies

## Alert 1: Revenue Drop

### Step-by-step in Grafana UI

1. Navigate to **Alerting > Alert rules > New alert rule**.

2. **Rule name:** `Low Revenue Alert`

3. **Define query and alert condition:**
   - Datasource: PostgreSQL Analytics
   - Query A (Code mode):
     ```sql
     SELECT
       window_start AS "time",
       total_revenue AS "value"
     FROM revenue_per_minute
     WHERE window_start >= NOW() - INTERVAL '5 minutes'
     ORDER BY window_start;
     ```
   - Expression B (Reduce): Function = `Mean`, Input = A
   - Expression C (Threshold): Input = B, IS BELOW = 10

4. **Set evaluation behavior:**
   - Folder: (create or select a folder, e.g., "E-Commerce Alerts")
   - Evaluation group: Create new, name "Revenue Alerts", evaluate every 1m
   - Pending period: 3m (must be below threshold for 3 consecutive minutes)

5. **Add annotations:**
   - Summary: `Revenue has dropped below $10/minute for 3 consecutive minutes`
   - Description: `The average revenue per minute over the last 5 minutes is {{ $values.B }}. Investigate the order pipeline.`

6. **Add labels:**
   - `severity` = `warning`
   - `team` = `ecommerce`

7. Click **Save rule and exit**.

## Alert 2: High Cancellation Rate

1. **Rule name:** `High Cancellation Rate`

2. **Query A:**
   ```sql
   SELECT
     COALESCE(
       (SELECT count::float FROM order_status_counts WHERE status = 'cancelled'),
       0
     ) /
     NULLIF(
       (SELECT SUM(count)::float FROM order_status_counts),
       0
     ) * 100 AS "value";
   ```

3. **Expression B (Reduce):** Function = Last, Input = A
4. **Expression C (Threshold):** Input = B, IS ABOVE = 20

5. **Evaluation:**
   - Evaluate every 2m
   - Pending period: 5m

6. **Annotations:**
   - Summary: `Cancellation rate exceeds 20%`
   - Description: `Current cancellation rate is {{ $values.B }}%. Review recent orders for patterns.`

7. **Labels:** `severity` = `critical`

## Alert 3: No New Orders (Pipeline Stall)

1. **Rule name:** `Pipeline Stall - No Orders`

2. **Query A:**
   ```sql
   SELECT
     COUNT(*)::float AS "value"
   FROM revenue_per_minute
   WHERE window_start >= NOW() - INTERVAL '5 minutes';
   ```

3. **Expression B (Reduce):** Function = Last, Input = A
4. **Expression C (Threshold):** Input = B, IS BELOW = 1

5. **Evaluation:**
   - Evaluate every 1m
   - Pending period: 5m

6. **Annotations:**
   - Summary: `No new orders in the last 5 minutes`
   - Description: `The pipeline may be stalled. Check: (1) Simulator is running, (2) Debezium connector status, (3) ksqlDB health.`

7. **Labels:** `severity` = `critical`

## Contact Point Configuration

### Email (for development/testing)

1. Go to **Alerting > Contact points > Add contact point**.
2. Name: `Email Notifications`
3. Integration: Email
4. Addresses: `your-email@example.com`
5. (Grafana must have SMTP configured in `grafana.ini` for email to work.)

### Webhook (simpler for testing)

1. Name: `Webhook Notifications`
2. Integration: Webhook
3. URL: `http://httpbin.org/post` (or any endpoint you control)
4. HTTP Method: POST

### Using Grafana Alertmanager (built-in, no external config needed)

The built-in Alertmanager works out of the box. Alerts will appear in the **Alerting > Alert rules** page with states:
- **Normal:** Condition is not met.
- **Pending:** Condition is met, waiting for the `for` duration to elapse.
- **Firing:** Condition has persisted for the required duration.

## Notification Policy

1. Go to **Alerting > Notification policies**.
2. Edit the **Default policy**:
   - Contact point: Select your contact point
   - Group by: `alertname`
   - Group wait: 30s
   - Group interval: 1m
   - Repeat interval: 5m

## Testing the Alerts

```bash
# 1. Start the platform
./setup.sh

# 2. Wait a few minutes for data to accumulate

# 3. Stop the simulator to trigger "No New Orders"
pkill -f ecommerce_simulator.py

# 4. Check Grafana Alerting > Alert rules -- the Pipeline Stall alert
#    should transition: Normal -> Pending -> Firing

# 5. Restart the simulator to resolve the alert
cd src && python3 ecommerce_simulator.py --speed 2 --duration 600 &
```

## Bonus: Dashboard Annotations from Alerts

To show alert events on your dashboard:

1. Open the E-Commerce Real-Time Analytics dashboard.
2. Click Settings (gear icon) > Annotations.
3. Add new annotation query:
   - Name: `Alert Events`
   - Data source: `-- Grafana --`
   - Filter by: Dashboard alerts
   - Color: Red
4. Save the dashboard.

Now when alerts fire, red vertical lines will appear on time series panels, correlating alert events with metric data.
