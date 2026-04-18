#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

rm -rf .test-run
mkdir -p .test-run

PYTHONPATH=src python -m unittest discover -s tests
