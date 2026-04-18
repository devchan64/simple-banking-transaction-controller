from __future__ import annotations

import sys

from controller import (
    ERROR_INVALID_STATE,
    FieldName,
    ResultStatus,
    SessionCommand,
)
from transport import FileTransport, SessionResponseEnvelope, WorkerMode


class WorkerController:
    def __init__(self, mode: WorkerMode) -> None:
        self._mode = mode

    def handle(self, command: SessionCommand) -> dict:
        if self._mode == WorkerMode.ERROR:
            raise ValueError(ERROR_INVALID_STATE)
        return {
            FieldName.STATUS: ResultStatus.OK,
            FieldName.COMMAND_TYPE: command.command_type,
        }


def main() -> int:
    transport_root = sys.argv[1]
    request_id = sys.argv[2]
    mode = WorkerMode(sys.argv[3])

    transport = FileTransport(transport_root)
    controller = WorkerController(mode)
    request = transport.wait_for_request(request_id)

    try:
        result = controller.handle(request.command)
        response = SessionResponseEnvelope(
            request_id=request.request_id,
            result=result,
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
