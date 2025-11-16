#!/bin/bash

set -e

cd "$(git rev-parse --show-toplevel)"

venv_py=$(./scripts/get_python_cmd.sh)

$venv_py -m ensurepip || true
$venv_py -m pip install pip
$venv_py -m pip install -r ./requirements.txt

$venv_py fake_csaf_server.py &
echo $! > /tmp/fake_csaf_server.pid

sleep 1
