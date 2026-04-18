#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [[ -f ".venv/bin/activate" ]]; then
    source ".venv/bin/activate"
fi

rm -rf .test-run
mkdir -p .test-run

PYTHONPATH=src:. python3 -m unittest \
    tests.banking.test_bank_gateway_spec \
    tests.banking.test_session_history_spec \
    tests.controller.test_command_validator_spec \
    tests.controller.test_controller_spec \
    tests.controller.test_session_result_spec \
    tests.transport.test_transport_spec
