#!/usr/bin/env python3
"""
Register Debezium MySQL Source and JDBC Sink connectors via Kafka Connect REST API.

This script:
1. Waits for Kafka Connect to be fully ready
2. Registers the MySQL source connector (Debezium CDC)
3. Registers the PostgreSQL JDBC sink connector
4. Verifies both connectors reach RUNNING state
"""

import json
import logging
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONNECT_URL = "http://localhost:8083"
CONFIG_DIR = "../config"

CONNECTORS = [
    {
        "name": "mysql-source-connector",
        "config_file": f"{CONFIG_DIR}/mysql-source-connector.json",
    },
    {
        "name": "postgres-sink-connector",
        "config_file": f"{CONFIG_DIR}/postgres-sink-connector.json",
    },
]

MAX_WAIT_SECONDS = 120
POLL_INTERVAL = 5

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("register-connectors")

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def wait_for_connect():
    """Wait for Kafka Connect REST API to be ready."""
    logger.info(f"Waiting for Kafka Connect at {CONNECT_URL} ...")
    start = time.time()

    while time.time() - start < MAX_WAIT_SECONDS:
        try:
            resp = requests.get(f"{CONNECT_URL}/connectors", timeout=5)
            if resp.status_code == 200:
                logger.info("Kafka Connect is ready.")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass

        elapsed = int(time.time() - start)
        logger.info(f"  Connect not ready yet ({elapsed}s elapsed). Retrying...")
        time.sleep(POLL_INTERVAL)

    logger.error(f"Kafka Connect did not become ready within {MAX_WAIT_SECONDS}s.")
    return False


def register_connector(config_path):
    """Register a connector from a JSON config file."""
    with open(config_path, "r") as f:
        connector_config = json.load(f)

    name = connector_config.get("name", "unknown")
    logger.info(f"Registering connector: {name}")

    # Check if connector already exists
    resp = requests.get(f"{CONNECT_URL}/connectors/{name}", timeout=10)
    if resp.status_code == 200:
        logger.info(f"Connector '{name}' already exists. Updating configuration...")
        resp = requests.put(
            f"{CONNECT_URL}/connectors/{name}/config",
            json=connector_config["config"],
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
    else:
        resp = requests.post(
            f"{CONNECT_URL}/connectors",
            json=connector_config,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

    if resp.status_code in (200, 201):
        logger.info(f"Connector '{name}' registered successfully.")
        return True
    else:
        logger.error(f"Failed to register '{name}': {resp.status_code} - {resp.text}")
        return False


def wait_for_connector_running(name, timeout=60):
    """Wait for a connector to reach RUNNING state."""
    logger.info(f"Waiting for connector '{name}' to be RUNNING...")
    start = time.time()

    while time.time() - start < timeout:
        try:
            resp = requests.get(
                f"{CONNECT_URL}/connectors/{name}/status", timeout=10
            )
            if resp.status_code == 200:
                status = resp.json()
                connector_state = status.get("connector", {}).get("state", "")
                tasks = status.get("tasks", [])

                if connector_state == "RUNNING":
                    task_states = [t.get("state", "") for t in tasks]
                    if all(s == "RUNNING" for s in task_states) and task_states:
                        logger.info(
                            f"Connector '{name}' is RUNNING with "
                            f"{len(tasks)} task(s)."
                        )
                        return True

                logger.info(
                    f"  Connector state: {connector_state}, "
                    f"tasks: {[t.get('state') for t in tasks]}"
                )

                if connector_state == "FAILED":
                    trace = status.get("connector", {}).get("trace", "")
                    logger.error(f"Connector FAILED: {trace[:500]}")
                    return False
        except Exception as e:
            logger.warning(f"  Error checking status: {e}")

        time.sleep(POLL_INTERVAL)

    logger.error(f"Connector '{name}' did not reach RUNNING within {timeout}s.")
    return False


def main():
    if not wait_for_connect():
        sys.exit(1)

    # Give Connect a few more seconds after initial readiness
    time.sleep(5)

    all_success = True
    for connector in CONNECTORS:
        config_path = connector["config_file"]
        name = connector["name"]

        try:
            if not register_connector(config_path):
                logger.error(f"Skipping wait for '{name}' due to registration failure.")
                all_success = False
                continue

            if not wait_for_connector_running(name, timeout=90):
                all_success = False
        except FileNotFoundError:
            logger.warning(
                f"Config file not found: {config_path}. "
                f"Skipping connector '{name}'."
            )
            # Sink connector is optional if using Python consumer
            if name == "postgres-sink-connector":
                logger.info(
                    "Sink connector is optional. "
                    "You can use sink_consumer.py instead."
                )
            else:
                all_success = False

    if all_success:
        logger.info("All connectors registered and running.")
    else:
        logger.warning("Some connectors may not be fully operational.")

    # Print final status
    try:
        resp = requests.get(f"{CONNECT_URL}/connectors", timeout=10)
        logger.info(f"Active connectors: {resp.json()}")
    except Exception:
        pass

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
