#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTROLLER_ROOT="${1:-$ROOT_DIR/.transport/runtime}"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

PYTHONUNBUFFERED=1 PYTHONPATH=src python -m controller "$CONTROLLER_ROOT"
