# Exercise 01: Monitoring

## Exercise 1.1: Set Up the Monitoring Stack

**Objective:** Deploy the full monitoring stack and generate load to observe metrics.

**Tasks:**

1. Start the monitoring stack using Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Wait for all services to be healthy, then create the monitoring topic:
   ```bash
   docker exec module10-kafka kafka-topics --bootstrap-server localhost:9092 \
     --create --topic monitoring-demo --partitions 6 --replication-factor 1
   ```

3. Install Python dependencies and run the monitoring producer:
   ```bash
   pip install -r requirements.txt
   python src/monitoring_producer.py
   ```

4. Open the Grafana dashboard at http://localhost:3000 (admin/admin) and verify:
   - The "Kafka Monitoring Dashboard" is loaded
   - Messages In Per Second graph shows incoming data
   - Bytes In/Out graph shows throughput
   - JVM Heap Memory graph shows memory usage

5. Open Prometheus at http://localhost:9090 and run these queries:
   - `kafka_server_messages_in_per_sec_aggregate` -- current message rate
   - `kafka_server_under_replicated_partitions` -- should be 0
   - `jvm_heap_memory_used_bytes / jvm_heap_memory_max_bytes` -- heap usage ratio

**Deliverable:** Screenshots of the Grafana dashboard showing live metrics and at least one Prometheus query result.

---

## Exercise 1.2: Create a Consumer Lag Alert

**Objective:** Set up a consumer group, observe lag, and write a Prometheus alerting rule.

**Tasks:**

1. With the monitoring producer still running, start a slow consumer that introduces lag:
   ```bash
   docker exec -it module10-kafka kafka-console-consumer \
     --bootstrap-server localhost:9092 \
     --topic monitoring-demo \
     --group slow-consumer \
     --max-messages 10
   ```
   Then stop the consumer (Ctrl+C). The group now has committed offsets but is no longer consuming, so lag will grow.

2. Run the consumer lag monitor to observe the lag:
   ```bash
   python src/consumer_lag_monitor.py
   ```

3. Write a Prometheus alerting rule that fires when consumer group lag exceeds 1000 messages for more than 2 minutes. Create a file `config/alert-rules.yml` with the rule.

   Hint: Use the `kafka_consumer_group_lag_total` metric from the consumer lag monitor.

4. Describe in a comment at the top of the file: what action should an on-call engineer take when this alert fires?

**Deliverable:** The `config/alert-rules.yml` file with the alerting rule and operational response documentation.

---

## Exercise 1.3: Interpret Metrics for a Production Incident

**Objective:** Given a set of metric observations, diagnose the root cause.

**Scenario:** You are on call and receive the following alerts at 3:00 AM:

- `kafka_server_under_replicated_partitions` jumped from 0 to 15
- `kafka_network_produce_total_time_ms_p99` increased from 5ms to 2500ms
- `kafka_request_handler_avg_idle_percent` dropped from 0.85 to 0.10
- `jvm_heap_memory_used_bytes / jvm_heap_memory_max_bytes` is at 0.95
- `jvm_gc_collection_count` rate increased 10x
- One broker's `kafka_server_messages_in_per_sec_aggregate` dropped to 0

**Tasks:**

1. What is the most likely root cause? Explain your reasoning step by step, citing which metrics support your diagnosis.

2. What immediate actions would you take to mitigate the impact?

3. What long-term fix would you recommend to prevent recurrence?

4. Write your analysis in a file `exercises/incident-analysis.md`.

**Deliverable:** The `exercises/incident-analysis.md` file with your analysis.
