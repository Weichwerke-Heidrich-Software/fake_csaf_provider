#!/bin/bash

set -e

cd "$(git rev-parse --show-toplevel)"

if [ -f /tmp/fake_csaf_provider.pid ]; then
    ./scripts/stop.sh
fi

venv_py=$(./scripts/get_python_cmd.sh)

$venv_py -m fake_csaf_provider.main &
echo $! > /tmp/fake_csaf_provider.pid

sleep 1
