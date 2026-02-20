# Module 3 Quiz: Schema Registry & Serialization

Test your understanding of Schema Registry concepts, Avro, schema evolution,
and compatibility modes. Choose the best answer for each question.

---

### Question 1

What is the primary purpose of the Schema Registry in a Kafka ecosystem?

A) To compress messages for smaller storage
B) To centralize schema management and enforce compatibility rules
C) To replace Zookeeper for broker coordination
D) To provide a UI for monitoring Kafka topics

---

### Question 2

What is the wire format prefix added to every message serialized through Schema Registry?

A) A 4-byte message length followed by the payload
B) A JSON header with the schema definition
C) A magic byte (0x00) followed by a 4-byte schema ID
D) A 2-byte version number followed by a 2-byte schema ID

---

### Question 3

Which Avro type should you use to represent a field that may or may not have a value?

A) An `optional` type annotation
B) A `union` with `null` and the desired type, e.g., `["null", "string"]`
C) A `nullable` modifier on the type
D) A `bytes` type with length 0 representing null

---

### Question 4

You have a schema in production and want to add a new field. Which approach is BACKWARD compatible?

A) Add the field with no default value
B) Add the field with a default value
C) Remove an existing field and add the new one
D) Change the type of an existing field to a union that includes the new type

---

### Question 5

What does BACKWARD compatibility guarantee?

A) Old producers can write data that new consumers can read
B) New consumers can read data written by old producers
C) Any schema change is allowed without restrictions
D) Old consumers can read data written by new producers

---

### Question 6

Under the default BACKWARD compatibility mode, which change will be REJECTED by Schema Registry?

A) Adding a new field with `"default": "unknown"`
B) Adding a new nullable field with `"default": null`
C) Adding a new field WITHOUT a default value
D) Removing a field that previously had a default value

---

### Question 7

Which serialization format produces the SMALLEST message size?

A) JSON Schema (because field names are human-readable)
B) Avro or Protobuf (both use compact binary encoding)
C) Plain JSON (because it has no schema overhead)
D) XML (because it supports compression attributes)

---

### Question 8

What is the default subject naming strategy in Schema Registry?

A) RecordNameStrategy -- subject = fully qualified record name
B) TopicNameStrategy -- subject = `{topic}-key` or `{topic}-value`
C) TopicRecordNameStrategy -- subject = `{topic}-{record name}`
D) SchemaNameStrategy -- subject = schema name + version

---

### Question 9

You need to rename a field from `email` to `customer_email` while maintaining backward compatibility. What is the correct approach?

A) Simply rename the field in the new schema version
B) Add `customer_email` with an `aliases` field containing `["email"]`
C) Delete the old field and add the new one with a default
D) Change the field type to a union of the old and new names

---

### Question 10

Your topic has messages written with schema V1, V2, and V3 over the past year. You set compatibility to `BACKWARD_TRANSITIVE`. What does this guarantee?

A) V3 consumer can only read V2 data
B) V3 consumer can read data from V1, V2, and V3
C) V1 consumer can read V3 data
D) All versions can read all other versions

---

## Answers

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | **B** | Schema Registry centralizes schema storage and enforces compatibility rules between schema versions, preventing breaking changes. |
| 2 | **C** | The wire format uses a magic byte (0x00) followed by a 4-byte schema ID, then the serialized payload. The consumer uses the schema ID to fetch the schema from the registry. |
| 3 | **B** | Avro uses unions to represent nullable fields. The convention is `["null", "string"]` with `"default": null`, where `null` is listed first. |
| 4 | **B** | Adding a field with a default value is backward compatible. When the new consumer reads old data that lacks the field, it uses the default value. |
| 5 | **B** | BACKWARD compatibility means the new (reader) schema can read data written with the old (writer) schema. The consumer is upgraded before the producer. |
| 6 | **C** | A new field without a default breaks backward compatibility. When the new consumer reads old data, it has no value and no default for the new field, causing deserialization to fail. |
| 7 | **B** | Avro and Protobuf both use compact binary encoding that omits field names from the payload. JSON Schema includes field names in every message, making it larger. |
| 8 | **B** | TopicNameStrategy is the default. It creates subjects named `{topic}-key` and `{topic}-value`. This means each topic has one key schema and one value schema. |
| 9 | **B** | The `aliases` field allows old field names to map to the new name. When reading old data with field `email`, the alias tells the deserializer to map it to `customer_email`. |
| 10 | **B** | BACKWARD_TRANSITIVE means the latest schema can read data from ALL previous versions (not just the immediately prior one). V3 consumer can read V1, V2, and V3 data. |

### Scoring

- **9-10 correct:** Excellent -- you have a strong grasp of Schema Registry concepts.
- **7-8 correct:** Good -- review the topics you missed before moving on.
- **5-6 correct:** Fair -- re-read the relevant README sections and try the exercises.
- **Below 5:** Review the entire module and run the demo scripts hands-on.
