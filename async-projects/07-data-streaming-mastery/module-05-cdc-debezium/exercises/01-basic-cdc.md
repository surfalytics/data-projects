# Exercise 01 -- Basic CDC Setup and Reading Events

## Prerequisites

Make sure the infrastructure is running:

```bash
cd module-05-cdc-debezium
docker compose up -d
python src/register_connector.py
```

---

## Exercise 1.1: Inspect the Debezium Connector

**Objective:** Understand the Debezium connector configuration and verify it is running.

**Tasks:**

1. Use the Kafka Connect REST API to list all registered connectors.
2. Retrieve the full configuration of the `ecommerce-mysql-source` connector.
3. Check the connector status and verify that both the connector and its task(s) are in the `RUNNING` state.
4. List all Kafka topics and identify which ones were created by Debezium.

**Questions to answer:**
- How many tasks does the connector have?
- What is the `topic.prefix` and how does it relate to the Kafka topic names?
- What snapshot mode is configured?

**Hint:** Use `curl` or `requests` to call `http://localhost:8083/connectors`, `http://localhost:8083/connectors/ecommerce-mysql-source/config`, and `http://localhost:8083/connectors/ecommerce-mysql-source/status`.

---

## Exercise 1.2: Read and Parse Snapshot Events

**Objective:** Write a Python script that reads the initial snapshot events from the `ecommerce.ecommerce.customers` topic, parses the Debezium envelope, and prints each customer's name and email.

**Requirements:**

1. Connect to Kafka at `localhost:9092` with consumer group `exercise-01`.
2. Subscribe to the topic `ecommerce.ecommerce.customers`.
3. Read from the beginning of the topic (`auto.offset.reset = earliest`).
4. For each message:
   - Parse the JSON value.
   - Extract the `payload` (handle the nested `schema`/`payload` structure).
   - Print the operation type (`op`), customer ID, first name, last name, and email.
   - Indicate whether the event is a snapshot event or a live change.
5. Stop after 10 seconds of no new messages.

**Expected output** (approximate):

```
[SNAPSHOT] Customer #1: John Doe (john.doe@example.com)
[SNAPSHOT] Customer #2: Jane Smith (jane.smith@example.com)
[SNAPSHOT] Customer #3: Bob Wilson (bob.wilson@example.com)
[SNAPSHOT] Customer #4: Alice Brown (alice.brown@example.com)
[SNAPSHOT] Customer #5: Charlie Davis (charlie.davis@example.com)
```

---

## Exercise 1.3: Before and After Comparison

**Objective:** Write a Python script that reads events from the `ecommerce.ecommerce.orders` topic, and for each UPDATE event, prints a side-by-side comparison of the `before` and `after` states.

**Requirements:**

1. Subscribe to `ecommerce.ecommerce.orders`.
2. For each event where `op == "u"`:
   - Print the order ID.
   - For every field that differs between `before` and `after`, print the field name with old and new values.
3. For `op == "c"` or `op == "r"` events, just print a summary line (e.g., "New order #4 created").
4. Ignore tombstones (null values).

**Tip:** Before running this script, execute `python src/trigger_changes.py` in another terminal to generate update events.

**Expected output** (approximate):

```
[SNAPSHOT] Order #1: delivered, total=$119.97
[SNAPSHOT] Order #2: shipped, total=$89.99
[SNAPSHOT] Order #3: pending, total=$249.98
[CREATE]   New order #4 created: pending, total=$109.97
[CREATE]   New order #5 created: pending, total=$249.97
[CREATE]   New order #6 created: pending, total=$489.97
[UPDATE]   Order #4: status 'pending' -> 'confirmed'
[UPDATE]   Order #5: status 'pending' -> 'confirmed'
[UPDATE]   Order #6: status 'pending' -> 'confirmed'
[UPDATE]   Order #4: status 'confirmed' -> 'shipped'
...
```
