# Exercise 03: Performance Tuning

## Exercise 3.1: Run the Performance Benchmark

**Objective:** Run the performance test and analyze the results.

**Tasks:**

1. Ensure the Kafka cluster is running:
   ```bash
   docker-compose up -d kafka
   ```

2. Run the performance benchmark:
   ```bash
   python src/performance_test.py
   ```

3. Examine the results table and answer:
   - Which `acks` setting gives the highest throughput? By what factor compared to `acks=all`?
   - Which compression algorithm provides the best throughput? Which provides the worst? Why?
   - What is the optimal batch size for your environment? Does doubling the batch size double throughput?
   - What effect does `linger.ms` have? Is there a point of diminishing returns?

4. Run the benchmark again with different message sizes to see how it affects results:
   ```bash
   MESSAGE_SIZE_BYTES=100 python src/performance_test.py
   MESSAGE_SIZE_BYTES=10240 python src/performance_test.py
   ```
   How does message size affect the relative performance of different configurations?

**Deliverable:** A file `exercises/benchmark-results.md` with the results table and your analysis.

---

## Exercise 3.2: Capacity Planning

**Objective:** Plan the Kafka cluster capacity for a production workload.

**Scenario:** You are designing a Kafka cluster for an e-commerce platform with these requirements:

- **Peak message rate:** 200,000 messages/second
- **Average message size:** 2 KB
- **Number of topics:** 15
- **Replication factor:** 3
- **Retention:** 14 days
- **Compression ratio:** 0.6 (40% reduction with lz4)
- **Target broker disk utilization:** no more than 70%
- **Single broker throughput limit:** 100 MB/sec write (based on your disk I/O benchmarks)

**Tasks:**

1. Calculate the following:
   - Raw throughput (MB/sec)
   - Compressed throughput (MB/sec)
   - Total cluster write throughput with replication (MB/sec)
   - Minimum number of brokers needed (based on throughput)
   - Daily storage per broker
   - Total storage per broker with 14-day retention
   - Storage with 70% utilization headroom

2. How many partitions would you recommend per topic? Show your reasoning, considering:
   - Consumer parallelism (assume max 20 consumers per topic)
   - Throughput per partition (use 10 MB/sec as a guideline)
   - Total partition count across the cluster

3. What instance type would you recommend on AWS for these brokers? Consider:
   - CPU requirements (network and I/O threads)
   - Memory requirements (page cache for log reads)
   - Storage requirements (EBS gp3 or io2?)
   - Network throughput requirements

**Deliverable:** A file `exercises/capacity-plan.md` with all calculations and recommendations.

---

## Exercise 3.3: Consumer Tuning

**Objective:** Diagnose and fix a slow consumer that causes frequent rebalances.

**Scenario:** Your consumer application processes messages from a topic with 12 partitions. The consumer group has 4 members. You observe:

- Frequent rebalances (every 5-10 minutes)
- Consumer lag growing steadily
- Each message requires a database lookup (average 50ms) and an HTTP API call (average 200ms)
- `max.poll.records` is set to 500 (default)
- `max.poll.interval.ms` is set to 300000 (5 minutes, default)
- `session.timeout.ms` is set to 10000 (10 seconds)
- `heartbeat.interval.ms` is set to 3000 (3 seconds)

**Tasks:**

1. Calculate the worst-case processing time for a single `poll()` call with the current settings. Is it possible that processing exceeds `max.poll.interval.ms`?

   Show: `max_poll_time = max.poll.records * (db_lookup_time + api_call_time)`

2. What specific configuration changes would you make? For each change, explain why:
   - `max.poll.records`
   - `max.poll.interval.ms`
   - `fetch.min.bytes`
   - `session.timeout.ms`

3. Beyond configuration changes, what architectural improvements would you recommend to reduce per-message processing time? Consider:
   - Batching database lookups
   - Async HTTP calls
   - Local caching
   - Increasing consumer count

4. After applying your changes, what metrics would you monitor to verify the fix?

**Deliverable:** A file `exercises/consumer-tuning.md` with your analysis and recommendations.
