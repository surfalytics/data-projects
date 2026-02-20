# Module 10 Quiz: Production Considerations

Test your understanding of Kafka monitoring, security, performance tuning, and operational best practices.

---

### Question 1

Which metric is considered the single most important indicator of Kafka cluster health?

A) Consumer group lag
B) Under-replicated partitions
C) Messages in per second
D) JVM heap memory usage

---

### Question 2

What does the JMX Exporter do in a Kafka monitoring stack?

A) It sends alerts to PagerDuty when metrics exceed thresholds
B) It translates JMX MBeans into Prometheus-compatible metrics on an HTTP endpoint
C) It stores Kafka metrics in a time-series database
D) It creates Grafana dashboards automatically from Kafka metrics

---

### Question 3

In SSL/TLS configuration, what is the purpose of a truststore?

A) It stores the private key used to encrypt messages
B) It stores the broker's login credentials
C) It stores CA certificates used to verify the identity of the other party
D) It stores consumer group offsets for recovery

---

### Question 4

Which SASL mechanism should you avoid using in production without SSL encryption?

A) SCRAM-SHA-512
B) GSSAPI (Kerberos)
C) PLAIN
D) OAUTHBEARER

---

### Question 5

A producer is configured with `batch.size=131072`, `linger.ms=50`, and `compression.type=lz4`. Which statement best describes the producer's behavior?

A) It sends each message individually with lz4 compression after a 50ms delay
B) It accumulates messages into batches up to 128KB, waits up to 50ms for the batch to fill, then compresses and sends the batch
C) It compresses each message with lz4 and waits 50ms before sending a batch of up to 131072 messages
D) It sends batches of 128KB every 50 milliseconds regardless of how many messages are available

---

### Question 6

Your consumer group with `max.poll.records=500` processes each message with a 100ms database call. What is the worst-case time for a single `poll()` cycle, and what configuration is at risk of being exceeded?

A) 5 seconds; `session.timeout.ms` is at risk
B) 50 seconds; `max.poll.interval.ms` is at risk
C) 500 seconds; `max.poll.interval.ms` is at risk
D) 50 seconds; `heartbeat.interval.ms` is at risk

---

### Question 7

When planning capacity for a Kafka cluster with a replication factor of 3, how does replication affect storage requirements?

A) No effect -- replicas share the same storage
B) Storage requirements are doubled (2x)
C) Storage requirements are tripled (3x)
D) Storage requirements increase by 50%

---

### Question 8

What is the primary advantage of MirrorMaker 2 over the original MirrorMaker for multi-datacenter replication?

A) MirrorMaker 2 supports compression while the original does not
B) MirrorMaker 2 provides automatic offset translation and consumer group sync
C) MirrorMaker 2 runs on Kubernetes while the original requires bare metal
D) MirrorMaker 2 supports SSL while the original only supports PLAINTEXT

---

### Question 9

In a Kafka Connect distributed mode deployment, what happens when you add a new Connect worker with the same `group.id`?

A) The new worker creates a separate cluster and operates independently
B) The new worker joins the group, and connector tasks are automatically redistributed across all workers
C) The new worker remains idle until a manual rebalance is triggered
D) The new worker takes over all tasks from existing workers

---

### Question 10

Your Kafka cluster is deployed on AWS MSK with 3 brokers. One availability zone (AZ) goes down, taking one broker offline. With `replication.factor=3` and `min.insync.replicas=2`, what happens?

A) All topics become unavailable because one replica is missing
B) Producers can still write and consumers can still read, because 2 of 3 replicas are still in sync
C) Producers are blocked but consumers can still read from the remaining brokers
D) The cluster automatically provisions a replacement broker in the remaining AZs

---

## Answers

1. **B) Under-replicated partitions** -- URPs indicate that replicas are falling behind, which can lead to data loss if the leader fails. It is the top-priority metric for cluster health.

2. **B) It translates JMX MBeans into Prometheus-compatible metrics on an HTTP endpoint** -- The JMX Exporter runs as a Java agent inside the Kafka JVM and exposes metrics in Prometheus format on an HTTP endpoint (typically port 7071).

3. **C) It stores CA certificates used to verify the identity of the other party** -- The truststore contains the Certificate Authority certificates that the broker or client trusts. During the TLS handshake, the truststore is used to verify that the other party's certificate was signed by a trusted CA.

4. **C) PLAIN** -- SASL/PLAIN sends the username and password in cleartext. Without SSL encryption, anyone who can capture network traffic can read the credentials. SCRAM, Kerberos, and OAUTHBEARER do not send the raw password over the wire.

5. **B) It accumulates messages into batches up to 128KB, waits up to 50ms for the batch to fill, then compresses and sends the batch** -- `batch.size` sets the maximum batch size in bytes, `linger.ms` sets the maximum wait time for the batch to fill, and `compression.type` specifies the compression algorithm applied to the entire batch before sending.

6. **B) 50 seconds; `max.poll.interval.ms` is at risk** -- Worst-case processing time = 500 records * 100ms = 50,000ms = 50 seconds. The default `max.poll.interval.ms` is 300,000ms (5 minutes), so 50 seconds is within the limit for average cases. However, if database latency spikes (e.g., P99 = 1 second), it would be 500 * 1000ms = 500 seconds, exceeding the 5-minute limit.

7. **C) Storage requirements are tripled (3x)** -- Each message is stored on 3 brokers (the leader and 2 followers). Total cluster storage = data volume * replication factor.

8. **B) MirrorMaker 2 provides automatic offset translation and consumer group sync** -- MM2 (based on Kafka Connect) can translate consumer group offsets between clusters, sync consumer group state, and handle topic prefixing with cycle detection. The original MirrorMaker had none of these features.

9. **B) The new worker joins the group, and connector tasks are automatically redistributed across all workers** -- Kafka Connect distributed mode uses the same group coordination protocol as consumer groups. When a new worker joins, a rebalance redistributes tasks evenly.

10. **B) Producers can still write and consumers can still read, because 2 of 3 replicas are still in sync** -- With `min.insync.replicas=2` and `acks=all`, the producer requires 2 replicas to acknowledge a write. With 2 out of 3 brokers still running, this requirement is met. The offline broker's partitions will be under-replicated but available.
