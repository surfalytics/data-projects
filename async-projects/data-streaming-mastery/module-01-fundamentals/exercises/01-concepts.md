# Exercise 1: Streaming Concepts

> These are thought exercises -- no code required. Write your answers in a notebook or text file. Compare with the [solutions](../solutions/01-concepts-solutions.md) when done.

---

## Exercise 1.1: Design an Event Schema for a Ride-Sharing App

A ride-sharing application (like Uber or Lyft) generates many events during the lifecycle of a single ride.

**Your task:**

1. List at least 6 distinct events that occur during the lifecycle of a ride, from the moment a rider opens the app to after the ride is completed.
2. For each event, define a schema that includes:
   - Event type name (e.g., `ride.requested`)
   - Key (what entity does this event belong to?)
   - Timestamp
   - Payload fields with data types
3. Explain why you chose the key you did. How does it affect partitioning and ordering?

**Hints:**
- Think about the full lifecycle: request, matching, pickup, transit, dropoff, payment, rating.
- Consider which events need strict ordering guarantees and which do not.

---

## Exercise 1.2: Identify the Right Delivery Guarantee

For each of the following scenarios, identify which delivery guarantee (at-most-once, at-least-once, or exactly-once) is most appropriate and explain your reasoning.

**Scenarios:**

1. **A real-time ad impression counter** that displays approximate view counts on a marketing dashboard updated every 5 seconds.

2. **A payment processing system** that charges customer credit cards when they complete a purchase.

3. **A user activity tracking pipeline** that feeds into a machine learning recommendation engine. The ML model is retrained weekly on aggregated data.

4. **An IoT temperature monitoring system** for a pharmaceutical cold storage facility where regulatory compliance requires provable records of every temperature reading.

5. **A chat application** that delivers messages between users in real time.

For each answer, also describe what would happen if you chose the wrong guarantee (e.g., what is the impact of duplicates or data loss in this context?).

---

## Exercise 1.3: Streaming vs Batch -- Make the Call

For each of the following business requirements, decide whether you would use batch processing, stream processing, or a hybrid approach. Justify your choice.

1. **End-of-month financial reconciliation** for a retail chain with 500 stores.

2. **Real-time inventory tracking** for a warehouse fulfillment center that processes 10,000 orders per hour.

3. **A social media feed** that shows users trending posts from the last 24 hours, updated every few seconds.

4. **A nightly ETL pipeline** that loads customer data from a CRM into a data warehouse, plus a real-time alert when a high-value customer churns.

5. **A fraud detection system** for credit card transactions that needs to block suspicious transactions before they are approved.

---

## Exercise 1.4: Time Semantics in Practice

A ride-sharing company is calculating "average trip duration by hour" for a real-time dashboard that city planners use to understand traffic patterns.

Consider this sequence of events:

| Event | Event Time | Ingestion Time | Processing Time |
|---|---|---|---|
| Trip A completed | 13:58:00 | 13:58:02 | 14:00:10 |
| Trip B completed | 14:01:30 | 14:01:31 | 14:01:45 |
| Trip C completed | 13:55:00 | 14:02:00 | 14:02:05 |
| Trip D completed | 14:03:00 | 14:03:01 | 14:03:15 |

**Questions:**

1. If you use **processing time** to assign trips to hourly windows, which trips fall into the 13:00-14:00 window and which fall into the 14:00-15:00 window? Would this give city planners an accurate picture?

2. If you use **event time**, which trips fall into which windows? Is this more accurate?

3. Trip C has a 7-minute gap between event time and ingestion time. What might have caused this delay? List at least 3 possible reasons.

4. Your watermark is currently at 14:01:00 and Trip C (event time 13:55:00) arrives. Is Trip C "late"? What should the system do with it?

5. How would you set the allowed lateness for this use case? What trade-offs are you making?

---

## Exercise 1.5: Backpressure Scenario Analysis

You are the architect for a log analytics platform. The platform ingests application logs from 200 microservices and processes them for alerting and dashboarding.

Normal throughput: 50,000 events/second.

During a major incident, services start logging at 10x the normal rate: 500,000 events/second. Your stream processor can only handle 100,000 events/second.

**Questions:**

1. Describe what happens if you have no backpressure handling in place. Walk through the failure cascade step by step.

2. For each of the five backpressure strategies (buffering, dropping, sampling, flow control, scaling), explain:
   - How you would implement it in this scenario
   - The pros and cons for a log analytics use case specifically
   - Under what conditions this strategy would fail

3. Which combination of strategies would you recommend for this platform? Design a multi-layered backpressure plan that handles both brief spikes and sustained overload.

4. How does Kafka's architecture naturally help with this problem compared to a push-based messaging system?
