# Exercise 03: Single Message Transforms (SMTs)

## Prerequisites

Ensure the environment is running:

```bash
cd module-04-kafka-connect
docker-compose up -d
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
     c. **InsertField (timestamp):** Add a field `kafka_ingest_time` with the current timestamp
     d. **MaskField:** Mask the `salary` field (replaces with zero/null)

2. Deploy the connector and wait for it to reach RUNNING state.

3. Consume messages from `transformed-employees` and verify:
   - Fields `given_name` and `surname` exist (not `first_name` / `last_name`)
   - Field `data_source` equals `mysql-hr-system`
   - Field `kafka_ingest_time` is a valid timestamp
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
- Use JsonConverter with `schemas.enable=false` for easier debugging

---

## Exercise 3.2: Topic Routing with TimestampRouter

### Objective

Deploy a connector that routes records to different topics based on the current date, and then deploy a second connector that uses RegexRouter to normalize topic names.

### Tasks

1. Create a connector configuration `smt-routing-connector.json` that:
   - Reads from the `projects` table using bulk mode
   - Uses TimestampRouter to route records to topics named `projects-YYYY-MM-DD` (using the format `${topic}-${timestamp}` with `timestamp.format=yyyy-MM-dd`)
   - Uses JsonConverter (schemas disabled) for readability

2. Deploy the connector and verify:
   - A topic is created with today's date appended (e.g., `mysql-projects-2024-01-15`)
   - The topic contains all 8 project records

3. Now create a second connector configuration `smt-regex-connector.json` that:
   - Reads from the `departments` table
   - Uses RegexRouter to transform the topic name from `mysql-departments` to `company-dept-data`
   - RegexRouter config: `regex=mysql-(.*)` and `replacement=company-$1-data`

4. Deploy both connectors and verify the topic names are as expected.

5. Write a Python script (`verify_routing.py`) that:
   - Lists all topics in the Kafka cluster
   - Finds topics matching the date-partitioned pattern
   - Finds the regex-routed topic
   - Validates message counts in each
   - Prints a summary report

### Expected Outcome

- TimestampRouter creates date-partitioned topics
- RegexRouter rewrites topic names according to the pattern
- Both routing strategies work independently and can be combined

### Hints

- TimestampRouter uses Java's SimpleDateFormat patterns
- RegexRouter uses Java regex syntax
- The `topic.prefix` from JDBC connector is applied BEFORE SMTs, so the input to TimestampRouter already has the prefix
- Use `poll.interval.ms: 60000` (1 minute) to avoid repeated bulk loads
