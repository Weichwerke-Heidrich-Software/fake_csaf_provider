#!/bin/bash

set -e

cd "$(git rev-parse --show-toplevel)"

venv_py=$(./scripts/get_python_cmd.sh)

$venv_py -m ensurepip --upgrade || true
$venv_py -m pip install --upgrade pip
$venv_py -m pip install -r ./requirements.txt
$venv_py -m pip list --format=freeze \
    | cut -d= -f1 \
    | xargs -r $venv_py -m pip install -U
$venv_py -m pip freeze > ./requirements.txt
