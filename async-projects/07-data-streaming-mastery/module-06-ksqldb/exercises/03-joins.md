# Exercise 3: Joins

## Prerequisites

- All services running (`docker compose up -d`)
- Seed data producing (`python src/seed_topics.py`)
- Streams and tables created (run `bash src/setup_ksqldb.sh`)

Open the ksqlDB CLI:
```bash
docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
```

Set the offset to earliest:
```sql
SET 'auto.offset.reset' = 'earliest';
```

---

## Exercise 3.1: Stream-Table Join -- Enrich Orders

**Task:** Write a query that joins `orders_stream` with `customers_table` to
produce enriched order records containing:

- `order_id`
- `customer_id`
- `customer_name` (from customers_table)
- `customer_region` (from customers_table)
- `product_id`
- `quantity`
- `price`
- `order_total` (price * quantity)

Use a LEFT JOIN so that orders are still emitted even if the customer record
is not found.

**Follow-up tasks:**
1. Create this as a persistent stream: `CREATE STREAM enriched_orders_ex AS ...`
2. Write a windowed aggregation on your enriched stream that calculates total
   revenue by `customer_region` in 5-minute tumbling windows.
3. Which region has the highest revenue? Run the push query and observe.

**Questions to consider:**
1. Why must the JOIN condition use the table's PRIMARY KEY?
2. What happens if a customer record is updated after an order was already
   enriched? Does the old enriched order retroactively change?
3. Could you use an INNER JOIN instead? What would be the trade-off?

---

## Exercise 3.2: Double Join -- Fully Enriched Orders

**Task:** Write a single query that joins `orders_stream` with BOTH
`customers_table` AND `products_table` to produce a fully enriched order
stream containing:

- `order_id`
- `customer_name`
- `customer_region`
- `product_name`
- `product_category`
- `quantity`
- `price`
- `order_total` (price * quantity)

**Follow-up tasks:**
1. Create this as a persistent stream.
2. Write a query that counts orders by `product_category` in 5-minute
   tumbling windows.
3. Create a materialized view (table) from this aggregation so you can run
   pull queries against it.

**Questions to consider:**
1. When joining with two tables, does the order of JOINs matter?
2. What underlying Kafka topic is created for your persistent stream?
   (Hint: `SHOW STREAMS;` and check the topic column.)
3. How would you add a third join to include, say, a `warehouses_table`?
