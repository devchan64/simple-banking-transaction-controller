#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRANSPORT_DIR="$ROOT_DIR/.transport"

cd "$ROOT_DIR"

mkdir -p "$TRANSPORT_DIR"
find "$TRANSPORT_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

echo "[clean] transport 디렉터리 정리 완료: $TRANSPORT_DIR"
