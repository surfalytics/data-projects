# Exercise 3: Partition Strategies

## Exercise 3.1: Key-Based Partitioning Analysis

**Difficulty:** Intermediate

Build a producer and consumer pair that analyzes partition distribution:

1. **Producer:** Send 200 messages to a topic `partition-test` (3 partitions) using 10 different keys (`user-0` through `user-9`).
2. **Consumer:** Read all messages and build a report showing:
   - Which keys landed in which partitions
   - Message count per partition
   - Whether the same key always maps to the same partition (it should!)

**Expected output:**
```
Partition Distribution Report
=============================
Partition 0: 70 messages
  Keys: user-1, user-4, user-7
Partition 1: 60 messages
  Keys: user-0, user-3, user-6, user-9
Partition 2: 70 messages
  Keys: user-2, user-5, user-8

Key Consistency Check: PASSED
  All messages with the same key landed in the same partition.
```

3. Print a warning if any key appears in more than one partition (this should NOT happen with a stable partition count).

**Hints:**
- Use a `defaultdict(set)` to track keys per partition.
- Use a `defaultdict(int)` for message counts per partition.
- The consumer should read until it has consumed all 200 messages or hits a timeout.

---

## Exercise 3.2: Custom Partitioner -- Geographic Routing

**Difficulty:** Advanced

Implement a geographic partitioner that routes messages to partitions based on region:

1. Create a topic `geo-events` with 3 partitions, each representing a geographic region:
   - Partition 0: Americas (US, CA, BR, MX, AR)
   - Partition 1: Europe (GB, DE, FR, ES, IT)
   - Partition 2: Asia-Pacific (JP, AU, IN, KR, SG)

2. **Producer:**
   - Generate 100 fake events with a `country_code` field.
   - Implement a `geo_partitioner(country_code, num_partitions)` function that maps country codes to the correct partition.
   - For unknown countries, use a hash-based fallback.

3. **Consumer:**
   - Read all messages and verify that geographic routing is correct.
   - Print a report showing messages per partition and any misrouted messages.

**Hints:**
- Define region-to-partition mappings in a dictionary.
- Pass the computed partition number directly to `producer.produce(partition=...)`.
- Use `faker.country_code()` to generate realistic country codes (some will be "unknown").

---

## Submission

Place your solution files in the `solutions/` directory:
- `solutions/ex07_partition_analysis.py`
- `solutions/ex08_geo_partitioner.py`
