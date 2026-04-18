#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRANSPORT_ROOT="${1:-$ROOT_DIR/.transport}"
RUNTIME_ROOT="${2:-$ROOT_DIR/.controller}"
BANKING_ROOT="${3:-$ROOT_DIR/.banking}"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

PYTHONUNBUFFERED=1 PYTHONPATH=src python -m controller \
    "$TRANSPORT_ROOT" \
    --runtime-root "$RUNTIME_ROOT" \
    --banking-root "$BANKING_ROOT"
