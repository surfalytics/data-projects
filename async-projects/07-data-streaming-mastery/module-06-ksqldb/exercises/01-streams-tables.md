# Exercise 1: Streams and Tables

## Prerequisites

- `docker compose up -d` is running
- `python src/seed_topics.py` is producing data
- `bash src/setup_ksqldb.sh` has been executed (or you will create objects manually)

Open the ksqlDB CLI:
```bash
docker exec -it ksqldb-cli ksql http://ksqldb-server:8088
```

---

## Exercise 1.1: Create a Stream from the Clickstream Topic

The `clickstream` topic contains page-view events with these fields:
- `user_id` (VARCHAR) -- the user who viewed the page
- `page` (VARCHAR) -- the URL path
- `referrer` (VARCHAR) -- the referring source
- `timestamp` (VARCHAR) -- ISO 8601 timestamp

**Task:** Write a `CREATE STREAM` statement for the `clickstream` topic.
Use `user_id` as the KEY and `JSON` as the value format.

**Verification:** Run `DESCRIBE clickstream_stream;` to confirm the schema.

---

## Exercise 1.2: Create a Table from the Products Topic

The `products` topic contains product records with these fields:
- `product_id` (VARCHAR) -- unique product identifier
- `name` (VARCHAR) -- product name
- `category` (VARCHAR) -- product category
- `price` (DOUBLE) -- product price

**Task:** Write a `CREATE TABLE` statement for the `products` topic.
Use `product_id` as the PRIMARY KEY and `JSON` as the value format.

**Verification:** Run `DESCRIBE products_table;` and confirm the columns.

**Bonus question:** Why do we use `PRIMARY KEY` for tables but `KEY` for
streams? What happens when two messages with the same `product_id` arrive?

---

## Exercise 1.3: Create a Derived Stream (Filtered)

**Task:** Create a new stream called `electronics_clicks` that contains only
clickstream events where the `page` starts with `/products/electronics`.

Hint: Use `CREATE STREAM ... AS SELECT ... WHERE ...` with the `LIKE` operator.

**Verification:**
1. Run `SHOW STREAMS;` to confirm `ELECTRONICS_CLICKS` exists.
2. Run a push query to see events: `SELECT * FROM electronics_clicks EMIT CHANGES;`
3. Check the underlying Kafka topic: `PRINT 'ELECTRONICS_CLICKS' FROM BEGINNING LIMIT 5;`
