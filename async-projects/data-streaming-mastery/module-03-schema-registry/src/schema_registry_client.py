#!/usr/bin/env python3
"""
Schema Registry REST API Client

A utility script for interacting with the Confluent Schema Registry REST API.
Provides functions to list subjects, get schemas, check compatibility,
and delete subjects. Useful for administration, debugging, and automation.

Usage:
    python schema_registry_client.py list-subjects
    python schema_registry_client.py get-schema <subject> [--version latest]
    python schema_registry_client.py get-versions <subject>
    python schema_registry_client.py check-compatibility <subject> <schema-file>
    python schema_registry_client.py get-config [--subject <subject>]
    python schema_registry_client.py set-config <level> [--subject <subject>]
    python schema_registry_client.py delete-subject <subject> [--permanent]
    python schema_registry_client.py get-schema-by-id <schema-id>

Prerequisites:
    - Schema Registry running on localhost:8081
    - pip install requests
"""

import argparse
import json
import sys

import requests

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------

DEFAULT_REGISTRY_URL = "http://localhost:8081"
HEADERS = {
    "Content-Type": "application/vnd.schemaregistry.v1+json",
    "Accept": "application/vnd.schemaregistry.v1+json",
}


class SchemaRegistryRESTClient:
    """A client for the Schema Registry REST API.

    Provides methods for all common Schema Registry operations including
    subject management, schema retrieval, compatibility checking, and
    configuration.

    Attributes:
        base_url: The base URL of the Schema Registry.
    """

    def __init__(self, base_url: str = DEFAULT_REGISTRY_URL):
        """Initialize the Schema Registry client.

        Args:
            base_url: The base URL of the Schema Registry (e.g., http://localhost:8081).
        """
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the Schema Registry.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API path (e.g., /subjects).
            **kwargs: Additional arguments passed to requests.

        Returns:
            requests.Response: The HTTP response.

        Raises:
            SystemExit: If the request fails with a non-success status.
        """
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", HEADERS)
        resp = requests.request(method, url, **kwargs)
        return resp

    # -------------------------------------------------------------------
    # Subjects
    # -------------------------------------------------------------------

    def list_subjects(self) -> list:
        """List all registered subjects in the Schema Registry.

        Returns:
            list: A list of subject name strings.
        """
        resp = self._request("GET", "/subjects")
        if resp.status_code == 200:
            return resp.json()
        print(f"Error listing subjects: {resp.status_code} - {resp.text}")
        return []

    def get_versions(self, subject: str) -> list:
        """Get all version numbers for a subject.

        Args:
            subject: The subject name (e.g., 'orders-avro-value').

        Returns:
            list: A list of integer version numbers.
        """
        resp = self._request("GET", f"/subjects/{subject}/versions")
        if resp.status_code == 200:
            return resp.json()
        print(f"Error getting versions for '{subject}': {resp.status_code} - {resp.text}")
        return []

    def get_schema(self, subject: str, version: str = "latest") -> dict:
        """Get a schema for a specific subject and version.

        Args:
            subject: The subject name.
            version: Version number or 'latest' (default: 'latest').

        Returns:
            dict: Schema metadata including id, version, and schema string.
        """
        resp = self._request("GET", f"/subjects/{subject}/versions/{version}")
        if resp.status_code == 200:
            data = resp.json()
            data["schema_parsed"] = json.loads(data["schema"])
            return data
        print(f"Error getting schema: {resp.status_code} - {resp.text}")
        return {}

    def get_schema_by_id(self, schema_id: int) -> dict:
        """Get a schema by its global ID.

        Args:
            schema_id: The global schema ID.

        Returns:
            dict: The schema definition.
        """
        resp = self._request("GET", f"/schemas/ids/{schema_id}")
        if resp.status_code == 200:
            data = resp.json()
            data["schema_parsed"] = json.loads(data["schema"])
            return data
        print(f"Error getting schema by ID {schema_id}: {resp.status_code} - {resp.text}")
        return {}

    def register_schema(self, subject: str, schema: dict, schema_type: str = "AVRO") -> int:
        """Register a new schema under a subject.

        Args:
            subject: The subject name.
            schema: The schema as a Python dictionary.
            schema_type: Schema type ('AVRO', 'PROTOBUF', 'JSON').

        Returns:
            int: The schema ID, or -1 on error.
        """
        payload = {"schema": json.dumps(schema)}
        if schema_type != "AVRO":
            payload["schemaType"] = schema_type
        resp = self._request("POST", f"/subjects/{subject}/versions", json=payload)
        if resp.status_code == 200:
            return resp.json()["id"]
        print(f"Error registering schema: {resp.status_code} - {resp.text}")
        return -1

    # -------------------------------------------------------------------
    # Compatibility
    # -------------------------------------------------------------------

    def check_compatibility(self, subject: str, schema: dict, version: str = "latest") -> dict:
        """Check if a schema is compatible with a specific version.

        Args:
            subject: The subject name.
            schema: The schema to check as a Python dictionary.
            version: Version to check against (default: 'latest').

        Returns:
            dict: Compatibility result with 'is_compatible' key.
        """
        payload = {"schema": json.dumps(schema)}
        resp = self._request(
            "POST",
            f"/compatibility/subjects/{subject}/versions/{version}",
            json=payload,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            return {"is_compatible": True, "note": "No existing schema to check against."}
        print(f"Error checking compatibility: {resp.status_code} - {resp.text}")
        return {"is_compatible": False, "error": resp.text}

    # -------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------

    def get_config(self, subject: str = None) -> dict:
        """Get the compatibility configuration.

        Args:
            subject: Optional subject name. If None, returns global config.

        Returns:
            dict: Configuration with 'compatibilityLevel' key.
        """
        path = f"/config/{subject}" if subject else "/config"
        resp = self._request("GET", path)
        if resp.status_code == 200:
            return resp.json()
        print(f"Error getting config: {resp.status_code} - {resp.text}")
        return {}

    def set_config(self, level: str, subject: str = None) -> dict:
        """Set the compatibility level.

        Args:
            level: Compatibility level (BACKWARD, FORWARD, FULL, NONE, etc.).
            subject: Optional subject name. If None, sets global config.

        Returns:
            dict: Updated configuration.
        """
        path = f"/config/{subject}" if subject else "/config"
        payload = {"compatibility": level}
        resp = self._request("PUT", path, json=payload)
        if resp.status_code == 200:
            return resp.json()
        print(f"Error setting config: {resp.status_code} - {resp.text}")
        return {}

    # -------------------------------------------------------------------
    # Deletion
    # -------------------------------------------------------------------

    def delete_subject(self, subject: str, permanent: bool = False) -> list:
        """Delete a subject and all its versions.

        Args:
            subject: The subject name to delete.
            permanent: If True, performs a hard delete (default: False for soft delete).

        Returns:
            list: List of deleted version numbers.
        """
        params = {"permanent": "true"} if permanent else {}
        resp = self._request("DELETE", f"/subjects/{subject}", params=params)
        if resp.status_code == 200:
            return resp.json()
        print(f"Error deleting subject '{subject}': {resp.status_code} - {resp.text}")
        return []


def print_json(data):
    """Pretty-print a Python object as JSON.

    Args:
        data: The object to print.
    """
    print(json.dumps(data, indent=2))


def main():
    """Main entry point. Parses CLI arguments and executes the requested command."""
    parser = argparse.ArgumentParser(
        description="Schema Registry REST API client for administration and debugging."
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_REGISTRY_URL,
        help=f"Schema Registry URL (default: {DEFAULT_REGISTRY_URL}).",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-subjects
    subparsers.add_parser("list-subjects", help="List all registered subjects.")

    # get-versions
    gv_parser = subparsers.add_parser("get-versions", help="Get all versions for a subject.")
    gv_parser.add_argument("subject", help="Subject name.")

    # get-schema
    gs_parser = subparsers.add_parser("get-schema", help="Get a schema by subject and version.")
    gs_parser.add_argument("subject", help="Subject name.")
    gs_parser.add_argument("--version", default="latest", help="Version number or 'latest'.")

    # get-schema-by-id
    gsi_parser = subparsers.add_parser("get-schema-by-id", help="Get a schema by global ID.")
    gsi_parser.add_argument("schema_id", type=int, help="Global schema ID.")

    # check-compatibility
    cc_parser = subparsers.add_parser("check-compatibility", help="Check schema compatibility.")
    cc_parser.add_argument("subject", help="Subject name.")
    cc_parser.add_argument("schema_file", help="Path to JSON file containing the schema.")
    cc_parser.add_argument("--version", default="latest", help="Version to check against.")

    # get-config
    gc_parser = subparsers.add_parser("get-config", help="Get compatibility configuration.")
    gc_parser.add_argument("--subject", default=None, help="Subject name (omit for global).")

    # set-config
    sc_parser = subparsers.add_parser("set-config", help="Set compatibility level.")
    sc_parser.add_argument(
        "level",
        choices=[
            "BACKWARD", "BACKWARD_TRANSITIVE",
            "FORWARD", "FORWARD_TRANSITIVE",
            "FULL", "FULL_TRANSITIVE",
            "NONE",
        ],
        help="Compatibility level.",
    )
    sc_parser.add_argument("--subject", default=None, help="Subject name (omit for global).")

    # delete-subject
    ds_parser = subparsers.add_parser("delete-subject", help="Delete a subject.")
    ds_parser.add_argument("subject", help="Subject name to delete.")
    ds_parser.add_argument(
        "--permanent",
        action="store_true",
        help="Perform a hard delete (cannot be undone).",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = SchemaRegistryRESTClient(base_url=args.url)

    if args.command == "list-subjects":
        subjects = client.list_subjects()
        print(f"Registered subjects ({len(subjects)}):")
        for s in sorted(subjects):
            print(f"  - {s}")

    elif args.command == "get-versions":
        versions = client.get_versions(args.subject)
        print(f"Versions for '{args.subject}': {versions}")

    elif args.command == "get-schema":
        schema = client.get_schema(args.subject, args.version)
        if schema:
            print(f"Subject: {schema.get('subject')}")
            print(f"Version: {schema.get('version')}")
            print(f"Schema ID: {schema.get('id')}")
            print(f"Schema Type: {schema.get('schemaType', 'AVRO')}")
            print("Schema:")
            print_json(schema.get("schema_parsed", {}))

    elif args.command == "get-schema-by-id":
        schema = client.get_schema_by_id(args.schema_id)
        if schema:
            print(f"Schema ID: {args.schema_id}")
            print("Schema:")
            print_json(schema.get("schema_parsed", {}))

    elif args.command == "check-compatibility":
        with open(args.schema_file, "r") as f:
            schema = json.load(f)
        result = client.check_compatibility(args.subject, schema, args.version)
        print_json(result)

    elif args.command == "get-config":
        config = client.get_config(args.subject)
        scope = f"subject '{args.subject}'" if args.subject else "global"
        print(f"Compatibility config ({scope}):")
        print_json(config)

    elif args.command == "set-config":
        result = client.set_config(args.level, args.subject)
        scope = f"subject '{args.subject}'" if args.subject else "global"
        print(f"Updated compatibility ({scope}):")
        print_json(result)

    elif args.command == "delete-subject":
        mode = "permanently" if args.permanent else "soft"
        confirm = input(f"Are you sure you want to {mode} delete '{args.subject}'? (yes/no): ")
        if confirm.lower() == "yes":
            deleted = client.delete_subject(args.subject, permanent=args.permanent)
            print(f"Deleted versions: {deleted}")
        else:
            print("Cancelled.")


if __name__ == "__main__":
    main()
