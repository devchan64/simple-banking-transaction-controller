#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_RUN_DIR="$ROOT_DIR/.test-run"

cd "$ROOT_DIR"

rm -rf "$TEST_RUN_DIR"
mkdir -p "$TEST_RUN_DIR"

echo "[clean] test-run 디렉터리 정리 완료: $TEST_RUN_DIR"
