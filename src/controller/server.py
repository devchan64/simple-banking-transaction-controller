from __future__ import annotations

import argparse
import time
from pathlib import Path

from banking import BankingSdk
from transport import FileTransport, SessionResponseEnvelope

from .controller import BankingFlowController
from .session_store import JsonSessionStore


def run_server(
    transport_root: str | Path,
    runtime_root: str | Path | None = None,
    banking_root: str | Path | None = None,
    poll_interval_seconds: float = 0.05,
) -> int:
    transport_root_path = Path(transport_root)
    runtime_root_path = (
        Path(runtime_root) if runtime_root is not None else transport_root_path
    )
    banking_root_path = Path(banking_root) if banking_root is not None else Path(".banking")
    controller = build_controller(runtime_root_path, banking_root_path)
    transport = FileTransport(
        transport_root=transport_root_path,
        poll_interval_seconds=poll_interval_seconds,
        timeout_seconds=3600,
    )

    print("[controller.server] started")
    print(f"[controller.server] transport_root={transport.root}")
    print(f"[controller.server] runtime_root={runtime_root_path}")
    print(f"[controller.server] banking_root={banking_root_path}")
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
        "--runtime-root",
        default=None,
        help="Controller state runtime root directory. Defaults to transport_root.",
    )
    parser.add_argument(
        "--banking-root",
        default=".banking",
        help="Banking server transport root directory.",
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
        runtime_root=args.runtime_root,
        banking_root=args.banking_root,
        poll_interval_seconds=args.poll_interval,
    )


def build_controller(runtime_root: Path, banking_root: Path) -> BankingFlowController:
    runtime_root.mkdir(parents=True, exist_ok=True)
    active_sessions_path = runtime_root / "active-sessions.json"

    return BankingFlowController(
        bank_gateway=BankingSdk(banking_root),
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
