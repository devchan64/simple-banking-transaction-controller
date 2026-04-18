from __future__ import annotations

import shutil
import sys
from pathlib import Path

from controller import (
    BankingFlowController,
    ControllerError,
    JsonSessionStore,
    SessionCommand,
)
from banking import JsonBankGateway, SessionHistoryStore
from transport import FileTransport, SessionResponseEnvelope


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


def main() -> int:
    transport_root = sys.argv[1]
    request_id = sys.argv[2]

    transport = FileTransport(
        transport_root=transport_root,
        poll_interval_seconds=0.01,
        timeout_seconds=3.0,
    )
    controller = build_controller(Path(transport_root))
    request = transport.wait_for_request(request_id)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
