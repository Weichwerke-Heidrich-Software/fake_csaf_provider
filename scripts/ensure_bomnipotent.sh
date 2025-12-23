#!/bin/bash

# Ensures that BOMnipotent Client, which is used to download the CSAF files, is available and up to date.

set -e

cd "$(git rev-parse --show-toplevel)"

function fetch_latest_version() {
    local url="https://www.bomnipotent.de/downloads/raw/latest/metadata.json"
    curl -s $url | grep -oP '"version":\s*"\K(.*?)(?=")'
}

function download() {
    local url="https://www.bomnipotent.de/downloads/raw/latest/debian-glibc/bomnipotent_client"
    echo "Downloading latest BOMnipotent Client from $url"
    curl -L $url -o bomnipotent_client
    chmod +x bomnipotent_client
    touch bomnipotent_client # To avoid immediate re-download
}

if [ ! -f "bomnipotent_client" ]; then
    download
fi

last_modified=$(stat -c %Y "bomnipotent_client")
current_time=$(date +%s)
age=$(( (current_time - last_modified) / 86400 ))
if [ $age -gt 7 ]; then
    echo "BOMnipotent Client is older than 7 days, checking for updates..."
    tool_version=$(./bomnipotent_client --version | awk '{print $2}')
    latest_version=$(fetch_latest_version)
    if [ "$tool_version" != "$latest_version" ]; then
        echo "Updating BOMnipotent Client from version $tool_version to $latest_version"
        download
    else
        echo "BOMnipotent Client is up to date."
        touch bomnipotent_client # Update timestamp to avoid re-checking too soon
    fi
fi
