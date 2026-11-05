#!/usr/bin/env bash
# =============================================================
# Module 9 Capstone: Master Setup Script
# Starts the full real-time e-commerce analytics platform.
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SIMULATOR_PID=""

# ---------------------------------------------------------------------------
# Cleanup on exit
# ---------------------------------------------------------------------------
cleanup() {
    echo -e "\n${YELLOW}Caught interrupt signal. Cleaning up...${NC}"
    if [ -n "$SIMULATOR_PID" ] && kill -0 "$SIMULATOR_PID" 2>/dev/null; then
        echo "Stopping simulator (PID: $SIMULATOR_PID)..."
        kill "$SIMULATOR_PID" 2>/dev/null || true
    fi
    echo -e "${YELLOW}To fully tear down, run: ./teardown.sh${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ---------------------------------------------------------------------------
# Helper: wait for a service to be healthy
# ---------------------------------------------------------------------------
wait_for_service() {
    local name="$1"
    local url="$2"
    local max_attempts="${3:-30}"
    local interval="${4:-5}"

    echo -e "${BLUE}Waiting for ${name}...${NC}"
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "${GREEN}  ${name} is ready.${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "  Attempt $attempt/$max_attempts - ${name} not ready yet..."
        sleep "$interval"
    done

    echo -e "${RED}  ERROR: ${name} did not become ready after $max_attempts attempts.${NC}"
    return 1
}

wait_for_mysql() {
    echo -e "${BLUE}Waiting for MySQL...${NC}"
    local attempt=0
    local max_attempts=30
    while [ $attempt -lt $max_attempts ]; do
        if docker exec module-09-mysql mysqladmin ping -h localhost -uroot -pdebezium --silent 2>/dev/null; then
            echo -e "${GREEN}  MySQL is ready.${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "  Attempt $attempt/$max_attempts - MySQL not ready yet..."
        sleep 5
    done
    echo -e "${RED}  ERROR: MySQL did not become ready.${NC}"
    return 1
}

# ---------------------------------------------------------------------------
# Step 1: Start Docker Compose
# ---------------------------------------------------------------------------
echo -e "${GREEN}=============================================================${NC}"
echo -e "${GREEN} Module 9 Capstone: Real-Time E-Commerce Analytics Platform${NC}"
echo -e "${GREEN}=============================================================${NC}"
echo ""
echo -e "${BLUE}Step 1: Starting all services with Docker Compose...${NC}"
docker compose up -d

# ---------------------------------------------------------------------------
# Step 2: Wait for services to be healthy
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}Step 2: Waiting for services to become healthy...${NC}"
echo ""

wait_for_mysql
wait_for_service "Kafka" "http://localhost:9092" 30 5 || true
wait_for_service "Schema Registry" "http://localhost:8081/subjects" 30 5
wait_for_service "Kafka Connect" "http://localhost:8083/connectors" 40 5
wait_for_service "ksqlDB" "http://localhost:8088/info" 40 5
wait_for_service "PostgreSQL" "http://localhost:5432" 20 3 || true
wait_for_service "Grafana" "http://localhost:3000/api/health" 20 5

echo ""
echo -e "${GREEN}All services are running.${NC}"

# ---------------------------------------------------------------------------
# Step 3: Register Debezium MySQL source connector
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}Step 3: Registering Debezium MySQL source connector...${NC}"

# Check if connector already exists
CONNECTOR_EXISTS=$(curl -sf http://localhost:8083/connectors/mysql-source-connector 2>/dev/null && echo "yes" || echo "no")

if [ "$CONNECTOR_EXISTS" = "yes" ]; then
    echo -e "${YELLOW}  Source connector already exists. Skipping.${NC}"
else
    curl -sf -X POST http://localhost:8083/connectors \
        -H "Content-Type: application/json" \
        -d @config/mysql-source-connector.json | python3 -m json.tool 2>/dev/null || {
        echo -e "${RED}  Failed to register source connector.${NC}"
    }
    echo -e "${GREEN}  Source connector registered.${NC}"
fi

# ---------------------------------------------------------------------------
# Step 4: Wait for source connector to be RUNNING
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}Step 4: Waiting for source connector to be RUNNING...${NC}"

attempt=0
max_attempts=30
while [ $attempt -lt $max_attempts ]; do
    STATE=$(curl -sf http://localhost:8083/connectors/mysql-source-connector/status 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['connector']['state'])" 2>/dev/null || echo "UNKNOWN")
    if [ "$STATE" = "RUNNING" ]; then
        echo -e "${GREEN}  Source connector is RUNNING.${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$max_attempts - State: $STATE"
    sleep 5
done

if [ "$STATE" != "RUNNING" ]; then
    echo -e "${RED}  WARNING: Source connector is not RUNNING (state: $STATE).${NC}"
    echo -e "${RED}  Check: curl http://localhost:8083/connectors/mysql-source-connector/status${NC}"
fi

# ---------------------------------------------------------------------------
# Step 5: Submit ksqlDB queries
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}Step 5: Submitting ksqlDB queries...${NC}"

# Allow Debezium to produce initial snapshot before creating ksqlDB objects
echo "  Waiting 15 seconds for initial CDC snapshot..."
sleep 15

cd "$SCRIPT_DIR/src"
python3 setup_ksqldb.py || {
    echo -e "${YELLOW}  WARNING: Some ksqlDB queries may have failed. Check logs above.${NC}"
}
cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# Step 6: Register PostgreSQL JDBC sink connector (optional)
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}Step 6: Registering PostgreSQL JDBC sink connector...${NC}"

SINK_EXISTS=$(curl -sf http://localhost:8083/connectors/postgres-sink-connector 2>/dev/null && echo "yes" || echo "no")

if [ "$SINK_EXISTS" = "yes" ]; then
    echo -e "${YELLOW}  Sink connector already exists. Skipping.${NC}"
else
    curl -sf -X POST http://localhost:8083/connectors \
        -H "Content-Type: application/json" \
        -d @config/postgres-sink-connector.json 2>/dev/null && {
        echo -e "${GREEN}  Sink connector registered.${NC}"
    } || {
        echo -e "${YELLOW}  JDBC Sink connector registration failed (plugin may not be available).${NC}"
        echo -e "${YELLOW}  Starting Python sink consumer as alternative...${NC}"
        cd "$SCRIPT_DIR/src"
        python3 sink_consumer.py &
        SINK_PID=$!
        cd "$SCRIPT_DIR"
        echo -e "${GREEN}  Python sink consumer started (PID: $SINK_PID).${NC}"
    }
fi

# ---------------------------------------------------------------------------
# Step 7: Start the e-commerce simulator
# ---------------------------------------------------------------------------
echo ""
echo -e "${BLUE}Step 7: Starting e-commerce simulator...${NC}"

cd "$SCRIPT_DIR/src"
python3 ecommerce_simulator.py --speed 2 --duration 3600 &
SIMULATOR_PID=$!
cd "$SCRIPT_DIR"

echo -e "${GREEN}  Simulator started (PID: $SIMULATOR_PID).${NC}"

# ---------------------------------------------------------------------------
# Step 8: Print status summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}=============================================================${NC}"
echo -e "${GREEN} Platform is RUNNING!${NC}"
echo -e "${GREEN}=============================================================${NC}"
echo ""
echo -e "  ${BLUE}Kafka UI:${NC}        http://localhost:8080"
echo -e "  ${BLUE}Grafana:${NC}         http://localhost:3000  (admin / admin)"
echo -e "  ${BLUE}ksqlDB:${NC}          http://localhost:8088"
echo -e "  ${BLUE}Schema Registry:${NC} http://localhost:8081"
echo -e "  ${BLUE}Kafka Connect:${NC}   http://localhost:8083"
echo -e "  ${BLUE}Prometheus:${NC}      http://localhost:9090"
echo ""
echo -e "  ${YELLOW}Simulator PID:${NC}   $SIMULATOR_PID"
echo ""
echo -e "  To stop everything: ${RED}./teardown.sh${NC}"
echo ""
echo -e "${GREEN}Open Grafana to see the live dashboard updating in real time.${NC}"
echo ""

# Keep the script running so trap works
echo "Press Ctrl+C to stop the simulator and exit."
wait "$SIMULATOR_PID" 2>/dev/null || true
