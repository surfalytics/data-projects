"""
Solution for Exercise 2.2: JDBC Sink Replication Checker

Queries both the source 'employees' table and the sink 'employees_replica' table,
compares their contents, and reports on replication status.

Usage:
    # Make sure both JDBC source and sink connectors are deployed
    python solutions/02-replication-checker.py
"""

import sys
import time
from datetime import datetime

import mysql.connector


MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "connect_user",
    "password": "connect_pass",
    "database": "company",
}


def get_table_data(table_name: str) -> list[dict]:
    """
    Fetch all rows from a table as a list of dictionaries.

    Args:
        table_name: Name of the MySQL table to query.

    Returns:
        A list of row dictionaries.
    """
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except mysql.connector.Error as e:
        print(f"ERROR querying {table_name}: {e}")
        return []


def compare_tables():
    """
    Compare the employees source table with the employees_replica sink table.

    Checks row counts, identifies missing/extra rows, and compares field values.
    """
    print("=" * 60)
    print("JDBC Sink Replication Checker")
    print("=" * 60)

    # Fetch data from both tables
    print("\nFetching source data (employees) ...")
    source_rows = get_table_data("employees")
    print(f"  Source rows: {len(source_rows)}")

    print("Fetching replica data (employees_replica) ...")
    replica_rows = get_table_data("employees_replica")
    print(f"  Replica rows: {len(replica_rows)}")

    if not source_rows:
        print("\nERROR: No data in source table. Check MySQL.")
        sys.exit(1)

    if not replica_rows:
        print("\nWARNING: Replica table is empty.")
        print("Make sure the JDBC sink connector is deployed and running.")
        print("Waiting 15 seconds and retrying ...")
        time.sleep(15)
        replica_rows = get_table_data("employees_replica")
        print(f"  Replica rows after wait: {len(replica_rows)}")
        if not replica_rows:
            print("Still empty. Check the sink connector status.")
            sys.exit(1)

    # Build lookup by ID
    source_by_id = {row["id"]: row for row in source_rows}
    replica_by_id = {row["id"]: row for row in replica_rows}

    source_ids = set(source_by_id.keys())
    replica_ids = set(replica_by_id.keys())

    # Check for missing and extra rows
    missing_in_replica = source_ids - replica_ids
    extra_in_replica = replica_ids - source_ids
    common_ids = source_ids & replica_ids

    print(f"\n{'=' * 60}")
    print("Replication Report")
    print(f"{'=' * 60}")
    print(f"  Source rows:       {len(source_rows)}")
    print(f"  Replica rows:      {len(replica_rows)}")
    print(f"  Common rows:       {len(common_ids)}")
    print(f"  Missing in replica: {len(missing_in_replica)}")
    print(f"  Extra in replica:  {len(extra_in_replica)}")

    if missing_in_replica:
        print(f"\n  Missing employee IDs: {sorted(missing_in_replica)}")
        for eid in sorted(missing_in_replica):
            emp = source_by_id[eid]
            print(f"    id={eid}: {emp['first_name']} {emp['last_name']}")

    if extra_in_replica:
        print(f"\n  Extra employee IDs in replica: {sorted(extra_in_replica)}")

    # Compare field values for common rows
    fields_to_compare = ["first_name", "last_name", "email", "department_id", "salary", "is_active"]
    field_mismatches = 0

    for eid in sorted(common_ids):
        src = source_by_id[eid]
        rep = replica_by_id[eid]
        for field in fields_to_compare:
            src_val = src.get(field)
            rep_val = rep.get(field)
            # Normalize types for comparison (e.g., Decimal vs float)
            if str(src_val) != str(rep_val):
                field_mismatches += 1
                if field_mismatches <= 10:  # Limit output
                    print(f"\n  FIELD MISMATCH id={eid}, field={field}:")
                    print(f"    Source:  {src_val} ({type(src_val).__name__})")
                    print(f"    Replica: {rep_val} ({type(rep_val).__name__})")

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")

    issues = len(missing_in_replica) + len(extra_in_replica) + field_mismatches
    if issues == 0:
        print("  RESULT: Replication is HEALTHY. All rows and fields match.")
    else:
        print(f"  RESULT: Replication has {issues} issue(s).")
        if missing_in_replica:
            print(f"    - {len(missing_in_replica)} rows missing in replica (may still be syncing)")
        if extra_in_replica:
            print(f"    - {len(extra_in_replica)} extra rows in replica")
        if field_mismatches:
            print(f"    - {field_mismatches} field value mismatch(es)")

    return issues == 0


def test_replication_lag():
    """
    Insert a new row and measure how long it takes to appear in the replica.
    """
    print(f"\n{'=' * 60}")
    print("Replication Lag Test")
    print(f"{'=' * 60}")

    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Insert a new employee with a unique email
    timestamp = int(time.time())
    email = f"lag.test.{timestamp}@company.com"

    try:
        cursor.execute("""
            INSERT INTO employees
                (first_name, last_name, email, department_id, hire_date, salary, is_active)
            VALUES
                ('Lag', 'Test', %s, 1, '2024-07-01', 100000.00, 1)
        """, (email,))
        conn.commit()
        insert_time = datetime.now()
        new_id = cursor.lastrowid
        print(f"  Inserted test row id={new_id} at {insert_time.strftime('%H:%M:%S')}")
    except mysql.connector.Error as e:
        print(f"  ERROR inserting test row: {e}")
        cursor.close()
        conn.close()
        return

    cursor.close()
    conn.close()

    # Poll the replica table for the new row
    max_wait = 30
    poll_interval = 2
    elapsed = 0

    print(f"  Polling replica table for id={new_id} (max {max_wait}s) ...")
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval

        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM employees_replica WHERE id = %s", (new_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            detect_time = datetime.now()
            lag = (detect_time - insert_time).total_seconds()
            print(f"  Row appeared in replica after {lag:.1f} seconds.")
            return

    print(f"  Row did not appear in replica within {max_wait} seconds.")
    print("  This may be normal if the poll interval is long or connectors are slow.")


if __name__ == "__main__":
    healthy = compare_tables()
    test_replication_lag()
    sys.exit(0 if healthy else 1)
