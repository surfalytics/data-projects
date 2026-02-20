# Solutions -- Exercise 01: Basic CDC Setup and Reading Events

## Solution 1.1: Inspect the Debezium Connector

### Using curl

```bash
# List all connectors
curl -s http://localhost:8083/connectors | python3 -m json.tool

# Get connector configuration
curl -s http://localhost:8083/connectors/ecommerce-mysql-source/config | python3 -m json.tool

# Check connector status
curl -s http://localhost:8083/connectors/ecommerce-mysql-source/status | python3 -m json.tool

# List all Kafka topics (using kafka-topics inside the container)
docker exec module05-kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Answers

- **Tasks:** The connector has 1 task (`tasks.max: 1`).
- **Topic prefix:** The `topic.prefix` is `ecommerce`. Topics are named `{prefix}.{database}.{table}`, so `ecommerce.ecommerce.customers`.
- **Snapshot mode:** `initial` -- snapshot on first startup, then stream.

### Python solution

See `solutions/exercise_1_1_inspect_connector.py`.

---

## Solution 1.2: Read and Parse Snapshot Events

See `solutions/exercise_1_2_snapshot_reader.py`.

---

## Solution 1.3: Before and After Comparison

See `solutions/exercise_1_3_before_after.py`.
