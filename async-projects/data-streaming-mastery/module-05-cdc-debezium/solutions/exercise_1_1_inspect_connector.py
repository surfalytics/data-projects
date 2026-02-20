#!/usr/bin/env python3
"""
Solution 1.1: Inspect the Debezium Connector via the Kafka Connect REST API.

This script queries the Kafka Connect REST API to:
1. List all registered connectors.
2. Retrieve the full configuration of the ecommerce connector.
3. Check the connector status (connector state + task states).
"""

import json
import sys

import requests

CONNECT_URL = "http://localhost:8083"


def main() -> None:
    """Query and display Debezium connector information."""

    # ---------------------------------------------------------------
    # 1. List all connectors
    # ---------------------------------------------------------------
    print("=" * 60)
    print("1. Registered Connectors")
    print("=" * 60)
    resp = requests.get(f"{CONNECT_URL}/connectors", timeout=10)
    if resp.status_code != 200:
        print(f"ERROR: Could not list connectors (HTTP {resp.status_code})")
        sys.exit(1)
    connectors = resp.json()
    print(json.dumps(connectors, indent=2))
    print()

    if not connectors:
        print("No connectors registered. Run register_connector.py first.")
        sys.exit(0)

    connector_name = connectors[0]  # Assume first connector

    # ---------------------------------------------------------------
    # 2. Get connector configuration
    # ---------------------------------------------------------------
    print("=" * 60)
    print(f"2. Configuration for '{connector_name}'")
    print("=" * 60)
    resp = requests.get(
        f"{CONNECT_URL}/connectors/{connector_name}/config", timeout=10
    )
    config = resp.json()
    print(json.dumps(config, indent=2))
    print()

    # Answer questions from the config.
    print("Key configuration values:")
    print(f"  topic.prefix:  {config.get('topic.prefix', '(not set)')}")
    print(f"  snapshot.mode: {config.get('snapshot.mode', '(not set)')}")
    print(f"  tasks.max:     {config.get('tasks.max', '(not set)')}")
    print(f"  table.include.list: {config.get('table.include.list', '(not set)')}")
    print()

    # ---------------------------------------------------------------
    # 3. Check connector status
    # ---------------------------------------------------------------
    print("=" * 60)
    print(f"3. Status of '{connector_name}'")
    print("=" * 60)
    resp = requests.get(
        f"{CONNECT_URL}/connectors/{connector_name}/status", timeout=10
    )
    status = resp.json()
    print(json.dumps(status, indent=2))
    print()

    connector_state = status.get("connector", {}).get("state", "UNKNOWN")
    tasks = status.get("tasks", [])
    print(f"Connector state: {connector_state}")
    print(f"Number of tasks: {len(tasks)}")
    for i, task in enumerate(tasks):
        print(f"  Task {i}: {task.get('state', 'UNKNOWN')}")

    print()
    print("=" * 60)
    print("Answers:")
    print(f"  - The connector has {len(tasks)} task(s).")
    print(f"  - topic.prefix is '{config.get('topic.prefix', '?')}', "
          f"so topics are named ecommerce.ecommerce.<table>.")
    print(f"  - snapshot.mode is '{config.get('snapshot.mode', '?')}'.")
    print("=" * 60)


if __name__ == "__main__":
    main()
