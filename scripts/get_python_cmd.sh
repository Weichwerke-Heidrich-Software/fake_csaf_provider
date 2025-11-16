#!/bin/bash

set -e

cd "$(git rev-parse --show-toplevel)"

if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required but not found. Install python3 and try again." >&2
    exit 1
fi

if [ ! -d venv ]; then
    python3 -m venv venv
fi

if [ -x venv/bin/python ]; then
    VENV_PY=venv/bin/python
elif [ -x venv/bin/python3 ]; then
    VENV_PY=venv/bin/python3
else
    VENV_PY=$(command -v python3 || command -v python || true)
    if [ -z "$VENV_PY" ]; then
        echo "No python executable available." >&2
        exit 1
    fi
fi

source venv/bin/activate

echo "$VENV_PY"
