"""
Solution for Exercise 3.1: SMT Field Transform Validator

Deploys a JDBC source connector with chained SMTs (ReplaceField, InsertField,
MaskField) and validates that all transforms are applied correctly.

Usage:
    python solutions/03-validate-transforms.py
"""

import json
import sys
import time

import requests
from confluent_kafka import Consumer, KafkaError


CONNECT_URL = "http://localhost:8083"
KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "transformed-employees"
CONNECTOR_NAME = "smt-field-transform-connector"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


def deploy_connector() -> bool:
    """
    Deploy the SMT field transform connector.

    Returns:
        True if deployment succeeded.
    """
    config = {
        "name": CONNECTOR_NAME,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "",
            "query": "SELECT id, first_name, last_name, email, department_id, salary, is_active FROM company.employees",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            "topic.prefix": "transformed-",
            "table.whitelist": "employees",
            # Chained SMTs
            "transforms": "renameFields,addSource,addTimestamp,maskSalary",
            # 1. Rename first_name -> given_name, last_name -> surname
            "transforms.renameFields.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
            "transforms.renameFields.renames": "first_name:given_name,last_name:surname",
            # 2. Add static field: data_source = mysql-hr-system
            "transforms.addSource.type": "org.apache.kafka.connect.transforms.InsertField$Value",
            "transforms.addSource.static.field": "data_source",
            "transforms.addSource.static.value": "mysql-hr-system",
            # 3. Add timestamp field: kafka_ingest_time
            "transforms.addTimestamp.type": "org.apache.kafka.connect.transforms.InsertField$Value",
            "transforms.addTimestamp.timestamp.field": "kafka_ingest_time",
            # 4. Mask salary field
            "transforms.maskSalary.type": "org.apache.kafka.connect.transforms.MaskField$Value",
            "transforms.maskSalary.fields": "salary",
        },
    }

    # Delete existing connector
    requests.delete(f"{CONNECT_URL}/connectors/{CONNECTOR_NAME}", timeout=10)
    time.sleep(2)

    resp = requests.post(
        f"{CONNECT_URL}/connectors",
        headers=HEADERS,
        json=config,
        timeout=30,
    )

    if resp.status_code in (200, 201):
        print(f"Connector '{CONNECTOR_NAME}' deployed.")
        return True
    else:
        print(f"ERROR deploying connector: HTTP {resp.status_code}")
        print(f"Response: {resp.text}")
        return False


def wait_for_running(timeout: int = 60) -> bool:
    """
    Wait for the connector to reach RUNNING state.

    Args:
        timeout: Maximum seconds to wait.

    Returns:
        True when running.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(
                f"{CONNECT_URL}/connectors/{CONNECTOR_NAME}/status", timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data["connector"]["state"] == "RUNNING":
                    tasks = data.get("tasks", [])
                    if tasks and all(t["state"] == "RUNNING" for t in tasks):
                        return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(3)
    return False


def consume_all(topic: str, timeout: int = 30) -> list[dict]:
    """
    Consume all available messages from a topic.

    Args:
        topic: Kafka topic name.
        timeout: Maximum seconds to wait.

    Returns:
        List of parsed message value dictionaries.
    """
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": f"smt-validator-{int(time.time())}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([topic])

    messages = []
    empty_count = 0

    while empty_count < timeout:
        msg = consumer.poll(1.0)
        if msg is None:
            empty_count += 1
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                empty_count += 1
                continue
            break
        empty_count = 0
        try:
            value = json.loads(msg.value().decode("utf-8"))
            messages.append(value)
        except (json.JSONDecodeError, AttributeError):
            messages.append({"_raw": msg.value()})

    consumer.close()
    return messages


def validate_transforms(messages: list[dict]) -> bool:
    """
    Validate that all SMT transforms were applied correctly.

    Args:
        messages: List of consumed message dictionaries.

    Returns:
        True if all validations pass.
    """
    print(f"\nValidating {len(messages)} message(s) ...")
    if not messages:
        print("  ERROR: No messages to validate.")
        return False

    all_passed = True

    for i, record in enumerate(messages):
        if i == 0:
            print(f"\n  Sample record fields: {list(record.keys())}")
            print(f"  Sample record: {json.dumps(record, indent=2, default=str)[:500]}")

    # Validation checks across all messages
    checks = {
        "given_name field exists (renamed from first_name)": [],
        "surname field exists (renamed from last_name)": [],
        "first_name field removed": [],
        "last_name field removed": [],
        "data_source == 'mysql-hr-system'": [],
        "kafka_ingest_time exists and is set": [],
        "salary is masked (zero)": [],
    }

    for record in messages:
        checks["given_name field exists (renamed from first_name)"].append(
            "given_name" in record
        )
        checks["surname field exists (renamed from last_name)"].append(
            "surname" in record
        )
        checks["first_name field removed"].append(
            "first_name" not in record
        )
        checks["last_name field removed"].append(
            "last_name" not in record
        )
        checks["data_source == 'mysql-hr-system'"].append(
            record.get("data_source") == "mysql-hr-system"
        )
        checks["kafka_ingest_time exists and is set"].append(
            "kafka_ingest_time" in record and record["kafka_ingest_time"] is not None
        )
        checks["salary is masked (zero)"].append(
            record.get("salary") == 0 or record.get("salary") == 0.0
        )

    print("\n  Validation Results:")
    print("  " + "-" * 56)

    for check_name, results in checks.items():
        passed = all(results)
        pass_count = sum(results)
        total = len(results)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check_name} ({pass_count}/{total})")
        if not passed:
            all_passed = False

    print("  " + "-" * 56)
    if all_passed:
        print("  RESULT: All transform validations PASSED!")
    else:
        print("  RESULT: Some validations FAILED. Check connector config.")

    return all_passed


def cleanup():
    """Remove the test connector."""
    try:
        requests.delete(f"{CONNECT_URL}/connectors/{CONNECTOR_NAME}", timeout=10)
        print(f"\nCleaned up connector '{CONNECTOR_NAME}'.")
    except Exception:
        pass


def main():
    """Run the full SMT validation pipeline."""
    print("=" * 60)
    print("SMT Field Transform Validator")
    print("=" * 60)

    # Wait for Connect
    print("\nWaiting for Kafka Connect ...")
    for _ in range(24):
        try:
            resp = requests.get(f"{CONNECT_URL}/", timeout=5)
            if resp.status_code == 200:
                break
        except requests.exceptions.ConnectionError:
            time.sleep(5)
    else:
        print("ERROR: Kafka Connect not available.")
        sys.exit(1)

    # Deploy
    if not deploy_connector():
        sys.exit(1)

    # Wait for running
    print("Waiting for connector to start ...")
    if not wait_for_running():
        print("ERROR: Connector did not reach RUNNING state.")
        cleanup()
        sys.exit(1)

    # Wait for data
    print("Waiting for data to be produced ...")
    time.sleep(10)

    # Consume and validate
    messages = consume_all(TOPIC, timeout=20)
    success = validate_transforms(messages)

    cleanup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
