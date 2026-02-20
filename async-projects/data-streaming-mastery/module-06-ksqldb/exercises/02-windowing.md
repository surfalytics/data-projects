# Exercise 2: Windowed Aggregations

## Prerequisites

- All services running (`docker compose up -d`)
- Seed data producing (`python src/seed_topics.py`)
- Streams and tables created (run `bash src/setup_ksqldb.sh` or Exercise 1)

Open the ksqlDB CLI:
```bash
docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
```

Set the offset to earliest so you can see historical data:
```sql
SET 'auto.offset.reset' = 'earliest';
```

---

## Exercise 2.1: Tumbling Window -- Orders Per Minute

**Task:** Write a push query that counts the number of orders and calculates
total revenue per `customer_id` in **1-minute tumbling windows**.

Your output should include:
- `customer_id`
- `order_count` (COUNT)
- `total_revenue` (SUM of price * quantity)
- `WINDOWSTART`
- `WINDOWEND`

**Questions to consider:**
1. How many windows does each order belong to?
2. What happens when a new minute starts -- do you see a new row or an update?
3. Why does `WINDOWSTART` appear as a large number (epoch milliseconds)?

---

## Exercise 2.2: Hopping Window -- Smoothed Revenue

**Task:** Write a push query that calculates average order value per
`product_id` using a **hopping window** with:
- Window size: 10 minutes
- Advance interval: 2 minutes

Your output should include:
- `product_id`
- `avg_order_value` (AVG of price * quantity)
- `order_count` (COUNT)

**Questions to consider:**
1. How many windows does a single order appear in? (Hint: size / advance)
2. Why might you prefer a hopping window over a tumbling window for a
   real-time dashboard?

---

## Exercise 2.3: Session Window -- User Engagement

**Task:** Write a push query on the `clickstream_stream` that groups page
views into **session windows** with a 3-minute inactivity gap, grouped by
`user_id`.

Your output should include:
- `user_id`
- `pages_viewed` (COUNT)
- `WINDOWSTART` (session start)
- `WINDOWEND` (session end)

**Bonus:** Create this as a persistent query (materialized view) using
`CREATE TABLE ... AS SELECT`. Then run a pull query to look up a specific
user's session data.

**Questions to consider:**
1. What determines when a session "closes"?
2. If a user views 5 pages in quick succession, then waits 4 minutes, then
   views 2 more pages -- how many sessions are created?
3. How does ksqlDB handle late-arriving events in session windows?
