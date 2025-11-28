#!/bin/bash

set -e

readonly SERVER="http://localhost:34080"

# Offer provider metadata over '/.well-known/csaf/provider-metadata.json'
well_known_meta=0
# Offer provider metadata over '/security/data/csaf/provider-metadata.json'
security_data_meta=0
# Offer provider metadata over '/advisories/csaf/provider-metadata.json'
advisories_csaf_meta=0
# Offer provider metadata over '/security/csaf/provider-metadata.json'
security_csaf_meta=0
# Offer security.txt over '/.well-known/security.txt', which contains a link to the provider metadata
security_txt=0
# Offer directory listings (not yet implemented)
directory_listing=0
# Offer a ROLIE feed for CSAF documents
rolie_feed=0
# Verify the configuration after applying it
verify=0

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --well-known-meta)
            well_known_meta=1
            shift
            ;;
        --security-data-meta)
            security_data_meta=1
            shift
            ;;
        --advisories-csaf-meta)
            advisories_csaf_meta=1
            shift
            ;;
        --security-csaf-meta)
            security_csaf_meta=1
            shift
            ;;
        --security-txt)
            security_txt=1
            shift
            ;;
        --directory-listing)
            directory_listing=1
            shift
            ;;
        --rolie-feed)
            rolie_feed=1
            shift
            ;;
        --all)
            well_known_meta=1
            security_data_meta=1
            advisories_csaf_meta=1
            security_csaf_meta=1
            security_txt=1
            dns_path=1
            directory_listing=1
            rolie_feed=1
            shift
            ;;
        --verify)
            verify=1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Construct JSON payload
to_bool() {
    [ "$1" -eq 1 ] && echo true || echo false
}

payload=$(cat <<JSON
{
    "well_known_meta": $(to_bool "$well_known_meta"),
    "security_data_meta": $(to_bool "$security_data_meta"),
    "advisories_csaf_meta": $(to_bool "$advisories_csaf_meta"),
    "security_csaf_meta": $(to_bool "$security_csaf_meta"),
    "security_txt": $(to_bool "$security_txt"),
    "directory_listing": $(to_bool "$directory_listing"),
    "rolie_feed": $(to_bool "$rolie_feed")
}
JSON
)

# Send PATCH request to configure the fake CSAF server
curl -X PATCH -H "Content-Type: application/json" -d "$payload" "${SERVER}/config"

if [ "$verify" -eq 0 ]; then
    exit 0
fi

function expect_url() {
    local path="$1"
    local expect_url_to_exist="$2"
    local expected_code="200"
    if [ "$expect_url_to_exist" -eq 0 ]; then
        expected_code="404"
    fi
    local actual_code=$(curl -o /dev/null -s -w "%{http_code}" "${SERVER}${path}")
    if [ "$actual_code" -ne "$expected_code" ]; then
        echo "Expected HTTP status code $expected_code for ${path}, but got $actual_code"
        return 1
    fi
}

# Verify the server configuration
expect_url "/.well-known/csaf/provider-metadata.json" "$well_known_meta"
expect_url "/security/data/csaf/provider-metadata.json" "$security_data_meta"
expect_url "/advisories/csaf/provider-metadata.json" "$advisories_csaf_meta"
expect_url "/security/csaf/provider-metadata.json" "$security_csaf_meta"
expect_url "/.well-known/security.txt" "$security_txt"
expect_url "/csaf/white/" "$directory_listing"
expect_url "some-white-rolie-dir/some-feed.json" "$rolie_feed"
