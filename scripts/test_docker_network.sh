#!/bin/bash
# Test script to verify host validation in Docker networks

set -e

PROJECT_ROOT="$(git rev-parse --show-toplevel)"

echo "=== Testing fake_csaf_provider in Docker network ==="
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

# Generate certificate for test domain if it doesn't exist
TEST_DOMAIN="testcsaf"
if [ ! -f "$PROJECT_ROOT/crypto/${TEST_DOMAIN}.crt.pem" ]; then
    echo "Generating certificate for domain: $TEST_DOMAIN"
    cd "$PROJECT_ROOT"
    python3 -m fake_tls_certificate.main "$TEST_DOMAIN"
    echo ""
fi

# Build the Docker image
echo "Building Docker image..."
docker build -t fake_csaf_provider "$PROJECT_ROOT"
echo ""

# Create a docker network
NETWORK_NAME="csaf_test_network"
echo "Creating Docker network: $NETWORK_NAME"
docker network create "$NETWORK_NAME" 2>/dev/null || echo "Network already exists"
echo ""

# Start the fake_csaf_provider container
CONTAINER_NAME="fake_csaf_test_server"
echo "Starting fake_csaf_provider container..."
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

docker run -d \
    --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    --network-alias "$TEST_DOMAIN" \
    -e FAKE_CSAF_DOMAIN="$TEST_DOMAIN" \
    -e FAKE_CSAF_PORT=443 \
    -e TRUSTED_HOSTS=any \
    -v "$PROJECT_ROOT/crypto:/app/crypto:ro" \
    -v "$PROJECT_ROOT/csafs:/app/csafs:ro" \
    fake_csaf_provider

echo "Waiting for server to start..."
sleep 3
echo ""

# Make the test request
docker run --rm \
    --network "$NETWORK_NAME" \
    -v "$PROJECT_ROOT/crypto:/crypto:ro" \
    curlimages/curl:latest \
    curl -f -v --cacert "/crypto/ca.crt.pem" \
    "https://${TEST_DOMAIN}/obscure/path/to/provider-metadata.json" 2>&1
echo ""

# Cleanup
echo "=== Cleanup ==="
docker rm -f "$CONTAINER_NAME"
docker network rm "$NETWORK_NAME"
echo ""
echo "=== Test complete ==="
