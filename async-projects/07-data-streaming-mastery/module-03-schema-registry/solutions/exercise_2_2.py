#!/usr/bin/env python3
"""
Solution: Exercise 2.2 - Breaking Changes Analysis

Attempts to register various schema changes against a V1 schema and
captures Schema Registry compatibility errors. Demonstrates what
breaks BACKWARD and FORWARD compatibility.

Usage:
    python exercise_2_2.py

Prerequisites:
    - Kafka broker running on localhost:9092
    - Schema Registry running on localhost:8081
"""

import json

import requests
from confluent_kafka import Producer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.serialization import (
    MessageField,
    SerializationContext,
    StringSerializer,
)

SCHEMA_REGISTRY_URL = "http://localhost:8081"
BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "user-profiles-breaking"

HEADERS = {"Content-Type": "application/vnd.schemaregistry.v1+json"}

# ---------------------------------------------------------------------------
# V1 Schema (baseline)
# ---------------------------------------------------------------------------

USER_PROFILE_V1 = {
    "type": "record",
    "name": "UserProfile",
    "namespace": "com.example.users",
    "fields": [
        {"name": "user_id", "type": "string"},
        {"name": "email", "type": "string"},
        {"name": "name", "type": "string"},
        {"name": "signup_date", "type": "long"},
    ],
}

# ---------------------------------------------------------------------------
# Breaking changes to test
# ---------------------------------------------------------------------------

CHANGE_A = {
    "label": "Change A: Rename field (name -> full_name)",
    "schema": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "full_name", "type": "string"},
            {"name": "signup_date", "type": "long"},
        ],
    },
    "breaks_backward": True,
    "breaks_forward": True,
    "reason_backward": "Renaming 'name' to 'full_name' without aliases means "
                       "the new schema cannot find the 'name' field in old data "
                       "(treated as removing 'name' without default and adding 'full_name' without default).",
    "reason_forward": "Old schema cannot find 'full_name' field in new data; "
                      "'name' is missing from new data and has no default.",
    "fix": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "full_name", "type": "string", "aliases": ["name"]},
            {"name": "signup_date", "type": "long"},
        ],
    },
    "fix_description": "Use aliases to map old field name 'name' to new field 'full_name'.",
}

CHANGE_B = {
    "label": "Change B: Change field type (signup_date: long -> string)",
    "schema": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "signup_date", "type": "string"},
        ],
    },
    "breaks_backward": True,
    "breaks_forward": True,
    "reason_backward": "Changing 'signup_date' from long to string is an incompatible type change. "
                       "The new consumer cannot deserialize old long data as a string.",
    "reason_forward": "Old consumer expects long but gets string data. Incompatible.",
    "fix": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "signup_date", "type": "long"},
            {"name": "signup_date_str", "type": ["null", "string"], "default": None},
        ],
    },
    "fix_description": "Keep the original field and add a new field with the desired type. "
                       "Migrate consumers to use the new field over time.",
}

CHANGE_C = {
    "label": "Change C: Add required field (country without default)",
    "schema": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "signup_date", "type": "long"},
            {"name": "country", "type": "string"},
        ],
    },
    "breaks_backward": True,
    "breaks_forward": False,
    "reason_backward": "New schema has 'country' without a default. When reading V1 data "
                       "(which lacks 'country'), the deserializer has no default to fill in.",
    "reason_forward": "Old schema simply ignores the extra 'country' field in new data. "
                      "Forward compatible because old readers can skip unknown fields.",
    "fix": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "signup_date", "type": "long"},
            {"name": "country", "type": "string", "default": "unknown"},
        ],
    },
    "fix_description": "Add a default value so old data gets 'unknown' for country.",
}

CHANGE_D = {
    "label": "Change D: Remove field (name)",
    "schema": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "signup_date", "type": "long"},
        ],
    },
    "breaks_backward": False,
    "breaks_forward": True,
    "reason_backward": "New schema omits 'name'. When reading old data, the new reader "
                       "simply skips the 'name' field. Backward compatible.",
    "reason_forward": "Old schema expects 'name' but it's absent from new data, "
                      "and 'name' has no default in V1. Old consumer fails.",
    "fix": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": "string", "default": ""},
            {"name": "signup_date", "type": "long"},
        ],
    },
    "fix_description": "Before removing 'name', first add a default to 'name' in an intermediate "
                       "version. Then in a later version you can remove it safely for FULL compatibility.",
}

CHANGE_E = {
    "label": "Change E: Make field nullable (email: string -> ['null','string'])",
    "schema": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": ["null", "string"], "default": None},
            {"name": "name", "type": "string"},
            {"name": "signup_date", "type": "long"},
        ],
    },
    "breaks_backward": False,
    "breaks_forward": True,
    "reason_backward": "New schema reads email as union. Old string data is promoted to the "
                       "string branch of the union. Backward compatible.",
    "reason_forward": "Old schema expects plain string for email. If new producer sends null "
                      "for email, old consumer cannot handle it. Also the type change from "
                      "string to union is technically forward-incompatible.",
    "fix": {
        "type": "record",
        "name": "UserProfile",
        "namespace": "com.example.users",
        "fields": [
            {"name": "user_id", "type": "string"},
            {"name": "email", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "signup_date", "type": "long"},
            {"name": "email_v2", "type": ["null", "string"], "default": None},
        ],
    },
    "fix_description": "If you need FULL compatibility, add a new nullable field instead of "
                       "changing the original. For BACKWARD-only, the original change is fine.",
}

ALL_CHANGES = [CHANGE_A, CHANGE_B, CHANGE_C, CHANGE_D, CHANGE_E]


def register_v1():
    """Register the V1 schema to establish a baseline.

    Returns:
        int: The schema ID, or -1 on error.
    """
    subject = f"{TOPIC}-value"
    # First produce a message to auto-register
    sr_client = SchemaRegistryClient({"url": SCHEMA_REGISTRY_URL})
    serializer = AvroSerializer(
        schema_registry_client=sr_client,
        schema_str=json.dumps(USER_PROFILE_V1),
        to_dict=lambda o, c: o,
    )
    string_serializer = StringSerializer("utf_8")
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS})

    event = {"user_id": "test-1", "email": "test@example.com", "name": "Test", "signup_date": 1000}
    producer.produce(
        topic=TOPIC,
        key=string_serializer(event["user_id"], SerializationContext(TOPIC, MessageField.KEY)),
        value=serializer(event, SerializationContext(TOPIC, MessageField.VALUE)),
    )
    producer.flush(timeout=10)
    print(f"  V1 schema registered under subject '{subject}'.")


def check_compat(schema_dict: dict, mode: str = "BACKWARD") -> tuple:
    """Check compatibility of a schema against the latest version.

    Args:
        schema_dict: The schema to check.
        mode: Compatibility mode to test under.

    Returns:
        tuple: (is_compatible: bool, error_message: str)
    """
    subject = f"{TOPIC}-value"

    # Temporarily set compatibility mode
    requests.put(
        f"{SCHEMA_REGISTRY_URL}/config/{subject}",
        json={"compatibility": mode},
        headers=HEADERS,
    )

    url = f"{SCHEMA_REGISTRY_URL}/compatibility/subjects/{subject}/versions/latest"
    payload = {"schema": json.dumps(schema_dict)}
    resp = requests.post(url, json=payload, headers=HEADERS)

    if resp.status_code == 200:
        result = resp.json()
        is_compat = result.get("is_compatible", False)
        messages = result.get("messages", [])
        return is_compat, "; ".join(messages) if messages else ""
    return False, resp.text


def main():
    """Analyze each breaking change against BACKWARD and FORWARD compatibility."""
    print("=" * 70)
    print("  Exercise 2.2: Breaking Changes Analysis")
    print("=" * 70)

    # Register V1 baseline
    print("\n[Setup] Registering V1 baseline schema...")
    register_v1()

    for i, change in enumerate(ALL_CHANGES, 1):
        print(f"\n{'=' * 70}")
        print(f"  {change['label']}")
        print(f"{'=' * 70}")

        # Check BACKWARD
        compat_bw, err_bw = check_compat(change["schema"], "BACKWARD")
        print(f"\n  BACKWARD compatible: {compat_bw}")
        print(f"  Expected:           {not change['breaks_backward']}")
        if err_bw:
            print(f"  Registry message:   {err_bw[:200]}")
        print(f"  Explanation:        {change['reason_backward']}")

        # Check FORWARD
        compat_fw, err_fw = check_compat(change["schema"], "FORWARD")
        print(f"\n  FORWARD compatible:  {compat_fw}")
        print(f"  Expected:            {not change['breaks_forward']}")
        if err_fw:
            print(f"  Registry message:    {err_fw[:200]}")
        print(f"  Explanation:         {change['reason_forward']}")

        # Show fix
        print(f"\n  Backward-compatible fix: {change['fix_description']}")

    # Reset to BACKWARD
    subject = f"{TOPIC}-value"
    requests.put(
        f"{SCHEMA_REGISTRY_URL}/config/{subject}",
        json={"compatibility": "BACKWARD"},
        headers=HEADERS,
    )

    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print(f"{'=' * 70}")
    print("  A (rename):     Breaks BACKWARD + FORWARD -> Use aliases")
    print("  B (type change):Breaks BACKWARD + FORWARD -> Add new field instead")
    print("  C (required):   Breaks BACKWARD only      -> Add default value")
    print("  D (remove):     Breaks FORWARD only        -> Add default first")
    print("  E (nullable):   Breaks FORWARD only        -> Add new nullable field")
    print()


if __name__ == "__main__":
    main()
