#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANKING_ROOT="${1:-$ROOT_DIR/.banking}"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

PYTHONPATH=src python -m banking "$BANKING_ROOT"
