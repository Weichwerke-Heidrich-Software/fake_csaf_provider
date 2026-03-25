#!/bin/bash

set -e

# Get the repository root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

readonly SERVER="https://localhost:34443"
readonly CERT_PATH="./crypto/ca.crt.pem"

echo "=========================================="
echo "CSAF Provider Showcase"
echo "=========================================="
echo ""

# Start the server
echo ">>> Starting the server..."
./scripts/run.sh
echo ""
echo "Waiting for server to be ready..."
sleep 3
echo ""

# Activate all endpoints using configure.sh
echo ">>> Activating all endpoints..."
./scripts/configure.sh --all
echo ""
echo "All endpoints activated successfully!"
echo ""

# Function to curl an endpoint and display output (max 20 lines)
function showcase_endpoint() {
    local path="$1"
    local description="$2"
    
    echo "=========================================="
    echo "Endpoint: ${path}"
    echo "Description: ${description}"
    echo "=========================================="
    
    # Curl the endpoint and limit output to 20 lines
    local output=$(curl -s --cacert "${CERT_PATH}" "${SERVER}${path}" 2>&1)
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo "Error: Failed to curl endpoint (exit code: $exit_code)"
        echo "$output" | head -n 20
    else
        echo "$output" | head -n 20
        local line_count=$(echo "$output" | wc -l)
        if [ "$line_count" -gt 20 ]; then
            echo "... (output truncated, showing 20 of $line_count lines)"
        fi
    fi
    
    echo ""
}

# Showcase all endpoints
showcase_endpoint "/.well-known/csaf/provider-metadata.json" "Provider metadata (well-known path)"
showcase_endpoint "/security/data/csaf/provider-metadata.json" "Provider metadata (security/data path)"
showcase_endpoint "/advisories/csaf/provider-metadata.json" "Provider metadata (advisories path)"
showcase_endpoint "/security/csaf/provider-metadata.json" "Provider metadata (security/csaf path)"
showcase_endpoint "/.well-known/security.txt" "Security.txt (well-known path)"
showcase_endpoint "/security.txt" "Security.txt (root path)"
showcase_endpoint "/some-csaf-base-path/index.txt" "Directory listing index"
showcase_endpoint "/some-csaf-base-path/changes.csv" "Directory listing changes"
showcase_endpoint "/some-white-rolie-dir/some-feed.json" "ROLIE feed"
showcase_endpoint "/.well-known/openpgpkey.asc" "OpenPGP public key"

echo "=========================================="
echo "Showcase complete!"
echo "=========================================="
echo ""

# Stop the server
echo ">>> Stopping the server..."
./scripts/stop.sh
echo ""
echo "Server stopped."
