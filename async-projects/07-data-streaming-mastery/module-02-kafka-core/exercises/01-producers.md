# Exercise 1: Kafka Producers

## Exercise 1.1: Sensor Data Producer

**Difficulty:** Beginner

Build a Kafka producer that simulates an IoT sensor network. Your producer should:

1. Generate JSON messages representing sensor readings with this schema:
   ```json
   {
     "sensor_id": "sensor-042",
     "temperature": 23.5,
     "humidity": 65.2,
     "pressure": 1013.25,
     "timestamp": "2024-01-15T10:30:00Z",
     "location": "building-A-floor-3"
   }
   ```
2. Use `sensor_id` as the message key (so readings from the same sensor always go to the same partition).
3. Include a delivery callback that logs success/failure.
4. Handle `KafkaException` and `BufferError` gracefully.
5. Send 30 messages across 5 simulated sensors, with a 0.5-second delay between messages.

**Topic:** `sensor-readings`

**Hints:**
- Use `faker` or `random` to generate realistic values.
- Temperature: 15.0 to 35.0. Humidity: 30.0 to 90.0. Pressure: 980.0 to 1040.0.
- Remember to `flush()` at the end.

---

## Exercise 1.2: Producer with Retry Metrics

**Difficulty:** Intermediate

Extend the basic producer to track and report delivery metrics:

1. Create a producer that sends 100 messages to the topic `metric-events`.
2. Implement a delivery callback that tracks:
   - Number of successful deliveries
   - Number of failures
   - Average delivery latency (using `msg.latency()`)
   - Per-partition delivery counts
3. Configure the producer with:
   - `acks=all`
   - `enable.idempotence=true`
   - `compression.type=gzip`
   - `linger.ms=100`
4. At the end, print a summary report showing all metrics.

**Hints:**
- Use a dictionary to track per-partition counts.
- `msg.latency()` returns delivery latency in seconds (float).
- You can use a class to encapsulate the metrics tracking.

---

## Exercise 1.3: Multi-Topic Event Router

**Difficulty:** Advanced

Build a producer that routes events to different topics based on event type:

1. Generate fake events of 3 types: `order`, `payment`, and `notification`.
2. Route each event type to its own topic:
   - `orders-topic`
   - `payments-topic`
   - `notifications-topic`
3. Each event should include common fields (`event_id`, `timestamp`, `event_type`) plus type-specific fields:
   - **Order:** `order_id`, `customer_id`, `items`, `total_amount`
   - **Payment:** `payment_id`, `order_id`, `amount`, `method`, `status`
   - **Notification:** `notification_id`, `user_id`, `channel`, `message`
4. Use message headers to include: `event_type`, `source_service`, and `correlation_id`.
5. Implement proper error handling and a final delivery report.

**Hints:**
- Create a helper function for each event type.
- Use `uuid.uuid4()` for IDs.
- The `headers` parameter in `producer.produce()` takes a list of tuples or a dict.

---

## Submission

Place your solution files in the `solutions/` directory:
- `solutions/ex01_sensor_producer.py`
- `solutions/ex02_metrics_producer.py`
- `solutions/ex03_event_router.py`
