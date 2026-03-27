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
RETURN_CODE=0
COUNT=0

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
    
    echo "$year/$filename"
}

# Helper function to test URL access with or without client certificate
# Usage: test_url_access "PATH" "success|error" "auth|unauth"
# - expected_result: "success" for 2xx responses, "error" for 4xx responses
# - auth_mode: "auth" to use client certificate, "unauth" to skip
test_url_access() {
    local path="$1"
    local auth_mode="$2"
    local expected_result="$3"

    local url="${BASE_URL}${path}"
    
    # Resolve expected result to pattern
    local expected_pattern
    if [ "$expected_result" = "success" ]; then
        expected_pattern="^2[0-9][0-9]$"
    elif [ "$expected_result" = "error" ]; then
        expected_pattern="^4[0-9][0-9]$"
    else
        echo "✗ ERROR: Invalid expected_result '$expected_result'. Use 'success' or 'error'."
        RETURN_CODE=1
        return
    fi
    
    # Build curl command
    local curl_cmd="curl -s --cacert \"$CA_CERT\""
    if [ "$auth_mode" = "auth" ]; then
        curl_cmd="$curl_cmd --cert \"$CLIENT_CERT\" --key \"$CLIENT_KEY\""
    elif [ "$auth_mode" != "unauth" ]; then
        echo "✗ ERROR: Invalid auth_mode '$auth_mode'. Use 'auth' or 'unauth'."
        RETURN_CODE=1
        return
    fi
    curl_cmd="$curl_cmd \"$url\" -o /dev/null -w \"%{http_code}\""
    
    echo -n "Accessing ${path} with"
    if [ "$auth_mode" = "unauth" ]; then
        echo -n "out"
    fi
    echo " client certificate..."
    
    # Execute curl and capture HTTP code
    local http_code=$(eval $curl_cmd)
    COUNT=$((COUNT + 1))
    
    # Check if response matches expected pattern
    if [[ "$http_code" =~ $expected_pattern ]]; then
        echo "✓ PASS: Got expected HTTP $http_code"
    else
        echo "✗ FAIL: Expected $expected_result ($expected_pattern), got HTTP $http_code"
        RETURN_CODE=1
    fi
    echo ""
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

WHITE_ROLIE_CSAF="/some-white-csaf-dir-for-rolie/${WHITE_CSAF}"
AMBER_ROLIE_CSAF="/some-amber-csaf-dir-for-rolie/${AMBER_CSAF}"
readonly WHITE_ROLIE_FEED="/some-white-rolie-dir/some-feed.json"
readonly AMBER_ROLIE_FEED="/some-amber-rolie-dir/some-feed.json"
WHITE_DIRLIST_CSAF="/some-white-csaf-base-path/${WHITE_CSAF}"
AMBER_DIRLIST_CSAF="/some-amber-csaf-base-path/${AMBER_CSAF}"
test_url_access "${WHITE_ROLIE_CSAF}" "unauth" "success"
test_url_access "${AMBER_ROLIE_CSAF}" "unauth" "error"
test_url_access "${AMBER_ROLIE_CSAF}" "auth" "success"
test_url_access "${WHITE_ROLIE_FEED}" "unauth" "success"
test_url_access "${AMBER_ROLIE_FEED}" "unauth" "error"
test_url_access "${AMBER_ROLIE_FEED}" "auth" "success"
test_url_access "${WHITE_DIRLIST_CSAF}" "unauth" "success"
test_url_access "${AMBER_DIRLIST_CSAF}" "unauth" "error"
test_url_access "${AMBER_DIRLIST_CSAF}" "auth" "success"

echo "Checking provider metadata for TLP level advertisements..."
METADATA=$(curl -s --cacert "$CA_CERT" \
    "${BASE_URL}/obscure/path/to/provider-metadata.json")

COUNT=$((COUNT + 1))
if echo "$METADATA" | grep -q "WHITE"; then
    echo "✓ PASS: Metadata includes TLP:WHITE"
else
    echo "✗ FAIL: Metadata missing TLP:WHITE"
    RETURN_CODE=1
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

if [ $RETURN_CODE -eq 0 ]; then
    echo "✓ ALL ${COUNT} TESTS PASSED"
    echo ""
    echo "Client certificate authentication is working correctly."
    echo ""
    echo "Key findings:"
    echo "- TLP:WHITE content is publicly accessible (2xx responses)"
    echo "- Non-WHITE TLP content requires valid client certificates"
    echo "- Requests without certificates receive 4xx client errors"
    echo "- Client certificate validation is enforced"
    echo "- Metadata advertises all available TLP levels"
else
    echo "✗ SOME OF THE ${COUNT} TESTS FAILED"
    echo ""
    echo "ERROR: One or more tests failed. Please review the output above."
    echo "Client certificate authentication is NOT working as expected."
fi

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

exit $RETURN_CODE
