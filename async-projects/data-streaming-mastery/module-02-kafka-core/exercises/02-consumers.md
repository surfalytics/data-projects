# Exercise 2: Kafka Consumers

## Exercise 2.1: JSON Message Consumer with Filtering

**Difficulty:** Beginner

Build a consumer that reads from the `sensor-readings` topic (produced in Exercise 1.1) and filters messages:

1. Subscribe to the `sensor-readings` topic.
2. Deserialize each message value from JSON.
3. Filter and print only readings where `temperature > 30.0` (high temperature alerts).
4. For each alert, print:
   ```
   [ALERT] sensor=sensor-042 temp=32.5 location=building-A-floor-3 time=2024-01-15T10:30:00Z
   ```
5. Track and display total messages read vs. alerts triggered.
6. Handle errors gracefully (malformed JSON, missing fields).
7. Exit cleanly on Ctrl+C.

**Topic:** `sensor-readings`
**Group ID:** `sensor-alert-group`

**Hints:**
- Use `json.loads()` to deserialize values.
- Wrap JSON parsing in a try/except block.
- Use `signal` module for clean shutdown.

---

## Exercise 2.2: Multi-Consumer Group Demo

**Difficulty:** Intermediate

Create a consumer script that demonstrates how two different consumer groups independently consume the same topic:

1. Accept `--group-id` and `--consumer-id` as CLI arguments.
2. Subscribe to the `user-events` topic.
3. For each consumed message, log:
   - Consumer ID, group ID, partition, offset, and a summary of the message content.
4. Implement rebalance callbacks (`on_assign`, `on_revoke`) that log which partitions are assigned/revoked.
5. Commit offsets every 10 messages (manual commit).

**Instructions for testing:**
- Open 3 terminals.
- Terminal 1: `python solution.py --group-id group-A --consumer-id A1`
- Terminal 2: `python solution.py --group-id group-A --consumer-id A2`
- Terminal 3: `python solution.py --group-id group-B --consumer-id B1`
- Run the advanced producer in a 4th terminal.
- Observe: A1 and A2 share partitions; B1 gets all partitions independently.

**Hints:**
- Use `enable.auto.commit=False` for manual commit control.
- Keep a counter and commit with `consumer.commit()` every N messages.

---

## Exercise 2.3: Dead Letter Queue Consumer

**Difficulty:** Advanced

Build a consumer that implements a Dead Letter Queue (DLQ) pattern:

1. Consume from the `user-events` topic.
2. For each message, attempt to "process" it (simulate with JSON parsing + validation).
3. If processing fails (malformed JSON, missing required fields, or simulated random failures), send the message to a DLQ topic (`user-events-dlq`) with:
   - The original message as the value
   - Headers: `original_topic`, `original_partition`, `original_offset`, `error_reason`, `retry_count`
4. If processing succeeds, commit the offset.
5. Track and print statistics: processed, failed, sent-to-DLQ.

**Required fields for validation:** `user_id`, `event_type`, `timestamp`

**Hints:**
- You need both a Consumer and a Producer in the same script.
- Use message headers to attach metadata about the failure.
- Consider wrapping the DLQ logic in a class for clean separation.

---

## Submission

Place your solution files in the `solutions/` directory:
- `solutions/ex04_filter_consumer.py`
- `solutions/ex05_multi_group_consumer.py`
- `solutions/ex06_dlq_consumer.py`
