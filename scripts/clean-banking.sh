#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BANKING_DIR="$ROOT_DIR/.banking"

cd "$ROOT_DIR"

rm -rf "$BANKING_DIR"
mkdir -p "$BANKING_DIR"

echo "[clean] banking 디렉터리 정리 완료: $BANKING_DIR"
