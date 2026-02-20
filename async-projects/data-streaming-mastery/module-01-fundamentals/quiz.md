# Quiz: Streaming Fundamentals

> 10 multiple-choice questions. Choose the best answer for each. Answers are at the bottom.

---

### Question 1

What is the defining characteristic of an event in a streaming system?

- A) It is a request for a specific action to be performed
- B) It is a mutable record that can be updated as new information arrives
- C) It is an immutable record of something that happened at a specific point in time
- D) It is a temporary message that is deleted after consumption

---

### Question 2

A checkout service publishes an `OrderPlaced` event. A billing service, a shipping service, and an analytics service all react to it. The checkout service has no knowledge of these consumers. Which architectural property does this demonstrate?

- A) Tight coupling
- B) Synchronous communication
- C) Loose coupling through event-driven architecture
- D) Command-query responsibility segregation

---

### Question 3

You are building a system that sends promotional push notifications to mobile users. Occasionally losing a notification is acceptable, but sending the same promotion twice would annoy users. Which delivery guarantee is most appropriate?

- A) At-most-once
- B) At-least-once
- C) Exactly-once
- D) Best-effort with retries

---

### Question 4

A temperature sensor records a reading at 14:00:00. Due to network delay, the reading arrives at the Kafka broker at 14:00:05. The Flink consumer processes it at 14:00:12. If you are computing hourly average temperatures and want the most accurate results, which timestamp should you use for windowing?

- A) Processing time (14:00:12)
- B) Ingestion time (14:00:05)
- C) Event time (14:00:00)
- D) The current wall-clock time when the window closes

---

### Question 5

What is backpressure in a streaming system?

- A) The force applied by consumers to request more data from producers
- B) The condition where a downstream system cannot keep up with the rate of incoming data
- C) The technique of compressing messages to reduce broker storage
- D) The process of replaying events from the beginning of a topic

---

### Question 6

Which statement best describes the difference between batch and stream processing?

- A) Batch processing is always faster than stream processing
- B) Stream processing works on bounded datasets while batch works on unbounded datasets
- C) Batch processing operates on finite datasets on a schedule; stream processing operates on continuous, unbounded data as it arrives
- D) Stream processing cannot perform aggregations, while batch processing can

---

### Question 7

In an event-sourced system, a bank account has the following event history:

1. `AccountOpened` (balance: $0)
2. `Deposited` ($500)
3. `Withdrawn` ($100)
4. `Deposited` ($200)

What is the current balance, and how is it derived?

- A) $200 -- it is stored directly in the database
- B) $600 -- it is computed by replaying all events: $0 + $500 - $100 + $200
- C) $500 -- only the last deposit is considered
- D) $600 -- it is the sum of all deposits

---

### Question 8

A ride-sharing application publishes events keyed by `ride_id`. What does this keying strategy guarantee in Kafka?

- A) All events are delivered exactly once
- B) All events for the same ride go to the same partition, preserving their order
- C) Events are distributed evenly across all consumers
- D) Events are automatically deduplicated

---

### Question 9

Your stream processor can handle 10,000 events per second, but during peak hours the producer emits 50,000 events per second. You are using Kafka as the broker. Which of the following is true about how Kafka helps manage this situation?

- A) Kafka automatically speeds up the consumer to match the producer rate
- B) Kafka's push-based model forces the consumer to process events immediately
- C) Kafka's pull-based model lets the consumer read at its own pace while durably storing the backlog on disk
- D) Kafka drops events that exceed the consumer's capacity

---

### Question 10

A company uses CQRS (Command Query Responsibility Segregation) alongside event sourcing. What is the primary benefit of separating the write model from the read model?

- A) It eliminates the need for a database entirely
- B) It guarantees strong consistency between reads and writes at all times
- C) It allows the read model to be optimized for queries independently of the write model, which is optimized for consistency
- D) It reduces the total number of events stored in the system

---

## Answers

### Question 1: **C**

An event is an immutable record of something that happened. It represents a fact. Option A describes a command, not an event. Option B is incorrect because events are immutable by definition. Option D describes a transient message, not an event.

### Question 2: **C**

This is the textbook example of loose coupling through event-driven architecture. The producer (checkout service) publishes events without knowing who consumes them. Consumers subscribe independently. Adding or removing consumers requires no changes to the producer.

### Question 3: **A**

At-most-once is the right choice. The notification is either delivered or lost, but never duplicated. Since losing a notification is acceptable but duplicates would annoy users, this is the correct trade-off. At-least-once would risk duplicate promotions. Exactly-once would add unnecessary complexity for a non-critical notification.

### Question 4: **C**

Event time (14:00:00) is the correct timestamp for accurate windowed aggregations. It represents when the reading actually occurred in the physical world. Processing time or ingestion time would misattribute the reading to a later time window, distorting the hourly averages.

### Question 5: **B**

Backpressure is the condition where a downstream component (consumer, processor) cannot keep up with the rate of data from an upstream component (producer, broker). It is a problem to be managed, not a feature. Strategies for handling it include buffering, dropping, sampling, flow control, and scaling.

### Question 6: **C**

Batch processing works on bounded (finite) datasets on a schedule (e.g., hourly, daily). Stream processing works on unbounded (continuous) data as it arrives in real time. Option A is wrong because batch is not always faster. Option B reverses the definitions. Option D is wrong because stream processing can and does perform aggregations using windowing.

### Question 7: **B**

In an event-sourced system, the current state is derived by replaying all events from the beginning. $0 (opened) + $500 (deposit) - $100 (withdrawal) + $200 (deposit) = $600. The balance is not stored directly -- it is computed from the event log. This provides a complete audit trail.

### Question 8: **B**

In Kafka, the message key determines the partition assignment (via a hash function). All messages with the same key go to the same partition, and Kafka guarantees ordering within a partition. This means all events for ride R1001 are ordered correctly. This does not provide exactly-once delivery, even distribution, or deduplication -- those are separate concerns.

### Question 9: **C**

Kafka uses a pull-based consumer model. Consumers poll for messages at their own rate. When the consumer is slower than the producer, the unconsumed messages are stored durably on Kafka's disk (up to the configured retention period). The consumer processes them when it can. Kafka does not speed up consumers, does not push messages, and does not drop messages due to slow consumption.

### Question 10: **C**

CQRS separates writes (optimized for consistency and validation) from reads (optimized for query performance). The write model can use an append-only event store, while the read model can use denormalized tables, search indexes, or caches tailored to specific query patterns. This does not eliminate databases (Option A), does not guarantee strong consistency (Option B -- it is typically eventually consistent), and does not reduce events stored (Option D).

---

**Score Interpretation:**
- 9-10: Excellent. You have a strong grasp of streaming fundamentals.
- 7-8: Good. Review the topics you missed before moving to Module 2.
- 5-6: Fair. Re-read the relevant sections in the README and try the exercises.
- Below 5: Spend more time with the material. These concepts are the foundation for everything that follows.

**[Continue to Module 2: Kafka Core -->](../module-02-kafka-core/)**
