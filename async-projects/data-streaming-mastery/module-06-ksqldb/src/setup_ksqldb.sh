#!/usr/bin/env bash
# =============================================================================
# setup_ksqldb.sh
# Wait for ksqlDB to be ready, then execute all SQL files in order via the
# ksqlDB REST API.
#
# Usage:
#   bash src/setup_ksqldb.sh
#
# Prerequisites:
#   - docker compose up -d  (ksqlDB and Kafka must be running)
#   - curl must be installed
# =============================================================================

set -e

KSQLDB_URL="${KSQLDB_URL:-http://localhost:8088}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUERIES_DIR="$(cd "${SCRIPT_DIR}/../queries" && pwd)"

# Maximum wait time for ksqlDB (seconds)
MAX_WAIT=120

# ---------------------------------------------------------------------------
# Helper: colored output
# ---------------------------------------------------------------------------
info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
ok()    { echo -e "\033[1;32m[OK]\033[0m    $*"; }
warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
fail()  { echo -e "\033[1;31m[FAIL]\033[0m  $*"; exit 1; }

# ---------------------------------------------------------------------------
# Wait for ksqlDB to be ready
# ---------------------------------------------------------------------------
wait_for_ksqldb() {
    info "Waiting for ksqlDB at ${KSQLDB_URL} (timeout: ${MAX_WAIT}s)..."

    local elapsed=0
    while [ $elapsed -lt $MAX_WAIT ]; do
        if curl -sf "${KSQLDB_URL}/info" > /dev/null 2>&1; then
            ok "ksqlDB is ready."
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
        echo -n "."
    done

    echo ""
    fail "ksqlDB did not become ready within ${MAX_WAIT} seconds."
}

# ---------------------------------------------------------------------------
# Execute a single SQL file against the ksqlDB REST API
#
# The function reads the file, strips comment-only lines and blank lines,
# then splits on semicolons to submit each statement individually.
# ---------------------------------------------------------------------------
execute_sql_file() {
    local filepath="$1"
    local filename
    filename="$(basename "$filepath")"

    info "Executing ${filename}..."

    # Read the file and filter out full-line comments and empty lines
    local sql_content
    sql_content=$(sed '/^[[:space:]]*--/d; /^[[:space:]]*$/d' "$filepath")

    # Split by semicolons and execute each non-empty statement
    local statement=""
    local stmt_count=0

    while IFS= read -r line; do
        statement="${statement} ${line}"

        # Check if the line ends with a semicolon (statement terminator)
        if echo "$line" | grep -q ';[[:space:]]*$'; then
            # Clean up the statement
            statement=$(echo "$statement" | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//')

            if [ -n "$statement" ]; then
                # Submit to ksqlDB REST API
                local response
                response=$(curl -sf -X POST "${KSQLDB_URL}/ksql" \
                    -H "Content-Type: application/vnd.ksql.v1+json; charset=utf-8" \
                    -d "$(printf '{"ksql": "%s", "streamsProperties": {"ksql.streams.auto.offset.reset": "earliest"}}' \
                        "$(echo "$statement" | tr '\n' ' ' | sed 's/"/\\"/g')")" \
                    2>&1) || true

                stmt_count=$((stmt_count + 1))

                # Check for errors in response
                if echo "$response" | grep -qi '"@type":"currentStatus"'; then
                    ok "  Statement ${stmt_count}: success"
                elif echo "$response" | grep -qi '"@type":"sourceDescription"'; then
                    ok "  Statement ${stmt_count}: success (describe)"
                elif echo "$response" | grep -qi 'already exists'; then
                    warn "  Statement ${stmt_count}: already exists (skipped)"
                elif echo "$response" | grep -qi 'error'; then
                    warn "  Statement ${stmt_count}: $(echo "$response" | head -c 200)"
                else
                    ok "  Statement ${stmt_count}: submitted"
                fi
            fi
            statement=""
        fi
    done <<< "$sql_content"

    ok "Finished ${filename} (${stmt_count} statements)."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    echo "============================================================"
    echo "  ksqlDB Setup -- Module 6"
    echo "============================================================"
    echo ""

    # Step 1: Wait for ksqlDB
    wait_for_ksqldb
    echo ""

    # Step 2: Execute SQL files in order
    # Only execute DDL files (01, 02) and materialized views (06).
    # Files 03-05 contain interactive push queries (not persistent).
    local ddl_files=(
        "${QUERIES_DIR}/01-create-streams.sql"
        "${QUERIES_DIR}/02-create-tables.sql"
        "${QUERIES_DIR}/06-materialized-views.sql"
    )

    for sql_file in "${ddl_files[@]}"; do
        if [ -f "$sql_file" ]; then
            execute_sql_file "$sql_file"
            echo ""
            # Brief pause between files to let ksqlDB process
            sleep 2
        else
            warn "File not found: ${sql_file}"
        fi
    done

    echo "============================================================"
    ok "Setup complete."
    echo ""
    info "Next steps:"
    echo "  1. Ensure seed_topics.py is producing data:"
    echo "     python src/seed_topics.py"
    echo ""
    echo "  2. Open the ksqlDB CLI:"
    echo "     docker exec -it ksqldb-cli ksql http://ksqldb-server:8088"
    echo ""
    echo "  3. Try interactive queries from queries/03-aggregations.sql"
    echo "============================================================"
}

main "$@"
