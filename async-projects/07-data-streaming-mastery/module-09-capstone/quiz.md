# Module 9 Quiz: End-to-End Streaming Pipelines

Test your understanding of the complete real-time analytics pipeline built in this capstone project.

---

### Question 1

What is the primary advantage of using Debezium CDC over a polling-based approach (e.g., SELECT queries on a timer) for capturing database changes?

A) Debezium is faster because it uses TCP instead of HTTP
B) Debezium reads the database binlog, capturing changes with low latency and no additional load on the database
C) Debezium writes directly to PostgreSQL, skipping Kafka entirely
D) Debezium only works with MySQL, making it more specialized and efficient

---

### Question 2

In the capstone architecture, what role does Schema Registry play?

A) It stores the actual data records as a backup
B) It manages Avro schemas so producers and consumers can evolve schemas without breaking compatibility
C) It replaces Kafka for small messages
D) It provides authentication for Kafka clients

---

### Question 3

Why does the Debezium source connector configuration include `transforms.unwrap.type: io.debezium.transforms.ExtractNewRecordState`?

A) It compresses the message payload to save disk space
B) It flattens the Debezium change event envelope to expose just the "after" state of the row, making downstream processing simpler
C) It encrypts sensitive fields in the record
D) It converts JSON to Avro format

---

### Question 4

In ksqlDB, what is the difference between a STREAM and a TABLE?

A) Streams are faster than tables
B) A STREAM represents an unbounded sequence of events (inserts), while a TABLE represents the current state derived from a changelog (upserts by key)
C) Tables can only be created from database sources, streams from files
D) There is no practical difference; they are interchangeable

---

### Question 5

The `revenue_per_minute` query uses `WINDOW TUMBLING (SIZE 1 MINUTE)`. What happens to an order event that arrives at 10:00:30?

A) It is placed in the window [10:00:00, 10:01:00)
B) It is placed in both [09:59:30, 10:00:30) and [10:00:00, 10:01:00)
C) It is dropped because tumbling windows only accept events at exact minute boundaries
D) It is placed in the window [10:00:30, 10:01:30)

---

### Question 6

The JDBC Sink Connector is configured with `"insert.mode": "upsert"`. What does this mean?

A) It inserts all records and ignores duplicates silently
B) It inserts new records and updates existing records that match the primary key
C) It deletes existing records before inserting new ones
D) It only inserts records that do not already exist

---

### Question 7

In the `orders_enriched` ksqlDB stream, orders are LEFT JOINed with the customers table. What happens if an order arrives before its customer record has been processed by ksqlDB?

A) The order event is dropped entirely
B) The order event is buffered indefinitely until the customer arrives
C) The order is emitted with NULL values for the customer fields (customer_name, customer_email)
D) ksqlDB throws an error and stops processing

---

### Question 8

Why does the e-commerce simulator use SQLAlchemy connection pooling instead of opening a new connection for each query?

A) SQLAlchemy requires connection pooling; it cannot work without it
B) Connection pooling reuses existing database connections, reducing the overhead of establishing new TCP connections and authentication for each operation
C) Connection pooling ensures that only one query runs at a time
D) It prevents SQL injection attacks

---

### Question 9

The Grafana dashboard has `"refresh": "5s"`. What are the tradeoffs of setting this to a very low value like `"1s"`?

A) There are no tradeoffs; lower refresh intervals are always better
B) Lower refresh intervals increase the query load on PostgreSQL and network traffic, potentially causing performance degradation, especially with many concurrent dashboard viewers
C) Grafana does not support refresh intervals below 5 seconds
D) It would cause data loss in PostgreSQL

---

### Question 10

If the Kafka broker goes down for 2 minutes and then comes back up, what happens to the data produced by the simulator during the outage?

A) All data is permanently lost
B) The simulator's MySQL writes succeed (MySQL is independent), and when Kafka recovers, Debezium resumes from its last committed offset in the binlog, replaying all missed changes
C) The simulator crashes because it cannot write to Kafka directly
D) Debezium starts capturing changes only from the moment Kafka recovers, losing the 2-minute gap

---

## Answers

<details>
<summary>Click to reveal answers</summary>

### Answer 1: **B**
Debezium reads the database's binary log (binlog), which captures every committed change. This means it detects changes with very low latency (sub-second) without executing any SELECT queries against the database, adding zero read load. Polling-based approaches must repeatedly query the database, introducing both latency and load.

### Answer 2: **B**
Schema Registry stores and validates Avro (and other format) schemas. It enforces compatibility rules so that producers can evolve their schemas (e.g., adding a new column) without breaking existing consumers. Every Avro-serialized message in Kafka references a schema ID in the registry.

### Answer 3: **B**
Debezium emits change events wrapped in an envelope containing `before`, `after`, `source`, `op`, and `ts_ms` fields. The `ExtractNewRecordState` SMT (Single Message Transform) unwraps this envelope and outputs just the `after` state, producing a flat record that is much easier for downstream consumers and ksqlDB to process.

### Answer 4: **B**
A STREAM in ksqlDB models an append-only, unbounded sequence of events -- each record is an independent event. A TABLE models the latest state per key -- records with the same key replace previous values, similar to a materialized view. Streams are for events (e.g., "an order was placed"), tables are for entities (e.g., "the current state of customer #42").

### Answer 5: **A**
Tumbling windows are fixed, non-overlapping, aligned to the epoch. A 1-minute tumbling window creates boundaries at [10:00:00, 10:01:00), [10:01:00, 10:02:00), etc. An event at 10:00:30 falls within [10:00:00, 10:01:00). Each event belongs to exactly one window.

### Answer 6: **B**
Upsert mode performs an INSERT if no record with the matching primary key exists, or an UPDATE if a matching record is found. This is essential for streaming sinks where the same key may produce multiple messages (e.g., as windowed aggregations update).

### Answer 7: **C**
A LEFT JOIN ensures that the left side (orders) is always emitted. If the right side (customer) has no matching record yet, the customer fields are filled with NULL. A regular (INNER) JOIN would drop the order. This is a common consideration in stream-table joins.

### Answer 8: **B**
Establishing a database connection involves TCP handshake, authentication, and protocol negotiation. Connection pooling maintains a set of pre-established connections that are reused across requests, dramatically reducing the overhead per query. This is especially important when multiple simulator threads are performing frequent operations.

### Answer 9: **B**
Every refresh cycle triggers SQL queries against PostgreSQL. At 1-second intervals, each panel fires a query per second. With 8 panels and 10 concurrent viewers, that is 80 queries/second on PostgreSQL. This can cause increased CPU usage, connection exhaustion, and slower dashboard rendering. The 5-second default provides near-real-time updates while keeping load manageable.

### Answer 10: **B**
The simulator writes to MySQL, which is completely independent of Kafka. MySQL commits succeed regardless of Kafka's availability. Debezium tracks its position in the MySQL binlog via Kafka Connect offsets. When Kafka recovers, Debezium resumes reading the binlog from where it left off, replaying all changes that occurred during the outage. This is one of the key reliability guarantees of the CDC + Kafka architecture.

</details>
