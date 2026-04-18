from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

from banking import JsonBankGateway, SessionHistoryStore
from transport import FileTransport, SessionResponseEnvelope

from .controller import BankingFlowController
from .session_store import JsonSessionStore


def run_server(
    transport_root: str | Path,
    poll_interval_seconds: float = 0.05,
) -> int:
    root = Path(transport_root)
    controller = build_controller(root)
    transport = FileTransport(
        transport_root=root,
        poll_interval_seconds=poll_interval_seconds,
        timeout_seconds=3600,
    )

    print("[controller.server] started")
    print(f"[controller.server] transport_root={transport.root}")
    print(f"[controller.server] requests_dir={transport.requests_dir}")
    print(f"[controller.server] responses_dir={transport.responses_dir}")

    while True:
        if not _process_next_request(controller, transport):
            time.sleep(poll_interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a continuous file-transport controller server."
    )
    parser.add_argument("transport_root", help="Controller transport runtime root directory.")
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.05,
        help="Polling interval in seconds while waiting for new requests.",
    )
    args = parser.parse_args(argv)
    return run_server(
        transport_root=args.transport_root,
        poll_interval_seconds=args.poll_interval,
    )


def build_controller(runtime_root: Path) -> BankingFlowController:
    mock_db_root = runtime_root / "mock-db"
    mock_db_root.mkdir(parents=True, exist_ok=True)

    cards_path = mock_db_root / "cards.json"
    accounts_path = mock_db_root / "accounts.json"
    if not cards_path.exists():
        shutil.copy(Path("mock-db/cards.json"), cards_path)
    if not accounts_path.exists():
        shutil.copy(Path("mock-db/accounts.json"), accounts_path)

    session_history_path = runtime_root / "session-history.json"
    active_sessions_path = runtime_root / "active-sessions.json"

    return BankingFlowController(
        bank_gateway=JsonBankGateway(cards_path, accounts_path),
        session_history_store=SessionHistoryStore(session_history_path),
        session_store=JsonSessionStore(active_sessions_path),
    )


def _process_next_request(
    controller: BankingFlowController,
    transport: FileTransport,
) -> bool:
    for request_path in sorted(transport.requests_dir.glob("*.json")):
        response_path = transport.response_path(request_path.stem)
        if response_path.exists():
            continue

        request = transport.read_request(request_path.stem)
        print(
            "[controller.server] request received "
            f"request_id={request.request_id} command_type={request.command.command_type}"
        )

        try:
            result = controller.handle(request.command)
            response = SessionResponseEnvelope(
                request_id=request.request_id,
                result=result.model_dump(mode="json"),
            )
        except Exception as exc:
            response = SessionResponseEnvelope(
                request_id=request.request_id,
                error_code=type(exc).__name__,
                error_message=str(exc),
            )

        transport.write_response(response)
        if response.error_code is None:
            print(
                f"[controller.server] response written request_id={request.request_id}"
            )
        else:
            print(
                "[controller.server] response written "
                f"request_id={request.request_id} error={response.error_code}"
            )
        return True
    return False


if __name__ == "__main__":
    raise SystemExit(main())
