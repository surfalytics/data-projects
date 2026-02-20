# Exercise 2: PyFlink

## Prerequisites

1. Start the Flink stack: `./src/setup_flink.sh`
2. Seed data: `python src/seed_data.py` (let it run in the background)
3. Install PyFlink: `pip install apache-flink==1.17.2`

---

## Exercise 2.1: PyFlink Order Filter and Transform

**Goal:** Write a PyFlink application that filters high-value orders and transforms them into a simplified format.

**Requirements:**
- Create a PyFlink `TableEnvironment` in streaming mode
- Define a Kafka source table reading from the `orders` topic
- Filter orders where `amount > 50.00`
- Transform each order into a simplified record containing:
  - `order_id`
  - `amount`
  - `order_status`
  - `order_time`
  - A new computed field `value_tier`: "premium" if amount > 200, "standard" if amount > 100, "basic" otherwise
- Write results to a new Kafka topic `filtered-orders` using the standard kafka connector

**Hints:**
- Use `CASE WHEN ... THEN ... ELSE ... END` for the value_tier computation
- You can define the entire pipeline in Flink SQL executed via `t_env.execute_sql()`
- Remember to configure checkpointing for fault tolerance

**Expected Output File:** `solutions/exercise_2_1_order_filter.py`

---

## Exercise 2.2: PyFlink Custom Aggregation

**Goal:** Write a PyFlink application that computes per-customer order statistics using a tumbling window.

**Requirements:**
- Read from the `orders` Kafka topic with event-time watermarks (5-second tolerance)
- Group by `customer_id` within 2-minute tumbling windows
- For each customer-window, compute:
  - Number of orders
  - Total amount spent
  - Average order value
  - Maximum single order amount
- Write results to a Kafka topic `customer-order-stats` using upsert-kafka

**Hints:**
- The source table needs `WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND`
- The sink needs a composite PRIMARY KEY: `(customer_id, window_start)`
- Use `TUMBLE(order_time, INTERVAL '2' MINUTE)` for windowing

**Expected Output File:** `solutions/exercise_2_2_customer_stats.py`

---

## Exercise 2.3: PyFlink Multi-Sink Pipeline

**Goal:** Write a single PyFlink application that reads orders and writes to multiple sinks simultaneously.

**Requirements:**
- Read from the `orders` Kafka topic
- Create three output paths (all running in the same Flink application):
  1. **All orders** -> print sink (for debugging)
  2. **Order count per minute** -> Kafka topic `orders-per-minute` (upsert-kafka)
  3. **Orders by status** -> Kafka topic `orders-by-status` (upsert-kafka)

**Hints:**
- Each `INSERT INTO ... SELECT ...` statement creates a separate Flink job
- You can submit multiple jobs from the same PyFlink script
- Only call `.wait()` on the last job to keep the script running

**Expected Output File:** `solutions/exercise_2_3_multi_sink.py`
