# Exercise 03: Single Message Transforms (SMTs)

## Prerequisites

Ensure the environment is running:

```bash
cd module-04-kafka-connect
docker compose up -d
```

---

## Exercise 3.1: Field Manipulation with SMTs

### Objective

Deploy a JDBC Source connector with multiple SMTs that transform employee records before they reach Kafka. Practice chaining transforms.

### Tasks

1. Create a new connector configuration (JSON file) named `smt-field-transform-connector.json` that:
   - Reads from the `employees` table
   - Writes to topic `transformed-employees`
   - Applies the following SMTs in order:
     a. **ReplaceField (rename):** Rename `first_name` to `given_name` and `last_name` to `surname`
     b. **InsertField (static):** Add a field `data_source` with value `mysql-hr-system`
     c. **InsertField (timestamp):** Add a field `kafka_ingest_time` (see the hint: its value is null for a JDBC source)
     d. **Cast + MaskField:** Cast `salary` to `float64`, then mask it (replaces with zero)

2. Deploy the connector and wait for it to reach RUNNING state.

3. Consume messages from `transformed-employees` and verify:
   - Fields `given_name` and `surname` exist (not `first_name` / `last_name`)
   - Field `data_source` equals `mysql-hr-system`
   - Field `kafka_ingest_time` exists (its value is null, see hints)
   - Field `salary` is masked (value is 0)

4. Write a Python validation script (`validate_transforms.py`) that:
   - Consumes all messages from `transformed-employees`
   - Validates each of the four transform conditions above
   - Prints a pass/fail report for each condition
   - Exits with code 0 if all pass, code 1 if any fail

### Expected Outcome

- All four SMTs are applied in the correct order
- The output messages have renamed fields, added fields, and masked salary
- The validation script confirms all transforms

### Hints

- SMTs are applied in the order listed in the `transforms` property
- Use `$Value` suffix for transforms on the record value (e.g., `ReplaceField$Value`)
- The MaskField SMT replaces numeric fields with 0 and string fields with empty string
- `salary` is a `DECIMAL` column. MaskField on a `DECIMAL` fails with `Decimal value has mismatching scale`. Add `Cast$Value` with `salary:float64` before MaskField.
- `InsertField` with `timestamp.field` uses the record timestamp. JDBC source records have no timestamp, so the value is null. In a sink connector the record comes from Kafka and has a timestamp.
- Use JsonConverter with `schemas.enable=false` for easier debugging

---

## Exercise 3.2: Topic Routing with TimestampRouter

### Objective

Deploy a connector that routes records to different topics based on the current date, and then deploy a second connector that uses RegexRouter to normalize topic names.

### Tasks

1. `TimestampRouter` needs a record timestamp. JDBC **source** records have none, and the task fails with `Timestamp missing on record`. So use it on a **sink**. Create two connectors:
   - A JDBC source (bulk mode, `projects` table, `topic.prefix=mysql-`, JsonConverter with schemas enabled) that writes topic `mysql-projects`.
   - A JDBC sink (`smt-routing-connector.json`) that reads `mysql-projects`, uses `table.name.format=${topic}`, `auto.create=true`, `pk.mode=none`, and TimestampRouter with `topic.format=${topic}-${timestamp}` and `timestamp.format=yyyy-MM-dd`.

2. Deploy both and verify:
   - A MySQL table named with today's date exists (e.g., `mysql-projects-2026-11-10`)
   - The table contains all 8 project records

3. Now create a second connector configuration `smt-regex-connector.json` that:
   - Reads from the `departments` table
   - Uses RegexRouter to transform the topic name from `mysql-departments` to `company-departments-data`
   - RegexRouter config: `regex=mysql-(.*)` and `replacement=company-$1-data`

4. Deploy both connectors and verify the topic names are as expected.

5. Write a Python script (`verify_routing.py`) that:
   - Lists all topics in the Kafka cluster and all tables in MySQL
   - Finds the date-named MySQL table
   - Finds the regex-routed topic
   - Validates message counts in each
   - Prints a summary report

### Expected Outcome

- TimestampRouter on a sink creates date-named targets
- RegexRouter rewrites topic names according to the pattern
- Both routing strategies work independently and can be combined

### Hints

- TimestampRouter uses Java's SimpleDateFormat patterns
- RegexRouter uses Java regex syntax
- The `topic.prefix` from JDBC connector is applied BEFORE SMTs, so the input to TimestampRouter already has the prefix
- Use `poll.interval.ms: 60000` (1 minute) to avoid repeated bulk loads
