# Exercise 01: File Connectors

## Prerequisites

Start the environment:

```bash
cd module-04-kafka-connect
docker-compose up -d
```

Wait for all services to be healthy (especially `kafka-connect`):

```bash
docker-compose ps
# Wait until kafka-connect shows "healthy"
curl http://localhost:8083/connectors
# Should return: []
```

---

## Exercise 1.1: FileStream Source Connector

### Objective

Deploy a FileStream Source connector that reads lines from a file and publishes them to a Kafka topic.

### Tasks

1. Create a test input file that the source connector will read:

```bash
mkdir -p data
echo "Hello from Kafka Connect" > data/input.txt
echo "This is line two" >> data/input.txt
echo "And line three" >> data/input.txt
```

2. Deploy the FileStream Source connector using the provided configuration in `config/file-source-connector.json`. Use either:
   - The `connect-management.sh` script
   - The `connector_manager.py` Python script
   - A direct `curl` command

3. Verify the connector is running:
   - Check the connector status via the REST API
   - Confirm the topic `file-stream-topic` was created

4. Consume messages from `file-stream-topic` and verify all three lines appear.

5. Append two more lines to `data/input.txt` and confirm they are picked up automatically.

### Expected Outcome

- The connector is in RUNNING state
- The topic `file-stream-topic` contains all lines from the file
- New lines appended to the file appear in the topic within seconds

### Hints

- The FileStream Source connector tails the file (like `tail -f`)
- Use `kafka-console-consumer` from within the Kafka container or use Kafka UI at http://localhost:8080
- To consume from the beginning: `docker exec module04-kafka kafka-console-consumer --bootstrap-server kafka:29092 --topic file-stream-topic --from-beginning`

---

## Exercise 1.2: FileStream Sink Connector (Round-Trip)

### Objective

Deploy a FileStream Sink connector that reads from the same topic and writes to an output file, completing a full round-trip: file -> Kafka -> file.

### Tasks

1. Deploy the FileStream Sink connector using `config/file-sink-connector.json`.

2. Verify the connector is running.

3. Check that the output file `data/output.txt` exists and contains the messages from the topic.

4. Write a Python script (`verify_roundtrip.py`) that:
   - Reads the original `data/input.txt`
   - Reads the sink output `data/output.txt`
   - Compares the contents and prints whether the round-trip was successful
   - Handles the case where the output file may have a different format (one JSON-encoded string per line vs plain text)

5. Add a new line to `data/input.txt` and verify it appears in `data/output.txt` within 10 seconds.

### Expected Outcome

- Both source and sink connectors are RUNNING
- `data/output.txt` contains the same content as `data/input.txt`
- New content flows through the full pipeline automatically

### Hints

- The sink connector writes one record per line
- The output format depends on the value converter (StringConverter produces plain text)
- If using JsonConverter, the output will be JSON-encoded strings
- Check both connectors' status if messages do not appear
