# Exercise 1: Designing Avro Schemas

## Learning Objectives

- Design Avro schemas for real-world data models
- Use primitive types, complex types, enums, arrays, and unions
- Apply logical types for dates and timestamps
- Understand nullable fields and default values

---

## Exercise 1.1: Customer Profile Schema

Design an Avro schema for a **Customer Profile** event with the following requirements:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| customer_id | string | Yes | UUID format |
| first_name | string | Yes | |
| last_name | string | Yes | |
| email | string | Yes | |
| phone | string | No | Nullable |
| date_of_birth | date | No | Nullable, use logical type |
| membership_tier | enum | Yes | BRONZE, SILVER, GOLD, PLATINUM |
| interests | array of strings | Yes | Can be empty |
| created_at | timestamp | Yes | Millisecond precision |
| updated_at | timestamp | Yes | Millisecond precision |

**Tasks:**
1. Write the complete Avro schema as JSON
2. Make sure nullable fields use unions with `null` as the first type and have `null` as default
3. Use the namespace `com.ecommerce.customers`
4. Add `doc` fields for at least 3 fields

**Bonus:** Write a Python script that registers this schema with Schema Registry and produces 5 sample messages.

---

## Exercise 1.2: Product Catalog Schema

Design an Avro schema for a **Product** in an e-commerce catalog:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| product_id | string | Yes | |
| name | string | Yes | |
| description | string | No | Nullable |
| category | enum | Yes | ELECTRONICS, CLOTHING, HOME, FOOD, SPORTS, OTHER |
| price_cents | int | Yes | Price in cents to avoid floating point |
| currency | string | Yes | Default "USD" |
| tags | array of strings | Yes | |
| dimensions | record | No | Nullable; contains length_cm, width_cm, height_cm (all doubles) |
| weight_grams | int | No | Nullable |
| in_stock | boolean | Yes | Default true |
| created_at | long (timestamp-millis) | Yes | |

**Tasks:**
1. Write the complete Avro schema
2. Handle the nested `dimensions` record correctly
3. Ensure nullable fields have proper union types and defaults
4. Use namespace `com.ecommerce.catalog`

---

## Exercise 1.3: Clickstream Event Schema

Design an Avro schema for a **Clickstream Event** that captures user behavior on a website:

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| event_id | string | Yes | UUID |
| session_id | string | Yes | |
| user_id | string | No | Nullable (anonymous users) |
| event_type | enum | Yes | PAGE_VIEW, CLICK, SCROLL, FORM_SUBMIT, ADD_TO_CART, PURCHASE |
| page_url | string | Yes | |
| referrer_url | string | No | Nullable |
| user_agent | string | Yes | |
| ip_address | string | Yes | |
| geo_location | record | No | Nullable; contains latitude (double), longitude (double), country (string), city (string nullable) |
| custom_properties | map of strings | Yes | Arbitrary key-value pairs |
| timestamp | long (timestamp-millis) | Yes | |

**Tasks:**
1. Write the complete Avro schema with namespace `com.analytics.clickstream`
2. The `geo_location` record must be nullable AND have a nullable `city` field inside it
3. Use `map` type for `custom_properties`
4. Add `doc` strings to document the schema purpose and at least 5 fields

---

## Validation

After completing each exercise, validate your schemas by:

1. Checking they are valid JSON
2. Registering them with Schema Registry using `schema_registry_client.py`
3. Producing a test message with your schema using a modified `avro_producer.py`

```bash
# Validate JSON syntax
python -c "import json; json.load(open('your_schema.json'))"

# Register with Schema Registry
python src/schema_registry_client.py register my-subject your_schema.json
```
