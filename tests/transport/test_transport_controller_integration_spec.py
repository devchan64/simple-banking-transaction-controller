from __future__ import annotations

import unittest
from pathlib import Path

from controller import CommandType, SessionCommand
from transport import (
    FileTransport,
    SessionRequestEnvelope,
    TRANSPORT_FILE_SUFFIX,
    TransportDirectoryName,
)
from tests.support.process_support import ModuleProcessSupport
from tests.support.spec_support import TestRootSupport, flow_text, spec_text


class FileTransportControllerIntegrationSpec(
    ModuleProcessSupport, TestRootSupport, unittest.TestCase
):
    """transport 경계를 통한 controller 연동만 얇게 검증하는 스펙."""

    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/transport-controller") / self._testMethodName
        self.reset_test_root(self.test_root, "transport controller test_root")
        self.transport_root = self.test_root / "transport"
        self.controller_root = self.test_root / "controller"
        self.banking_root = self.test_root / "banking"

    def test_dispatch_returns_success_envelope_from_controller_server(self) -> None:
        print(spec_text("controller server 는 transport 경계로 성공 envelope 를 쓴다"))
        transport = FileTransport(self.transport_root, timeout_seconds=3.0)
        request = SessionRequestEnvelope(
            request_id="req-101",
            session_id=None,
            command=SessionCommand(
                command_type=CommandType.INSERT_CARD,
                card_number="4000-1234-5678-0001",
            ),
        )

        request_path = (
            self.transport_root
            / TransportDirectoryName.REQUESTS
            / f"req-101{TRANSPORT_FILE_SUFFIX}"
        )
        response_path = (
            self.transport_root
            / TransportDirectoryName.RESPONSES
            / f"req-101{TRANSPORT_FILE_SUFFIX}"
        )

        banking_server = self._start_banking_server()
        controller_server = self._start_controller_server()
        self.addCleanup(self._stop_process, controller_server)
        self.addCleanup(self._stop_process, banking_server)

        response = transport.dispatch(request)

        print(flow_text(f"request 파일 생성 위치={request_path}"))
        print(flow_text(f"response 파일 생성 위치={response_path}"))
        print(spec_text(f"응답={response}"))

        self.assertEqual("req-101", response.request_id)
        self.assertIsNone(response.error_code)
        self.assertIsNone(response.error_message)
        self.assertIsInstance(response.result, dict)
        self.assertTrue(response.result)
        self.assertTrue(request_path.exists())
        self.assertTrue(response_path.exists())

    def test_dispatch_returns_error_envelope_when_controller_fails(self) -> None:
        print(spec_text("controller 실패는 transport error envelope 로 기록한다"))
        transport = FileTransport(self.transport_root, timeout_seconds=3.0)
        request = SessionRequestEnvelope(
            request_id="req-102",
            session_id="session-001",
            command=SessionCommand(
                command_type=CommandType.REQUEST_WITHDRAW,
                session_token="session-unknown",
                amount=100,
            ),
        )

        banking_server = self._start_banking_server()
        controller_server = self._start_controller_server()
        self.addCleanup(self._stop_process, controller_server)
        self.addCleanup(self._stop_process, banking_server)

        response = transport.dispatch(request)

        print(spec_text(f"응답={response}"))
        self.assertEqual("req-102", response.request_id)
        self.assertIsNone(response.result)
        self.assertEqual("ControllerError", response.error_code)
        self.assertTrue(response.error_message)

    def _start_banking_server(self):
        return self.start_module("banking", self.banking_root)

    def _start_controller_server(self):
        return self.start_module(
            "controller",
            self.transport_root,
            "--runtime-root",
            self.controller_root,
            "--banking-root",
            self.banking_root,
        )

    @staticmethod
    def _stop_process(process) -> None:
        process.terminate()
        process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
