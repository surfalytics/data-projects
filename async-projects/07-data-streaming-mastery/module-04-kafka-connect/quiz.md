# Module 4: Kafka Connect Quiz

Test your understanding of Kafka Connect concepts. Choose the best answer for each question.

---

### Question 1: What is the primary purpose of Kafka Connect?

A) To provide a SQL interface for querying Kafka topics
B) To scalably and reliably stream data between Kafka and other systems
C) To manage Kafka broker configurations
D) To monitor Kafka cluster health

---

### Question 2: In distributed mode, where does Kafka Connect store connector configurations?

A) In a local file on each worker node
B) In ZooKeeper
C) In internal Kafka topics
D) In an external database

---

### Question 3: What is the difference between a connector and a task in Kafka Connect?

A) A connector is a JVM process; a task is a thread
B) A connector defines the job; tasks are the units of work that execute data copying
C) They are the same thing with different names
D) A task creates connectors; a connector creates topics

---

### Question 4: Which JDBC source connector mode detects both new rows AND updates to existing rows?

A) `bulk`
B) `incrementing`
C) `timestamp`
D) `timestamp+incrementing`

---

### Question 5: What does the `errors.tolerance=all` configuration do?

A) Retries failed records indefinitely
B) Skips bad records and continues processing
C) Stops the connector on any error
D) Sends all records to the dead letter queue

---

### Question 6: Which SMT would you use to add the current processing timestamp to every record?

A) `TimestampRouter`
B) `TimestampConverter`
C) `InsertField`
D) `ReplaceField`

---

### Question 7: What is the role of a converter in Kafka Connect?

A) It transforms record values using SMTs
B) It controls how data is serialized to and deserialized from Kafka
C) It converts Kafka topics to database tables
D) It converts standalone mode to distributed mode

---

### Question 8: Which REST API endpoint would you use to check if a connector and its tasks are running?

A) `GET /connectors/{name}`
B) `GET /connectors/{name}/config`
C) `GET /connectors/{name}/status`
D) `GET /connectors/{name}/tasks`

---

### Question 9: What happens in distributed mode when a Kafka Connect worker crashes?

A) All connectors stop permanently
B) The remaining workers automatically rebalance and take over the failed worker's tasks
C) An administrator must manually restart the tasks
D) The connector configurations are lost

---

### Question 10: You want to route records to different topics based on a date in the record (e.g., `orders-20240115`). Which SMT should you use?

A) `RegexRouter`
B) `Filter`
C) `TimestampRouter`
D) `ValueToKey`

---

## Answers

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | **B** | Kafka Connect is designed to stream data between Kafka and external systems without writing custom producer/consumer code. |
| 2 | **C** | Distributed mode stores configurations, offsets, and status in internal Kafka topics (`connect-configs`, `connect-offsets`, `connect-status`). |
| 3 | **B** | A connector is the logical job definition. It creates one or more tasks, which are the actual units of work that read/write data. |
| 4 | **D** | `timestamp+incrementing` mode uses both a timestamp column (to detect updates) and an incrementing column (to detect new rows), covering both cases. |
| 5 | **B** | `errors.tolerance=all` tells Connect to skip problematic records rather than failing the task. Bad records can optionally be routed to a dead letter queue. |
| 6 | **C** | `InsertField` with `timestamp.field` adds the current timestamp. `TimestampRouter` changes the topic name, not the record content. |
| 7 | **B** | Converters handle serialization (writing to Kafka) and deserialization (reading from Kafka). Common converters include StringConverter, JsonConverter, and AvroConverter. |
| 8 | **C** | `GET /connectors/{name}/status` returns the state of both the connector and each of its tasks (RUNNING, PAUSED, FAILED, etc.). |
| 9 | **B** | In distributed mode, the remaining workers detect the failure and automatically rebalance, reassigning the orphaned tasks to healthy workers. |
| 10 | **C** | `TimestampRouter` modifies the topic name based on a timestamp, using a configurable date format pattern. `RegexRouter` uses regex patterns on the existing topic name. |
