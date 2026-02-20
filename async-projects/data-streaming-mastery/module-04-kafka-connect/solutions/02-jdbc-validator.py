"""
Solution for Exercise 2.1: JDBC Source Connector Validator

Connects to MySQL to count employees, then counts messages in the
mysql-employees Kafka topic, and compares the two counts.

Usage:
    # Make sure the JDBC source connector is deployed first
    python solutions/02-jdbc-validator.py
"""

import sys
import time

import mysql.connector
from confluent_kafka import Consumer, KafkaError, TopicPartition
from confluent_kafka.admin import AdminClient


# Configuration
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "connect_user",
    "password": "connect_pass",
    "database": "company",
}
KAFKA_BOOTSTRAP = "localhost:9092"
TOPIC = "mysql-employees"


def get_mysql_employee_count() -> int:
    """
    Query MySQL for the total number of employees.

    Returns:
        The count of rows in the employees table.
    """
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except mysql.connector.Error as e:
        print(f"ERROR connecting to MySQL: {e}")
        return -1


def get_kafka_message_count(topic: str) -> int:
    """
    Count total messages in a Kafka topic by consuming from beginning to end.

    Args:
        topic: The Kafka topic to count messages in.

    Returns:
        The number of messages in the topic, or -1 on error.
    """
    admin = AdminClient({"bootstrap.servers": KAFKA_BOOTSTRAP})

    # Check if topic exists
    metadata = admin.list_topics(timeout=10)
    if topic not in metadata.topics:
        print(f"Topic '{topic}' does not exist.")
        return -1

    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP,
        "group.id": f"jdbc-validator-{int(time.time())}",
        "auto.offset.reset": "earliest",
        "enable.auto.commit": False,
    })

    consumer.subscribe([topic])

    count = 0
    empty_polls = 0
    max_empty = 10  # Stop after 10 empty polls (10 seconds)

    while empty_polls < max_empty:
        msg = consumer.poll(1.0)
        if msg is None:
            empty_polls += 1
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                empty_polls += 1
                continue
            print(f"Consumer error: {msg.error()}")
            break
        count += 1
        empty_polls = 0  # Reset on successful message

    consumer.close()
    return count


def insert_test_employee() -> bool:
    """
    Insert a test employee to verify the connector picks up new rows.

    Returns:
        True if the insert succeeded.
    """
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employees
                (first_name, last_name, email, department_id, hire_date, salary, is_active)
            VALUES
                ('Zara', 'Ahmed', 'zara.ahmed@company.com', 1, '2024-06-01', 132000.00, 1)
        """)
        conn.commit()
        new_id = cursor.lastrowid
        print(f"  Inserted test employee with id={new_id}")
        cursor.close()
        conn.close()
        return True
    except mysql.connector.Error as e:
        if "Duplicate entry" in str(e):
            print("  Test employee already exists (duplicate email). Skipping insert.")
            return True
        print(f"ERROR inserting test employee: {e}")
        return False


def main():
    """
    Validate the JDBC Source connector by comparing MySQL row count
    with Kafka message count.
    """
    print("=" * 60)
    print("JDBC Source Connector Validator")
    print("=" * 60)

    # Step 1: Count employees in MySQL
    print("\n1. Counting employees in MySQL ...")
    mysql_count = get_mysql_employee_count()
    if mysql_count < 0:
        print("   Cannot connect to MySQL. Is it running?")
        sys.exit(1)
    print(f"   MySQL employee count: {mysql_count}")

    # Step 2: Count messages in Kafka
    print("\n2. Counting messages in Kafka topic '{0}' ...".format(TOPIC))
    kafka_count = get_kafka_message_count(TOPIC)
    if kafka_count < 0:
        print(f"   Topic '{TOPIC}' not found. Is the JDBC source connector deployed?")
        sys.exit(1)
    print(f"   Kafka message count: {kafka_count}")

    # Step 3: Compare
    print("\n3. Comparison:")
    if kafka_count == mysql_count:
        print(f"   MATCH: MySQL ({mysql_count}) == Kafka ({kafka_count})")
        print("   The JDBC Source connector has captured all rows.")
    elif kafka_count < mysql_count:
        print(f"   MISMATCH: MySQL ({mysql_count}) > Kafka ({kafka_count})")
        print("   The connector may still be catching up. Wait for the next poll.")
    else:
        print(f"   MISMATCH: Kafka ({kafka_count}) > MySQL ({mysql_count})")
        print("   There may be duplicate messages (e.g., from connector restarts in bulk mode).")

    # Step 4: Test new row detection
    print("\n4. Testing new row detection ...")
    before_count = mysql_count
    if insert_test_employee():
        new_mysql_count = get_mysql_employee_count()
        print(f"   MySQL count after insert: {new_mysql_count}")
        print("   Waiting 10 seconds for connector to poll ...")
        time.sleep(10)
        new_kafka_count = get_kafka_message_count(TOPIC)
        print(f"   Kafka count after wait: {new_kafka_count}")
        if new_kafka_count >= new_mysql_count:
            print("   SUCCESS: New row detected by connector!")
        else:
            print("   New row not yet in Kafka. Try waiting longer or check connector status.")

    print("\nDone.")


if __name__ == "__main__":
    main()
