#!/usr/bin/env python3
"""
Submit ksqlDB queries via REST API.

Reads SQL statements from the ksqlDB queries file and submits them
one at a time to the ksqlDB server. Waits for ksqlDB to be ready
before starting.
"""

import logging
import re
import sys
import time

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KSQLDB_URL = "http://localhost:8088"
QUERIES_FILE = "../config/ksqldb-queries.sql"
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
logger = logging.getLogger("setup-ksqldb")

# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def wait_for_ksqldb():
    """Wait for ksqlDB to be ready."""
    logger.info(f"Waiting for ksqlDB at {KSQLDB_URL} ...")
    start = time.time()

    while time.time() - start < MAX_WAIT_SECONDS:
        try:
            resp = requests.get(f"{KSQLDB_URL}/info", timeout=5)
            if resp.status_code == 200:
                info = resp.json()
                version = info.get("KsqlServerInfo", {}).get("version", "unknown")
                logger.info(f"ksqlDB is ready. Version: {version}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass

        elapsed = int(time.time() - start)
        logger.info(f"  ksqlDB not ready ({elapsed}s elapsed). Retrying...")
        time.sleep(POLL_INTERVAL)

    logger.error(f"ksqlDB did not become ready within {MAX_WAIT_SECONDS}s.")
    return False


def parse_sql_file(filepath):
    """Parse SQL file into individual statements, stripping comments."""
    with open(filepath, "r") as f:
        content = f.read()

    # Remove single-line comments
    content = re.sub(r"--[^\n]*", "", content)

    # Split on semicolons
    statements = [s.strip() for s in content.split(";") if s.strip()]

    return statements


def submit_ksql_statement(statement):
    """Submit a single ksqlDB statement via REST API."""
    payload = {
        "ksql": statement + ";",
        "streamsProperties": {
            "ksql.streams.auto.offset.reset": "earliest"
        },
    }

    try:
        resp = requests.post(
            f"{KSQLDB_URL}/ksql",
            json=payload,
            headers={"Content-Type": "application/vnd.ksql.v1+json"},
            timeout=30,
        )

        if resp.status_code == 200:
            result = resp.json()
            for item in result:
                status = item.get("commandStatus", {}).get("status", "")
                message = item.get("commandStatus", {}).get("message", "")
                if status:
                    logger.info(f"  Status: {status} - {message[:200]}")
            return True
        else:
            error = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
            # Ignore "already exists" errors
            error_text = str(error)
            if "already exists" in error_text.lower():
                logger.info("  Object already exists. Skipping.")
                return True
            logger.error(f"  ksqlDB error ({resp.status_code}): {error_text[:500]}")
            return False

    except Exception as e:
        logger.error(f"  Request error: {e}")
        return False


def main():
    if not wait_for_ksqldb():
        sys.exit(1)

    # Give ksqlDB additional time to fully initialize
    logger.info("Waiting 10 seconds for ksqlDB to fully initialize...")
    time.sleep(10)

    # Parse queries
    try:
        statements = parse_sql_file(QUERIES_FILE)
    except FileNotFoundError:
        logger.error(f"Queries file not found: {QUERIES_FILE}")
        sys.exit(1)

    logger.info(f"Found {len(statements)} SQL statements to submit.")

    success_count = 0
    fail_count = 0

    for i, stmt in enumerate(statements, 1):
        # Extract first line for logging
        first_line = stmt.split("\n")[0][:80]
        logger.info(f"[{i}/{len(statements)}] {first_line}...")

        if submit_ksql_statement(stmt):
            success_count += 1
        else:
            fail_count += 1

        # Small delay between statements to avoid overwhelming ksqlDB
        time.sleep(2)

    logger.info("=" * 60)
    logger.info(f"ksqlDB Setup Complete: {success_count} succeeded, {fail_count} failed")
    logger.info("=" * 60)

    # List all streams and tables
    try:
        resp = requests.post(
            f"{KSQLDB_URL}/ksql",
            json={"ksql": "SHOW STREAMS;"},
            headers={"Content-Type": "application/vnd.ksql.v1+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            streams = resp.json()
            logger.info("Active streams:")
            for item in streams:
                for stream in item.get("streams", []):
                    logger.info(f"  - {stream.get('name', 'unknown')}")

        resp = requests.post(
            f"{KSQLDB_URL}/ksql",
            json={"ksql": "SHOW TABLES;"},
            headers={"Content-Type": "application/vnd.ksql.v1+json"},
            timeout=10,
        )
        if resp.status_code == 200:
            tables = resp.json()
            logger.info("Active tables:")
            for item in tables:
                for table in item.get("tables", []):
                    logger.info(f"  - {table.get('name', 'unknown')}")
    except Exception:
        pass

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
