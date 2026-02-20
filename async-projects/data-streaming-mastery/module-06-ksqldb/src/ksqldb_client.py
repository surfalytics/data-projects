#!/usr/bin/env python3
"""
ksqlDB REST API client for Module 6.

Provides helper functions to interact with ksqlDB:
  - Execute DDL/DML statements (CREATE STREAM, CREATE TABLE, etc.)
  - Run push queries (streaming results via HTTP/2 chunked transfer)
  - Run pull queries (point-in-time lookups)
  - List streams and tables
  - Check server health and info

Usage:
    python src/ksqldb_client.py

The script demonstrates all capabilities when run directly.
"""

import json
import sys
import time
from typing import Generator

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KSQLDB_URL = "http://localhost:8088"
HEADERS = {
    "Content-Type": "application/vnd.ksql.v1+json; charset=utf-8",
    "Accept": "application/vnd.ksql.v1+json",
}


# ---------------------------------------------------------------------------
# Core API Functions
# ---------------------------------------------------------------------------

def get_server_info() -> dict:
    """
    Retrieve ksqlDB server metadata.

    Returns:
        dict with server version, cluster ID, ksqlDB service ID, and status.
    """
    response = requests.get(f"{KSQLDB_URL}/info", timeout=10)
    response.raise_for_status()
    return response.json()


def check_health() -> dict:
    """
    Check ksqlDB server health status.

    Returns:
        dict with health status details.
    """
    response = requests.get(f"{KSQLDB_URL}/healthcheck", timeout=10)
    response.raise_for_status()
    return response.json()


def execute_statement(statement: str, stream_properties: dict | None = None) -> dict:
    """
    Execute a ksqlDB statement (DDL or DML).

    Supports: CREATE STREAM, CREATE TABLE, DROP, INSERT INTO, TERMINATE, etc.

    Args:
        statement: The ksqlDB SQL statement to execute.
        stream_properties: Optional dict of stream properties
                          (e.g., {"ksql.streams.auto.offset.reset": "earliest"}).

    Returns:
        dict with the server response (command status, query ID, etc.).
    """
    payload = {"ksql": statement}
    if stream_properties:
        payload["streamsProperties"] = stream_properties

    response = requests.post(
        f"{KSQLDB_URL}/ksql",
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def run_pull_query(query: str) -> list[dict]:
    """
    Execute a pull query and return the result set.

    Pull queries return a finite result set (like traditional SQL).
    They work on materialized views and tables.

    Args:
        query: A SELECT statement WITHOUT EMIT CHANGES.

    Returns:
        List of result rows as dicts.
    """
    payload = {"sql": query}
    response = requests.post(
        f"{KSQLDB_URL}/query",
        headers=HEADERS,
        data=json.dumps(payload),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def run_push_query(query: str, timeout_seconds: int = 10) -> Generator[dict, None, None]:
    """
    Execute a push query and yield results as they arrive.

    Push queries stream results continuously. This function yields each
    row as a dict. The caller should break out of the loop when done.

    Args:
        query: A SELECT statement WITH EMIT CHANGES.
        timeout_seconds: Max seconds to wait for results before stopping.

    Yields:
        dict: Each result row from the push query.
    """
    payload = {"sql": query, "properties": {"auto.offset.reset": "earliest"}}

    with requests.post(
        f"{KSQLDB_URL}/query",
        headers={
            "Content-Type": "application/vnd.ksql.v1+json; charset=utf-8",
            "Accept": "application/vnd.ksql.v1+json",
        },
        data=json.dumps(payload),
        stream=True,
        timeout=timeout_seconds,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    row = json.loads(line.rstrip(","))
                    yield row
                except json.JSONDecodeError:
                    continue


def list_streams() -> list[dict]:
    """
    List all ksqlDB streams.

    Returns:
        List of stream metadata dicts (name, topic, key format, value format).
    """
    result = execute_statement("SHOW STREAMS;")
    if result and len(result) > 0:
        return result[0].get("streams", [])
    return []


def list_tables() -> list[dict]:
    """
    List all ksqlDB tables.

    Returns:
        List of table metadata dicts (name, topic, key format, value format).
    """
    result = execute_statement("SHOW TABLES;")
    if result and len(result) > 0:
        return result[0].get("tables", [])
    return []


def list_queries() -> list[dict]:
    """
    List all running persistent queries.

    Returns:
        List of query metadata dicts (query ID, query string, status).
    """
    result = execute_statement("SHOW QUERIES;")
    if result and len(result) > 0:
        return result[0].get("queries", [])
    return []


def describe_source(name: str) -> dict:
    """
    Describe a stream or table.

    Args:
        name: Name of the stream or table.

    Returns:
        dict with source description (columns, topic, format, etc.).
    """
    result = execute_statement(f"DESCRIBE {name};")
    if result and len(result) > 0:
        return result[0]
    return {}


# ---------------------------------------------------------------------------
# Demo / Main
# ---------------------------------------------------------------------------

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def main():
    """Demonstrate all ksqlDB client capabilities."""
    print("ksqlDB Python Client -- Module 6 Demo")
    print("=" * 60)

    # 1. Server info
    print_section("Server Info")
    try:
        info = get_server_info()
        print(json.dumps(info, indent=2))
    except requests.ConnectionError:
        print("ERROR: Cannot connect to ksqlDB at", KSQLDB_URL)
        print("Make sure docker compose is running: docker compose up -d")
        sys.exit(1)

    # 2. Health check
    print_section("Health Check")
    health = check_health()
    print(json.dumps(health, indent=2))

    # 3. List streams
    print_section("Streams")
    streams = list_streams()
    if streams:
        for s in streams:
            print(f"  - {s.get('name', 'N/A'):<30} topic={s.get('topic', 'N/A')}")
    else:
        print("  No streams found. Run setup_ksqldb.sh first.")

    # 4. List tables
    print_section("Tables")
    tables = list_tables()
    if tables:
        for t in tables:
            print(f"  - {t.get('name', 'N/A'):<30} topic={t.get('topic', 'N/A')}")
    else:
        print("  No tables found. Run setup_ksqldb.sh first.")

    # 5. List persistent queries
    print_section("Persistent Queries")
    queries = list_queries()
    if queries:
        for q in queries:
            print(f"  - {q.get('id', 'N/A')}: {q.get('queryString', 'N/A')[:80]}...")
    else:
        print("  No persistent queries running.")

    # 6. Pull query example
    print_section("Pull Query Example")
    if any(t.get("name", "").upper() == "CUSTOMER_ORDER_SUMMARY" for t in tables):
        try:
            result = run_pull_query(
                "SELECT * FROM customer_order_summary WHERE customer_id = 'C0001';"
            )
            for row in result:
                print(f"  {row}")
        except Exception as e:
            print(f"  Pull query error: {e}")
    else:
        print("  Table CUSTOMER_ORDER_SUMMARY not found. Run 06-materialized-views.sql first.")

    # 7. Push query example (limited to 5 rows)
    print_section("Push Query Example (first 5 rows)")
    if streams:
        try:
            print("  Listening for orders (5 rows max, 10s timeout)...")
            count = 0
            for row in run_push_query(
                "SELECT order_id, customer_id, price FROM orders_stream EMIT CHANGES LIMIT 5;",
                timeout_seconds=15,
            ):
                print(f"  Row {count + 1}: {row}")
                count += 1
                if count >= 5:
                    break
        except requests.exceptions.ReadTimeout:
            print("  Timeout reached (no new data). Ensure seed_topics.py is running.")
        except Exception as e:
            print(f"  Push query error: {e}")
    else:
        print("  No streams available. Run setup_ksqldb.sh first.")

    print_section("Done")
    print("  All demonstrations complete.")


if __name__ == "__main__":
    main()
