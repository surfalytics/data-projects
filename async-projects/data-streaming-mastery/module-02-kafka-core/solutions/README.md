# Solutions -- Module 2: Kafka Core Concepts

## Solution Files

| Exercise | File | Description |
|---|---|---|
| 1.1 | `ex01_sensor_producer.py` | IoT sensor data producer with JSON payloads and key-based partitioning |
| 1.2 | `ex02_metrics_producer.py` | Producer with delivery metrics tracking (latency, per-partition counts) |
| 1.3 | `ex03_event_router.py` | Multi-topic event router with message headers |
| 2.1 | `ex04_filter_consumer.py` | Consumer that filters sensor readings for high-temperature alerts |
| 2.2 | `ex05_multi_group_consumer.py` | Consumer group demo with rebalance callbacks and manual commit |
| 2.3 | `ex06_dlq_consumer.py` | Dead Letter Queue pattern with validation and error routing |
| 3.1 | `ex07_partition_analysis.py` | Key-based partition distribution analysis (producer + consumer) |
| 3.2 | `ex08_geo_partitioner.py` | Geographic partitioner routing events by country code |

## Running the Solutions

1. Start the Kafka infrastructure:
   ```bash
   cd module-02-kafka-core
   docker-compose up -d
   ```

2. Wait for Kafka to be healthy:
   ```bash
   docker-compose ps
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run any solution:
   ```bash
   python solutions/ex01_sensor_producer.py
   python solutions/ex04_filter_consumer.py
   ```

## Key Concepts Demonstrated

- **ex01-ex03:** Producer patterns (basic, metrics, routing)
- **ex04-ex06:** Consumer patterns (filtering, groups, DLQ)
- **ex07-ex08:** Partitioning strategies (key-based, geographic custom)
