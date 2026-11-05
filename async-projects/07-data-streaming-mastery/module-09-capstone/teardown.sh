#!/usr/bin/env bash
# =============================================================
# Module 9 Capstone: Teardown Script
# Stops all services and removes volumes.
# =============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping the e-commerce simulator (if running)...${NC}"
pkill -f "ecommerce_simulator.py" 2>/dev/null || true
pkill -f "sink_consumer.py" 2>/dev/null || true

echo -e "${YELLOW}Stopping all Docker Compose services and removing volumes...${NC}"
docker compose down -v

echo -e "${GREEN}All services stopped and volumes removed.${NC}"
echo -e "${GREEN}To restart, run: ./setup.sh${NC}"
