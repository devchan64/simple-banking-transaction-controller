# AGENTS.md

Use the root `AGENTS.md` as the shared instruction source for VS Code and Codex-style agents.

## Goal

- Keep the project controller-centric.
- Preserve deterministic ATM session flow behavior.
- Prefer simple mock-based boundaries over premature abstraction.

## Read First

- `README.md`
- `docs/ssot/controller.md`
- `docs/ssot/bank-gateway.md`
- `docs/ssot/prompt-adapter.md`
- `docs/ssot/transport.md`
- `docs/ssot/persistence.md`
- `docs/ssot/persistence-json.md`
- `docs/ssot/session-command.md`
- `docs/ssot/session-result.md`

## Code Map

- `src/controller`: session state machine and controller contracts
- `src/banking`: mock banking runtime and gateway behavior
- `src/transport`: file-based request/response transport
- `src/prompt_adapter`: human-driven ATM CLI
- `tests/controller`: controller rules
- `tests/banking`: banking behavior
- `tests/transport`: transport behavior
- `tests/e2e`: end-to-end flow

## Commands

- Setup: `bash scripts/setup.sh`
- Basic tests: `bash scripts/test-basic.sh`
- E2E tests: `bash scripts/test-e2e.sh`
- Full tests: `bash scripts/test-all.sh`
- Format: `bash scripts/run-black.sh`
- Byte check: `bash scripts/check-bytes.sh`

## Runtime Dirs

- `.transport`
- `.controller`
- `.banking`
- `.test-run`

## Working Rules

- Read the relevant SSOT and tests before changing behavior.
- When controller rules change, review both `tests/controller` and `tests/e2e`.
- Keep transport, CLI, and persistence simple and subordinate to controller design.
- Treat `mock-db` as the mock data source of truth.
- Do not mix runtime artifacts with source files.

## Language Rules

- Write `AGENTS.md` in English for token efficiency.
- Write code comments mainly in Korean.
- Write docstrings mainly in Korean.
- Write user-visible system output mainly in Korean.
- Write repository documents mainly in Korean unless a file has a strong reason to stay English.

## Verification

- Run `bash scripts/test-basic.sh` after meaningful changes when possible.
- Run `bash scripts/test-e2e.sh` too when flow behavior changes.
- Use cleanup scripts if runtime artifacts interfere with verification.
