# Exercise 02 -- Advanced CDC: Filtering, Transforms, and Schema Evolution

## Prerequisites

Make sure the infrastructure is running and the connector is registered:

```bash
cd module-05-cdc-debezium
docker compose up -d
python src/register_connector.py
```

---

## Exercise 2.1: Filtered Event Router

**Objective:** Build a CDC event router that reads from all Debezium topics and routes events to different handlers based on the operation type and table name.

**Requirements:**

1. Subscribe to all six Debezium topics.
2. Implement a routing mechanism:
   - **INSERT events** on `customers` -> print "NEW CUSTOMER ALERT: {name}"
   - **UPDATE events** on `orders` where status changes to `shipped` -> print "SHIPPING NOTIFICATION: Order #{id}"
   - **DELETE events** on any table -> print "DELETION WARNING: {table} #{id}"
   - All other events -> print a one-line summary with table, operation, and row ID.
3. Track and print a count of events routed to each handler.
4. Handle tombstone events gracefully (log but do not crash).

**Bonus:** Add a command-line argument `--route-config` that accepts a JSON file defining routing rules, so the router is configurable without code changes.

---

## Exercise 2.2: Schema Evolution Detector

**Objective:** Write a script that connects to MySQL, performs an `ALTER TABLE` to add a new column, inserts a row using the new column, and then consumes the resulting CDC events to observe how Debezium handles the schema change.

**Tasks:**

1. Connect to MySQL and run:
   ```sql
   ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(20) DEFAULT 'bronze';
   ```
2. Insert a new customer with the `loyalty_tier` set to `'gold'`.
3. Update an existing customer's `loyalty_tier` to `'silver'`.
4. Write a CDC consumer that:
   - Detects when a new field (`loyalty_tier`) first appears in an event.
   - Prints a clear message: "SCHEMA CHANGE DETECTED: 'customers' table now includes 'loyalty_tier'"
   - For subsequent events, prints the loyalty_tier value alongside the customer info.
5. After the exercise, clean up by dropping the column:
   ```sql
   ALTER TABLE customers DROP COLUMN loyalty_tier;
   ```

**Questions to answer:**
- What happens to events for existing customers (before the ALTER) -- do they include `loyalty_tier`?
- What value does `loyalty_tier` have for customers that existed before the column was added?
- Check the schema history topic (`schema-changes.ecommerce`). What do you see?

---

## Exercise 2.3: Dead Letter Queue and Error Handling

**Objective:** Build a robust CDC consumer that handles malformed events, tracks processing failures, and routes problematic messages to a dead letter queue (DLQ) topic.

**Requirements:**

1. Create a Kafka topic named `cdc-dlq` (dead letter queue).
2. Write a consumer that reads from `ecommerce.ecommerce.orders` and for each event:
   - Attempts to validate the event structure (has `payload`, has `op`, has valid `after`/`before`).
   - If validation fails, produce the raw message to the `cdc-dlq` topic with an error description in a header.
   - If validation passes, process normally and print a summary.
3. Maintain counters for: total processed, successful, failed (sent to DLQ).
4. Simulate a bad event by producing a malformed JSON message directly to the orders topic using a Kafka producer.
5. Verify the malformed message ends up in the DLQ topic.

**Hint:** Use `confluent_kafka.Producer` to write to the DLQ topic. You can add headers to Kafka messages to store error metadata.

**Expected output:**

```
Processed: 15 | Success: 14 | DLQ: 1
DLQ entry: topic=ecommerce.ecommerce.orders, partition=0, offset=42, error="Missing 'op' field"
```
