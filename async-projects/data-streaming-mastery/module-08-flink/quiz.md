# Module 8 Quiz: Apache Flink

Test your understanding of Apache Flink concepts. Choose the best answer for each question.

---

### Question 1: Flink Architecture

What is the role of the **JobManager** in a Flink cluster?

- A) It executes the data processing tasks across multiple threads
- B) It coordinates job execution, scheduling, checkpointing, and failover
- C) It stores the state of all running operators on disk
- D) It manages the Kafka consumer group offsets

---

### Question 2: Task Slots

What is a **task slot** in Flink?

- A) A time window during which a task can execute
- B) A fixed subset of a TaskManager's resources that can run one parallel pipeline
- C) A position in a Kafka partition assigned to a Flink consumer
- D) A placeholder for a checkpoint barrier in the data stream

---

### Question 3: Checkpointing

How does Flink achieve **exactly-once** processing semantics?

- A) By replaying all messages from the beginning after every failure
- B) By using distributed locks to prevent concurrent processing
- C) By periodically injecting checkpoint barriers into the stream and snapshotting operator state
- D) By deduplicating output records using a hash-based filter

---

### Question 4: Watermarks

What does a **watermark** with value `W = 10:05:00` mean?

- A) All events before 10:05:00 have been processed and their windows can be closed
- B) No events with a timestamp less than 10:05:00 are expected to arrive after this point
- C) The processing time of the Flink cluster is 10:05:00
- D) The Kafka consumer has read up to offset 10:05:00

---

### Question 5: Window Types

Which window type creates **overlapping** windows where a single event can belong to multiple windows?

- A) Tumbling window
- B) Session window
- C) Sliding (hopping) window
- D) Global window

---

### Question 6: State Backends

When should you use **EmbeddedRocksDBStateBackend** instead of **HashMapStateBackend**?

- A) When you need the fastest possible read/write performance
- B) When your application state is small and fits in JVM heap
- C) When your application state is very large (potentially exceeding available memory)
- D) When you want to avoid serialization overhead

---

### Question 7: Flink SQL

What is the purpose of the `WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND` clause in a Flink SQL `CREATE TABLE` statement?

- A) It delays all events by 5 seconds before processing
- B) It declares that events may arrive up to 5 seconds late and sets event_time as the event-time attribute
- C) It filters out all events older than 5 seconds
- D) It creates a 5-second tumbling window on the event_time column

---

### Question 8: Flink CDC

What is the key advantage of **Flink CDC** over using **Debezium + Kafka Connect** for change data capture?

- A) Flink CDC supports more database types
- B) Flink CDC eliminates the need for a separate Connect cluster and enables inline stream processing
- C) Flink CDC is the only way to get exactly-once semantics
- D) Flink CDC does not require database binlog access

---

### Question 9: Savepoints vs Checkpoints

Which statement correctly describes the difference between **savepoints** and **checkpoints**?

- A) Savepoints are triggered automatically; checkpoints are triggered manually
- B) Savepoints are for crash recovery; checkpoints are for planned maintenance
- C) Savepoints are triggered manually for planned operations (upgrades, scaling); checkpoints are triggered automatically for fault tolerance
- D) There is no functional difference; the terms are interchangeable

---

### Question 10: Upsert-Kafka Connector

When should you use the **upsert-kafka** connector instead of the standard **kafka** connector in Flink SQL?

- A) When reading from a Kafka topic with multiple partitions
- B) When the query produces a changelog stream (updates and deletes), such as aggregation results
- C) When you need higher throughput for append-only writes
- D) When the Kafka topic uses Avro serialization

---

## Answers

1. **B** -- The JobManager is the master process that coordinates job execution, schedules tasks across TaskManagers, triggers checkpoints, and handles failover when TaskManagers fail.

2. **B** -- A task slot is a fixed subset of a TaskManager's resources (primarily memory). Each slot can run one parallel pipeline of chained operators, allowing multiple tasks to share a single JVM process.

3. **C** -- Flink achieves exactly-once semantics by periodically injecting checkpoint barriers into the data stream. When all operators have received a barrier and snapshotted their state, the checkpoint is complete. On failure, Flink restores from the last successful checkpoint.

4. **B** -- A watermark W = 10:05:00 is a declaration that no events with a timestamp earlier than 10:05:00 are expected to arrive. This allows Flink to safely close windows whose end time is at or before 10:05:00.

5. **C** -- Sliding (hopping) windows create overlapping windows. For example, a 10-minute window sliding every 1 minute means an event at 10:05 belongs to windows [09:56-10:06), [09:57-10:07), ..., [10:05-10:15). Tumbling windows are non-overlapping.

6. **C** -- EmbeddedRocksDBStateBackend stores state on local disk (SSD) using RocksDB, allowing state to exceed available memory. It also supports incremental checkpoints. Use it for production workloads with large state. HashMapStateBackend is faster but limited by JVM heap.

7. **B** -- The WATERMARK clause serves two purposes: (1) it designates event_time as the event-time attribute for the table, and (2) it defines the watermark strategy, declaring that events may arrive up to 5 seconds late (out of order).

8. **B** -- Flink CDC reads database changelogs directly into the Flink engine, eliminating the need for a separate Kafka Connect cluster. This reduces architectural complexity, lowers latency (no extra hop through Kafka), and allows inline transformations with Flink SQL or the DataStream API.

9. **C** -- Checkpoints are automatic, periodic snapshots for fault tolerance (managed by Flink). Savepoints are manual, user-triggered snapshots designed for planned operations like job upgrades, scaling changes, or migration. Savepoints are portable and not automatically cleaned up.

10. **B** -- The upsert-kafka connector is needed when the query produces a changelog stream with updates and deletes (e.g., aggregations, joins on CDC tables). It uses a primary key to determine which records to update or delete. The standard kafka connector only supports append-only (INSERT) output.
