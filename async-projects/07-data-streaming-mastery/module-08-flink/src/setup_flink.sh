#!/usr/bin/env bash
# =============================================================================
# setup_flink.sh
# =============================================================================
# Starts the Flink module Docker Compose stack, waits for all services to be
# ready, and optionally submits the Flink SQL initialization statements.
#
# Usage:
#   ./setup_flink.sh          # Start stack and submit SQL
#   ./setup_flink.sh --no-sql # Start stack only, skip SQL submission
#   ./setup_flink.sh --down   # Tear down the stack
#
# Prerequisites:
#   - Docker with Compose v2 installed
#   - Run from the module-08-flink directory (or set MODULE_DIR)
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MODULE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${MODULE_DIR}/docker-compose.yml"
SQL_DIR="${MODULE_DIR}/sql"

FLINK_REST_URL="http://localhost:8081"
KAFKA_BOOTSTRAP="localhost:9092"
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="debezium"
MYSQL_PASSWORD="dbz"

MAX_RETRIES=60
RETRY_INTERVAL=5

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') $*"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') $*" >&2
}

log_success() {
    echo "[OK]   $(date '+%Y-%m-%d %H:%M:%S') $*"
}

# ---------------------------------------------------------------------------
# Wait for a service to be ready
# ---------------------------------------------------------------------------

wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local retries=0

    log_info "Waiting for ${service_name} to be ready..."

    while [ $retries -lt $MAX_RETRIES ]; do
        if eval "$check_command" > /dev/null 2>&1; then
            log_success "${service_name} is ready"
            return 0
        fi
        retries=$((retries + 1))
        log_info "  ${service_name} not ready yet (attempt ${retries}/${MAX_RETRIES})..."
        sleep $RETRY_INTERVAL
    done

    log_error "${service_name} failed to start after ${MAX_RETRIES} attempts"
    return 1
}

# ---------------------------------------------------------------------------
# Tear down
# ---------------------------------------------------------------------------

teardown() {
    log_info "Tearing down Flink stack..."
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
    log_success "Stack torn down"
}

# ---------------------------------------------------------------------------
# Start the stack
# ---------------------------------------------------------------------------

start_stack() {
    log_info "Starting Flink module Docker Compose stack..."
    log_info "Compose file: ${COMPOSE_FILE}"

    # Build the Flink image (downloads the connector JARs) and start services.
    # Kafka runs in KRaft mode. There is no ZooKeeper.
    log_info "Building Flink image and starting services..."
    docker compose -f "$COMPOSE_FILE" up -d --build kafka mysql jobmanager taskmanager kafka-ui

    # Wait for Kafka
    wait_for_service "Kafka" \
        "docker exec flink-kafka kafka-broker-api-versions --bootstrap-server kafka:29092"

    # Wait for MySQL
    wait_for_service "MySQL" \
        "docker exec flink-mysql mysqladmin ping -h localhost -uroot -pdebezium"

    # Wait for Flink JobManager REST API
    wait_for_service "Flink JobManager" \
        "curl -sf ${FLINK_REST_URL}/overview"

    # Wait for at least one TaskManager to register
    wait_for_service "Flink TaskManager" \
        "curl -sf ${FLINK_REST_URL}/taskmanagers | grep -q 'taskmanagers'"

    log_success "All services are up and running!"
    echo ""
    log_info "Service URLs:"
    log_info "  Flink Web UI:  ${FLINK_REST_URL}"
    log_info "  Kafka UI:      http://localhost:8080"
    log_info "  Kafka Broker:  ${KAFKA_BOOTSTRAP}"
    log_info "  MySQL:         ${MYSQL_HOST}:${MYSQL_PORT}"
    echo ""
}

# ---------------------------------------------------------------------------
# Create Kafka topics
# ---------------------------------------------------------------------------

create_kafka_topics() {
    log_info "Creating Kafka topics..."

    local topics=("orders" "customers" "products" "enriched-orders"
                  "order-metrics-per-minute" "revenue-by-category"
                  "high-value-orders" "word-counts" "words"
                  "tumbling-order-stats" "sliding-order-stats"
                  "session-order-stats" "revenue-per-hour"
                  "top-products" "order-status-summary")

    for topic in "${topics[@]}"; do
        docker exec flink-kafka kafka-topics \
            --bootstrap-server kafka:29092 \
            --create \
            --if-not-exists \
            --topic "$topic" \
            --partitions 3 \
            --replication-factor 1 \
            2>/dev/null || true
        log_info "  Topic: ${topic}"
    done

    log_success "All Kafka topics created"
}

# ---------------------------------------------------------------------------
# Submit SQL statements to Flink SQL Client
# ---------------------------------------------------------------------------

submit_sql() {
    log_info "Creating the Kafka tables with the Flink SQL client..."
    # The SQL client runs in the same image as the cluster, so it has the connector JARs.
    # Note: tables created with -f live only for that session. Use SOURCE in an
    # interactive session to keep them (see the README).
    docker compose -f "$COMPOSE_FILE" run --rm -T sql-client \
        /opt/flink/bin/sql-client.sh -f /opt/flink/sql-scripts/01-create-kafka-tables.sql \
        2>&1 || log_error "SQL submission failed"

    log_success "SQL submission complete"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

main() {
    case "${1:-}" in
        --down)
            teardown
            exit 0
            ;;
        --no-sql)
            start_stack
            create_kafka_topics
            log_success "Setup complete (SQL submission skipped)"
            exit 0
            ;;
        *)
            start_stack
            create_kafka_topics
            submit_sql
            echo ""
            log_success "=== Flink Module Setup Complete ==="
            echo ""
            log_info "Next steps:"
            log_info "  1. Run the seed data generator:"
            log_info "     python src/seed_data.py"
            log_info ""
            log_info "  2. Open the Flink SQL Client:"
            log_info "     docker compose run --rm sql-client"
            log_info ""
            log_info "  3. Try the exercises in the exercises/ directory"
            log_info ""
            log_info "  4. When finished, tear down:"
            log_info "     ./src/setup_flink.sh --down"
            exit 0
            ;;
    esac
}

main "$@"
