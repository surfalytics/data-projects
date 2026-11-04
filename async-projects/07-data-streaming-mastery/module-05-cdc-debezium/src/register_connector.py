#!/usr/bin/env python3
"""
Register the Debezium MySQL source connector via the Kafka Connect REST API.

This script:
1. Waits for Kafka Connect to be ready (healthy and accepting requests).
2. Reads the connector configuration from config/mysql-source-connector.json.
3. Registers (or updates) the connector.
4. Polls the connector status until it is RUNNING.

Usage:
    python src/register_connector.py
"""

import json
import os
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONNECT_URL = os.getenv("KAFKA_CONNECT_URL", "http://localhost:8083")
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "mysql-source-connector.json",
)
MAX_WAIT_SECONDS = 120
POLL_INTERVAL = 5


def wait_for_connect(url: str, timeout: int = MAX_WAIT_SECONDS) -> None:
    """Block until the Kafka Connect REST API is reachable.

    Args:
        url: Base URL of the Kafka Connect cluster (e.g. http://localhost:8083).
        timeout: Maximum number of seconds to wait before giving up.

    Raises:
        SystemExit: If the service does not become available within the timeout.
    """
    print(f"Waiting for Kafka Connect at {url} ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(f"{url}/connectors", timeout=5)
            if resp.status_code == 200:
                print("Kafka Connect is ready.")
                return
        except requests.ConnectionError:
            pass
        except requests.Timeout:
            pass
        time.sleep(POLL_INTERVAL)
    print(f"ERROR: Kafka Connect did not become ready within {timeout}s.")
    sys.exit(1)


def load_connector_config(path: str) -> dict:
    """Load the connector configuration JSON from disk.

    Args:
        path: Absolute or relative path to the JSON configuration file.

    Returns:
        Parsed JSON as a dictionary with 'name' and 'config' keys.

    Raises:
        SystemExit: If the file cannot be read or parsed.
    """
    try:
        with open(path, "r") as f:
            config = json.load(f)
        print(f"Loaded connector config from {path}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: Could not load config from {path}: {exc}")
        sys.exit(1)


def register_connector(url: str, config: dict) -> None:
    """Register or update a Kafka Connect connector.

    If the connector already exists, it is updated with a PUT request.
    Otherwise, a POST request creates it.

    Args:
        url: Base URL of the Kafka Connect cluster.
        config: Connector configuration dict with 'name' and 'config' keys.
    """
    connector_name = config["name"]
    connector_config = config["config"]

    # Check if the connector already exists.
    check_resp = requests.get(f"{url}/connectors/{connector_name}", timeout=10)

    if check_resp.status_code == 200:
        print(f"Connector '{connector_name}' already exists. Updating configuration ...")
        resp = requests.put(
            f"{url}/connectors/{connector_name}/config",
            headers={"Content-Type": "application/json"},
            data=json.dumps(connector_config),
            timeout=30,
        )
    else:
        print(f"Creating connector '{connector_name}' ...")
        resp = requests.post(
            f"{url}/connectors",
            headers={"Content-Type": "application/json"},
            data=json.dumps(config),
            timeout=30,
        )

    if resp.status_code in (200, 201):
        print(f"Connector '{connector_name}' registered successfully.")
    else:
        print(f"ERROR: Failed to register connector. Status {resp.status_code}")
        print(resp.text)
        sys.exit(1)


def wait_for_connector_running(
    url: str, connector_name: str, timeout: int = 60
) -> None:
    """Poll the connector status until all tasks are RUNNING.

    Args:
        url: Base URL of the Kafka Connect cluster.
        connector_name: Name of the connector to check.
        timeout: Maximum seconds to wait.

    Raises:
        SystemExit: If the connector does not reach RUNNING state.
    """
    print(f"Waiting for connector '{connector_name}' to reach RUNNING state ...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(
                f"{url}/connectors/{connector_name}/status", timeout=10
            )
            if resp.status_code == 200:
                status = resp.json()
                connector_state = status.get("connector", {}).get("state", "UNKNOWN")
                tasks = status.get("tasks", [])

                task_states = [t.get("state", "UNKNOWN") for t in tasks]
                print(
                    f"  Connector: {connector_state} | "
                    f"Tasks: {task_states or ['(none yet)']}"
                )

                if connector_state == "RUNNING" and all(
                    s == "RUNNING" for s in task_states
                ):
                    print("All tasks are RUNNING. Connector is ready.")
                    return

                if connector_state == "FAILED" or "FAILED" in task_states:
                    print("ERROR: Connector or task is in FAILED state.")
                    print(json.dumps(status, indent=2))
                    sys.exit(1)
        except requests.RequestException as exc:
            print(f"  Warning: {exc}")

        time.sleep(POLL_INTERVAL)

    print(f"ERROR: Connector did not reach RUNNING state within {timeout}s.")
    sys.exit(1)


def main() -> None:
    """Main entry point: wait, register, verify."""
    wait_for_connect(CONNECT_URL)

    config = load_connector_config(CONFIG_PATH)
    register_connector(CONNECT_URL, config)

    connector_name = config["name"]
    wait_for_connector_running(CONNECT_URL, connector_name)

    print("\n--- Registered Connectors ---")
    resp = requests.get(f"{CONNECT_URL}/connectors", timeout=10)
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    main()
