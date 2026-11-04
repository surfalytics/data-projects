# Module 6 Quiz: ksqlDB

Test your understanding of ksqlDB concepts. Choose the best answer for each
question. Answers are at the bottom.

---

### Question 1

What is the fundamental difference between a ksqlDB **stream** and a **table**?

A) Streams can only hold text data; tables can hold any data type.
B) Streams are append-only (every event is a new row); tables are changelog-based (rows are updated by key).
C) Streams are stored in memory; tables are stored on disk.
D) Tables support SQL; streams do not.

---

### Question 2

Which clause makes a ksqlDB query a **push query** (continuously streaming results)?

A) `LIMIT 100`
B) `WHERE key = 'value'`
C) `EMIT CHANGES`
D) `GROUP BY`

---

### Question 3

In a **tumbling window** of size 5 minutes, how many windows does a single event belong to?

A) 0
B) 1
C) 5
D) It depends on the advance interval

---

### Question 4

In a **hopping window** with SIZE 10 MINUTES and ADVANCE BY 2 MINUTES, how many windows does a single event appear in?

A) 1
B) 2
C) 5
D) 10

---

### Question 5

What is required when performing a **stream-stream join** in ksqlDB?

A) Both streams must have the same key
B) A `WITHIN` clause specifying the time window for the join
C) Both streams must use Avro format
D) The streams must be in the same consumer group

---

### Question 6

In a **stream-table join**, what happens if the table row is updated AFTER an order has already been enriched?

A) The previously emitted enriched record is retroactively updated.
B) The previously emitted enriched record is NOT changed; only future events use the updated table row.
C) ksqlDB throws an error.
D) The enriched record is deleted and re-emitted.

---

### Question 7

What does `CREATE TABLE order_counts AS SELECT customer_id, COUNT(*) FROM orders_stream GROUP BY customer_id EMIT CHANGES;` create?

A) A temporary in-memory table that disappears when ksqlDB restarts.
B) A persistent query that continuously updates a materialized view backed by a Kafka topic.
C) A one-time snapshot of the current counts.
D) A new Kafka consumer group.

---

### Question 8

Which window type should you use to group user clickstream events into **browsing sessions** separated by periods of inactivity?

A) Tumbling window
B) Hopping window
C) Session window
D) Sliding window

---

### Question 9

What is the purpose of a **pull query** in ksqlDB?

A) To continuously stream all changes from a topic.
B) To retrieve the current state of a materialized view at a point in time, then terminate.
C) To pull data from an external database into Kafka.
D) To delete rows from a table.

---

### Question 10

When creating a ksqlDB table from a Kafka topic, why must you specify a `PRIMARY KEY`?

A) Because Kafka requires a key for every message.
B) So ksqlDB can perform upsert behavior -- updating the row when a new message arrives with the same key.
C) To enable encryption of the data at rest.
D) Primary keys are optional; they just improve performance.

---

## Answers

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | **B** | Streams are append-only event logs; tables maintain the latest state per key (changelog semantics). |
| 2 | **C** | `EMIT CHANGES` tells ksqlDB to continuously push new results as data arrives. Without it, the query is a pull query. |
| 3 | **B** | Tumbling windows are non-overlapping. Each event falls into exactly one window. |
| 4 | **C** | With size 10 and advance 2, an event appears in 10/2 = 5 overlapping windows. |
| 5 | **B** | Stream-stream joins require a `WITHIN` clause to bound the time range for matching events from both streams. |
| 6 | **B** | Stream-table joins are point-in-time lookups. Once an event is enriched and emitted, it is immutable. Only future events use the updated table state. |
| 7 | **B** | `CREATE TABLE ... AS SELECT` creates a persistent query (a Kafka Streams application) that writes to an output topic and maintains a materialized view. |
| 8 | **C** | Session windows group events by activity bursts. A session closes after a configurable inactivity gap. |
| 9 | **B** | Pull queries return the current state of a materialized view and terminate -- like a traditional SQL SELECT. |
| 10 | **B** | The primary key enables changelog/upsert semantics. When a message arrives with an existing key, the table row is updated rather than appended. |
