#!/bin/bash

set -e

cd "$(git rev-parse --show-toplevel)"

./scripts/collect_example_csaf_docs.sh

venv_py=$(./scripts/get_python_cmd.sh)

$venv_py -m ensurepip || true
$venv_py -m pip install pip
$venv_py -m pip install -r ./requirements.txt

$venv_py -m fake_tls_certificate.main
