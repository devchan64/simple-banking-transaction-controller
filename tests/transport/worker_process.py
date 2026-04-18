from __future__ import annotations

import sys
from pathlib import Path

from controller.server import build_controller
from transport import FileTransport, SessionResponseEnvelope


def main() -> int:
    transport_root = Path(sys.argv[1])
    request_id = sys.argv[2]
    runtime_root = Path(sys.argv[3])
    banking_root = Path(sys.argv[4])

    transport = FileTransport(
        transport_root=transport_root,
        poll_interval_seconds=0.01,
        timeout_seconds=3.0,
    )
    controller = build_controller(runtime_root, banking_root)
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
