# Solutions: Exercise 03 - Performance Tuning

## Solution 3.1: Performance Benchmark Analysis

### Expected Results (typical single-broker local environment)

Results will vary by hardware, but the relative patterns should be consistent:

**acks comparison:**
- `acks=0` is the fastest (2-5x faster than `acks=all`) because the producer does not wait for any broker acknowledgment. It fires and forgets.
- `acks=1` waits for the leader to write to its local log (moderate latency).
- `acks=all` waits for all in-sync replicas to acknowledge (highest latency, highest durability). With replication factor 1 (our test setup), `acks=1` and `acks=all` perform similarly.

**Compression comparison:**
- `lz4` typically provides the best throughput because it has the fastest compression/decompression speed with reasonable compression ratio.
- `zstd` provides a better compression ratio than lz4 but uses more CPU, so throughput may be slightly lower.
- `snappy` is similar to lz4 but typically has slightly lower compression ratio.
- `gzip` has the highest compression ratio but the highest CPU cost, so it usually has the lowest throughput.
- `none` has no CPU overhead for compression, but sends more data over the network and to disk.

**Batch size comparison:**
- Increasing batch size generally improves throughput up to a point. Larger batches mean fewer network round trips.
- Going from 16KB to 64KB usually shows significant improvement.
- Going from 64KB to 128KB shows diminishing returns.
- Going from 128KB to 256KB may show no improvement or even slight degradation (larger batches increase memory pressure and may delay sending).
- Doubling batch size does NOT double throughput. The relationship is logarithmic.

**linger.ms comparison:**
- `linger.ms=0` sends batches immediately, resulting in smaller batches and more network requests.
- `linger.ms=5-20` allows batches to fill up, significantly improving throughput.
- `linger.ms=50-100` shows diminishing returns for most workloads; the batch is already near capacity.
- The point of diminishing returns depends on the production rate. At high rates, batches fill quickly even with `linger.ms=0`.

**Message size effect:**
- Small messages (100 bytes): Compression helps less (overhead of compression metadata). Batching and linger.ms matter more because per-message overhead dominates.
- Large messages (10KB+): Compression helps significantly (more compressible data). Network throughput becomes the bottleneck. acks setting has more impact because each acknowledgment involves more data.

---

## Solution 3.2: Capacity Planning

### Calculations

```
Given:
  Peak rate: 200,000 msg/sec
  Message size: 2 KB
  Replication factor: 3
  Retention: 14 days
  Compression ratio: 0.6
  Broker write limit: 100 MB/sec
  Max disk utilization: 70%

1. Raw throughput:
   200,000 msg/sec * 2 KB = 400,000 KB/sec = 390.6 MB/sec

2. Compressed throughput:
   390.6 MB/sec * 0.6 = 234.4 MB/sec (network ingress to cluster)

3. Total cluster write throughput with replication:
   234.4 MB/sec * 3 (replicas) = 703.1 MB/sec (total disk writes across cluster)

4. Minimum number of brokers (throughput-based):
   703.1 MB/sec / 100 MB/sec per broker = 7.03 -> 8 brokers minimum
   With headroom (20%): 8 * 1.2 = 9.6 -> 10 brokers recommended

5. Daily storage per broker:
   Total daily compressed writes: 234.4 MB/sec * 86,400 sec = 20,252 GB/day = 19.8 TB/day
   Per broker (10 brokers): 19.8 / 10 = 1.98 TB/day per broker
   Note: Each broker stores its share of leaders PLUS replicas.
   With RF=3 and 10 brokers, each broker is leader for 1/10 of partitions
   and follower for 2/10 more (on average).
   So each broker stores ~3/10 of all data: 19.8 TB * 3/10 / 3 = still ~1.98 TB/day
   (because 19.8 TB already includes the RF=3 multiplication)

   Correction - let's recalculate:
   Total daily compressed data (before replication): 234.4 MB/sec * 86,400 = 20,252 GB = 19.8 TB
   This 19.8 TB needs to be stored 3 times (RF=3): 59.3 TB total cluster storage per day
   Per broker (10 brokers): 59.3 / 10 = 5.93 TB/day per broker

6. Storage per broker with 14-day retention:
   5.93 TB/day * 14 days = 83.0 TB per broker

7. Storage with 70% utilization headroom:
   83.0 TB / 0.70 = 118.6 TB per broker -> ~120 TB per broker
```

### Partition Recommendations

```
Throughput-based:
  Compressed throughput per topic: 234.4 MB/sec / 15 topics = 15.6 MB/sec per topic
  At 10 MB/sec per partition: 15.6 / 10 = 2 partitions minimum per topic

Consumer parallelism:
  Max 20 consumers per topic -> need at least 20 partitions per topic

Recommendation: 20-24 partitions per topic
  - 15 topics * 24 partitions = 360 partitions total
  - With RF=3: 360 * 3 = 1,080 partition-replicas across 10 brokers
  - ~108 partition-replicas per broker (well within the 4,000 limit)
```

### AWS Instance Recommendation

```
Recommended: i3en.2xlarge or r6gd.2xlarge

CPU:  8 vCPUs
  - num.network.threads=4 (half of vCPUs)
  - num.io.threads=8
  - Sufficient for compression/decompression

Memory: 64 GB RAM
  - JVM heap: 6 GB (sufficient for Kafka broker)
  - Page cache: ~58 GB (caches recent log segments for fast consumer reads)
  - Page cache covers: 58 GB / 5.93 TB = ~1% of total data
    But recent data (last ~10 minutes) fits: 5.93 TB / 1440 min * 10 min = 41 GB

Storage: 120 TB per broker
  - Option A: EBS gp3 volumes, 120 TB total (multiple volumes in JBOD)
    - 8 x 16 TB gp3 volumes
    - Provision 1000 IOPS and 250 MB/sec per volume
  - Option B: i3en.2xlarge has 2 x 2.5 TB NVMe SSDs (only 5 TB, insufficient)
    - Would need i3en.6xlarge (3 x 7.5 TB = 22.5 TB) -- still insufficient
  - Recommendation: Use r6gd.2xlarge with EBS gp3 for storage flexibility

Network: r6gd.2xlarge provides up to 10 Gbps
  - Broker write throughput: ~100 MB/sec = 800 Mbps
  - Replication traffic: ~200 MB/sec = 1,600 Mbps
  - Consumer read traffic: ~300 MB/sec = 2,400 Mbps
  - Total: ~4,800 Mbps -- within 10 Gbps limit

Estimated monthly cost (us-east-1):
  - 10 x r6gd.2xlarge: ~$4,500/month
  - 80 x 16TB gp3 EBS: ~$128,000/month
  - Total: ~$132,500/month
  Note: Storage dominates cost. Consider tiered storage or Confluent Cloud.
```

---

## Solution 3.3: Consumer Tuning

### 1. Worst-Case Processing Time

```
max_poll_time = max.poll.records * (db_lookup_time + api_call_time)
max_poll_time = 500 * (50ms + 200ms)
max_poll_time = 500 * 250ms
max_poll_time = 125,000ms = 125 seconds

max.poll.interval.ms = 300,000ms (5 minutes)

125 seconds < 300 seconds, so normally it should NOT exceed the limit.

HOWEVER: This is the average case. If the API call has P99 latency of 2 seconds:
worst_case = 500 * (50ms + 2000ms) = 500 * 2050ms = 1,025,000ms = 17.1 minutes

17.1 minutes >> 5 minutes -> This WILL exceed max.poll.interval.ms and trigger a rebalance.

The frequent rebalances (every 5-10 minutes) confirm that API call latency spikes
are causing processing to exceed the poll interval.
```

### 2. Configuration Changes

```properties
# Reduce max.poll.records from 500 to 50
# Why: Reduces the maximum processing time per poll() call.
# New worst case: 50 * 2050ms = 102.5 seconds (within 5-minute limit)
# New average case: 50 * 250ms = 12.5 seconds (fast)
max.poll.records=50

# Increase max.poll.interval.ms from 300000 to 600000 (10 minutes)
# Why: Provides additional headroom for API latency spikes.
# Even with worst-case latency and 50 records, 102.5s << 600s.
max.poll.interval.ms=600000

# Increase fetch.min.bytes from 1 to 10240 (10 KB)
# Why: Reduces the number of fetch requests when data rate is low.
# Broker will wait until 10 KB of data is available before responding.
# At 2 KB per message, this means batches of ~5 messages minimum.
fetch.min.bytes=10240

# Increase session.timeout.ms from 10000 to 30000 (30 seconds)
# Why: During GC pauses or brief network hiccups, 10 seconds is too aggressive.
# 30 seconds reduces false-positive "consumer is dead" detections.
# Set heartbeat.interval.ms to session.timeout.ms / 3 = 10000.
session.timeout.ms=30000
heartbeat.interval.ms=10000
```

### 3. Architectural Improvements

**Batch database lookups:**
Instead of one database query per message, collect a batch of messages from `poll()`, extract all the keys needed for lookup, and run a single `WHERE id IN (...)` query. This reduces round trips from 50 to 1.

```python
# Before: 50 database calls
for msg in messages:
    result = db.query("SELECT * FROM users WHERE id = ?", msg.user_id)

# After: 1 database call
user_ids = [msg.user_id for msg in messages]
results = db.query("SELECT * FROM users WHERE id IN (?)", user_ids)
lookup = {r.id: r for r in results}
```

**Async HTTP calls:**
Use `asyncio` or `concurrent.futures.ThreadPoolExecutor` to make API calls in parallel instead of sequentially.

```python
# Before: 50 sequential API calls = 50 * 200ms = 10 seconds
# After: 50 parallel API calls = ~200ms (limited by slowest call)
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(call_api, msg) for msg in messages]
    results = [f.result() for f in futures]
```

**Local caching:**
Cache frequently accessed database results in memory (using `functools.lru_cache` or Redis). If user data does not change frequently, a 5-minute TTL cache can eliminate 80-90% of database lookups.

**Increase consumer count:**
Currently 4 consumers for 12 partitions = 3 partitions per consumer. Increasing to 12 consumers (one per partition) triples the parallelism.

### 4. Metrics to Monitor After Fix

- **Consumer group lag**: Should stop growing and stabilize or decrease
- **Rebalance count**: Should drop to near-zero (monitor `kafka.consumer:type=consumer-coordinator-metrics,name=rebalance-rate-per-hour`)
- **Poll latency**: Measure the time between `poll()` calls -- should be well under `max.poll.interval.ms`
- **Processing time per batch**: Instrument with a timer to ensure it stays under 60 seconds
- **API call latency (P99)**: Monitor the downstream API to catch latency spikes early
- **Database query latency**: Monitor the batch query time to ensure it scales with batch size
- **Committed offset rate**: Should be steady, indicating the consumer is making consistent progress
