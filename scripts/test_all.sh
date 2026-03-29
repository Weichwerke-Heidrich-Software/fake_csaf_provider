#!/bin/bash

set -e

cd $(git rev-parse --show-toplevel)

./scripts/run.sh
./scripts/configure.sh --verify
./scripts/configure.sh --all --verify
./scripts/stop.sh

for test in ./scripts/test_*; do
    # Skip this script to avoid infinite recursion
    if [ "$(basename $test)" = "$(basename $0)" ]; then
        continue
    fi
    echo "== Running $test =="
    "$test"
done
