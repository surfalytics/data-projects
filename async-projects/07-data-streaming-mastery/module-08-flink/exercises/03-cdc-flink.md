# Exercise 3: CDC with Flink

## Prerequisites

1. Start the Flink stack: `./src/setup_flink.sh`
2. Seed data: `python src/seed_data.py` (let it run in the background -- it also generates MySQL updates)
3. Open the Flink SQL Client: `docker exec -it flink-sql-client /opt/flink/bin/sql-client.sh`

---

## Exercise 3.1: Real-Time Order Status Tracker

**Goal:** Build a Flink SQL pipeline that tracks order status changes in MySQL in real time and publishes an enriched status feed to Kafka.

**Requirements:**
1. Create a MySQL CDC source table for `orders` (see `sql/03-cdc-source.sql` for reference)
2. Create a MySQL CDC source table for `customers`
3. Join orders with customers to get the customer name and email
4. Create a Kafka upsert sink table `order-status-tracker` with columns:
   - `order_id` (INT, primary key)
   - `customer_name` (STRING)
   - `customer_email` (STRING)
   - `amount` (DECIMAL)
   - `status` (STRING)
   - `updated_at` (TIMESTAMP)
5. Insert the joined, enriched data into the sink

**Expected Behavior:**
- When a new order is inserted into MySQL, it appears in the Kafka topic within seconds
- When an order's status is updated in MySQL (the seed script does this automatically), the Kafka topic reflects the change
- When a customer's name changes, the enriched orders for that customer update

**Verification:**
- Check the `order-status-tracker` topic in Kafka UI
- Manually update an order in MySQL and verify the change propagates:
  ```sql
  -- Run in MySQL CLI:
  -- docker exec -it flink-mysql mysql -uroot -pdebezium inventory
  UPDATE orders SET status = 'shipped' WHERE order_id = 1;
  ```

**Hints:**
- Use `'connector' = 'mysql-cdc'` for CDC source tables
- Both CDC tables produce a changelog stream; a regular join between them continuously updates
- The upsert-kafka sink handles updates and deletes automatically

**Expected Output:** SQL statements (can be saved as `solutions/exercise_3_1_status_tracker.sql`)

---

## Exercise 3.2: CDC-Powered Real-Time Dashboard

**Goal:** Build a PyFlink application that reads CDC data from MySQL and computes a real-time analytics dashboard with multiple metrics.

**Requirements:**
1. Create MySQL CDC sources for `orders`, `customers`, and `products`
2. Compute three analytics views and write each to a separate Kafka topic:

   **View A: Revenue by City** (`revenue-by-city` topic)
   - Join orders with customers
   - Group by customer city
   - Compute total revenue and order count per city

   **View B: Category Performance** (`category-performance` topic)
   - Join orders with products
   - Group by product category
   - Compute total revenue, average order value, and total quantity sold

   **View C: Hourly Order Trend** (`hourly-order-trend` topic)
   - Use a 1-hour tumbling window on `created_at`
   - Compute order count and total revenue per hour

**Verification:**
- Check all three output topics in Kafka UI
- Insert a new order in MySQL and verify all three views update:
  ```sql
  INSERT INTO orders (customer_id, product_id, quantity, amount, status)
  VALUES (1, 1, 3, 150.00, 'confirmed');
  ```

**Hints:**
- Structure your PyFlink script with separate DDL functions for each table
- Submit all three INSERT INTO queries before calling `.wait()` on the last one
- Use upsert-kafka for all sinks since CDC sources produce changelog streams

**Expected Output File:** `solutions/exercise_3_2_cdc_dashboard.py`
