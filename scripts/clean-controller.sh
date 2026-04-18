#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTROLLER_DIR="$ROOT_DIR/.controller"

cd "$ROOT_DIR"

rm -rf "$CONTROLLER_DIR"
mkdir -p "$CONTROLLER_DIR"

echo "[clean] controller 디렉터리 정리 완료: $CONTROLLER_DIR"
