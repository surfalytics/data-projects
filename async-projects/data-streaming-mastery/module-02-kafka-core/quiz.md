# Module 2 Quiz: Apache Kafka Core Concepts

Test your understanding of Kafka fundamentals. Choose the best answer for each question.

---

### Question 1
What is the primary unit of parallelism in Kafka?

A) Topic
B) Broker
C) Partition
D) Consumer Group

---

### Question 2
When a producer sends a message with a non-null key, how is the target partition determined (by default)?

A) Round-robin across all partitions
B) The producer randomly selects a partition
C) `hash(key) % number_of_partitions`
D) The broker assigns the partition based on load

---

### Question 3
What does `acks=all` guarantee?

A) The message is written to the leader only
B) The message is written to all brokers in the cluster
C) The message is acknowledged by all in-sync replicas (ISR)
D) The message is delivered to all consumers

---

### Question 4
In a consumer group with 3 consumers subscribed to a topic with 4 partitions, how are partitions assigned?

A) Each consumer gets 1 partition, 1 partition is unassigned
B) Two consumers get 1 partition each, one consumer gets 2 partitions
C) All consumers get all 4 partitions
D) Kafka randomly assigns partitions each poll cycle

---

### Question 5
What happens when a consumer group has MORE consumers than partitions?

A) The extra consumers throw an error
B) The extra consumers sit idle (no partitions assigned)
C) Partitions are shared between consumers
D) Kafka automatically creates more partitions

---

### Question 6
What is the difference between "committed offset" and "current offset"?

A) They are the same thing
B) Current offset is where the consumer is reading; committed offset is persisted to Kafka
C) Committed offset is always ahead of current offset
D) Current offset is stored in ZooKeeper; committed offset is stored in the topic

---

### Question 7
Which `auto.offset.reset` value should you use if you want a NEW consumer group to read all existing messages from the beginning?

A) `latest`
B) `earliest`
C) `none`
D) `beginning`

---

### Question 8
What does an idempotent producer (`enable.idempotence=true`) prevent?

A) Message loss during network failures
B) Duplicate messages from producer retries within a single partition
C) Consumers reading the same message twice
D) Brokers running out of disk space

---

### Question 9
Given `replication.factor=3` and `min.insync.replicas=2`, how many brokers can fail while still allowing writes (with `acks=all`)?

A) 0
B) 1
C) 2
D) 3

---

### Question 10
During a consumer group rebalance, what happens to message processing?

A) Processing continues uninterrupted
B) Processing pauses for consumers whose partitions are being reassigned (stop-the-world with eager protocol)
C) The topic becomes read-only
D) All messages in the topic are replayed

---

## Answers

| Question | Answer | Explanation |
|---|---|---|
| 1 | **C) Partition** | Partitions are the fundamental unit of parallelism. Each partition can be consumed by exactly one consumer in a group, and partitions are the unit of replication. |
| 2 | **C) `hash(key) % number_of_partitions`** | By default, Kafka uses a hash of the key (murmur2) modulo the number of partitions. This guarantees the same key always maps to the same partition. |
| 3 | **C) The message is acknowledged by all in-sync replicas (ISR)** | `acks=all` means the leader waits for all in-sync replicas to acknowledge the write. It does not mean ALL brokers or all consumers -- only ISR members. |
| 4 | **B) Two consumers get 1 partition each, one consumer gets 2 partitions** | With 4 partitions and 3 consumers, one consumer will be assigned 2 partitions and the other two will get 1 each (exact assignment depends on the strategy). |
| 5 | **B) The extra consumers sit idle** | Each partition can only be assigned to one consumer in a group. If there are more consumers than partitions, the excess consumers are idle. This is why you should not have more consumers than partitions. |
| 6 | **B) Current offset is where the consumer is reading; committed offset is persisted to Kafka** | The current offset tracks the consumer's position in memory. The committed offset is durably stored in the `__consumer_offsets` topic and survives restarts. |
| 7 | **B) `earliest`** | `earliest` tells the consumer to start from the beginning of the partition when there is no committed offset. `latest` would skip all existing messages. |
| 8 | **B) Duplicate messages from producer retries within a single partition** | The idempotent producer assigns a PID and sequence number to each message, allowing the broker to deduplicate retries. It does not prevent cross-partition or cross-session duplicates. |
| 9 | **B) 1** | With RF=3 and min.insync.replicas=2, you need at least 2 replicas (including the leader) to be alive to accept writes. So 1 broker can fail. If 2 fail, only 1 replica remains, which is below the minimum. |
| 10 | **B) Processing pauses for consumers whose partitions are being reassigned** | With the eager (default) rebalance protocol, all consumers revoke their partitions and stop processing during rebalance. The cooperative protocol (CooperativeSticky) reduces this by only reassigning partitions that need to move. |
