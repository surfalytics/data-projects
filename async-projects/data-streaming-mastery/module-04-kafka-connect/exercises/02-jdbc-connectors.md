# Exercise 02: JDBC Connectors

## Prerequisites

Ensure the environment is running:

```bash
cd module-04-kafka-connect
docker-compose up -d
```

Verify MySQL is accessible and has data:

```bash
docker exec module04-mysql mysql -uconnect_user -pconnect_pass -e "SELECT COUNT(*) FROM company.employees;"
# Should return: 20
```

---

## Exercise 2.1: JDBC Source Connector (Incrementing Mode)

### Objective

Deploy a JDBC Source connector that reads the `employees` and `departments` tables from MySQL and publishes them to Kafka topics. Then insert new rows and verify they are captured.

### Tasks

1. Deploy the JDBC Source connector using `config/jdbc-source-connector.json`.

2. Verify the connector is running and check its task status.

3. Confirm that two new topics were created:
   - `mysql-employees`
   - `mysql-departments`

4. Consume messages from `mysql-employees` and verify:
   - There are 20 messages (matching the 20 employees in the database)
   - Each message contains the full employee record (id, first_name, last_name, email, etc.)

5. Insert a new employee into MySQL:

```sql
INSERT INTO company.employees
    (first_name, last_name, email, department_id, hire_date, salary, is_active)
VALUES
    ('Zara', 'Ahmed', 'zara.ahmed@company.com', 1, '2024-06-01', 132000.00, 1);
```

6. Wait for the next poll interval (5 seconds) and verify the new employee appears in the `mysql-employees` topic.

7. Write a Python script (`jdbc_validator.py`) that:
   - Connects to MySQL and counts employees
   - Counts messages in the `mysql-employees` topic
   - Compares the counts and reports whether they match

### Expected Outcome

- The JDBC Source connector reads all existing rows on first poll
- New rows inserted into MySQL appear in Kafka after the poll interval
- Employee count in MySQL matches message count in Kafka

### Hints

- The connector uses `mode: incrementing` with `incrementing.column.name: id`
- This mode only detects NEW rows (not updates to existing rows)
- To also capture updates, use `mode: timestamp+incrementing`
- Messages are serialized with Avro (check Schema Registry at http://localhost:8081/subjects)

---

## Exercise 2.2: JDBC Sink Connector (Replication)

### Objective

Deploy a JDBC Sink connector that reads from the `mysql-employees` topic and writes to the `employees_replica` table, creating a replicated copy of the data.

### Tasks

1. First, make sure Exercise 2.1 is complete and `mysql-employees` has data.

2. Deploy the JDBC Sink connector using `config/jdbc-sink-connector.json`.

3. Verify the connector is running.

4. Query the `employees_replica` table in MySQL and verify it contains the same data as `employees`:

```bash
docker exec module04-mysql mysql -uconnect_user -pconnect_pass \
    -e "SELECT id, first_name, last_name FROM company.employees_replica ORDER BY id;"
```

5. Insert another new employee into the `employees` table. Verify the data flows through the full pipeline:
   - MySQL `employees` -> JDBC Source -> Kafka `mysql-employees` -> JDBC Sink -> MySQL `employees_replica`

6. Write a Python script (`replication_checker.py`) that:
   - Queries both `employees` and `employees_replica` tables
   - Compares row counts
   - Identifies any missing or extra rows in the replica
   - Reports the replication lag (time difference between source insert and replica appearance)

### Expected Outcome

- The `employees_replica` table mirrors the `employees` table
- New employees appear in the replica within ~10 seconds (poll interval + processing)
- The full pipeline (source -> Kafka -> sink) works end-to-end

### Hints

- The sink connector uses `insert.mode: upsert` and `pk.mode: record_value` with `pk.fields: id`
- Upsert mode means duplicate records are updated rather than causing errors
- The `auto.create` and `auto.evolve` settings handle schema changes automatically
- If the replica table already exists (from init.sql), the sink connector will use it
