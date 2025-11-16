#!/bin/bash

# Ensures that various tools from https://github.com/gocsaf/csaf are available and up to date.

set -e

cd "$(git rev-parse --show-toplevel)"

readonly REPO="gocsaf/csaf"
readonly TOOLS=("csaf_downloader" "csaf_checker")

function fetch_latest_version() {
    curl -s https://api.github.com/repos/$REPO/releases/latest | grep -Po '"tag_name": "\K.*?(?=")'
}

function download_tools() {
    echo "Downloading latest CSAF tools from $REPO..."
    local version=$(fetch_latest_version)
    local version_trimmed=${version#v}
    echo "Latest version is $version"
    local url="https://github.com/$REPO/releases/download/v$version_trimmed/csaf-$version_trimmed-gnulinux-amd64.tar.gz"
    echo "Downloading from $url"
    curl -L $url -o /tmp/gocsaf.tar.gz
    tar -xvf /tmp/gocsaf.tar.gz -C /tmp
    for TOOL in "${TOOLS[@]}"; do
        mv /tmp/csaf-$version_trimmed-gnulinux-amd64/bin-linux-amd64/$TOOL .
        chmod +x $TOOL
        touch $TOOL # To avoid immediate re-download
    done
}

for TOOL in "${TOOLS[@]}"; do
    if [ ! -f "$TOOL" ]; then
        download_tools
    fi

    last_modified=$(stat -c %Y "$TOOL")
    current_time=$(date +%s)
    age=$(( (current_time - last_modified) / 86400 ))
    if [ $age -gt 7 ]; then
        echo "$TOOL is older than 7 days, checking for updates..."
        tool_version=$(./$TOOL --version)
        latest_version=$(fetch_latest_version)
        if [ "$tool_version" != "$latest_version" ]; then
            echo "Updating $TOOL from version $tool_version to $latest_version"
            download_tools
        else
            echo "$TOOL is up to date."
            touch $TOOL # Update timestamp to avoid re-checking too soon
        fi
    fi
done
