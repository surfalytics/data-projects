# Solutions: Exercise 01 - Monitoring

## Solution 1.1: Set Up the Monitoring Stack

The monitoring stack setup is procedural. The key verification steps are:

**Prometheus Queries:**

```promql
# Current message rate (should show ~50 msg/sec with default producer settings)
kafka_server_messages_in_per_sec_aggregate

# Under-replicated partitions (should be 0 in a healthy single-broker setup)
kafka_server_under_replicated_partitions

# Heap usage ratio (should be well below 1.0)
jvm_heap_memory_used_bytes / jvm_heap_memory_max_bytes

# Additional useful queries:
# Bytes in per second across all topics
kafka_server_bytes_in_per_sec_aggregate

# Request latency p99
kafka_network_produce_total_time_ms_p99
```

**Expected Grafana Dashboard Observations:**
- Messages In Per Second: ~50 msg/sec (matching MESSAGES_PER_SECOND default)
- Bytes In/Out: Proportional to message size (512 bytes default * 50 msg/sec = ~25 KB/sec)
- JVM Heap Memory: Typically 100-300 MB used out of the default heap size
- Under-replicated partitions: 0 (single broker, replication factor 1)
- Active Controller: 1

---

## Solution 1.2: Create a Consumer Lag Alert

### alert-rules.yml

```yaml
# Operational Response:
# When this alert fires, an on-call engineer should:
# 1. Check if the consumer application is running (it may have crashed or been scaled to 0)
# 2. Check consumer application logs for errors (serialization failures, downstream timeouts)
# 3. Check if the consumer group is stuck in a rebalance (kafka-consumer-groups.sh --describe)
# 4. Check if the production rate spiked (look at kafka_server_messages_in_per_sec)
# 5. If the consumer is running but slow, consider scaling out (add more consumers)
# 6. If the consumer crashed, restart it and monitor lag recovery

groups:
  - name: kafka-consumer-alerts
    rules:
      - alert: KafkaConsumerGroupHighLag
        expr: kafka_consumer_group_lag_total > 1000
        for: 2m
        labels:
          severity: warning
          team: data-engineering
        annotations:
          summary: "Consumer group {{ $labels.group }} has high lag"
          description: >
            Consumer group {{ $labels.group }} has a total lag of
            {{ $value }} messages, which exceeds the threshold of 1000.
            This has been sustained for more than 2 minutes.
          runbook: "https://wiki.example.com/runbooks/kafka-consumer-lag"

      - alert: KafkaConsumerGroupCriticalLag
        expr: kafka_consumer_group_lag_total > 10000
        for: 5m
        labels:
          severity: critical
          team: data-engineering
        annotations:
          summary: "CRITICAL: Consumer group {{ $labels.group }} lag exceeds 10000"
          description: >
            Consumer group {{ $labels.group }} has a total lag of
            {{ $value }} messages. Immediate investigation required.
          runbook: "https://wiki.example.com/runbooks/kafka-consumer-lag-critical"
```

---

## Solution 1.3: Interpret Metrics for a Production Incident

### Diagnosis

**Root Cause: One broker is experiencing severe JVM garbage collection (GC) pressure, likely due to a memory leak or heap misconfiguration, causing it to become unresponsive.**

**Step-by-step reasoning:**

1. **`jvm_heap_memory_used_bytes / jvm_heap_memory_max_bytes` at 0.95** -- The JVM heap is nearly full. This is the primary indicator. When heap usage is this high, the JVM spends most of its time in garbage collection rather than processing requests.

2. **`jvm_gc_collection_count` rate increased 10x** -- Confirms the GC hypothesis. The JVM is running GC constantly but cannot free enough memory. This is a "GC death spiral."

3. **`kafka_request_handler_avg_idle_percent` dropped from 0.85 to 0.10** -- The I/O threads are nearly 100% busy. But they are not busy processing real requests -- they are stalled waiting for GC pauses to complete. During a GC pause, the entire JVM freezes.

4. **`kafka_network_produce_total_time_ms_p99` increased from 5ms to 2500ms** -- Produce requests are taking 500x longer because the broker cannot process them during GC pauses. Clients experience timeouts.

5. **One broker's `kafka_server_messages_in_per_sec_aggregate` dropped to 0** -- This broker is effectively dead (GC pauses are so long that clients have timed out and stopped sending to it). Clients fail over to other brokers for partitions they lead on.

6. **`kafka_server_under_replicated_partitions` jumped to 15** -- The sick broker is the leader or follower for 15 partitions. Since it cannot respond, those partitions become under-replicated (followers cannot fetch from the leader, or the sick broker as follower cannot keep up).

**Immediate Mitigation:**

1. **Restart the sick broker.** This clears the JVM heap and restarts fresh. It is the fastest way to restore service.
2. **Monitor replication catch-up** after restart. The broker needs to replicate data it missed.
3. **If restart does not help**, consider removing the broker from the cluster temporarily and redistributing partitions.

**Long-term Fix:**

1. **Increase heap size** if the current setting is too low for the workload (e.g., increase from 1G to 6G).
2. **Switch to G1GC** if not already using it, with tuning: `-XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=35`.
3. **Investigate the root cause** of high memory usage: check for large message batches, excessive partition count, or a log compaction backlog.
4. **Set up alerting** on `jvm_heap_memory_used_bytes / jvm_heap_memory_max_bytes > 0.80` so you catch this before it becomes a full outage.
5. **Consider enabling JMX monitoring** for GC pause duration to alert on long pauses.
