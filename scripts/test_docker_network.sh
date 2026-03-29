#!/bin/bash
# Test script to verify host validation in Docker networks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

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

# Create a docker network
NETWORK_NAME="csaf_test_network"
echo "Creating Docker network: $NETWORK_NAME"
docker network create "$NETWORK_NAME" 2>/dev/null || echo "Network already exists"
echo ""

# Build the image if it doesn't exist
if ! docker image inspect fake_csaf_provider >/dev/null 2>&1; then
    echo "Building Docker image..."
    cd "$PROJECT_ROOT"
    docker build -t fake_csaf_provider .
    echo ""
fi

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
    -v "$PROJECT_ROOT/crypto:/app/crypto:ro" \
    -v "$PROJECT_ROOT/csafs:/app/csafs:ro" \
    fake_csaf_provider

echo "Waiting for server to start..."
sleep 3
echo ""

# Check server logs
echo "=== Server logs ==="
docker logs "$CONTAINER_NAME"
echo ""

# Test 1: Request without TRUSTED_HOSTS (should fail with host validation error)
echo "=== Test 1: Request WITHOUT TRUSTED_HOSTS (expecting host validation error) ==="
docker run --rm \
    --network "$NETWORK_NAME" \
    -v "$PROJECT_ROOT/crypto:/crypto:ro" \
    curlimages/curl:latest \
    curl -v --cacert "/crypto/ca.crt.pem" \
    "https://${TEST_DOMAIN}/.well-known/csaf/provider-metadata.json" 2>&1 || true
echo ""

# Stop the container
docker rm -f "$CONTAINER_NAME"
echo ""

# Test 2: Request WITH TRUSTED_HOSTS=any (should succeed)
echo "=== Test 2: Request WITH TRUSTED_HOSTS=any (expecting success) ==="
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

# Configure the server
echo "Configuring server..."
docker run --rm \
    --network "$NETWORK_NAME" \
    -v "$PROJECT_ROOT/crypto:/crypto:ro" \
    curlimages/curl:latest \
    curl -X PATCH --cacert "/crypto/ca.crt.pem" \
    -H "Content-Type: application/json" \
    -d '{"well_known_meta": true}' \
    "https://${TEST_DOMAIN}/config" 2>&1 || true
echo ""

# Make the test request
docker run --rm \
    --network "$NETWORK_NAME" \
    -v "$PROJECT_ROOT/crypto:/crypto:ro" \
    curlimages/curl:latest \
    curl -v --cacert "/crypto/ca.crt.pem" \
    "https://${TEST_DOMAIN}/.well-known/csaf/provider-metadata.json" 2>&1
echo ""

# Cleanup
echo "=== Cleanup ==="
docker rm -f "$CONTAINER_NAME"
docker network rm "$NETWORK_NAME"
echo ""
echo "=== Test complete ==="
