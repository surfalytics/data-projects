# Solutions Explanation

## Exercise 1: Streams and Tables

### 1.1 -- Clickstream Stream

The key insight is choosing `user_id` as the KEY column. This maps to the
Kafka message key and controls how data is partitioned. Downstream GROUP BY
operations on `user_id` will be efficient because the data is already
co-partitioned.

### 1.2 -- Products Table

Tables use `PRIMARY KEY` because they maintain **upsert semantics**. When a
second message arrives with the same `product_id`, the table row is updated
rather than appended. This is fundamentally different from streams.

### 1.3 -- Filtered Stream

`CREATE STREAM ... AS SELECT` creates a **persistent query** -- a continuously
running process that reads from the source stream, applies the filter, and
writes matching events to a new Kafka topic. This is one of the most powerful
patterns in ksqlDB: you build processing pipelines declaratively with SQL.

---

## Exercise 2: Windowed Aggregations

### 2.1 -- Tumbling Windows

Each order belongs to exactly one 1-minute window. The key point is that
ksqlDB emits **intermediate results** as each new event arrives. Within a
single window, you will see the same key (customer_id + window) appear
multiple times with updated counts. The final result is available when the
window closes (plus a grace period).

### 2.2 -- Hopping Windows

With SIZE 10 and ADVANCE 2, each order appears in 5 overlapping windows.
This is useful for **smoothed moving averages** on dashboards. The trade-off
is higher processing cost and more output rows.

### 2.3 -- Session Windows

Sessions are **dynamic** -- their size depends on user activity. A session
closes when no event arrives for the inactivity gap (3 minutes in this case).
This makes them ideal for modeling user engagement, but they are harder to
reason about than fixed windows because session boundaries can shift as
late-arriving events merge sessions.

---

## Exercise 3: Joins

### 3.1 -- Stream-Table Join

The critical concept: stream-table joins are **point-in-time lookups**. When
an order arrives, ksqlDB looks up the current state of the customer in the
table. If the customer updates their info later, previously enriched orders
are NOT retroactively changed. This is by design -- streams represent
immutable facts.

LEFT JOIN vs INNER JOIN: LEFT JOIN is safer in production because it ensures
no data is silently dropped. If a customer record has not yet arrived (race
condition at startup), INNER JOIN would discard those orders permanently.

### 3.2 -- Double Join

Multiple stream-table joins chain naturally. The output stream contains
columns from all three sources. The underlying Kafka topic is auto-created
with the stream name in uppercase.

Creating a materialized view on top of the enriched stream enables pull
queries -- point-in-time lookups that behave like a traditional database
query. This pattern (stream -> enrich -> aggregate -> materialize) is the
core ksqlDB design pattern for building real-time serving layers.
