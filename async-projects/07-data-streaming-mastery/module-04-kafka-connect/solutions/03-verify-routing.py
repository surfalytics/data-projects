"""
Solution for Exercise 3.2: Topic Routing Verification

Deploys connectors with TimestampRouter and RegexRouter SMTs, then
verifies that topics are created with the expected names and contain
the correct data.

Usage:
    python solutions/03-verify-routing.py
"""

import json
import re
import sys
import time
from datetime import datetime

import requests
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.admin import AdminClient


CONNECT_URL = "http://localhost:8083"
KAFKA_BOOTSTRAP = "localhost:9092"
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


def wait_for_connect(timeout: int = 120) -> bool:
    """
    Wait for Kafka Connect REST API to be available.

    Args:
        timeout: Maximum seconds to wait.

    Returns:
        True if available.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{CONNECT_URL}/", timeout=5)
            if resp.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(5)
    return False


def deploy_connector(config: dict) -> bool:
    """
    Deploy a connector, deleting any existing one with the same name first.

    Args:
        config: Connector configuration.

    Returns:
        True if deployment succeeded.
    """
    name = config["name"]
    requests.delete(f"{CONNECT_URL}/connectors/{name}", timeout=10)
    time.sleep(2)

    resp = requests.post(
        f"{CONNECT_URL}/connectors",
        headers=HEADERS,
        json=config,
        timeout=30,
    )
    if resp.status_code in (200, 201):
        print(f"  Connector '{name}' deployed.")
        return True
    print(f"  ERROR deploying '{name}': HTTP {resp.status_code} - {resp.text[:200]}")
    return False


def wait_for_running(name: str, timeout: int = 60) -> bool:
    """
    Wait for a connector to reach RUNNING state.

    Args:
        name: Connector name.
        timeout: Maximum seconds to wait.

    Returns:
        True when RUNNING.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(
                f"{CONNECT_URL}/connectors/{name}/status", timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data["connector"]["state"] == "RUNNING":
                    tasks = data.get("tasks", [])
                    if tasks and all(t["state"] == "RUNNING" for t in tasks):
                        return True
                elif data["connector"]["state"] == "FAILED":
                    return False
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(3)
    return False


def list_topics() -> list[str]:
    """
    List all topics in the Kafka cluster.

    Returns:
        Sorted list of topic names.
    """
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP})
    metadata = admin.list_topics(timeout=10)
    return sorted(metadata.topics.keys())


def count_messages(topic: str, timeout: int = 15) -> int:
    """
    Count messages in a Kafka topic.

    Args:
        topic: Topic name.
        timeout: Maximum seconds to consume.

    Returns:
        Message count.
    """
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": f"routing-check-{int(time.time())}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    })
    consumer.subscribe([topic])

    count = 0
    empty = 0
    while empty < timeout:
        msg = consumer.poll(1.0)
        if msg is None:
            empty += 1
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                empty += 1
                continue
            break
        count += 1
        empty = 0

    consumer.close()
    return count


def cleanup(names: list[str]):
    """Delete connectors by name."""
    for name in names:
        try:
            requests.delete(f"{CONNECT_URL}/connectors/{name}", timeout=10)
        except Exception:
            pass


def main():
    """Deploy routing connectors and verify topic names."""
    print("=" * 60)
    print("Topic Routing Verification (TimestampRouter + RegexRouter)")
    print("=" * 60)

    if not wait_for_connect():
        print("ERROR: Kafka Connect not available.")
        sys.exit(1)

    connector_names = []

    # ----------------------------------------------------------------
    # 1. TimestampRouter connector
    # ----------------------------------------------------------------
    print("\n--- Step 1: Deploy TimestampRouter connector ---")
    ts_connector = "smt-routing-timestamp"
    connector_names.append(ts_connector)

    ts_config = {
        "name": ts_connector,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "mysql-",
            "table.whitelist": "projects",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            "transforms": "routeByDate",
            "transforms.routeByDate.type": "org.apache.kafka.connect.transforms.TimestampRouter",
            "transforms.routeByDate.topic.format": "${topic}-${timestamp}",
            "transforms.routeByDate.timestamp.format": "yyyy-MM-dd",
        },
    }

    if not deploy_connector(ts_config):
        cleanup(connector_names)
        sys.exit(1)

    if not wait_for_running(ts_connector):
        print(f"  ERROR: '{ts_connector}' did not start.")
        cleanup(connector_names)
        sys.exit(1)

    # ----------------------------------------------------------------
    # 2. RegexRouter connector
    # ----------------------------------------------------------------
    print("\n--- Step 2: Deploy RegexRouter connector ---")
    regex_connector = "smt-routing-regex"
    connector_names.append(regex_connector)

    regex_config = {
        "name": regex_connector,
        "config": {
            "connector.class": "io.confluent.connect.jdbc.JdbcSourceConnector",
            "tasks.max": "1",
            "connection.url": "jdbc:mysql://mysql:3306/company",
            "connection.user": "connect_user",
            "connection.password": "connect_pass",
            "mode": "bulk",
            "topic.prefix": "mysql-",
            "table.whitelist": "departments",
            "poll.interval.ms": "60000",
            "key.converter": "org.apache.kafka.connect.storage.StringConverter",
            "value.converter": "org.apache.kafka.connect.json.JsonConverter",
            "value.converter.schemas.enable": "false",
            "transforms": "renameTopic",
            "transforms.renameTopic.type": "org.apache.kafka.connect.transforms.RegexRouter",
            "transforms.renameTopic.regex": "mysql-(.*)",
            "transforms.renameTopic.replacement": "company-$1-data",
        },
    }

    if not deploy_connector(regex_config):
        cleanup(connector_names)
        sys.exit(1)

    if not wait_for_running(regex_connector):
        print(f"  ERROR: '{regex_connector}' did not start.")
        cleanup(connector_names)
        sys.exit(1)

    # ----------------------------------------------------------------
    # 3. Wait for data and verify
    # ----------------------------------------------------------------
    print("\n--- Step 3: Waiting for data (15 seconds) ---")
    time.sleep(15)

    topics = list_topics()
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"\n--- Step 4: Topic Verification ---")
    print(f"  All topics in cluster:")
    for t in topics:
        if not t.startswith("_"):
            print(f"    {t}")

    # Check TimestampRouter topic
    expected_ts_topic = f"mysql-projects-{today}"
    ts_topic_found = expected_ts_topic in topics
    ts_date_topics = [t for t in topics if re.match(r"mysql-projects-\d{4}-\d{2}-\d{2}", t)]

    print(f"\n  TimestampRouter check:")
    print(f"    Expected topic: {expected_ts_topic}")
    print(f"    Found: {ts_topic_found}")
    if ts_date_topics:
        print(f"    Date-partitioned topics: {ts_date_topics}")
        ts_count = count_messages(ts_date_topics[0], timeout=10)
        print(f"    Message count in {ts_date_topics[0]}: {ts_count}")
    else:
        ts_count = 0
        print("    No date-partitioned topics found.")

    # Check RegexRouter topic
    expected_regex_topic = "company-departments-data"
    regex_topic_found = expected_regex_topic in topics

    print(f"\n  RegexRouter check:")
    print(f"    Expected topic: {expected_regex_topic}")
    print(f"    Found: {regex_topic_found}")
    if regex_topic_found:
        regex_count = count_messages(expected_regex_topic, timeout=10)
        print(f"    Message count: {regex_count}")
    else:
        regex_count = 0
        print("    Topic not found. Check connector logs.")

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")

    checks = {
        "TimestampRouter topic created": ts_topic_found or len(ts_date_topics) > 0,
        "TimestampRouter has messages": ts_count > 0,
        "RegexRouter topic created": regex_topic_found,
        "RegexRouter has messages": regex_count > 0,
    }

    all_passed = True
    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n  All routing checks PASSED!")
    else:
        print("\n  Some checks failed. Review connector configurations and logs.")

    cleanup(connector_names)
    print("\nDone. Connectors cleaned up.")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
