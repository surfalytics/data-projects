# Solutions: Exercise 2 -- Architecture Design

---

## Solution 2.1: E-Commerce Order Pipeline

### 1. Producers, Consumers, and Event Types

**Producers:**
| Producer | Events Published |
|---|---|
| Order Service | `order.placed`, `order.cancelled` |
| Payment Service | `payment.completed`, `payment.failed` |
| Inventory Service | `inventory.reserved`, `inventory.released` |
| Warehouse Service | `fulfillment.started`, `fulfillment.shipped` |

**Consumers:**
| Consumer | Events Consumed |
|---|---|
| Payment Service | `order.placed` |
| Inventory Service | `order.placed`, `payment.failed` |
| Email Service | `order.placed`, `payment.completed`, `fulfillment.shipped` |
| Warehouse Service | `payment.completed` |
| Analytics Service | All events |

### 2. Architecture Diagram

```
Customer --> [Order Service]
                   |
                   | order.placed
                   v
             [Event Broker (Kafka)]
              /    |     |    \     \
             v     v     v     v     v
    [Payment] [Inventory] [Email] [Warehouse] [Analytics]
         |         |                    |
         | payment |                    | fulfillment
         | .completed                   | .shipped
         v         v                    v
   [Event Broker (Kafka)] <-------------+
         |
         v
    [Email: "Payment confirmed"]
    [Warehouse: begin fulfillment]
    [Analytics: update dashboard]
```

The key insight is that services are both producers and consumers. The Payment Service consumes `order.placed` and produces `payment.completed`. This forms an event chain.

### 3. Should Payment Be Synchronous or Asynchronous?

**Recommendation: Synchronous for the initial payment authorization, asynchronous for the rest.**

- **Payment authorization** (checking if the card is valid and funds are available) should be synchronous because the customer is waiting on the checkout page. A 2-3 second response is expected.
- **Payment capture** (actually charging the card) can be asynchronous. The customer sees "Order Placed" and the actual charge happens moments later via the event pipeline.

If the payment authorization fails, the order is rejected immediately. The customer knows right away and can try another card.

If you make the entire payment flow asynchronous, the customer sees "Order Placed" but might receive an email 30 seconds later saying "Payment failed." This is a poor user experience.

### 4. Email Service Down

This is where event-driven architecture shines:

1. The `order.placed` event is written to Kafka and persisted durably.
2. The Email Service is a consumer. When it is down, it simply stops consuming.
3. Kafka retains the event (default retention: 7 days).
4. When the Email Service recovers, it resumes from where it left off and processes all pending events.
5. The customer receives the confirmation email late, but they do receive it.

**No events are lost.** No other services are affected. This is impossible in a synchronous request-response architecture where the Order Service would need to call the Email Service directly and handle its failure.

### 5. Ordering Requirements

**Strict ordering required:**
- All events for the same order must be processed in order: `order.placed` -> `payment.completed` -> `fulfillment.started` -> `fulfillment.shipped`. Use the `order_id` as the Kafka message key to ensure all events for one order go to the same partition.

**No ordering requirement:**
- Events for different orders are independent. Order #100 and Order #101 can be processed in any order relative to each other.
- Analytics events can be processed in any order since they are aggregated.

### 6. Delivery Guarantees

| Event | Guarantee | Justification |
|---|---|---|
| `order.placed` | At-least-once | Cannot lose orders. Idempotent consumers use `order_id` to deduplicate. |
| `payment.completed` | Exactly-once | Financial transaction. Use Kafka transactions + idempotent payment processor. |
| `payment.failed` | At-least-once | Must trigger inventory release. Idempotent release using `order_id`. |
| `inventory.reserved` | At-least-once | Reserving twice for the same order is handled idempotently. |
| `fulfillment.shipped` | At-least-once | Duplicate ship notifications are filtered by `order_id`. |
| Analytics events | At-most-once | Approximate counts are acceptable for dashboards. |

---

## Solution 2.2: IoT Sensor Monitoring

### 1. Data Volume Calculation

```
Sensors:              10,000
Readings per sensor:  1 per second
Events per second:    10,000
Events per minute:    600,000
Events per hour:      36,000,000
Events per day:       864,000,000  (~864 million)
Events per 90 days:   77,760,000,000  (~78 billion)
```

Assuming each event is approximately 200 bytes:
```
Per second:    10,000 x 200 B = 2 MB/sec
Per day:       864M x 200 B = ~173 GB/day
Per 90 days:   ~15.6 TB (raw storage)
```

This is well within the capabilities of Kafka + object storage but requires careful capacity planning.

### 2. Event Schema

```json
{
  "type": "sensor.reading",
  "key": "sensor-S4521",
  "timestamp": "2026-02-19T14:00:00.000Z",
  "payload": {
    "sensor_id": "S4521",
    "factory_id": "F03",
    "sensor_type": "temperature",
    "value": 72.3,
    "unit": "fahrenheit",
    "quality": "good",
    "battery_pct": 85
  },
  "metadata": {
    "firmware_version": "2.1.0",
    "schema_version": 3
  }
}
```

### 3. Architecture

```
[10,000 Sensors]
       |
       | (MQTT / HTTP)
       v
[Ingestion Gateway]  -- validates, enriches, publishes
       |
       v
[Kafka: sensor-readings topic]  (partitioned by sensor_id)
       |
       +----> [Stream Processor: Anomaly Detection]
       |         |
       |         +--> [Kafka: alerts topic] --> [Alert Service] --> PagerDuty / SMS
       |
       +----> [Stream Processor: Windowed Aggregation]
       |         |
       |         +--> [TimescaleDB / ClickHouse] --> [Grafana Dashboards]
       |              (1-min, 5-min, 1-hour aggregates)
       |
       +----> [Kafka Connect S3 Sink]
                |
                +--> [S3 / Object Storage]  (raw readings, 90-day retention)
                     (Parquet format, partitioned by date + factory)
```

**Component-to-requirement mapping:**
| Requirement | Component |
|---|---|
| Real-time anomaly detection | Stream processor reading from Kafka, emitting to alerts topic |
| Windowed aggregations | Stream processor with tumbling windows (1m, 5m, 1h), output to TimescaleDB |
| 90-day raw storage | Kafka Connect S3 Sink writing Parquet files to object storage |
| 5-second alerting SLA | Dedicated stream processor for anomalies with minimal processing latency |

### 4. Partitioning Strategy

**Recommended: Partition by `sensor_id`.**

| Strategy | Pros | Cons |
|---|---|---|
| By `sensor_id` | Even distribution. All readings for one sensor are ordered. Anomaly detection can maintain per-sensor state. | 10,000 sensors means you need enough partitions (e.g., 50-100 partitions, sensors hash to partitions). |
| By `factory_id` | Only 5 factories, simple. All data for one factory is co-located. | Extremely uneven if factories have different sensor counts. Only 5 partitions means limited parallelism. |
| By `sensor_type` | Good for type-specific processing (temperature rules differ from pressure rules). | Very uneven distribution. If 80% are temperature sensors, one partition is overloaded. |

**Partition by `sensor_id` with 50 partitions**: 10,000 sensors distributed across 50 partitions gives ~200 sensors per partition. This provides good parallelism and even distribution. Each partition processes ~200 events/sec, which is trivially manageable.

### 5. Handling the Network Reconnection Burst

**The scenario**: Factory loses connectivity for 10 minutes. When it reconnects, 600,000 delayed readings arrive at once (10 minutes x 1,000 sensors x 1 reading/sec, assuming 1,000 sensors in that factory).

**Backpressure:**
- Kafka absorbs the burst naturally. 600,000 events at 200 bytes each is only 120 MB, which Kafka can ingest in seconds.
- The stream processor may temporarily lag but catches up since normal throughput (10K events/sec) is well within its capacity.
- If needed, the ingestion gateway can rate-limit the burst from the factory to smooth it out.

**Late-arriving data:**
- All 600,000 events have event times from 10 minutes ago. The watermark has advanced past them.
- Configure allowed lateness on the windowed aggregations to at least 15 minutes. This keeps the 1-minute and 5-minute windows open long enough to accept late data.
- The anomaly detection processor should use event time so that a threshold breach 8 minutes ago is still detected (even though the alert is late).
- Late events that miss the window should be sent to a side output for batch reconciliation.

**Compliance (no data loss):**
- The Kafka Connect S3 Sink is downstream from Kafka. As long as events are in Kafka, they will be written to S3 eventually.
- Use at-least-once delivery with the S3 Sink. Deduplicate at the storage level using `sensor_id + timestamp` as a unique key in the Parquet files.
- Monitor consumer lag on the S3 Sink connector to ensure it stays healthy during bursts.

---

## Solution 2.3: Event Sourcing for a Shopping Cart

### 1. Complete Event Set

| Event Type | Payload |
|---|---|
| `cart.created` | `{ cart_id, user_id, created_at }` |
| `cart.item_added` | `{ cart_id, product_id, product_name, quantity, unit_price }` |
| `cart.item_removed` | `{ cart_id, product_id }` |
| `cart.item_quantity_changed` | `{ cart_id, product_id, new_quantity }` |
| `cart.discount_applied` | `{ cart_id, discount_code, discount_type, discount_value }` |
| `cart.discount_removed` | `{ cart_id, discount_code }` |
| `cart.checked_out` | `{ cart_id, order_id, final_total }` |
| `cart.abandoned` | `{ cart_id, reason }` |

### 2. Reconstructing Cart State -- Worked Example

**Event sequence:**

| # | Event | Details |
|---|---|---|
| 1 | `cart.created` | cart_id: C-50, user_id: U-10 |
| 2 | `cart.item_added` | product: "Blue T-Shirt", qty: 1, price: $25.00 |
| 3 | `cart.item_added` | product: "Black Jeans", qty: 1, price: $60.00 |
| 4 | `cart.item_quantity_changed` | product: "Blue T-Shirt", new_qty: 3 |
| 5 | `cart.discount_applied` | code: "SAVE10", type: percentage, value: 10% |

**Replay:**

After event 1:
```
Cart C-50: { items: [], discounts: [], total: $0.00 }
```

After event 2:
```
Cart C-50: { items: [{ "Blue T-Shirt", qty: 1, price: $25.00 }], total: $25.00 }
```

After event 3:
```
Cart C-50: { items: [{ "Blue T-Shirt", qty: 1, $25 }, { "Black Jeans", qty: 1, $60 }], total: $85.00 }
```

After event 4:
```
Cart C-50: { items: [{ "Blue T-Shirt", qty: 3, $25 }, { "Black Jeans", qty: 1, $60 }], total: $135.00 }
```

After event 5:
```
Cart C-50: {
  items: [{ "Blue T-Shirt", qty: 3, $25 }, { "Black Jeans", qty: 1, $60 }],
  discounts: [{ "SAVE10", 10% }],
  subtotal: $135.00,
  discount: -$13.50,
  total: $121.50
}
```

### 3. Debugging the Discount Issue

With event sourcing, debugging is straightforward:

1. **Query the event store** for all events for this cart, ordered by timestamp.
2. **Find the `cart.discount_applied` event**: Verify the discount code, type, and value are correct.
3. **Replay events up to that point**: Check if the discount was applied correctly by the projection logic.
4. **Look for subsequent events**: Did a `cart.discount_removed` event accidentally follow? Did an `item_quantity_changed` event recalculate the total without applying the discount?
5. **Compare the read model**: The current state in the read model should match the replay result. If it does not, the read model projection has a bug.

In a traditional CRUD system, you would only see the current state: "total is $135.00, no discount." You would have no idea if the discount was applied and then removed, or if it was never applied, or if there is a calculation bug.

### 4. "Restore Cart from 24 Hours Ago"

**Event sourcing approach:**
1. Query all events for the cart with timestamps up to 24 hours ago.
2. Replay only those events to reconstruct the cart state at that point.
3. Create a new cart with that state (by emitting new `cart.item_added` events that mirror the historical state).

This is trivial because the entire history is stored. It is essentially "time travel."

**Traditional CRUD approach:**
This would require one of the following:
- A separate audit/history table that captures every change (essentially rebuilding event sourcing on top of CRUD).
- Database temporal tables or point-in-time recovery, which are complex and not designed for per-entity time travel.
- Regular snapshots/backups, which only give you hourly or daily granularity.

Most CRUD systems simply cannot do this without significant additional infrastructure.

### 5. CQRS Read Model for Cart Summary

**Read model schema (e.g., in Redis or a fast database):**

```json
{
  "cart_id": "C-50",
  "user_id": "U-10",
  "item_count": 4,
  "unique_items": 2,
  "subtotal": 135.00,
  "discounts": [
    { "code": "SAVE10", "type": "percentage", "value": 10, "savings": 13.50 }
  ],
  "total": 121.50,
  "last_updated": "2026-02-19T14:05:00Z"
}
```

**Synchronization:**
A projection process subscribes to the cart event stream and updates the read model:

- On `cart.item_added`: increment `item_count` by quantity, increment `unique_items`, recalculate `subtotal` and `total`.
- On `cart.item_removed`: decrement accordingly.
- On `cart.item_quantity_changed`: adjust `item_count`, recalculate totals.
- On `cart.discount_applied`: add to `discounts` array, recalculate `total`.
- On `cart.checked_out`: mark the read model as finalized or delete it.

The read model is eventually consistent with the event store. If the projection crashes, it replays events from the last known position and rebuilds the read model.

---

## Solution 2.4: Multi-Region Event Architecture

### 1. High-Level Architecture

```
                    [Global Dashboard]
                     /      |       \
                    v       v        v
            +--------+ +--------+ +--------+
            | US-East| | EU-West| | AP-SE  |
            |        | |        | |        |
            | Kafka  | | Kafka  | | Kafka  |
            | Cluster| | Cluster| | Cluster|
            |        | |        | |        |
            | Local  | | Local  | | Local  |
            |Services| |Services| |Services|
            +--------+ +--------+ +--------+
                 \          |          /
                  \         |         /
                   v        v        v
              [Cross-Region Replicator]
              (MirrorMaker 2 / Confluent
               Cluster Linking)
```

Each region has:
- A local Kafka cluster for low-latency event processing.
- Local services that produce and consume events.
- A replicator that selectively copies events to other regions.

### 2. Event Classification

**Global replication (all regions):**
| Event Type | Reason |
|---|---|
| `account.created`, `account.updated` | User accounts must be accessible globally for login |
| `billing.charged`, `billing.refunded` | Financial records must be consistent across regions |
| `subscription.changed` | Subscription state affects feature access globally |
| `product.updated`, `pricing.changed` | Product catalog must be consistent everywhere |

**Local only (stay in originating region):**
| Event Type | Reason |
|---|---|
| `clickstream.*` | High volume, only needed for local analytics |
| `session.*` | User sessions are handled by the local region |
| `search.query` | Search analytics are processed locally |
| `log.*` | Operational logs are region-specific |
| `eu_user.*` (PII-containing events) | GDPR requires EU user data stays in EU |

### 3. Conflict Resolution Strategies

**Strategy 1: Last-Writer-Wins (LWW)**
- Each event includes a vector clock or Lamport timestamp.
- When the same entity is updated in two regions, the update with the latest timestamp wins.
- **Pros**: Simple to implement. Works well for most cases.
- **Cons**: The "lost" update is silently discarded. If a user changes their email in US-East and their name in EU-West simultaneously, one change is lost.

**Strategy 2: Conflict-Free Replicated Data Types (CRDTs)**
- Model state using data structures that can be merged without conflicts (counters, sets, registers).
- Example: A user profile as a map of LWW-registers. Each field (name, email, address) is an independent register. Concurrent updates to different fields merge cleanly. Concurrent updates to the same field use LWW for that field only.
- **Pros**: No data loss for updates to different fields. Mathematically guaranteed convergence.
- **Cons**: More complex to implement. Not all data models fit CRDTs naturally.

**Strategy 3: Application-Level Resolution**
- Detect conflicts and present them to the user or an admin for manual resolution.
- Example: "Your account was updated from two locations. Please confirm your current email address."
- **Pros**: No data loss. User controls the outcome.
- **Cons**: Poor user experience. Not suitable for high-frequency conflicts.

### 4. EU User Traveling to US

**Routing strategy:**

1. The user authenticates in the US region. The auth service recognizes the user's home region as EU-West (stored in the user's account metadata).
2. **Option A -- Route to home region**: All write operations for this user are proxied to EU-West. Reads can be served from a local EU-West replica in US-East. This ensures all PII stays in the EU but adds latency (~100-150ms for cross-Atlantic requests).
3. **Option B -- Process locally, replicate selectively**: Process the event in US-East but tag it with `data_residency: EU`. The cross-region replicator sends this event to EU-West and then deletes it from US-East after confirmation. This is faster but more complex.

**Recommendation**: Option A is simpler and safer for GDPR compliance. The added latency is acceptable for most SaaS applications. Option B is an optimization for latency-sensitive applications but requires careful implementation to ensure the US copy is reliably purged.

**Key principle**: The user's data residency follows the user's account settings, not their physical location.

### 5. Cross-Region Delivery Guarantee

**Recommendation: At-least-once with idempotent consumers.**

**At-least-once justification:**
- Cross-region networks are unreliable. Connections drop, packets are lost, replicators restart. At-least-once ensures no events are permanently lost.
- The replicator retries failed deliveries until acknowledged.

**Why not exactly-once:**
- Exactly-once across independent Kafka clusters requires distributed transactions spanning two clusters. This is extremely expensive in terms of latency (two-phase commit across 100ms+ network links) and complexity.
- The performance impact on cross-region replication would be severe, potentially doubling or tripling replication latency.

**Handling duplicates:**
- Each event carries a globally unique `event_id`.
- Consumers in the receiving region deduplicate using this `event_id` (store processed IDs in a set with a TTL).
- For billing events: the payment processor is idempotent on `transaction_id`, so duplicate replication is safe.
- For account events: updates are idempotent (setting email to "alice@example.com" twice has no side effect).

**Consequences of at-least-once**: Slight overhead for deduplication. Occasional duplicate processing during replicator restarts (typically a few seconds of duplicates). No data loss.

**Consequences if exactly-once were chosen**: Replication latency increases by 2-3x. Throughput drops significantly. If the transaction coordinator fails, replication stalls entirely until recovery. The added complexity introduces more failure modes.

---

## Solution 2.5: Designing a Real-Time Leaderboard

### 1. Event Schema

```json
{
  "type": "player.scored",
  "key": "player-P12345",
  "timestamp": "2026-02-19T14:30:00.123Z",
  "payload": {
    "player_id": "P12345",
    "game_id": "G-5001",
    "match_id": "M-88234",
    "points": 100,
    "scoring_action": "headshot_bonus",
    "event_id": "EVT-a1b2c3d4"
  }
}
```

The `event_id` is a UUID generated by the game server. It is critical for idempotency (see question 4).

### 2. Approach B -- Direct Data Store Update

**Chosen approach: Approach B (Redis sorted set).**

**Justification:**

| Criteria | Approach A (Stream Processor) | Approach B (Redis) |
|---|---|---|
| Latency | Higher (event -> Kafka -> processor -> output) | Lower (event -> Kafka -> consumer -> Redis, or even event -> Redis directly) |
| Leaderboard query | Must maintain full sorted state in the processor. Complex for 1M players. | Redis ZRANGEBYSCORE is O(log N + M), optimized for this exact use case. |
| Rank lookup | Full scan or secondary index needed. | Redis ZRANK is O(log N). Instant rank for any player. |
| Scalability | Limited by processor memory for 1M-player state. | Redis handles millions of sorted set members natively. Cluster mode for more. |
| Complexity | Must implement sorting, windowing, eviction. | Redis sorted set does it all out of the box. |

**Architecture:**

```
[Game Servers] --> [Kafka: player-scores topic] --> [Score Consumer]
                                                         |
                                                    (ZINCRBY)
                                                         v
                                                   [Redis Sorted Set]
                                                     "leaderboard"
                                                         |
                                                    (ZREVRANGE 0 99)
                                                    (ZRANK player_id)
                                                         v
                                                 [Leaderboard API] --> [Players]
```

**Redis commands:**
- `ZINCRBY leaderboard 100 "P12345"` -- Add 100 points to player P12345.
- `ZREVRANGE leaderboard 0 99 WITHSCORES` -- Get top 100 players.
- `ZREVRANK leaderboard "P12345"` -- Get a specific player's rank (0-indexed from top).
- `ZSCORE leaderboard "P12345"` -- Get a player's total score.

### 3. Handling Score Bursts During Tournaments

**Multi-layered approach:**

1. **Kafka as a buffer**: Score events go through Kafka, which absorbs the 10x spike effortlessly. The topic has enough partitions (e.g., 20) to parallelize consumption.

2. **Consumer auto-scaling**: Run multiple Score Consumer instances (one per partition). During tournaments, scale from 5 to 20 instances. Each consumer handles a subset of partitions.

3. **Redis pipelining**: Instead of one ZINCRBY per event, batch updates using Redis pipelines. Accumulate 100-500ms of score events in memory, then send them to Redis in a single pipeline. This reduces round trips by 100x.

4. **Accept brief staleness**: During the peak of a burst, the leaderboard may be up to 1-2 seconds stale. This is acceptable for gameplay. Players do not notice a 1-second delay in leaderboard updates.

5. **Pre-provision for tournaments**: If tournament schedules are known in advance, scale up consumers and Redis capacity before the tournament starts.

### 4. Handling Duplicate Score Events

**Idempotency mechanism using `event_id`:**

The consumer maintains a deduplication set:

```
1. Receive score event with event_id: "EVT-a1b2c3d4"
2. Check: SISMEMBER processed_events "EVT-a1b2c3d4"
3. If already processed: skip (do not ZINCRBY)
4. If new:
   a. ZINCRBY leaderboard 100 "P12345"
   b. SADD processed_events "EVT-a1b2c3d4"
   c. EXPIRE processed_events:EVT-a1b2c3d4 3600  (1 hour TTL)
```

**Implementation details:**
- Use a Redis set with TTL for the deduplication window. Events older than 1 hour are extremely unlikely to be re-delivered.
- The dedup check and score update should be done in a Redis Lua script (EVAL) to make it atomic. This prevents a race condition where two consumer instances process the same duplicate simultaneously.

```lua
-- Redis Lua script for atomic dedup + score update
local event_id = KEYS[1]
local leaderboard = KEYS[2]
local player_id = ARGV[1]
local points = tonumber(ARGV[2])

if redis.call("SISMEMBER", "processed_events", event_id) == 1 then
    return 0  -- already processed
end

redis.call("SADD", "processed_events", event_id)
redis.call("EXPIRE", "processed_events", 3600)
redis.call("ZINCRBY", leaderboard, points, player_id)
return 1
```

### 5. Historical Leaderboards

**Extension architecture:**

```
[Score Consumer] --+--> [Redis: live-leaderboard]  (real-time)
                   |
                   +--> [Kafka: scored-events topic]
                           |
                           v
                   [Flink / Batch Job]
                           |
                           v
                   [PostgreSQL / ClickHouse]
                   (historical_scores table)
                           |
                   Columns: player_id, points, scored_at, game_id, period
                           |
                           v
                   [Leaderboard API]
                   GET /leaderboard?period=2026-01
```

**How it works without affecting real-time:**

1. The Score Consumer writes to Redis for real-time AND publishes to a separate Kafka topic (or the same one is consumed by a second consumer group).
2. A separate Flink job or batch process reads scored events and aggregates them into a `historical_scores` table, partitioned by time period (month, week, season).
3. The historical leaderboard is a simple SQL query: `SELECT player_id, SUM(points) FROM historical_scores WHERE period = '2026-01' GROUP BY player_id ORDER BY SUM(points) DESC LIMIT 100`.
4. This can be precomputed nightly or weekly and cached.

**Key point**: The real-time Redis leaderboard and the historical database are completely separate. The historical batch job can take minutes to run without affecting the 1-second real-time SLA. This is a classic CQRS pattern -- different read models optimized for different query patterns.
