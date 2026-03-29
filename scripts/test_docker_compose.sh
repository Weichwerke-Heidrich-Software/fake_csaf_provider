#!/bin/bash
# Test script to verify host validation using Docker Compose

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.test.yml"

echo "=== Testing fake_csaf_provider with Docker Compose ==="
echo ""

# Check if crypto and csafs directories exist
if [ ! -d "$PROJECT_ROOT/crypto" ]; then
    echo "Error: crypto directory not found. Run scripts/setup.sh first."
    exit 1
fi

if [ ! -d "$PROJECT_ROOT/csafs" ]; then
    echo "Error: csafs directory not found. Run scripts/setup.sh first."
    exit 1
fi

# Check if docker-compose.test.yml exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: docker-compose.test.yml not found in project root."
    exit 1
fi

# Generate certificate for test domain if it doesn't exist
TEST_DOMAIN="fake_csaf_provider"
if [ ! -f "$PROJECT_ROOT/crypto/${TEST_DOMAIN}.crt.pem" ]; then
    echo "Generating certificate for domain: $TEST_DOMAIN"
    cd "$PROJECT_ROOT"
    python3 -m fake_tls_certificate.main "$TEST_DOMAIN"
    echo ""
fi

# Build and start services
echo "Building and starting services with Docker Compose..."
cd "$PROJECT_ROOT"
docker compose -f "$COMPOSE_FILE" up -d --build
echo ""

echo "Waiting for server to start..."
sleep 3
echo ""

# Make the test request using docker exec
echo "Making test request..."
docker exec fake_csaf_compose_test_client \
    curl -f -v --cacert "/crypto/ca.crt.pem" \
    "https://${TEST_DOMAIN}/obscure/path/to/provider-metadata.json" 2>&1
echo ""

# Cleanup
echo "=== Cleanup ==="
docker compose -f "$COMPOSE_FILE" down
echo ""
echo "=== Test complete ==="
