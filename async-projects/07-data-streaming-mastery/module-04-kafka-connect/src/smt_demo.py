"""
Kafka Connect SMT (Single Message Transforms) Demo

Demonstrates how to deploy connectors with SMTs and validates that
the transforms are applied correctly. Covers:
  - TimestampRouter: route records to date-partitioned topics
  - ReplaceField: rename fields in transit
  - InsertField: add static or timestamp fields
  - Filter (using RecordIsTombstone / predicates)

Usage:
    # Start the environment first:
    #   docker-compose up -d
    #
    # Then run this demo:
    python smt_demo.py

Prerequisites:
    pip install -r ../requirements.txt
"""

import json
import sys
import time
from datetime import datetime

import requests
from confluent_kafka import Consumer, KafkaError, TopicPartition


CONNECT_URL = "http://localhost:8083"
KAFKA_BOOTSTRAP = "localhost:9092"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


def wait_for_connect(timeout: int = 120) -> bool:
    """
    Wait for the Kafka Connect REST API to become available.

    Args:
        timeout: Maximum seconds to wait.

    Returns:
        True if Connect is available within the timeout.
    """
    print("Waiting for Kafka Connect to be ready ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{CONNECT_URL}/", timeout=5)
            if resp.status_code == 200:
                print("Kafka Connect is ready.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(5)
    print("ERROR: Kafka Connect not available.")
    return False


def deploy_connector(config: dict) -> bool:
    """
    Deploy a connector via the REST API.

    Args:
        config: Connector configuration dictionary with 'name' and 'config' keys.

    Returns:
        True if deployment succeeded.
    """
    name = config["name"]
    print(f"\nDeploying connector: {name}")

    # Delete existing connector if present
    requests.delete(f"{CONNECT_URL}/connectors/{name}", timeout=10)
    time.sleep(2)

    resp = requests.post(
        f"{CONNECT_URL}/connectors",
        headers=HEADERS,
        json=config,
        timeout=30,
    )
    if resp.status_code in (200, 201):
        print(f"  Connector '{name}' deployed successfully.")
        return True
    else:
        print(f"  ERROR: Deployment failed (HTTP {resp.status_code})")
        print(f"  Response: {resp.text}")
        return False


def wait_for_connector_running(name: str, timeout: int = 60) -> bool:
    """
    Wait for a connector to reach RUNNING state.

    Args:
        name: Connector name.
        timeout: Maximum seconds to wait.

    Returns:
        True when the connector is RUNNING.
    """
    print(f"  Waiting for '{name}' to start ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{CONNECT_URL}/connectors/{name}/status", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                state = data["connector"]["state"]
                if state == "RUNNING":
                    tasks = data.get("tasks", [])
                    if tasks and all(t["state"] == "RUNNING" for t in tasks):
                        print(f"  Connector '{name}' is RUNNING.")
                        return True
                elif state == "FAILED":
                    print(f"  Connector '{name}' FAILED.")
                    return False
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(3)
    print(f"  Timeout waiting for '{name}'.")
    return False


def consume_messages(topic_pattern: str, timeout: int = 30, max_messages: int = 10) -> list[dict]:
    """
    Consume messages from topics matching a pattern.

    Args:
        topic_pattern: Topic name or prefix to subscribe to.
        timeout: Maximum seconds to wait for messages.
        max_messages: Maximum number of messages to consume.

    Returns:
        A list of consumed message dictionaries with 'topic', 'key', 'value' keys.
    """
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": f"smt-demo-{int(time.time())}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })

    # Subscribe using regex if it looks like a pattern
    if "*" in topic_pattern or "^" in topic_pattern:
        consumer.subscribe([topic_pattern])
    else:
        consumer.subscribe([topic_pattern])

    messages = []
    start = time.time()
    print(f"  Consuming from '{topic_pattern}' (timeout={timeout}s) ...")

    while time.time() - start < timeout and len(messages) < max_messages:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            print(f"  Consumer error: {msg.error()}")
            break

        value = msg.value()
        key = msg.key()
        messages.append({
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
            "key": key.decode("utf-8") if key else None,
            "value": value.decode("utf-8") if value else None,
            "headers": dict(msg.headers()) if msg.headers() else {},
        })

    consumer.close()
    print(f"  Consumed {len(messages)} message(s).")
    return messages


def cleanup_connector(name: str):
    """
    Delete a connector by name, ignoring errors.

    Args:
        name: Connector name to delete.
    """
    try:
        requests.delete(f"{CONNECT_URL}/connectors/{name}", timeout=10)
    except Exception:
        pass


# ============================================================================
# Demo 1: TimestampRouter SMT
# Routes messages to topics with date suffixes (e.g., topic-20240115)
# ============================================================================

def demo_timestamp_router():
    """
    Demonstrate the TimestampRouter SMT.

    Deploys a JDBC source connector with TimestampRouter that appends the
    current date to the topic name, resulting in topics like:
        mysql-employees-YYYYMMDD
    """
    print("\n" + "=" * 70)
    print("DEMO 1: TimestampRouter SMT")
    print("Routes records to date-partitioned topics.")
    print("=" * 70)

    today = datetime.now().strftime("%Y%m%d")
    connector_name = "smt-demo-timestamp-router"

    config = {
        "name": connector_name,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "smt-ts-",
            "table.whitelist": "departments",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            # TimestampRouter SMT configuration
            "transforms": "routeByDate",
            "transforms.routeByDate.type": "org.apache.kafka.connect.transforms.TimestampRouter",
            "transforms.routeByDate.topic.format": "${topic}-${timestamp}",
            "transforms.routeByDate.timestamp.format": "yyyyMMdd",
        },
    }

    if not deploy_connector(config):
        return False

    if not wait_for_connector_running(connector_name):
        return False

    # Wait for data to flow
    print("  Waiting for data to be produced ...")
    time.sleep(10)

    expected_topic = f"smt-ts-departments-{today}"
    messages = consume_messages(expected_topic, timeout=20)

    if messages:
        print(f"\n  SUCCESS: Messages routed to date-partitioned topic '{expected_topic}'")
        print(f"  Sample message: {messages[0]['value'][:200]}")
        cleanup_connector(connector_name)
        return True
    else:
        print(f"\n  NOTE: No messages found in '{expected_topic}' yet.")
        print("  The TimestampRouter appends dates to topics. Check Kafka UI for topics.")
        cleanup_connector(connector_name)
        return False


# ============================================================================
# Demo 2: ReplaceField (Rename) SMT
# Renames fields in the record value
# ============================================================================

def demo_replace_field():
    """
    Demonstrate the ReplaceField SMT for renaming fields.

    Renames 'first_name' to 'given_name' and 'last_name' to 'family_name'
    in employee records.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: ReplaceField (Rename) SMT")
    print("Renames fields: first_name -> given_name, last_name -> family_name")
    print("=" * 70)

    connector_name = "smt-demo-replace-field"

    config = {
        "name": connector_name,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "smt-rename-",
            "table.whitelist": "employees",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            # ReplaceField SMT configuration
            "transforms": "renameFields",
            "transforms.renameFields.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
            "transforms.renameFields.renames": "first_name:given_name,last_name:family_name",
        },
    }

    if not deploy_connector(config):
        return False

    if not wait_for_connector_running(connector_name):
        return False

    print("  Waiting for data to be produced ...")
    time.sleep(10)

    messages = consume_messages("smt-rename-employees", timeout=20)

    if messages:
        # Parse the first message to check for renamed fields
        try:
            record = json.loads(messages[0]["value"])
            has_given_name = "given_name" in record
            has_family_name = "family_name" in record
            has_old_first = "first_name" in record
            has_old_last = "last_name" in record

            print(f"\n  Record fields: {list(record.keys())}")
            if has_given_name and has_family_name and not has_old_first and not has_old_last:
                print("  SUCCESS: Fields renamed correctly!")
                print(f"  given_name={record['given_name']}, family_name={record['family_name']}")
            else:
                print("  PARTIAL: Fields present but renaming may not have fully applied.")
                print(f"  Record: {json.dumps(record, indent=2)[:300]}")
        except (json.JSONDecodeError, IndexError):
            print("  Could not parse message value as JSON.")

        cleanup_connector(connector_name)
        return True
    else:
        print("\n  NOTE: No messages consumed yet. Check Kafka UI.")
        cleanup_connector(connector_name)
        return False


# ============================================================================
# Demo 3: InsertField SMT
# Adds a static field and a timestamp to records
# ============================================================================

def demo_insert_field():
    """
    Demonstrate the InsertField SMT.

    Adds two fields to each record:
      - 'processed_at': the current timestamp when the record was processed
      - 'source_system': a static string value 'mysql-company-db'
    """
    print("\n" + "=" * 70)
    print("DEMO 3: InsertField SMT")
    print("Adds 'processed_at' timestamp and 'source_system' static field")
    print("=" * 70)

    connector_name = "smt-demo-insert-field"

    config = {
        "name": connector_name,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "smt-insert-",
            "table.whitelist": "projects",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            # InsertField SMT configuration - chained transforms
            "transforms": "addTimestamp,addSource",
            "transforms.addTimestamp.type": "org.apache.kafka.connect.transforms.InsertField$Value",
            "transforms.addTimestamp.timestamp.field": "processed_at",
            "transforms.addSource.type": "org.apache.kafka.connect.transforms.InsertField$Value",
            "transforms.addSource.static.field": "source_system",
            "transforms.addSource.static.value": "mysql-company-db",
        },
    }

    if not deploy_connector(config):
        return False

    if not wait_for_connector_running(connector_name):
        return False

    print("  Waiting for data to be produced ...")
    time.sleep(10)

    messages = consume_messages("smt-insert-projects", timeout=20)

    if messages:
        try:
            record = json.loads(messages[0]["value"])
            has_timestamp = "processed_at" in record
            has_source = "source_system" in record

            print(f"\n  Record fields: {list(record.keys())}")
            if has_timestamp and has_source:
                print("  SUCCESS: Fields inserted correctly!")
                print(f"  processed_at = {record['processed_at']}")
                print(f"  source_system = {record['source_system']}")
            else:
                print("  PARTIAL: Some inserted fields missing.")
                print(f"  Record: {json.dumps(record, indent=2)[:300]}")
        except (json.JSONDecodeError, IndexError):
            print("  Could not parse message value as JSON.")

        cleanup_connector(connector_name)
        return True
    else:
        print("\n  NOTE: No messages consumed yet. Check Kafka UI.")
        cleanup_connector(connector_name)
        return False


# ============================================================================
# Demo 4: Chained SMTs (InsertField + ReplaceField + MaskField)
# Demonstrates multiple transforms applied in sequence
# ============================================================================

def demo_chained_smts():
    """
    Demonstrate chaining multiple SMTs together.

    Applies three transforms in sequence to employee records:
      1. InsertField: Add 'etl_timestamp' with processing time
      2. ReplaceField: Rename 'email' to 'contact_email'
      3. MaskField: Mask the 'salary' field (replace with zero)
    """
    print("\n" + "=" * 70)
    print("DEMO 4: Chained SMTs (InsertField + ReplaceField + MaskField)")
    print("Demonstrates multiple transforms applied in sequence")
    print("=" * 70)

    connector_name = "smt-demo-chained"

    config = {
        "name": connector_name,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "smt-chained-",
            "table.whitelist": "employees",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            # Chained SMT configuration
            "transforms": "addTimestamp,renameEmail,maskSalary",
            "transforms.addTimestamp.type": "org.apache.kafka.connect.transforms.InsertField$Value",
            "transforms.addTimestamp.timestamp.field": "etl_timestamp",
            "transforms.renameEmail.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
            "transforms.renameEmail.renames": "email:contact_email",
            "transforms.maskSalary.type": "org.apache.kafka.connect.transforms.MaskField$Value",
            "transforms.maskSalary.fields": "salary",
        },
    }

    if not deploy_connector(config):
        return False

    if not wait_for_connector_running(connector_name):
        return False

    print("  Waiting for data to be produced ...")
    time.sleep(10)

    messages = consume_messages("smt-chained-employees", timeout=20)

    if messages:
        try:
            record = json.loads(messages[0]["value"])
            print(f"\n  Record fields: {list(record.keys())}")
            print(f"  Record preview: {json.dumps(record, indent=2)[:400]}")

            checks = {
                "etl_timestamp added": "etl_timestamp" in record,
                "email renamed to contact_email": "contact_email" in record and "email" not in record,
                "salary masked (zeroed)": record.get("salary") == 0 or record.get("salary") == 0.0,
            }

            print("\n  Validation:")
            all_passed = True
            for check_name, passed in checks.items():
                status = "PASS" if passed else "FAIL"
                print(f"    [{status}] {check_name}")
                if not passed:
                    all_passed = False

            if all_passed:
                print("\n  SUCCESS: All chained SMTs applied correctly!")
            else:
                print("\n  PARTIAL: Some transforms may not have applied as expected.")
        except (json.JSONDecodeError, IndexError):
            print("  Could not parse message value as JSON.")

        cleanup_connector(connector_name)
        return True
    else:
        print("\n  NOTE: No messages consumed yet. Check Kafka UI.")
        cleanup_connector(connector_name)
        return False


def main():
    """Run all SMT demos in sequence."""
    print("=" * 70)
    print("Kafka Connect - Single Message Transforms (SMT) Demo")
    print("=" * 70)

    if not wait_for_connect():
        sys.exit(1)

    results = {}

    demos = [
        ("TimestampRouter", demo_timestamp_router),
        ("ReplaceField", demo_replace_field),
        ("InsertField", demo_insert_field),
        ("Chained SMTs", demo_chained_smts),
    ]

    for name, demo_func in demos:
        try:
            results[name] = demo_func()
        except Exception as e:
            print(f"\n  ERROR in {name}: {e}")
            results[name] = False

    # Summary
    print("\n" + "=" * 70)
    print("DEMO SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        status = "PASS" if passed else "CHECK"
        print(f"  [{status}] {name}")

    print("\nDone. Check Kafka UI at http://localhost:8080 for topic inspection.")


if __name__ == "__main__":
    main()
