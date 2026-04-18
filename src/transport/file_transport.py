from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .contracts import (
    TRANSPORT_FILE_SUFFIX,
    TRANSPORT_REQUESTS_DIR,
    TRANSPORT_RESPONSES_DIR,
    TRANSPORT_ROOT_ENV,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRANSPORT_ROOT = Path(
    os.environ.get(
        TRANSPORT_ROOT_ENV,
        str(WORKSPACE_ROOT / ".transport" / "runtime"),
    )
)


@dataclass(frozen=True)
class SessionRequestEnvelope:
    request_id: str
    session_id: str | None
    command: dict[str, Any]


@dataclass(frozen=True)
class SessionResponseEnvelope:
    request_id: str
    result: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None


class FileTransport:
    def __init__(
        self,
        transport_root: str | Path | None = None,
        poll_interval_seconds: float = 0.01,
        timeout_seconds: float = 1.0,
    ) -> None:
        self._root = (
            Path(transport_root)
            if transport_root is not None
            else DEFAULT_TRANSPORT_ROOT
        )
        self._requests_dir = self._root / TRANSPORT_REQUESTS_DIR
        self._responses_dir = self._root / TRANSPORT_RESPONSES_DIR
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._requests_dir.mkdir(parents=True, exist_ok=True)
        self._responses_dir.mkdir(parents=True, exist_ok=True)

    def dispatch(self, request: SessionRequestEnvelope) -> SessionResponseEnvelope:
        # CLI 쪽 프로세스는 request 파일을 생성하고 response 파일이 생길 때까지 기다린다.
        self.write_request(request)
        return self.wait_for_response(request.request_id)

    def request_path(self, request_id: str) -> Path:
        return self._requests_dir / f"{request_id}{TRANSPORT_FILE_SUFFIX}"

    def response_path(self, request_id: str) -> Path:
        return self._responses_dir / f"{request_id}{TRANSPORT_FILE_SUFFIX}"

    @property
    def root(self) -> Path:
        return self._root

    @property
    def requests_dir(self) -> Path:
        return self._requests_dir

    @property
    def responses_dir(self) -> Path:
        return self._responses_dir

    def write_request(self, request: SessionRequestEnvelope) -> None:
        self._write_json(self.request_path(request.request_id), asdict(request))

    def read_request(self, request_id: str) -> SessionRequestEnvelope:
        return SessionRequestEnvelope(**self._read_json(self.request_path(request_id)))

    def write_response(self, response: SessionResponseEnvelope) -> None:
        self._write_json(self.response_path(response.request_id), asdict(response))

    def read_response(self, request_id: str) -> SessionResponseEnvelope:
        return SessionResponseEnvelope(
            **self._read_json(self.response_path(request_id))
        )

    def wait_for_request(self, request_id: str) -> SessionRequestEnvelope:
        request_path = self.request_path(request_id)
        deadline = time.monotonic() + self._timeout_seconds

        while time.monotonic() < deadline:
            if request_path.exists():
                return self.read_request(request_id)
            time.sleep(self._poll_interval_seconds)

        raise TimeoutError(f"Timed out waiting for request: {request_id}")

    def wait_for_response(self, request_id: str) -> SessionResponseEnvelope:
        response_path = self.response_path(request_id)
        deadline = time.monotonic() + self._timeout_seconds

        while time.monotonic() < deadline:
            if response_path.exists():
                return self.read_response(request_id)
            time.sleep(self._poll_interval_seconds)

        raise TimeoutError(f"Timed out waiting for response: {request_id}")

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))
