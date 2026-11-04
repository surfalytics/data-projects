# Module 05 Quiz -- Change Data Capture with Debezium

Test your understanding of CDC concepts and Debezium. Choose the single best answer for each question.

---

### Question 1

What is the primary advantage of log-based CDC over query-based CDC?

A) It requires less disk space on the source database
B) It captures DELETE operations and the before-state of rows without impacting source performance
C) It does not require any database configuration
D) It works with databases that do not have a transaction log

---

### Question 2

Which MySQL binary log format does Debezium require?

A) STATEMENT
B) MIXED
C) ROW
D) MINIMAL

---

### Question 3

In a Debezium change event, what does the `op` field value `"r"` represent?

A) A row that was rolled back
B) A row read during the initial snapshot
C) A row that was replicated from another server
D) A row that was restored from a backup

---

### Question 4

For an UPDATE event, what do the `before` and `after` fields contain?

A) `before` is null, `after` contains the new row state
B) `before` contains the old row state, `after` contains the new row state
C) `before` contains the SQL statement, `after` contains the result
D) `before` and `after` both contain the new row state

---

### Question 5

What is the purpose of the schema history topic in Debezium?

A) To store a backup of all table data
B) To record DDL statements so the connector can reconstruct table schemas after a restart
C) To track which consumers have read from each topic
D) To store the Kafka Connect worker configuration

---

### Question 6

What is a tombstone event in the context of Debezium and Kafka?

A) A message indicating the connector has stopped
B) A message with the same key as a deleted row but a null value, enabling log compaction to remove the key
C) An error message produced when Debezium encounters a corrupt binlog entry
D) A heartbeat message sent when no changes occur

---

### Question 7

When does the initial snapshot occur by default?

A) Every time the connector restarts
B) Only when explicitly triggered via the REST API
C) On the connector's first startup, before switching to binlog streaming
D) After every schema change

---

### Question 8

How does Debezium read changes from MySQL?

A) It periodically runs SELECT queries against the tables
B) It uses database triggers to capture changes
C) It connects as a MySQL replica and reads the binary log
D) It monitors the filesystem for changes to MySQL data files

---

### Question 9

What is the Debezium topic naming convention for a table called `orders` in a database called `ecommerce` with topic prefix `myapp`?

A) `myapp.orders`
B) `myapp.ecommerce.orders`
C) `ecommerce.orders`
D) `debezium.myapp.ecommerce.orders`

---

### Question 10

You add a new column `loyalty_tier` to the `customers` table while Debezium is running. What happens?

A) The connector crashes and must be restarted
B) Debezium detects the ALTER TABLE in the binlog, updates its internal schema, and subsequent events include the new column
C) All existing events in Kafka are retroactively updated to include the new column
D) Debezium ignores schema changes and continues using the original schema

---

## Answers

1. **B** -- Log-based CDC reads the transaction log (not the tables), so it has minimal impact on the source. It also captures DELETEs and provides the before-state (the old row values), which query-based CDC cannot do.

2. **C** -- Debezium requires `binlog_format = ROW` because it needs the actual row data (before and after images), not just the SQL statements. STATEMENT format logs the SQL text, which cannot be reliably used to reconstruct row-level changes.

3. **B** -- The operation code `"r"` stands for "read" and indicates the event was produced during the initial snapshot, not from a live binlog change. Snapshot events have `before = null` and `after = <row data>`.

4. **B** -- For UPDATE events (`op = "u"`), `before` contains the complete row state before the change, and `after` contains the complete row state after the change. This allows consumers to see exactly what changed.

5. **B** -- The schema history topic stores DDL statements (CREATE TABLE, ALTER TABLE) along with the binlog position where each DDL was encountered. When the connector restarts, it replays this topic to rebuild its understanding of the table schemas at the current binlog position.

6. **B** -- After producing a DELETE event (with `before` = deleted row data), Debezium emits a second message with the same key but a `null` value. This tombstone tells Kafka's log compactor that the key can be completely removed during compaction.

7. **C** -- With the default `snapshot.mode = initial`, the connector takes a snapshot of all monitored tables on its first startup. After the snapshot completes, it begins streaming from the binlog position recorded at the start of the snapshot. Subsequent restarts skip the snapshot.

8. **C** -- Debezium opens a replication connection to MySQL, identifying itself as a replica server. It then reads binlog events sequentially, just as a real replica would, but instead of applying the changes locally, it converts them into Kafka messages.

9. **B** -- Debezium names topics as `{topic.prefix}.{database}.{table}`. With prefix `myapp`, database `ecommerce`, and table `orders`, the topic is `myapp.ecommerce.orders`.

10. **B** -- Debezium monitors the binlog for DDL statements. When it sees `ALTER TABLE customers ADD COLUMN loyalty_tier ...`, it records the DDL in the schema history topic, updates its in-memory schema representation, and all subsequent events for the `customers` table will include the new column. Events produced before the ALTER are not modified.
