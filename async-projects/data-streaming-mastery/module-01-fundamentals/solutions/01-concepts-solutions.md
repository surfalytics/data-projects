# Solutions: Exercise 1 -- Streaming Concepts

---

## Solution 1.1: Design an Event Schema for a Ride-Sharing App

### Ride Lifecycle Events

Here are 8 events covering the full lifecycle of a ride:

#### 1. `ride.requested`

```json
{
  "type": "ride.requested",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:00:00Z",
  "payload": {
    "ride_id": "R1001",
    "rider_id": "USR-500",
    "pickup_location": { "lat": 37.7749, "lng": -122.4194 },
    "dropoff_location": { "lat": 37.7849, "lng": -122.4094 },
    "ride_type": "standard",
    "estimated_fare": 18.50
  }
}
```

#### 2. `ride.driver_matched`

```json
{
  "type": "ride.driver_matched",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:00:15Z",
  "payload": {
    "ride_id": "R1001",
    "driver_id": "DRV-200",
    "driver_location": { "lat": 37.7730, "lng": -122.4180 },
    "estimated_arrival_minutes": 4
  }
}
```

#### 3. `ride.driver_arrived`

```json
{
  "type": "ride.driver_arrived",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:04:30Z",
  "payload": {
    "ride_id": "R1001",
    "driver_id": "DRV-200",
    "arrival_location": { "lat": 37.7749, "lng": -122.4194 }
  }
}
```

#### 4. `ride.started`

```json
{
  "type": "ride.started",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:05:00Z",
  "payload": {
    "ride_id": "R1001",
    "actual_pickup_location": { "lat": 37.7749, "lng": -122.4194 }
  }
}
```

#### 5. `ride.location_updated`

```json
{
  "type": "ride.location_updated",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:07:00Z",
  "payload": {
    "ride_id": "R1001",
    "driver_id": "DRV-200",
    "location": { "lat": 37.7790, "lng": -122.4140 },
    "speed_mph": 25,
    "heading": 45
  }
}
```

#### 6. `ride.completed`

```json
{
  "type": "ride.completed",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:15:00Z",
  "payload": {
    "ride_id": "R1001",
    "actual_dropoff_location": { "lat": 37.7849, "lng": -122.4094 },
    "distance_miles": 1.2,
    "duration_minutes": 10,
    "final_fare": 17.80
  }
}
```

#### 7. `ride.payment_processed`

```json
{
  "type": "ride.payment_processed",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:15:05Z",
  "payload": {
    "ride_id": "R1001",
    "rider_id": "USR-500",
    "amount": 17.80,
    "currency": "USD",
    "payment_method": "card_ending_4242",
    "transaction_id": "TXN-88201"
  }
}
```

#### 8. `ride.rated`

```json
{
  "type": "ride.rated",
  "key": "ride-R1001",
  "timestamp": "2026-02-19T14:20:00Z",
  "payload": {
    "ride_id": "R1001",
    "rated_by": "USR-500",
    "rated_entity": "DRV-200",
    "rating": 5,
    "comment": "Great driver!"
  }
}
```

### Why `ride_id` as the Key

The key is `ride-R1001` (the ride ID) for all events. This ensures:

- **Ordering**: All events for a single ride are sent to the same partition, guaranteeing they are consumed in order. This is critical because `ride.started` must be processed before `ride.completed`.
- **Partitioning**: Different rides are distributed across partitions for parallelism. Ride R1001 and ride R1002 can be processed concurrently by different consumers.
- **Compaction**: If log compaction is enabled, the latest state per ride is retained.

**Alternative key considerations:**
- Using `driver_id` as the key would ensure all events for a single driver are ordered, useful for driver analytics. But it would mean different rides by the same driver cannot be processed in parallel.
- Using `rider_id` would be useful for rider-centric views but has the same trade-off.

The choice depends on the primary access pattern. For ride lifecycle management, `ride_id` is the best choice.

---

## Solution 1.2: Identify the Right Delivery Guarantee

### 1. Real-time ad impression counter -- **At-Most-Once**

**Reasoning**: The dashboard shows approximate counts and updates every 5 seconds. Losing a small percentage of impressions has minimal impact on an approximate metric. The high volume of ad impressions (potentially millions per second) makes at-most-once attractive for performance.

**Wrong choice impact**:
- At-least-once: Duplicate impressions inflate the count. Advertisers are overcharged. This could be a legal issue.
- Exactly-once: Overkill for an approximate counter. The added latency and complexity are not justified.

### 2. Payment processing system -- **Exactly-Once**

**Reasoning**: Charging a credit card is a financial transaction. Charging twice is unacceptable (customer complaints, chargebacks, legal liability). Not charging at all means lost revenue. This is the textbook case for exactly-once semantics.

**Wrong choice impact**:
- At-most-once: Payments could be silently lost. Orders are fulfilled but never paid for.
- At-least-once without idempotency: Customers are charged multiple times. This results in support tickets, chargebacks, and loss of trust.

**Implementation note**: In practice, this is often at-least-once delivery combined with idempotent payment processing (using the `transaction_id` to deduplicate). The payment gateway checks if `TXN-88201` was already processed before charging again.

### 3. User activity tracking for ML -- **At-Least-Once**

**Reasoning**: The ML model is retrained weekly on aggregated data. A few duplicate events in millions of training samples have negligible impact on model quality. However, losing significant amounts of activity data would create blind spots in the recommendation model.

**Wrong choice impact**:
- At-most-once: Lost activity events mean the model does not learn about user preferences. Recommendations degrade.
- Exactly-once: Unnecessary complexity for a use case where slight duplication is absorbed by aggregation.

### 4. IoT temperature monitoring for compliance -- **At-Least-Once (with idempotent storage)**

**Reasoning**: Regulatory compliance requires provable records of every reading. Losing a reading could mean a compliance violation and potential fines. Duplicate readings can be deduplicated at the storage layer using the sensor ID + timestamp as a unique key.

**Wrong choice impact**:
- At-most-once: Missing temperature readings during a compliance audit. If temperatures exceeded thresholds during the gap, the company cannot prove compliance.
- Exactly-once: While ideal, the cost and complexity may not be justified when sensor_id + timestamp provides natural deduplication.

### 5. Chat application -- **At-Least-Once (with deduplication at display)**

**Reasoning**: Users expect every message to be delivered. A lost message is a terrible user experience. Duplicate messages can be filtered at the client side using a message ID. This is how most chat applications work (WhatsApp, Slack, etc.).

**Wrong choice impact**:
- At-most-once: Messages disappear silently. Users lose trust in the platform.
- Exactly-once: While desirable, the client-side deduplication approach (at-least-once + message IDs) achieves the same result at lower infrastructure cost.

---

## Solution 1.3: Streaming vs Batch -- Make the Call

### 1. End-of-month financial reconciliation -- **Batch**

**Justification**: Financial reconciliation is inherently periodic. It compares records from multiple systems (POS, bank, ERP) at a specific point in time. The output is a monthly report, not a real-time dashboard. Batch processing aligns perfectly with this cadence.

- Data freshness requirement: Once per month.
- Complexity: Requires joining large datasets from multiple sources.
- Tools: Spark, dbt, Airflow for orchestration.

### 2. Real-time inventory tracking -- **Streaming**

**Justification**: At 10,000 orders/hour, inventory changes constantly. A fulfillment center needs to know current stock levels to avoid overselling or mispicking. A batch process that runs hourly would mean inventory counts could be off by up to 10,000 orders.

- Data freshness requirement: Seconds.
- Key concern: Overselling if inventory counts lag.
- Tools: Kafka + stream processor updating an inventory database in real time.

### 3. Social media trending posts -- **Hybrid**

**Justification**: This requires both:
- **Streaming**: Continuously count interactions (likes, shares, comments) in sliding windows to detect what is trending right now.
- **Batch**: Periodically recalculate "trending over the last 24 hours" using complete data to correct for late-arriving events and ensure accuracy.

The real-time stream provides immediate trending signals; the batch process provides the authoritative ranking.

### 4. CRM data loading + churn alert -- **Hybrid**

**Justification**: Two distinct requirements with different latency needs:
- **Batch**: Nightly ETL from CRM to data warehouse. This is a classic batch use case -- the warehouse consumers (analysts, reports) operate on a daily cadence.
- **Streaming**: Real-time monitoring of customer activity signals. When a high-value customer shows churn indicators (cancellation page visit, support ticket, usage drop), trigger an immediate alert to the account team.

### 5. Fraud detection -- **Streaming**

**Justification**: Fraud detection must happen before the transaction is approved. A batch process that runs after the fact can only detect fraud retrospectively and initiate chargebacks. Real-time stream processing can block the transaction within milliseconds.

- Latency requirement: Sub-second (the payment authorization window is typically 1-3 seconds).
- Tools: Kafka Streams or Flink with a fraud scoring model.
- Note: A batch layer may supplement this by training the fraud model on historical data.

---

## Solution 1.4: Time Semantics in Practice

### 1. Processing Time Windows

Using processing time:

| Event | Processing Time | Window |
|---|---|---|
| Trip A | 14:00:10 | 14:00 - 15:00 |
| Trip B | 14:01:45 | 14:00 - 15:00 |
| Trip C | 14:02:05 | 14:00 - 15:00 |
| Trip D | 14:03:15 | 14:00 - 15:00 |

**All four trips fall into the 14:00-15:00 window.** The 13:00-14:00 window is empty.

**Is this accurate?** No. Trips A and C actually occurred in the 13:00-14:00 hour. City planners would see no traffic in the 13:00 hour and a spike in the 14:00 hour, which misrepresents reality. Traffic models built on this data would be wrong.

### 2. Event Time Windows

Using event time:

| Event | Event Time | Window |
|---|---|---|
| Trip A | 13:58:00 | 13:00 - 14:00 |
| Trip C | 13:55:00 | 13:00 - 14:00 |
| Trip B | 14:01:30 | 14:00 - 15:00 |
| Trip D | 14:03:00 | 14:00 - 15:00 |

**Trips A and C fall into 13:00-14:00; Trips B and D fall into 14:00-15:00.** This accurately reflects when trips actually happened and gives city planners a true picture of traffic patterns.

### 3. Why Trip C has a 7-minute delay

Possible reasons for the 7-minute gap between event time (13:55:00) and ingestion time (14:02:00):

1. **Network connectivity loss**: The driver's phone lost cellular signal (tunnel, rural area, parking garage) and the event was buffered locally until connectivity resumed.
2. **Client-side batching**: The mobile app batches events and sends them periodically to conserve battery. Trip C's completion event was waiting in the batch queue.
3. **Service outage**: The ingestion service was temporarily down, and the event was retried after recovery.
4. **Clock skew**: The driver's phone clock is out of sync with the server clock (though 7 minutes is extreme for NTP-synced devices).
5. **Upstream processing delay**: An intermediate service (e.g., trip finalization service) held the event for additional processing before publishing it to the broker.

### 4. Is Trip C late?

Yes, Trip C is late. The watermark is at 14:01:00, meaning the system believes all events with timestamps up to 14:01:00 have arrived. Trip C's event time is 13:55:00, which is before the watermark.

**What the system should do depends on the allowed lateness configuration:**
- If allowed lateness >= 6 minutes: The event is accepted and the 13:00-14:00 window is updated (a retraction/update is emitted).
- If allowed lateness < 6 minutes: The event is dropped or sent to a side output (dead letter queue) for later processing.

### 5. Setting allowed lateness

**Recommendation**: Set allowed lateness to 10-15 minutes.

**Reasoning for this use case:**
- City planning dashboards do not require sub-second precision. A delay of 10-15 minutes in finalizing an hourly window is acceptable.
- Trip events can be delayed by mobile network issues, which commonly cause delays of up to 5-10 minutes.
- The cost of inaccurate traffic data (making infrastructure decisions on wrong data) outweighs the cost of slightly delayed results.

**Trade-offs:**
- **Higher allowed lateness (e.g., 30 minutes)**: More accurate results but windows stay open longer, consuming more memory. Results are delayed. For hourly windows this may be acceptable.
- **Lower allowed lateness (e.g., 2 minutes)**: Results are available quickly but you lose late events. Trip C would be dropped.
- **Compromise**: Use 15 minutes of allowed lateness and send late-late events to a dead letter topic for batch reconciliation.

---

## Solution 1.5: Backpressure Scenario Analysis

### 1. Failure Cascade Without Backpressure

Step-by-step failure:

1. **t=0**: Incident begins. Log rate jumps from 50K to 500K events/sec.
2. **t=1s**: Stream processor's input buffer begins filling. Processing latency increases.
3. **t=5s**: Input buffer is full. If the broker is push-based, it keeps sending. The processor starts rejecting or timing out on connections.
4. **t=10s**: Broker's internal buffers begin filling as it cannot deliver to the processor. Broker memory usage climbs.
5. **t=30s**: Broker hits memory limits. Depending on the system:
   - It starts dropping messages silently.
   - It slows down accepting messages from producers.
   - It crashes entirely.
6. **t=30s+**: If the broker crashes, the 200 microservices' logging libraries start buffering locally or blocking application threads waiting to send logs.
7. **t=1m**: Application threads blocked on logging cause request timeouts. The incident that generated the logs is now amplified -- services are failing because their logging is blocked.
8. **Cascading failure**: The original incident (maybe one service was unhealthy) has now taken down the entire platform because the logging infrastructure could not handle the load.

This is a real pattern. Logging should never take down production services.

### 2. Strategy Analysis

#### Buffering

- **Implementation**: Use Kafka as the buffer. With sufficient retention and disk space, Kafka can absorb hours of backlog. The processor reads at its own pace.
- **Pros**: No data loss. Simple to implement. Kafka is designed for exactly this.
- **Cons**: Buffer has finite size. During sustained overload, even Kafka's disks will fill. Increasing lag means alerts are delayed.
- **Failure condition**: The overload lasts longer than your buffer capacity. If Kafka has 1TB of disk and each event is 1KB, you can buffer roughly 1 billion events. At 400K excess events/sec, you have about 40 minutes before disk fills.

#### Dropping

- **Implementation**: Configure the stream processor to drop events when queue depth exceeds a threshold. Alternatively, use a Kafka consumer that skips to the latest offset when too far behind.
- **Pros**: System stays healthy. Processing latency stays low for events that are processed.
- **Cons**: Data loss. For a log analytics platform, you lose visibility into the incident exactly when you need it most.
- **Failure condition**: If you drop too aggressively, you miss the critical log lines that explain the root cause of the incident.

#### Sampling

- **Implementation**: Process every Nth event (e.g., 1 in 5). Or use probabilistic sampling based on a hash of the event key.
- **Pros**: Maintains statistical visibility with reduced throughput. Alerts on high-frequency errors still fire (just with a slight detection delay).
- **Cons**: Rare but critical log lines (e.g., a specific error that appears once) might be sampled out. Not suitable for compliance or auditing.
- **Failure condition**: The one log line that explains the root cause happens to be in the dropped 80%.

#### Flow Control

- **Implementation**: The processor signals the broker to slow delivery. Or the broker signals producers to slow down. In Kafka, this is not natively supported (pull model handles it differently), but in push-based systems, TCP flow control or explicit protocol-level signals can throttle producers.
- **Pros**: No data loss. No duplicates. Back-propagates pressure to the source.
- **Cons**: In a logging scenario, slowing down producers means slowing down the applications themselves. This amplifies the original incident. This is the worst strategy for logging.
- **Failure condition**: The 200 microservices slow down because logging is blocked, turning a logging overload into a platform outage.

#### Scaling (Auto-scaling)

- **Implementation**: Add more consumer instances. If you have 10 partitions and 5 consumers, scale to 10 consumers. With Kubernetes, configure HPA (Horizontal Pod Autoscaler) based on consumer lag.
- **Pros**: Increases actual processing capacity. No data loss or degradation.
- **Cons**: Scaling takes time (seconds to minutes). May not be fast enough for sudden spikes. Limited by the number of partitions. Costs money.
- **Failure condition**: The spike happens faster than auto-scaling can react. Or you are already at partition-limit (number of consumers cannot exceed number of partitions in Kafka).

### 3. Recommended Multi-Layered Plan

**Layer 1 -- Kafka as a buffer (always active):**
Configure Kafka topics with generous retention (7 days, ample disk). This absorbs short spikes naturally. The processor reads at its own pace.

**Layer 2 -- Auto-scaling (reactive, 30-second response):**
Monitor consumer lag. When lag exceeds 60 seconds, auto-scale processor instances up to the partition count. Pre-provision enough Kafka partitions (e.g., 50) to allow meaningful scaling.

**Layer 3 -- Priority-based processing (sustained overload):**
If lag exceeds 5 minutes, switch to priority mode:
- Process ERROR and FATAL level logs at full throughput (these are needed for incident response).
- Sample INFO and DEBUG logs at 10% (these are high-volume but low-urgency).
- This is a form of intelligent dropping/sampling.

**Layer 4 -- Overflow to cold storage (last resort):**
If lag exceeds 30 minutes, start writing raw events directly to object storage (S3) without processing. These can be batch-processed later for compliance and historical analysis. The real-time pipeline focuses on alerts only.

### 4. How Kafka Helps

Kafka's **pull-based consumer model** is fundamentally different from push-based systems:

- **Pull model (Kafka)**: Consumers poll for new records at their own pace. If they are slow, they simply fall behind. The data stays in the topic, retained by Kafka's retention policy. There is no mechanism for the broker to overwhelm the consumer.
- **Push model (RabbitMQ, WebSockets)**: The broker pushes messages to the consumer. If the consumer cannot keep up, messages queue in the broker's memory. The broker must implement complex flow control, dead-letter queues, or TTL-based expiry.

Additionally, Kafka stores messages on disk with configurable retention, acting as a natural buffer. The broker does not need to keep messages in memory. This means Kafka can absorb hours or days of backlog without performance degradation, while a push-based system's memory-resident queues would overflow in minutes.
