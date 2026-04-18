#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRANSPORT_ROOT="${1:-$ROOT_DIR/.transport}"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

PYTHONPATH=src python -m prompt_adapter "$TRANSPORT_ROOT"
