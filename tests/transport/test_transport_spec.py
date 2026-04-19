from __future__ import annotations

"""transport 테스트의 과도기 스펙 모음.

이 파일은 원래 transport 자체를 검증하려는 목적에서 시작했지만,
controller 서버가 충분히 정리되기 전 단계에서 서버 경계 검증까지 함께 떠안으면서
범위가 넓어진 상태를 반영한다.

따라서 현재 이 스펙 코드는 경계 분리가 필요한 상태로 보는 편이 맞다.
transport 자체의 단순 계약을 검증하는 스펙과,
실제 서버를 띄운 뒤 일부 프로토콜과 데이터 처리를 검토하는 스펙은
장기적으로 서로 다른 파일이나 계층으로 나뉘는 편이 자연스럽다.

현재 관점에서 보면 관심사는 두 갈래로 분리되는 편이 자연스럽다.

1. transport 단일 명령 테스트
- request 파일을 올바른 위치에 기록하는지
- response 파일을 올바른 위치에서 읽는지
- ``dispatch()`` 가 요청 기록과 응답 대기를 올바르게 연결하는지
- ``session_id`` 나 command payload를 재해석하지 않고 그대로 직렬화하는지

2. 서버 구동을 통한 일부 프로토콜 검증
- 실제 controller 서버가 transport 경계를 통해 request를 읽고 response를 쓰는지
- 서버가 성공/실패 응답 구조를 transport 계약에 맞춰 기록하는지
- 파일 경계를 넘는 최소 프로토콜만 확인하고, controller 세부 상태 전이나
  비즈니스 결과 의미 검증은 더 상위의 통합 테스트로 넘기는지

즉 이 파일은 장기적으로 transport 자체 검증과 서버 데이터 처리 검토 사이를
정리해 나가기 위한 중간 상태의 테스트 묶음으로 이해하는 편이 맞다.
"""

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
from tests.support.process_support import ModuleProcessSupport
from tests.support.spec_support import TestRootSupport, flow_text, spec_text


class FileTransportSpec(ModuleProcessSupport, TestRootSupport, unittest.TestCase):
    """transport 계약 검증과 서버 경계 검토가 함께 남아 있는 과도기 테스트 클래스.

    이상적으로는 여기서 transport 자체의 단순 계약만 남기고,
    실제 서버를 띄워 데이터를 처리하는 검토는 별도 서버/통합 스펙으로
    분리하는 편이 테스트 의도와 책임 구분에 더 잘 맞는다.
    즉 현재 클래스는 유지보다 경계 분리 방향의 정리가 필요한 테스트 묶음에 가깝다.
    """

    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/transport") / self._testMethodName
        self.reset_test_root(self.test_root, "transport test_root")
        self.transport_root = self.test_root / "transport"
        self.controller_root = self.test_root / "controller"
        self.banking_root = self.test_root / "banking"

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
        banking_server = self._start_banking_server()
        worker = self._start_worker_process(
            self.transport_root,
            "req-001",
        )
        started_at = time.monotonic()
        print(flow_text("2. CLI 프로세스가 request 파일 작성"))
        response = transport.dispatch(request)
        elapsed_ms = (time.monotonic() - started_at) * 1000
        worker.wait(timeout=5)
        banking_server.terminate()
        banking_server.wait(timeout=5)
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
        banking_server = self._start_banking_server()
        worker = self._start_worker_process(
            self.transport_root,
            "req-002",
        )
        started_at = time.monotonic()
        response = transport.dispatch(request)
        elapsed_ms = (time.monotonic() - started_at) * 1000
        worker.wait(timeout=5)
        banking_server.terminate()
        banking_server.wait(timeout=5)

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
        banking_server = self._start_banking_server()
        worker = self._start_worker_process(
            self.transport_root,
            "req-003",
        )
        started_at = time.monotonic()
        response = transport.dispatch(request)
        elapsed_ms = (time.monotonic() - started_at) * 1000
        worker.wait(timeout=5)
        banking_server.terminate()
        banking_server.wait(timeout=5)

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

    def _start_banking_server(self) -> subprocess.Popen[str]:
        return self.start_module("banking", self.banking_root)

    def _start_worker_process(
        self,
        transport_root: Path,
        request_id: str,
    ) -> subprocess.Popen[str]:
        """현재 transport 스펙이 의존하는 과도기 worker 프로세스를 시작한다.

        이 helper는 transport 단일 기능 검증만 놓고 보면 불필요하게 무겁다.
        향후에는 실제 controller 서버를 직접 띄우는 검토와,
        transport 자체를 단독으로 검증하는 테스트를 분리하는 쪽이 더 자연스럽다.
        """
        return subprocess.Popen(
            [
                "python3",
                "tests/transport/worker_process.py",
                str(transport_root),
                request_id,
                str(self.controller_root),
                str(self.banking_root),
            ],
            cwd=self.repo_root(),
            env=self.python_env(),
            text=True,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
