#!/usr/bin/env bash
# ============================================================
# Module 05 -- CDC with Debezium: Setup and Demo Script
# ============================================================
# This script starts the infrastructure, registers the Debezium
# connector, triggers database changes, and then consumes the
# CDC events to show the end-to-end pipeline.
#
# Usage:
#     chmod +x src/setup_and_demo.sh
#     ./src/setup_and_demo.sh
# ============================================================

set -e

MODULE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$MODULE_DIR"

echo "============================================================"
echo " Module 05 -- CDC with Debezium: Setup & Demo"
echo "============================================================"
echo ""
echo "Working directory: $MODULE_DIR"
echo ""

# --------------------------------------------------
# Step 1: Start Docker Compose
# --------------------------------------------------
echo "[Step 1/5] Starting Docker Compose services ..."
docker compose up -d

echo ""
echo "Waiting for services to become healthy ..."
echo "(This may take 60-90 seconds on first run.)"
echo ""

# Wait for Kafka Connect (the slowest service) to be ready.
MAX_WAIT=180
ELAPSED=0
until curl -sf http://localhost:8083/connectors > /dev/null 2>&1; do
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: Kafka Connect did not start within ${MAX_WAIT}s."
        echo "Check logs with: docker compose logs kafka-connect"
        exit 1
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo "  ... waiting ($ELAPSED/${MAX_WAIT}s)"
done

echo ""
echo "All services are up and running."
echo ""

# --------------------------------------------------
# Step 2: Register the Debezium connector
# --------------------------------------------------
echo "[Step 2/5] Registering the Debezium MySQL source connector ..."
python src/register_connector.py
echo ""

# --------------------------------------------------
# Step 3: Wait for initial snapshot to complete
# --------------------------------------------------
echo "[Step 3/5] Waiting for the initial snapshot to complete ..."
echo "(Giving Debezium 15 seconds to snapshot the seed data.)"
sleep 15
echo "Snapshot should be complete."
echo ""

# --------------------------------------------------
# Step 4: Trigger database changes
# --------------------------------------------------
echo "[Step 4/5] Triggering database changes ..."
python src/trigger_changes.py
echo ""

# --------------------------------------------------
# Step 5: Consume and display CDC events
# --------------------------------------------------
echo "[Step 5/5] Consuming CDC events (will stop after 20s of silence) ..."
echo ""
python src/cdc_consumer.py --timeout 20
echo ""

# --------------------------------------------------
# Summary
# --------------------------------------------------
echo "============================================================"
echo " Demo Complete"
echo "============================================================"
echo ""
echo "Services still running. Explore further:"
echo "  - Kafka UI:         http://localhost:8080"
echo "  - Connect REST API: http://localhost:8083/connectors"
echo "  - MySQL:            mysql -h localhost -P 3306 -u root -pdebezium ecommerce"
echo ""
echo "To consume more events:  python src/cdc_consumer.py --timeout 0"
echo "To run the processor:    python src/cdc_event_processor.py"
echo "To stop everything:      docker compose down -v"
echo ""
