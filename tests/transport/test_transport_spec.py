from __future__ import annotations

import os
import subprocess
import time
import unittest
from pathlib import Path

from controller import (
    CommandType,
    SessionCommand,
    SessionState,
)
from transport import (
    FileTransport,
    SessionRequestEnvelope,
    TRANSPORT_FILE_SUFFIX,
    TransportDirectoryName,
)
from tests.support.spec_support import TestRootSupport, flow_text, spec_text


class FileTransportSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        self.transport_root = Path(".test-run/transport") / self._testMethodName
        self.reset_test_root(self.transport_root, "transport test_root")

    def test_dispatch_writes_request_and_returns_response_file_result(self) -> None:
        # 정상 흐름: 서로 다른 두 프로세스가 request/response 파일로 통신해야 한다.
        print(
            spec_text(
                "두 개의 프로세스가 request/response 파일로 성공 응답을 주고받는다"
            )
        )
        transport = FileTransport(self.transport_root)
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
        request = SessionRequestEnvelope(
            request_id="req-001",
            session_id=None,
            command=SessionCommand(
                command_type=CommandType.INSERT_CARD,
                card_number="4000-1234-5678-0001",
            ),
        )

        print(flow_text(f"transport root={self.transport_root}"))
        print(flow_text(f"request 파일 생성 위치={request_path}"))
        print(flow_text(f"response 파일 생성 위치={response_path}"))
        print(flow_text("1. worker 프로세스 시작"))
        worker = self._start_worker_process(
            self.transport_root,
            "req-001",
        )
        started_at = time.monotonic()
        print(flow_text("2. CLI 프로세스가 request 파일 작성"))
        response = transport.dispatch(request)
        elapsed_ms = (time.monotonic() - started_at) * 1000
        worker.wait(timeout=5)
        print(flow_text("3. worker 프로세스가 request 파일 읽기"))
        print(flow_text("4. worker 프로세스가 response 파일 작성"))
        print(flow_text("5. CLI 프로세스가 response 파일 읽기"))

        print(spec_text(f"응답={response}"))
        print(spec_text(f"왕복 지연시간={elapsed_ms:.3f}ms"))
        print(spec_text(f"request 파일 존재 여부={request_path.exists()}"))
        print(spec_text(f"response 파일 존재 여부={response_path.exists()}"))

        self.assertEqual("req-001", response.request_id)
        self.assertEqual("SESSION_STARTED", response.result["status_code"])
        self.assertEqual(SessionState.CARD_INSERTED, response.result["session_state"])
        self.assertEqual(False, response.result["session_closed"])
        self.assertTrue(response.result["session_token"])
        self.assertIsNone(response.error_code)
        self.assertIsNone(response.error_message)
        self.assertTrue(request_path.exists())
        self.assertTrue(response_path.exists())

    def test_dispatch_maps_controller_exception_to_error_response_file(self) -> None:
        # 실패 흐름: 별도 프로세스의 controller 예외는 response 파일 error 필드로 기록되어야 한다.
        print(
            spec_text(
                "controller 프로세스 예외를 response 파일의 error 응답으로 변환한다"
            )
        )
        transport = FileTransport(self.transport_root)
        request_path = (
            self.transport_root
            / TransportDirectoryName.REQUESTS
            / f"req-002{TRANSPORT_FILE_SUFFIX}"
        )
        response_path = (
            self.transport_root
            / TransportDirectoryName.RESPONSES
            / f"req-002{TRANSPORT_FILE_SUFFIX}"
        )
        request = SessionRequestEnvelope(
            request_id="req-002",
            session_id="session-001",
            command=SessionCommand(
                command_type=CommandType.REQUEST_WITHDRAW,
                session_token="session-unknown",
                amount=100,
            ),
        )

        print(flow_text(f"transport root={self.transport_root}"))
        print(flow_text(f"request 파일 생성 위치={request_path}"))
        print(flow_text(f"response 파일 생성 위치={response_path}"))
        worker = self._start_worker_process(
            self.transport_root,
            "req-002",
        )
        started_at = time.monotonic()
        response = transport.dispatch(request)
        elapsed_ms = (time.monotonic() - started_at) * 1000
        worker.wait(timeout=5)

        print(spec_text(f"응답={response}"))
        print(spec_text(f"왕복 지연시간={elapsed_ms:.3f}ms"))
        print(spec_text(f"request 파일 존재 여부={request_path.exists()}"))
        print(spec_text(f"response 파일 존재 여부={response_path.exists()}"))

        self.assertEqual("req-002", response.request_id)
        self.assertIsNone(response.result)
        self.assertEqual("ControllerError", response.error_code)
        self.assertEqual("알 수 없는 세션 토큰입니다: session-unknown", response.error_message)

    def test_dispatch_keeps_session_id_in_request_file_without_reinterpretation(
        self,
    ) -> None:
        # transport는 두 프로세스 사이에서 session_id를 판단하지 않고 그대로 전달해야 한다.
        print(
            spec_text(
                "session_id는 두 프로세스 사이에서 재해석하지 않고 그대로 유지한다"
            )
        )
        transport = FileTransport(self.transport_root)
        request_path = (
            self.transport_root
            / TransportDirectoryName.REQUESTS
            / f"req-003{TRANSPORT_FILE_SUFFIX}"
        )
        response_path = (
            self.transport_root
            / TransportDirectoryName.RESPONSES
            / f"req-003{TRANSPORT_FILE_SUFFIX}"
        )
        request = SessionRequestEnvelope(
            request_id="req-003",
            session_id=None,
            command=SessionCommand(
                command_type=CommandType.INSERT_CARD,
                card_number="4000-1234-5678-0001",
            ),
        )

        print(flow_text(f"transport root={self.transport_root}"))
        print(flow_text(f"request 파일 생성 위치={request_path}"))
        print(flow_text(f"response 파일 생성 위치={response_path}"))
        worker = self._start_worker_process(
            self.transport_root,
            "req-003",
        )
        started_at = time.monotonic()
        response = transport.dispatch(request)
        elapsed_ms = (time.monotonic() - started_at) * 1000
        worker.wait(timeout=5)

        request_text = request_path.read_text(encoding="utf-8")

        print(spec_text(f"응답={response}"))
        print(spec_text(f"request 파일={request_text}"))
        print(spec_text(f"왕복 지연시간={elapsed_ms:.3f}ms"))
        print(spec_text(f"request 파일 존재 여부={request_path.exists()}"))
        print(spec_text(f"response 파일 존재 여부={response_path.exists()}"))

        self.assertEqual("SESSION_STARTED", response.result["status_code"])
        self.assertEqual(SessionState.CARD_INSERTED, response.result["session_state"])
        self.assertIn('"session_id": null', request_text)
        self.assertIn('"card_number": "4000-1234-5678-0001"', request_text)

    @staticmethod
    def _start_worker_process(
        transport_root: Path,
        request_id: str,
    ) -> subprocess.Popen[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"src{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(
            os.pathsep
        )
        return subprocess.Popen(
            [
                "python3",
                "tests/transport/worker_process.py",
                str(transport_root),
                request_id,
            ],
            cwd=Path(__file__).resolve().parents[2],
            env=env,
            text=True,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
