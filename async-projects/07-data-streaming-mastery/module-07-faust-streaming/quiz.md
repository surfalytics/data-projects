# Module 7 Quiz: Stream Processing with Faust

Test your understanding of Faust stream processing concepts.

---

### Question 1

What is the correct package to install for the maintained fork of Faust?

A) `faust`
B) `robinhood-faust`
C) `faust-streaming`
D) `kafka-faust`

---

### Question 2

Which Faust abstraction is responsible for processing a stream of events from a Kafka topic?

A) Table
B) Record
C) App
D) Agent

---

### Question 3

What is the purpose of a Faust `Record`?

A) To store state in RocksDB
B) To define typed models for message serialization and deserialization
C) To create Kafka topics
D) To manage consumer group offsets

---

### Question 4

How does Faust achieve fault-tolerant state in Tables?

A) By writing state to a PostgreSQL database
B) By backing tables with Kafka changelog topics and optionally RocksDB for local persistence
C) By replicating state across all workers via gossip protocol
D) By periodically checkpointing state to HDFS

---

### Question 5

Which of the following correctly creates a 5-minute tumbling window on a Faust Table?

A) `app.Table('counts', default=int).window(minutes=5)`
B) `app.Table('counts', default=int).tumbling(300)`
C) `app.Table('counts', default=int).tumbling(timedelta(seconds=300))`
D) Both B and C are correct

---

### Question 6

What is the difference between tumbling and hopping windows in Faust?

A) Tumbling windows overlap; hopping windows do not
B) Tumbling windows are non-overlapping fixed-size windows; hopping windows overlap with a configurable step size
C) There is no difference; they are aliases for the same concept
D) Tumbling windows are time-based; hopping windows are count-based

---

### Question 7

How do you access the value of a windowed table for the current window?

A) `table[key]`
B) `table[key].current()`
C) `table.get_current(key)`
D) `table[key].now()`

---

### Question 8

Which of the following is a valid way to scale a Faust application horizontally?

A) Increase the `concurrency` parameter on agents
B) Run multiple Faust worker processes that share the same app name and consumer group
C) Deploy the app on a Flink cluster
D) Add more Kafka brokers only (no changes to Faust)

---

### Question 9

What built-in feature does Faust provide for exposing table state over HTTP?

A) REST API auto-generated from Record schemas
B) GraphQL endpoint
C) Web views using `@app.page()` decorator backed by aiohttp
D) gRPC service

---

### Question 10

In the stream-table join pattern for enrichment, where does the reference data (e.g., customer info) typically come from?

A) A REST API called for each event
B) A database query for each event
C) A Faust Table populated from a compacted Kafka topic
D) A static file loaded at startup

---

---

## Answers

1. **C** -- `faust-streaming` is the maintained community fork. The original `faust` package from Robinhood is no longer maintained.

2. **D** -- An Agent is an async function decorated with `@app.agent()` that processes a stream of events from a topic.

3. **B** -- Records are typed model classes (similar to dataclasses) that provide automatic JSON serialization and deserialization for Kafka messages.

4. **B** -- Faust Tables are backed by Kafka changelog topics for durability and can use RocksDB for fast local state storage. On restart, state is restored from the changelog.

5. **D** -- Both `tumbling(300)` (integer seconds) and `tumbling(timedelta(seconds=300))` are valid ways to create a 5-minute tumbling window.

6. **B** -- Tumbling windows are non-overlapping, fixed-size time windows. Hopping windows have a fixed size but advance by a configurable step, so they overlap.

7. **B** -- `.current()` returns the value for the current (most recent) window. Without it, you get a `WindowSet` object, not a scalar value.

8. **B** -- Faust scales horizontally by running multiple worker processes with the same app name. Kafka automatically rebalances partitions across workers.

9. **C** -- Faust includes a built-in web server (aiohttp) with the `@app.page()` decorator for defining HTTP endpoints that can query tables and return JSON.

10. **C** -- The standard pattern is to populate a Faust Table from a compacted Kafka topic containing reference data. The agent then joins incoming events with the table for enrichment.
