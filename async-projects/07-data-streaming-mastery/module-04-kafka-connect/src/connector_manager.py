"""
Kafka Connect Connector Manager

A Python utility for managing Kafka Connect connectors via the REST API.
Supports deploying, monitoring, pausing, resuming, and deleting connectors.

Usage:
    python connector_manager.py --action deploy --config ../config/jdbc-source-connector.json
    python connector_manager.py --action status --name jdbc-source-connector
    python connector_manager.py --action list
    python connector_manager.py --action delete --name jdbc-source-connector
"""

import argparse
import json
import sys
import time
from typing import Any, Optional

import requests


class ConnectorManager:
    """Manages Kafka Connect connectors through the REST API."""

    def __init__(self, connect_url: str = "http://localhost:8083"):
        """
        Initialize the ConnectorManager.

        Args:
            connect_url: Base URL of the Kafka Connect REST API.
        """
        self.connect_url = connect_url.rstrip("/")
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def _request(self, method: str, path: str, data: Optional[dict] = None) -> requests.Response:
        """
        Send an HTTP request to the Connect REST API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            path: API path (e.g., /connectors).
            data: Optional JSON payload.

        Returns:
            The HTTP response object.

        Raises:
            requests.exceptions.ConnectionError: If the Connect worker is unreachable.
        """
        url = f"{self.connect_url}{path}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                timeout=30,
            )
            return response
        except requests.exceptions.ConnectionError:
            print(f"ERROR: Cannot connect to Kafka Connect at {self.connect_url}")
            print("Make sure the Connect worker is running: docker-compose up -d")
            sys.exit(1)

    def wait_for_connect(self, timeout: int = 120, interval: int = 5) -> bool:
        """
        Wait for Kafka Connect to become available.

        Args:
            timeout: Maximum seconds to wait.
            interval: Seconds between retry attempts.

        Returns:
            True if Connect is available, False if timeout reached.
        """
        print(f"Waiting for Kafka Connect at {self.connect_url} ...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.connect_url}/", timeout=5)
                if resp.status_code == 200:
                    print("Kafka Connect is ready.")
                    return True
            except requests.exceptions.ConnectionError:
                pass
            print(f"  Not ready yet, retrying in {interval}s ...")
            time.sleep(interval)
        print(f"ERROR: Kafka Connect not available after {timeout}s")
        return False

    def list_connectors(self) -> list[str]:
        """
        List all deployed connectors.

        Returns:
            A list of connector names.
        """
        resp = self._request("GET", "/connectors")
        if resp.status_code == 200:
            connectors = resp.json()
            print(f"Deployed connectors ({len(connectors)}):")
            for name in connectors:
                print(f"  - {name}")
            return connectors
        print(f"ERROR: Failed to list connectors (HTTP {resp.status_code})")
        return []

    def deploy_connector(self, config: dict[str, Any]) -> bool:
        """
        Deploy a new connector or update an existing one.

        Args:
            config: Full connector configuration with 'name' and 'config' keys.

        Returns:
            True if deployment succeeded.
        """
        name = config.get("name", "unknown")
        print(f"Deploying connector: {name}")

        # Check if connector already exists
        check = self._request("GET", f"/connectors/{name}")
        if check.status_code == 200:
            print(f"  Connector '{name}' already exists. Updating configuration ...")
            resp = self._request("PUT", f"/connectors/{name}/config", config["config"])
        else:
            resp = self._request("POST", "/connectors", config)

        if resp.status_code in (200, 201):
            print(f"  Connector '{name}' deployed successfully.")
            return True
        else:
            print(f"  ERROR: Deployment failed (HTTP {resp.status_code})")
            print(f"  Response: {resp.text}")
            return False

    def get_status(self, name: str) -> Optional[dict]:
        """
        Get the status of a connector and its tasks.

        Args:
            name: Connector name.

        Returns:
            Status dictionary or None if not found.
        """
        resp = self._request("GET", f"/connectors/{name}/status")
        if resp.status_code == 200:
            status = resp.json()
            connector_state = status["connector"]["state"]
            print(f"Connector '{name}': {connector_state}")
            for task in status.get("tasks", []):
                task_state = task["state"]
                task_id = task["id"]
                print(f"  Task {task_id}: {task_state}")
                if task_state == "FAILED" and "trace" in task:
                    # Print first 3 lines of the stack trace
                    trace_lines = task["trace"].strip().split("\n")[:3]
                    for line in trace_lines:
                        print(f"    {line}")
            return status
        elif resp.status_code == 404:
            print(f"Connector '{name}' not found.")
        else:
            print(f"ERROR: Failed to get status (HTTP {resp.status_code})")
        return None

    def delete_connector(self, name: str) -> bool:
        """
        Delete a connector.

        Args:
            name: Connector name to delete.

        Returns:
            True if deletion succeeded.
        """
        print(f"Deleting connector: {name}")
        resp = self._request("DELETE", f"/connectors/{name}")
        if resp.status_code == 204:
            print(f"  Connector '{name}' deleted successfully.")
            return True
        elif resp.status_code == 404:
            print(f"  Connector '{name}' not found (already deleted?).")
            return True
        else:
            print(f"  ERROR: Deletion failed (HTTP {resp.status_code})")
            return False

    def pause_connector(self, name: str) -> bool:
        """
        Pause a running connector.

        Args:
            name: Connector name.

        Returns:
            True if the pause request succeeded.
        """
        print(f"Pausing connector: {name}")
        resp = self._request("PUT", f"/connectors/{name}/pause")
        if resp.status_code == 202:
            print(f"  Connector '{name}' paused.")
            return True
        print(f"  ERROR: Pause failed (HTTP {resp.status_code})")
        return False

    def resume_connector(self, name: str) -> bool:
        """
        Resume a paused connector.

        Args:
            name: Connector name.

        Returns:
            True if the resume request succeeded.
        """
        print(f"Resuming connector: {name}")
        resp = self._request("PUT", f"/connectors/{name}/resume")
        if resp.status_code == 202:
            print(f"  Connector '{name}' resumed.")
            return True
        print(f"  ERROR: Resume failed (HTTP {resp.status_code})")
        return False

    def restart_connector(self, name: str) -> bool:
        """
        Restart a connector and its tasks.

        Args:
            name: Connector name.

        Returns:
            True if the restart request succeeded.
        """
        print(f"Restarting connector: {name}")
        resp = self._request("POST", f"/connectors/{name}/restart")
        if resp.status_code in (200, 204):
            print(f"  Connector '{name}' restarted.")
            return True
        print(f"  ERROR: Restart failed (HTTP {resp.status_code})")
        return False

    def list_plugins(self) -> list[dict]:
        """
        List all installed connector plugins.

        Returns:
            A list of plugin info dictionaries.
        """
        resp = self._request("GET", "/connector-plugins")
        if resp.status_code == 200:
            plugins = resp.json()
            print(f"Installed plugins ({len(plugins)}):")
            for plugin in plugins:
                print(f"  - {plugin['class']}")
            return plugins
        print(f"ERROR: Failed to list plugins (HTTP {resp.status_code})")
        return []

    def deploy_from_file(self, config_path: str) -> bool:
        """
        Deploy a connector from a JSON configuration file.

        Args:
            config_path: Path to the JSON configuration file.

        Returns:
            True if deployment succeeded.
        """
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"ERROR: Config file not found: {config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {config_path}: {e}")
            return False

        return self.deploy_connector(config)

    def wait_for_running(self, name: str, timeout: int = 60, interval: int = 5) -> bool:
        """
        Wait until a connector and all its tasks reach RUNNING state.

        Args:
            name: Connector name.
            timeout: Maximum seconds to wait.
            interval: Seconds between status checks.

        Returns:
            True if all components are RUNNING within the timeout.
        """
        print(f"Waiting for connector '{name}' to reach RUNNING state ...")
        start = time.time()
        while time.time() - start < timeout:
            status = self._request("GET", f"/connectors/{name}/status")
            if status.status_code == 200:
                data = status.json()
                conn_state = data["connector"]["state"]
                tasks = data.get("tasks", [])
                task_states = [t["state"] for t in tasks]

                if conn_state == "RUNNING" and all(s == "RUNNING" for s in task_states):
                    print(f"  Connector '{name}' is RUNNING with {len(tasks)} task(s).")
                    return True

                if conn_state == "FAILED" or "FAILED" in task_states:
                    print(f"  Connector '{name}' has FAILED.")
                    self.get_status(name)
                    return False

            time.sleep(interval)

        print(f"  Timeout: connector '{name}' did not reach RUNNING in {timeout}s.")
        self.get_status(name)
        return False


def main():
    """Main entry point for the connector manager CLI."""
    parser = argparse.ArgumentParser(
        description="Kafka Connect Connector Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python connector_manager.py --action list
  python connector_manager.py --action deploy --config ../config/jdbc-source-connector.json
  python connector_manager.py --action status --name jdbc-source-connector
  python connector_manager.py --action pause --name jdbc-source-connector
  python connector_manager.py --action resume --name jdbc-source-connector
  python connector_manager.py --action restart --name jdbc-source-connector
  python connector_manager.py --action delete --name jdbc-source-connector
  python connector_manager.py --action plugins
        """,
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["list", "deploy", "status", "delete", "pause", "resume", "restart", "plugins"],
        help="Action to perform.",
    )
    parser.add_argument("--name", help="Connector name (required for status/delete/pause/resume/restart).")
    parser.add_argument("--config", help="Path to connector JSON config file (required for deploy).")
    parser.add_argument("--url", default="http://localhost:8083", help="Kafka Connect REST API URL.")
    parser.add_argument("--wait", action="store_true", help="Wait for connector to reach RUNNING state after deploy.")

    args = parser.parse_args()
    manager = ConnectorManager(connect_url=args.url)

    if args.action == "list":
        manager.list_connectors()

    elif args.action == "deploy":
        if not args.config:
            parser.error("--config is required for deploy action")
        if not manager.wait_for_connect(timeout=60):
            sys.exit(1)
        success = manager.deploy_from_file(args.config)
        if success and args.wait:
            # Extract connector name from config
            with open(args.config, "r") as f:
                config = json.load(f)
            manager.wait_for_running(config["name"])
        if not success:
            sys.exit(1)

    elif args.action == "status":
        if not args.name:
            parser.error("--name is required for status action")
        manager.get_status(args.name)

    elif args.action == "delete":
        if not args.name:
            parser.error("--name is required for delete action")
        if not manager.delete_connector(args.name):
            sys.exit(1)

    elif args.action == "pause":
        if not args.name:
            parser.error("--name is required for pause action")
        manager.pause_connector(args.name)

    elif args.action == "resume":
        if not args.name:
            parser.error("--name is required for resume action")
        manager.resume_connector(args.name)

    elif args.action == "restart":
        if not args.name:
            parser.error("--name is required for restart action")
        manager.restart_connector(args.name)

    elif args.action == "plugins":
        manager.list_plugins()


if __name__ == "__main__":
    main()
