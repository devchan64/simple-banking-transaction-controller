from __future__ import annotations

import threading
import time
import unittest
from pathlib import Path

from controller import CommandType, SessionCommand
from transport import (
    FileTransport,
    SessionRequestEnvelope,
    SessionResponseEnvelope,
    TRANSPORT_FILE_SUFFIX,
    TransportDirectoryName,
)
from tests.support.spec_support import TestRootSupport, flow_text, spec_text


class FileTransportSpec(TestRootSupport, unittest.TestCase):
    """통신 계약만 검증하는 transport 스펙."""

    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/transport") / self._testMethodName
        self.reset_test_root(self.test_root, "transport test_root")
        self.transport_root = self.test_root / "transport"

    def test_dispatch_writes_request_and_returns_response_file_result(self) -> None:
        print(spec_text("dispatch 는 request 파일을 쓰고 response 파일 결과를 반환한다"))
        transport = FileTransport(self.transport_root, timeout_seconds=1.0)
        request = SessionRequestEnvelope(
            request_id="req-001",
            session_id=None,
            command=SessionCommand(
                command_type=CommandType.INSERT_CARD,
                card_number="4000-1234-5678-0001",
            ),
        )
        response = SessionResponseEnvelope(
            request_id="req-001",
            result={"status_code": "OK"},
        )

        request_path = (
            self.transport_root
            / TransportDirectoryName.REQUESTS
            / f"req-001{TRANSPORT_FILE_SUFFIX}"
        )
        response_path = (
            self.transport_root
            / TransportDirectoryName.RESPONSES
            / f"req-001{TRANSPORT_FILE_SUFFIX}"
        )

        responder = threading.Thread(
            target=self._write_response_after_request,
            args=(transport, request.request_id, response),
            daemon=True,
        )
        responder.start()

        result = transport.dispatch(request)
        responder.join(timeout=1.0)

        print(flow_text(f"request 파일 생성 위치={request_path}"))
        print(flow_text(f"response 파일 생성 위치={response_path}"))
        print(spec_text(f"응답={result}"))

        self.assertEqual("req-001", result.request_id)
        self.assertEqual({"status_code": "OK"}, result.result)
        self.assertTrue(request_path.exists())
        self.assertTrue(response_path.exists())

    def test_write_request_keeps_session_id_without_reinterpretation(self) -> None:
        print(spec_text("session_id 는 재해석 없이 request 파일에 그대로 기록한다"))
        transport = FileTransport(self.transport_root)
        request = SessionRequestEnvelope(
            request_id="req-002",
            session_id=None,
            command=SessionCommand(
                command_type=CommandType.INSERT_CARD,
                card_number="4000-1234-5678-0001",
            ),
        )

        request_path = (
            self.transport_root
            / TransportDirectoryName.REQUESTS
            / f"req-002{TRANSPORT_FILE_SUFFIX}"
        )
        transport.write_request(request)
        request_text = request_path.read_text(encoding="utf-8")

        print(spec_text(f"request 파일={request_text}"))
        self.assertIn('"session_id": null', request_text)
        self.assertIn('"card_number": "4000-1234-5678-0001"', request_text)

    def test_wait_for_request_reads_existing_request_file(self) -> None:
        print(spec_text("wait_for_request 는 생성된 request 파일을 읽는다"))
        transport = FileTransport(self.transport_root, timeout_seconds=1.0)
        request = SessionRequestEnvelope(
            request_id="req-003",
            session_id="session-001",
            command=SessionCommand(
                command_type=CommandType.REQUEST_BALANCE,
                session_token="session-001",
            ),
        )

        transport.write_request(request)
        loaded = transport.wait_for_request(request.request_id)

        self.assertEqual(request, loaded)

    def test_wait_for_response_times_out_when_response_file_is_missing(self) -> None:
        print(spec_text("wait_for_response 는 response 파일이 없으면 timeout 된다"))
        transport = FileTransport(
            self.transport_root,
            poll_interval_seconds=0.01,
            timeout_seconds=0.05,
        )

        with self.assertRaisesRegex(TimeoutError, "Timed out waiting for response"):
            transport.wait_for_response("req-timeout")

    @staticmethod
    def _write_response_after_request(
        transport: FileTransport,
        request_id: str,
        response: SessionResponseEnvelope,
    ) -> None:
        request_path = transport.request_path(request_id)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if request_path.exists():
                transport.write_response(response)
                return
            time.sleep(0.01)
        raise TimeoutError(f"Timed out waiting for request file: {request_path}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
