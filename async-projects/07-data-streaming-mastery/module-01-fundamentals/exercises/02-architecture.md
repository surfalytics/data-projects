# Exercise 2: Architecture Design

> These are design exercises -- sketch diagrams on paper or use any diagramming tool. Compare with the [solutions](../solutions/02-architecture-solutions.md) when done.

---

## Exercise 2.1: E-Commerce Order Pipeline

Design an event-driven architecture for an e-commerce platform that handles the following requirements:

- Customers place orders through a web application.
- When an order is placed, the system must:
  1. Process payment
  2. Update inventory
  3. Send a confirmation email
  4. Notify the warehouse to begin fulfillment
  5. Update the analytics dashboard in real time

**Your task:**

1. Identify the producers, consumers, and event types in this system.
2. Draw the architecture diagram showing how events flow between services.
3. Should payment processing be synchronous or asynchronous? Justify your answer.
4. What happens if the email service is down when an order is placed? How does your architecture handle this?
5. Which events need strict ordering? Which can be processed in any order?
6. Choose a delivery guarantee for each event type and justify your choice.

---

## Exercise 2.2: IoT Sensor Monitoring

A manufacturing company has 10,000 sensors across 5 factories. Each sensor emits a reading every second. The system must:

- Detect anomalies in real time (e.g., temperature exceeding a threshold).
- Aggregate readings into 1-minute, 5-minute, and 1-hour windows for dashboards.
- Store all raw readings for 90 days for regulatory compliance.
- Alert on-call engineers within 5 seconds of detecting a critical anomaly.

**Your task:**

1. Calculate the data volume: how many events per second, per minute, per day?
2. Design the event schema for a sensor reading.
3. Design an architecture that handles all four requirements. Identify which components handle which requirement.
4. How would you partition the data? By sensor ID? By factory? By sensor type? Explain the trade-offs.
5. What happens when a factory loses network connectivity for 10 minutes and then reconnects, sending a burst of 600,000 delayed readings? How does your system handle:
   - The backpressure from the burst
   - The late-arriving data affecting your windowed aggregations
   - Ensuring no readings are lost for compliance

---

## Exercise 2.3: Event Sourcing for a Shopping Cart

Design an event-sourced shopping cart system. The cart supports the following operations:

- Add item to cart
- Remove item from cart
- Change item quantity
- Apply discount code
- Checkout (finalize cart)

**Your task:**

1. Define the complete set of events for this shopping cart. Name each event and define its payload.
2. Show how you would reconstruct the current cart state from a sequence of events. Walk through a specific example with at least 5 events.
3. A customer reports that a discount code was applied but their total does not reflect it. How would you use the event log to debug this?
4. The business wants to add a new feature: "Restore cart from 24 hours ago." How does event sourcing make this easy? What would this look like in a traditional CRUD system?
5. Design a CQRS read model optimized for the "cart summary" view (item count, total price, applied discounts). How does this read model stay in sync with the event store?

---

## Exercise 2.4: Multi-Region Event Architecture

A global SaaS company operates in three regions: US-East, EU-West, and AP-Southeast. They need to:

- Process user events locally in each region for low latency.
- Replicate critical events (e.g., account changes, billing) across all regions for consistency.
- Comply with GDPR by keeping EU user data in the EU region.
- Provide a global dashboard that aggregates metrics from all regions.

**Your task:**

1. Design a high-level architecture showing event flow within and between regions.
2. Which events should be replicated globally and which should stay local? Create a classification.
3. How do you handle conflicts when the same entity is updated in two regions simultaneously? Describe at least two conflict resolution strategies.
4. A user in the EU region travels to the US and uses the application. Where should their events be processed? How do you route them correctly while maintaining GDPR compliance?
5. What delivery guarantee would you use for cross-region replication? What are the consequences of choosing at-least-once vs exactly-once for this use case?

---

## Exercise 2.5: Designing a Real-Time Leaderboard

An online gaming platform needs a real-time leaderboard that:

- Updates within 1 second of a player scoring points.
- Shows the top 100 players globally.
- Supports 1 million concurrent players.
- Handles "score bursts" during tournaments (10x normal traffic).
- Allows players to see their own rank even if they are not in the top 100.

**Your task:**

1. Design the event schema for scoring events.
2. Choose between these two approaches and justify your decision:
   - **Approach A**: Process every score event through a stream processor that maintains the full leaderboard state.
   - **Approach B**: Score events update a fast data store (e.g., Redis sorted set) directly, and the leaderboard is read from the store.
3. How do you handle the "score bursts" during tournaments? What backpressure strategy would you use?
4. A player scores 100 points, but due to a bug, the event is published twice. How does your system handle this? Design an idempotency mechanism.
5. The company wants to add historical leaderboards ("Top players last month"). How would you extend your architecture to support this without affecting real-time performance?
