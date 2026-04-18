#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

rm -rf .test-run
mkdir -p .test-run

PYTHONPATH=src python3 -m unittest discover -s tests
