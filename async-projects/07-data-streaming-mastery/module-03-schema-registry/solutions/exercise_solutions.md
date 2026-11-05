# Solutions: Module 3 Exercises

## Exercise 1.1: Customer Profile Schema

### Schema Design

The key decisions in this schema:

1. **Nullable fields** (`phone`, `date_of_birth`): Use `["null", "type"]` unions with `null` as the first element and `default: null`. This ensures the field is optional.

2. **Logical types** (`date_of_birth`, `created_at`, `updated_at`): Avro stores dates as integers under the hood. `date` is days since epoch (int), `timestamp-millis` is milliseconds since epoch (long).

3. **Enum** (`membership_tier`): Fixed set of values. Adding new symbols later requires careful compatibility consideration.

4. **Array** (`interests`): The array can be empty, which is different from null. An empty array means "no interests specified" while null would mean "interests unknown."

### Running the Solution

```bash
python solutions/exercise_1_1.py
```

---

## Exercise 1.2: Product Catalog Schema

### Schema Design

Key decisions:

1. **Nested nullable record** (`dimensions`): The union `["null", {"type": "record", ...}]` allows the entire dimensions object to be null. This is common for optional structured data.

2. **Price in cents** (`price_cents`): Using `int` for cents avoids floating-point precision issues. Always store monetary values as integers in the smallest unit.

3. **Default values** (`currency: "USD"`, `in_stock: true`): These reduce the amount of data producers need to send for common cases.

### Running the Solution

```bash
python solutions/exercise_1_2.py
```

---

## Exercise 1.3: Clickstream Event Schema

### Schema Design

Key decisions:

1. **Nested nullable record with nullable fields inside**: `geo_location` is nullable (IP lookup may fail), AND `city` inside geo_location is also nullable (city may not be determinable). This is a two-level nullable pattern.

2. **Map type** (`custom_properties`): Maps are ideal for arbitrary key-value metadata that varies by event type. Keys are always strings in Avro.

3. **Enum for event types**: Restricts values to a known set, preventing typos and enabling downstream filtering.

4. **Documentation**: The `doc` fields serve as living documentation that travels with the schema.

### Running the Solution

```bash
python solutions/exercise_1_3.py
```

---

## Exercise 2.1: Backward-Compatible Evolution

### Why Each Field Is Backward Compatible

| Field | Type | Default | Why Compatible |
|-------|------|---------|---------------|
| `phone_number` | `["null", "string"]` | `null` | V1 data has no phone; consumer gets null |
| `account_status` | enum | `"ACTIVE"` | V1 data has no status; consumer gets ACTIVE |
| `last_login` | `["null", "long"]` | `null` | V1 data has no login time; consumer gets null |
| `preferences` | `["null", map]` | `null` | V1 data has no prefs; consumer gets null |

The rule is simple: **every new field must have a default value** so the consumer knows what to use when reading old data that lacks the field.

### Running the Solution

```bash
python solutions/exercise_2_1.py
```

---

## Exercise 2.2: Breaking Changes Analysis

### Summary Table

| Change | Description | Breaks BACKWARD | Breaks FORWARD | Fix |
|--------|-------------|:-:|:-:|-----|
| A | Rename field | Yes | Yes | Use `aliases` |
| B | Change type | Yes | Yes | Add new field |
| C | Add required field | Yes | No | Add default |
| D | Remove field | No | Yes | Add default first |
| E | Make nullable | No | Yes | Add new nullable field |

### Key Insight

- **BACKWARD** cares about: "Can the NEW consumer read OLD data?"
- **FORWARD** cares about: "Can the OLD consumer read NEW data?"
- **FULL** requires both directions to work.

### Running the Solution

```bash
python solutions/exercise_2_2.py
```

---

## Exercise 2.3: Multi-Version Consumer

### Transitive Compatibility

BACKWARD_TRANSITIVE means the latest schema can read data from ALL previous versions, not just the immediately prior one. This is critical for long-lived topics.

```
V3 consumer reads V1 data:
  - update_type -> "ADJUSTMENT" (default)
  - location_aisle -> null (default)
  - batch_id -> null (default)
  - expiry_date -> null (default)

V3 consumer reads V2 data:
  - batch_id -> null (default)
  - expiry_date -> null (default)
```

### Can V1 Consumer Read V3 Data?

With Avro schema resolution: **Yes, partially.** The V1 reader schema projects only the 4 fields it knows about (product_id, warehouse_id, quantity, timestamp). The extra V3 fields are skipped.

However, this requires the V1 consumer to use Avro's schema resolution mechanism (writer schema + reader schema). With raw byte deserialization, it would fail.

### Running the Solution

```bash
python solutions/exercise_2_3.py
```
