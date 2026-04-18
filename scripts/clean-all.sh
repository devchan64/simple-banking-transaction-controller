#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

bash scripts/clean-transport.sh
bash scripts/clean-controller.sh
bash scripts/clean-banking.sh
bash scripts/clean-test-run.sh

echo "[clean] 전체 실행 디렉터리 정리 완료"
