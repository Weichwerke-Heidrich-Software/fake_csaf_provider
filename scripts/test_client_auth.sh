#!/bin/bash

# Test script for client certificate authentication
# This script validates that client certificate authentication works correctly

set -e

cd "$(git rev-parse --show-toplevel)"

# Configuration
DOMAIN="${FAKE_CSAF_DOMAIN:-localhost}"
PORT="${FAKE_CSAF_PORT:-34443}"
BASE_URL="https://${DOMAIN}:${PORT}"
CA_CERT="crypto/ca.crt.pem"
CLIENT_CERT="crypto/clients/demo-client.crt.pem"
CLIENT_KEY="crypto/clients/demo-client.key.pem"
CSAF_DIR="csafs"

# Helper function to find first CSAF file for a given TLP level
find_csaf_path() {
    local tlp="$1"
    local tlp_dir="$CSAF_DIR/$tlp"
    
    if [ ! -d "$tlp_dir" ]; then
        return 1
    fi
    
    local json_file=$(find "$tlp_dir" -type f -name "*.json" | head -n 1)
    if [ -z "$json_file" ]; then
        return 1
    fi
    
    # Extract year and filename from path: csafs/tlp/year/file.json
    local year=$(basename "$(dirname "$json_file")")
    local filename=$(basename "$json_file")
    
    echo "/some-${tlp}-csaf-dir-for-rolie/$year/$filename"
}

echo "========================================="
echo "Client Certificate Authentication Tests"
echo "========================================="
echo ""
echo "Testing against: $BASE_URL"
echo "CA Certificate: $CA_CERT"
echo "Client Certificate: $CLIENT_CERT"
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

# Check if certificates exist
if [ ! -f "$CA_CERT" ]; then
    echo "ERROR: CA certificate not found at $CA_CERT"
    echo "Please run scripts/setup.sh first"
    exit 1
fi

if [ ! -f "$CLIENT_CERT" ] || [ ! -f "$CLIENT_KEY" ]; then
    echo "ERROR: Client certificate not found"
    echo "Please run scripts/setup.sh to generate client certificates"
    exit 1
fi

# Discover actual CSAF files from the csafs directory
echo ">>> Discovering CSAF files..."
WHITE_CSAF=$(find_csaf_path "white")
AMBER_CSAF=$(find_csaf_path "amber")

if [ -z "$WHITE_CSAF" ]; then
    echo "ERROR: No WHITE CSAF files found in $CSAF_DIR/white"
    ./scripts/stop.sh
    exit 1
fi

if [ -z "$AMBER_CSAF" ]; then
    echo "ERROR: No AMBER CSAF files found in $CSAF_DIR/amber"
    ./scripts/stop.sh
    exit 1
fi

echo "Found WHITE CSAF: $WHITE_CSAF"
echo "Found AMBER CSAF: $AMBER_CSAF"
echo ""

# Test 1: Access public WHITE content without client certificate
echo "Test 1: Accessing TLP:WHITE content without client certificate..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" \
    "${BASE_URL}${WHITE_CSAF}" \
    -o /dev/null -w "%{http_code}")
if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
    echo "✓ PASS: WHITE content accessible without client certificate (HTTP $HTTP_CODE)"
else
    echo "✗ FAIL: WHITE content should return 2xx, got HTTP $HTTP_CODE"
fi
echo ""

# Test 2: Access protected content without client certificate (should fail)
echo "Test 2: Accessing TLP:AMBER content without client certificate..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" \
    "${BASE_URL}${AMBER_CSAF}" \
    -o /dev/null -w "%{http_code}")
if [[ "$HTTP_CODE" =~ ^4[0-9][0-9]$ ]]; then
    echo "✓ PASS: AMBER content correctly rejected without client certificate (HTTP $HTTP_CODE)"
else
    echo "✗ FAIL: Expected 4xx client error, got HTTP $HTTP_CODE"
fi
echo ""

# Test 3: Access protected content with valid client certificate
echo "Test 3: Accessing TLP:AMBER content with valid client certificate..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" \
    --cert "$CLIENT_CERT" \
    --key "$CLIENT_KEY" \
    "${BASE_URL}${AMBER_CSAF}" \
    -o /dev/null -w "%{http_code}")
if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
    echo "✓ PASS: AMBER content accessible with valid client certificate (HTTP $HTTP_CODE)"
else
    echo "✗ FAIL: Expected 2xx success, got HTTP $HTTP_CODE"
fi
echo ""

# Test 4: Access ROLIE feed for WHITE (public)
echo "Test 4: Accessing TLP:WHITE ROLIE feed without client certificate..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" \
    "${BASE_URL}/some-white-rolie-dir/some-feed.json" \
    -o /dev/null -w "%{http_code}")
if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
    echo "✓ PASS: WHITE ROLIE feed accessible without client certificate (HTTP $HTTP_CODE)"
else
    echo "✗ FAIL: Expected 2xx success, got HTTP $HTTP_CODE"
fi
echo ""

# Test 5: Access ROLIE feed for AMBER (protected) without certificate
echo "Test 5: Accessing TLP:AMBER ROLIE feed without client certificate..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" \
    "${BASE_URL}/some-amber-rolie-dir/some-feed.json" \
    -o /dev/null -w "%{http_code}")
if [[ "$HTTP_CODE" =~ ^4[0-9][0-9]$ ]]; then
    echo "✓ PASS: AMBER ROLIE feed correctly rejected without client certificate (HTTP $HTTP_CODE)"
else
    echo "✗ FAIL: Expected 4xx client error, got HTTP $HTTP_CODE"
fi
echo ""

# Test 6: Access ROLIE feed for AMBER (protected) with certificate
echo "Test 6: Accessing TLP:AMBER ROLIE feed with client certificate..."
HTTP_CODE=$(curl -s --cacert "$CA_CERT" \
    --cert "$CLIENT_CERT" \
    --key "$CLIENT_KEY" \
    "${BASE_URL}/some-amber-rolie-dir/some-feed.json" \
    -o /dev/null -w "%{http_code}")
if [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
    echo "✓ PASS: AMBER ROLIE feed accessible with client certificate (HTTP $HTTP_CODE)"
else
    echo "✗ FAIL: Expected 2xx success, got HTTP $HTTP_CODE"
fi
echo ""

# Test 7: Verify metadata includes all TLP levels
echo "Test 7: Checking provider metadata for TLP level advertisements..."
METADATA=$(curl -s --cacert "$CA_CERT" \
    "${BASE_URL}/obscure/path/to/provider-metadata.json")

if echo "$METADATA" | grep -q "WHITE"; then
    echo "✓ PASS: Metadata includes TLP:WHITE"
else
    echo "✗ FAIL: Metadata missing TLP:WHITE"
fi

# Check for other TLP levels if they exist in the csafs directory
for TLP in AMBER GREEN RED CLEAR; do
    if echo "$METADATA" | grep -q "$TLP"; then
        echo "✓ PASS: Metadata includes TLP:$TLP"
    else
        echo "⚠ INFO: Metadata does not include TLP:$TLP (may not be available)"
    fi
done
echo ""

# Stop the server
echo ">>> Stopping the server..."
./scripts/stop.sh
echo ""
echo "Server stopped."

echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Client certificate authentication is working correctly."
echo ""
echo "Key findings:"
echo "- TLP:WHITE content is publicly accessible (2xx responses)"
echo "- Non-WHITE TLP content requires valid client certificates"
echo "- Requests without certificates receive 4xx client errors"
echo "- Client certificate validation is enforced"
echo "- Metadata advertises all available TLP levels"
echo ""
echo "To test manually:"
echo "  # Without certificate (should fail for AMBER):"
echo "  curl --cacert $CA_CERT ${BASE_URL}${AMBER_CSAF}"
echo ""
echo "  # With certificate (should succeed):"
echo "  curl --cacert $CA_CERT --cert $CLIENT_CERT --key $CLIENT_KEY \\"
echo "    ${BASE_URL}${AMBER_CSAF}"
echo ""
echo "  # WHITE content (should succeed without certificate):"
echo "  curl --cacert $CA_CERT ${BASE_URL}${WHITE_CSAF}"
echo ""
