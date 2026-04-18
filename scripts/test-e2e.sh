#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

rm -rf .test-run
mkdir -p .test-run

echo "[test-e2e] running E2E specs"

PYTHONPATH=src:. python3 -m unittest \
    tests.e2e.test_flow_e2e_spec
