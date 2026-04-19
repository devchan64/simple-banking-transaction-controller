from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .bank_gateway import BankGateway, BankGatewayError, JsonBankGateway
from .protocol import BankAction, BankRequest, BankResponse
from .runtime import prepare_banking_runtime
from .session import BankingSessionStore, SessionHistoryStore


def run_server(
    transport_root: str | Path,
    maintenance_enabled: bool = False,
    poll_interval_seconds: float = 0.05,
) -> int:
    root = Path(transport_root)
    requests_dir = root / "requests"
    responses_dir = root / "responses"
    requests_dir.mkdir(parents=True, exist_ok=True)
    responses_dir.mkdir(parents=True, exist_ok=True)

    runtime = prepare_banking_runtime(root)
    history_store = SessionHistoryStore(runtime.session_history_path)
    session_store = BankingSessionStore(
        runtime.active_sessions_path,
        history_store,
    )
    gateway = JsonBankGateway(
        runtime.cards_path,
        runtime.accounts_path,
        session_store=session_store,
        maintenance_enabled=maintenance_enabled,
    )
    print("[banking.server] started")
    print(f"[banking.server] transport_root={root}")
    print(f"[banking.server] requests_dir={requests_dir}")
    print(f"[banking.server] responses_dir={responses_dir}")
    print(f"[banking.server] maintenance_enabled={maintenance_enabled}")

    while True:
        if not _process_next_request(gateway, requests_dir, responses_dir):
            time.sleep(poll_interval_seconds)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a continuous file-transport banking server."
    )
    parser.add_argument("transport_root", help="Bank transport runtime root directory.")
    parser.add_argument(
        "--maintenance",
        action="store_true",
        help="Enable bank maintenance mode for the running server.",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=0.05,
        help="Polling interval in seconds while waiting for new requests.",
    )
    args = parser.parse_args(argv)
    return run_server(
        transport_root=args.transport_root,
        maintenance_enabled=args.maintenance,
        poll_interval_seconds=args.poll_interval,
    )


def _process_next_request(
    gateway: BankGateway,
    requests_dir: Path,
    responses_dir: Path,
) -> bool:
    for request_path in sorted(requests_dir.glob("*.json")):
        response_path = responses_dir / request_path.name
        if response_path.exists():
            continue
        request = BankRequest.model_validate(
            json.loads(request_path.read_text(encoding="utf-8"))
        )
        print(
            f"[banking.server] request received request_id={request.request_id} action={request.action}"
        )
        response = _handle_request(gateway, request)
        response_path.write_text(
            json.dumps(response.model_dump(mode="json"), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
        if response.error_code is None:
            print(f"[banking.server] response written request_id={request.request_id}")
        else:
            print(
                f"[banking.server] response written request_id={request.request_id} error={response.error_code}"
            )
        return True
    return False


def _handle_request(gateway: BankGateway, request: BankRequest) -> BankResponse:
    try:
        payload = _dispatch_action(gateway, request)
        return BankResponse(request_id=request.request_id, payload=payload)
    except Exception as exc:
        return BankResponse(
            request_id=request.request_id,
            error_code=type(exc).__name__,
            error_message=str(exc),
            error_details={
                key: value
                for key, value in {
                    "remaining_attempts": getattr(exc, "remaining_attempts", None),
                    "card_locked": getattr(exc, "card_locked", None),
                }.items()
                if value is not None
            }
            or None,
        )


def _dispatch_action(
    gateway: BankGateway,
    request: BankRequest,
) -> dict[str, object]:
    if request.action == BankAction.CREATE_SESSION:
        return gateway.create_session(request.card_id).__dict__
    if request.action == BankAction.GET_SESSION:
        return gateway.get_session(request.session_token).__dict__
    if request.action == BankAction.REFRESH_SESSION:
        return gateway.refresh_session(request.session_token).__dict__
    if request.action == BankAction.GET_CARD_BY_NUMBER:
        return gateway.get_card_by_number(request.card_number).__dict__
    if request.action == BankAction.GET_CARD_BY_ID:
        return gateway.get_card_by_id(request.card_id).__dict__
    if request.action == BankAction.VERIFY_PIN:
        return gateway.verify_pin(request.card_number, request.pin).__dict__
    if request.action == BankAction.LIST_ACCOUNTS:
        return {"account_ids": gateway.list_accounts(request.card_id)}
    if request.action == BankAction.GET_BALANCE:
        return {"balance": gateway.get_balance(request.account_id)}
    if request.action == BankAction.DEPOSIT:
        return {"balance": gateway.deposit(request.account_id, request.amount)}
    if request.action == BankAction.WITHDRAW:
        return {"balance": gateway.withdraw(request.account_id, request.amount)}
    raise BankGatewayError(f"Unsupported bank action: {request.action}")


if __name__ == "__main__":
    raise SystemExit(main())
