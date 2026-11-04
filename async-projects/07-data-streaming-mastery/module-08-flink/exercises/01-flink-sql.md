# Exercise 1: Flink SQL

## Prerequisites

1. Start the Flink stack: `./src/setup_flink.sh`
2. Seed data: `python src/seed_data.py` (let it run in the background)
3. Open the Flink SQL Client: `docker exec -it flink-sql-client /opt/flink/bin/sql-client.sh`
4. Run the table creation script: `sql/01-create-kafka-tables.sql`

---

## Exercise 1.1: Real-Time Order Dashboard

**Goal:** Create a real-time dashboard showing order metrics in 5-minute tumbling windows.

**Requirements:**
- Read from the `orders` Kafka source table
- Create a 5-minute tumbling window based on `order_time`
- For each window, compute:
  - Total number of orders
  - Total revenue
  - Average order value
  - Number of distinct customers
- Write results to a new Kafka topic `order-dashboard-5min` using upsert-kafka

**Hints:**
- Use `TUMBLE(order_time, INTERVAL '5' MINUTE)` for windowing
- Use `COUNT(DISTINCT customer_id)` for distinct customer count
- The sink needs a PRIMARY KEY for upsert-kafka

**Verification:**
- Check the `order-dashboard-5min` topic in Kafka UI (http://localhost:8080)
- You should see one record per 5-minute window with aggregated metrics

---

## Exercise 1.2: Sliding Window Anomaly Detection

**Goal:** Detect periods of unusually high order volume using a sliding window.

**Requirements:**
- Use a 10-minute sliding window that advances every 1 minute (HOP window)
- Compute the rolling order count and average order value
- Filter to only emit windows where the order count exceeds 15 (potential spike)
- Write results to a `print` sink so you can observe the output

**Hints:**
- Use `HOP(order_time, INTERVAL '1' MINUTE, INTERVAL '10' MINUTE)`
- You can filter aggregation results using a `HAVING` clause
- A print sink is useful for debugging: `'connector' = 'print'`

**Verification:**
- Watch the TaskManager logs: `docker logs -f flink-taskmanager`
- You should see output only when a 10-minute window has more than 15 orders

---

## Exercise 1.3: Multi-Table Join with Windowed Output

**Goal:** Enrich orders with customer and product data, then aggregate revenue by product category per minute.

**Requirements:**
1. Join the `orders` table with `customers` and `products` tables
2. Group by product category within 1-minute tumbling windows
3. Compute: category, order count, total revenue, and the most common order status
4. Create a Kafka sink table `revenue-by-category-per-minute` and write results there

**Hints:**
- For a three-way join: `FROM orders o JOIN customers c ON ... JOIN products p ON ...`
- Window the joined result with `TUMBLE(o.order_time, INTERVAL '1' MINUTE)`
- For "most common status," you can use a simpler approach: just count per category (skip the mode calculation if it's too complex)

**Verification:**
- Check the `revenue-by-category-per-minute` topic in Kafka UI
- Each record should contain: window_start, window_end, category, order_count, total_revenue
