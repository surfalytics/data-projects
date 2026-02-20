# Exercise 2: Schema Evolution

## Learning Objectives

- Evolve schemas safely using backward-compatible changes
- Understand what breaks each compatibility mode
- Use the Schema Registry compatibility check API
- Handle multi-version data in consumers

---

## Exercise 2.1: Backward-Compatible Evolution

You have a production topic `user-profiles` with the following V1 schema that has been running for 6 months:

```json
{
  "type": "record",
  "name": "UserProfile",
  "namespace": "com.example.users",
  "fields": [
    {"name": "user_id", "type": "string"},
    {"name": "email", "type": "string"},
    {"name": "name", "type": "string"},
    {"name": "signup_date", "type": "long"}
  ]
}
```

The product team wants the following changes:

1. Add a `phone_number` field (optional)
2. Add an `account_status` field with values ACTIVE, SUSPENDED, DELETED (default: ACTIVE)
3. Add a `last_login` timestamp (optional)
4. Add a `preferences` map for user settings (optional)

**Tasks:**

1. Write the V2 schema that adds ALL four fields while maintaining **BACKWARD** compatibility with V1
2. Write a Python script that:
   - Registers the V1 schema
   - Checks that V2 is compatible with V1
   - Registers the V2 schema
   - Produces 3 messages with V1 format and 3 messages with V2 format
   - Consumes all 6 messages with a V2-aware consumer
3. Explain WHY each field you added is backward compatible (what default does the consumer use when reading V1 data?)

---

## Exercise 2.2: Breaking Changes (What NOT to Do)

Given the same V1 schema from Exercise 2.1, determine which of the following V2 changes would **break backward compatibility** and explain why:

### Change A: Rename a field
```json
{"name": "full_name", "type": "string"}
```
(Replacing the `name` field with `full_name`)

### Change B: Change field type
```json
{"name": "signup_date", "type": "string"}
```
(Changing `signup_date` from `long` to `string`)

### Change C: Add required field
```json
{"name": "country", "type": "string"}
```
(Adding a new field without a default)

### Change D: Remove a field
Remove the `name` field entirely from V2.

### Change E: Make a field nullable
```json
{"name": "email", "type": ["null", "string"], "default": null}
```
(Changing `email` from `string` to `["null", "string"]`)

**Tasks:**

1. For each change (A-E), state whether it breaks BACKWARD compatibility and explain why
2. For each change (A-E), state whether it breaks FORWARD compatibility and explain why
3. Write a Python script that attempts to register each breaking change and captures the Schema Registry error messages
4. For each breaking change, propose an alternative that IS backward compatible

---

## Exercise 2.3: Multi-Version Consumer

Build a consumer that can handle messages from THREE different schema versions of an `inventory-updates` topic:

### V1 Schema
```json
{
  "type": "record",
  "name": "InventoryUpdate",
  "namespace": "com.warehouse.inventory",
  "fields": [
    {"name": "product_id", "type": "string"},
    {"name": "warehouse_id", "type": "string"},
    {"name": "quantity", "type": "int"},
    {"name": "timestamp", "type": "long"}
  ]
}
```

### V2 Schema (adds location and update_type)
```json
{
  "type": "record",
  "name": "InventoryUpdate",
  "namespace": "com.warehouse.inventory",
  "fields": [
    {"name": "product_id", "type": "string"},
    {"name": "warehouse_id", "type": "string"},
    {"name": "quantity", "type": "int"},
    {"name": "timestamp", "type": "long"},
    {"name": "update_type", "type": "string", "default": "ADJUSTMENT"},
    {"name": "location_aisle", "type": ["null", "string"], "default": null}
  ]
}
```

### V3 Schema (adds batch tracking)
```json
{
  "type": "record",
  "name": "InventoryUpdate",
  "namespace": "com.warehouse.inventory",
  "fields": [
    {"name": "product_id", "type": "string"},
    {"name": "warehouse_id", "type": "string"},
    {"name": "quantity", "type": "int"},
    {"name": "timestamp", "type": "long"},
    {"name": "update_type", "type": "string", "default": "ADJUSTMENT"},
    {"name": "location_aisle", "type": ["null", "string"], "default": null},
    {"name": "batch_id", "type": ["null", "string"], "default": null},
    {"name": "expiry_date", "type": ["null", "long"], "default": null}
  ]
}
```

**Tasks:**

1. Write a Python script that:
   - Registers V1, V2, and V3 schemas in sequence (checking compatibility at each step)
   - Produces 3 messages with V1, 3 with V2, and 3 with V3
   - Consumes all 9 messages with a single consumer
   - For each message, prints which schema version it was written with and shows default values for missing fields
2. Verify that BACKWARD_TRANSITIVE compatibility holds across all three versions
3. Answer: Could a V1 consumer read V3 data? Why or why not?

---

## Validation

Test your solutions by running them against the local infrastructure:

```bash
# Start infrastructure
docker-compose up -d

# Run your solutions
python solutions/exercise_2_1.py
python solutions/exercise_2_2.py
python solutions/exercise_2_3.py

# Inspect schemas in the registry
python src/schema_registry_client.py list-subjects
python src/schema_registry_client.py get-versions user-profiles-value
```
