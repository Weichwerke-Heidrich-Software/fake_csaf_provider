#!/bin/bash

set -e

readonly CSAF_DIR="csafs"

tlp="$1"

if [ -z "$tlp" ]; then
    echo "Error: TLP argument is required" >&2
    echo "Usage: $0 <tlp>" >&2
    exit 1
fi

cd "$(git rev-parse --show-toplevel)"
tlp_dir="$CSAF_DIR/$tlp"

if [ ! -d "$tlp_dir" ]; then
    echo "Error: TLP directory '$tlp_dir' does not exist" >&2
    exit 1
fi

json_file=$(find "$tlp_dir" -type f -name "*.json" | head -n 1)
if [ -z "$json_file" ]; then
    echo "Error: No JSON files found in '$tlp_dir'" >&2
    exit 1
fi

# Extract year and filename from path: csafs/tlp/year/file.json
year=$(basename "$(dirname "$json_file")")
filename=$(basename "$json_file")
echo "$year/$filename"
