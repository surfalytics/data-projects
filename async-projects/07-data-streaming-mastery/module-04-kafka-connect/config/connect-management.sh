#!/usr/bin/env bash
set -e

# ============================================================================
# Kafka Connect Management Script
# Provides functions to manage connectors via the Kafka Connect REST API.
# ============================================================================

CONNECT_URL="${CONNECT_URL:-http://localhost:8083}"

# ----------------------------------------------------------------------------
# Helper: pretty-print JSON if jq is available, otherwise cat
# ----------------------------------------------------------------------------
pretty_print() {
    if command -v jq &>/dev/null; then
        jq .
    else
        cat
    fi
}

# ----------------------------------------------------------------------------
# List all connectors
# Usage: list_connectors
# ----------------------------------------------------------------------------
list_connectors() {
    echo "=== Listing all connectors ==="
    curl -s "${CONNECT_URL}/connectors" | pretty_print
    echo ""
}

# ----------------------------------------------------------------------------
# Create a connector from a JSON config file
# Usage: create_connector <path-to-json-file>
# ----------------------------------------------------------------------------
create_connector() {
    local config_file="$1"
    if [ -z "${config_file}" ]; then
        echo "ERROR: Usage: create_connector <path-to-json-file>"
        return 1
    fi
    if [ ! -f "${config_file}" ]; then
        echo "ERROR: Config file not found: ${config_file}"
        return 1
    fi
    echo "=== Creating connector from ${config_file} ==="
    curl -s -X POST "${CONNECT_URL}/connectors" \
        -H "Content-Type: application/json" \
        -d @"${config_file}" | pretty_print
    echo ""
}

# ----------------------------------------------------------------------------
# Get connector status
# Usage: get_connector_status <connector-name>
# ----------------------------------------------------------------------------
get_connector_status() {
    local name="$1"
    if [ -z "${name}" ]; then
        echo "ERROR: Usage: get_connector_status <connector-name>"
        return 1
    fi
    echo "=== Status for connector: ${name} ==="
    curl -s "${CONNECT_URL}/connectors/${name}/status" | pretty_print
    echo ""
}

# ----------------------------------------------------------------------------
# Get connector configuration
# Usage: get_connector_config <connector-name>
# ----------------------------------------------------------------------------
get_connector_config() {
    local name="$1"
    if [ -z "${name}" ]; then
        echo "ERROR: Usage: get_connector_config <connector-name>"
        return 1
    fi
    echo "=== Config for connector: ${name} ==="
    curl -s "${CONNECT_URL}/connectors/${name}/config" | pretty_print
    echo ""
}

# ----------------------------------------------------------------------------
# Delete a connector
# Usage: delete_connector <connector-name>
# ----------------------------------------------------------------------------
delete_connector() {
    local name="$1"
    if [ -z "${name}" ]; then
        echo "ERROR: Usage: delete_connector <connector-name>"
        return 1
    fi
    echo "=== Deleting connector: ${name} ==="
    curl -s -X DELETE "${CONNECT_URL}/connectors/${name}"
    echo ""
    echo "Connector '${name}' deleted."
}

# ----------------------------------------------------------------------------
# Pause a connector
# Usage: pause_connector <connector-name>
# ----------------------------------------------------------------------------
pause_connector() {
    local name="$1"
    if [ -z "${name}" ]; then
        echo "ERROR: Usage: pause_connector <connector-name>"
        return 1
    fi
    echo "=== Pausing connector: ${name} ==="
    curl -s -X PUT "${CONNECT_URL}/connectors/${name}/pause"
    echo ""
    echo "Connector '${name}' paused."
}

# ----------------------------------------------------------------------------
# Resume a connector
# Usage: resume_connector <connector-name>
# ----------------------------------------------------------------------------
resume_connector() {
    local name="$1"
    if [ -z "${name}" ]; then
        echo "ERROR: Usage: resume_connector <connector-name>"
        return 1
    fi
    echo "=== Resuming connector: ${name} ==="
    curl -s -X PUT "${CONNECT_URL}/connectors/${name}/resume"
    echo ""
    echo "Connector '${name}' resumed."
}

# ----------------------------------------------------------------------------
# Restart a connector
# Usage: restart_connector <connector-name>
# ----------------------------------------------------------------------------
restart_connector() {
    local name="$1"
    if [ -z "${name}" ]; then
        echo "ERROR: Usage: restart_connector <connector-name>"
        return 1
    fi
    echo "=== Restarting connector: ${name} ==="
    curl -s -X POST "${CONNECT_URL}/connectors/${name}/restart"
    echo ""
    echo "Connector '${name}' restarted."
}

# ----------------------------------------------------------------------------
# List installed connector plugins
# Usage: list_plugins
# ----------------------------------------------------------------------------
list_plugins() {
    echo "=== Installed connector plugins ==="
    curl -s "${CONNECT_URL}/connector-plugins" | pretty_print
    echo ""
}

# ----------------------------------------------------------------------------
# Get all connector statuses at once
# Usage: get_all_statuses
# ----------------------------------------------------------------------------
get_all_statuses() {
    echo "=== All connector statuses ==="
    local connectors
    connectors=$(curl -s "${CONNECT_URL}/connectors")
    if command -v jq &>/dev/null; then
        for name in $(echo "${connectors}" | jq -r '.[]'); do
            echo "--- ${name} ---"
            curl -s "${CONNECT_URL}/connectors/${name}/status" | jq .
        done
    else
        echo "Install jq for formatted output. Raw connector list:"
        echo "${connectors}"
    fi
    echo ""
}

# ----------------------------------------------------------------------------
# Main: run a function by name if script is called with arguments
# Usage: ./connect-management.sh <function-name> [args...]
# Example: ./connect-management.sh list_connectors
#          ./connect-management.sh create_connector ../config/file-source-connector.json
# ----------------------------------------------------------------------------
if [ $# -gt 0 ]; then
    func_name="$1"
    shift
    if declare -f "${func_name}" >/dev/null 2>&1; then
        "${func_name}" "$@"
    else
        echo "ERROR: Unknown function '${func_name}'"
        echo "Available functions:"
        echo "  list_connectors"
        echo "  create_connector <config-file>"
        echo "  get_connector_status <name>"
        echo "  get_connector_config <name>"
        echo "  delete_connector <name>"
        echo "  pause_connector <name>"
        echo "  resume_connector <name>"
        echo "  restart_connector <name>"
        echo "  list_plugins"
        echo "  get_all_statuses"
        exit 1
    fi
else
    echo "Kafka Connect Management Script"
    echo "================================"
    echo "Usage: $0 <function-name> [args...]"
    echo ""
    echo "Functions:"
    echo "  list_connectors                  - List all connectors"
    echo "  create_connector <config-file>   - Create connector from JSON file"
    echo "  get_connector_status <name>      - Get connector status"
    echo "  get_connector_config <name>      - Get connector configuration"
    echo "  delete_connector <name>          - Delete a connector"
    echo "  pause_connector <name>           - Pause a connector"
    echo "  resume_connector <name>          - Resume a paused connector"
    echo "  restart_connector <name>         - Restart a connector"
    echo "  list_plugins                     - List installed plugins"
    echo "  get_all_statuses                 - Get status of all connectors"
    echo ""
    echo "Environment: CONNECT_URL=${CONNECT_URL}"
fi
