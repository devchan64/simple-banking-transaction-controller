from __future__ import annotations

import unittest
from itertools import count
from pathlib import Path

from controller import CommandType, SessionState, SessionCommand
from tests.support.process_support import ModuleProcessSupport
from tests.support.spec_support import TestRootSupport, flow_text, spec_text
from transport import FileTransport, SessionRequestEnvelope


class FlowE2ESpec(ModuleProcessSupport, TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/e2e") / self._testMethodName
        self.reset_test_root(self.test_root, "e2e test_root")
        self._request_sequence = count(1)

    def test_end_to_end_balance_procedure_reports_each_step(self) -> None:
        print(spec_text("카드 입력부터 잔액 조회까지 절차를 실제 controller 서버로 검증한다"))

        server = self.start_module("controller", self.test_root)
        try:
            insert_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.INSERT_CARD,
                    card_number="4000-1234-5678-0001",
                )
            )
            print(flow_text(f"카드 입력 응답={insert_response.result}"))

            session_token = insert_response.result["session_token"]
            submit_pin_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin="1234",
                ),
                session_id=session_token,
            )
            print(flow_text(f"PIN 인증 응답={submit_pin_response.result}"))

            account_id = submit_pin_response.result["available_account_ids"][0]
            select_account_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SELECT_ACCOUNT,
                    session_token=session_token,
                    account_id=account_id,
                ),
                session_id=session_token,
            )
            print(flow_text(f"계좌 선택 응답={select_account_response.result}"))

            balance_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.REQUEST_BALANCE,
                    session_token=session_token,
                ),
                session_id=session_token,
            )
            print(flow_text(f"잔액 조회 응답={balance_response.result}"))
        finally:
            server.terminate()
            server.wait(timeout=5)

        self.assertEqual("SESSION_STARTED", insert_response.result["status_code"])
        self.assertEqual(
            "카드를 확인했습니다. PIN을 입력해주세요.",
            insert_response.result["message"],
        )
        self.assertEqual("PIN_VERIFIED", submit_pin_response.result["status_code"])
        self.assertEqual(
            "PIN이 확인되었습니다. 계좌를 선택해주세요.",
            submit_pin_response.result["message"],
        )
        self.assertEqual("ACCOUNT_SELECTED", select_account_response.result["status_code"])
        self.assertEqual(
            "계좌가 선택되었습니다. 거래를 선택해주세요.",
            select_account_response.result["message"],
        )
        self.assertEqual("BALANCE_REPORTED", balance_response.result["status_code"])
        self.assertEqual(
            "현재 잔액을 안내했습니다.",
            balance_response.result["message"],
        )
        self.assertEqual(SessionState.RESULT_REPORTED, balance_response.result["session_state"])
        self.assertEqual(1200, balance_response.result["balance"])

    def test_end_to_end_invalid_pin_runs_retry_feedback_loop(self) -> None:
        print(spec_text("잘못된 PIN 1,2회는 남은 횟수를 안내하고 3회째에 세션을 종료해야 한다"))

        server = self.start_module("controller", self.test_root)
        try:
            insert_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.INSERT_CARD,
                    card_number="4000-1234-5678-0001",
                )
            )
            session_token = insert_response.result["session_token"]

            first_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin="9999",
                ),
                session_id=session_token,
            )
            print(flow_text(f"1차 PIN 실패 응답={first_response.result}"))

            second_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin="8888",
                ),
                session_id=session_token,
            )
            print(flow_text(f"2차 PIN 실패 응답={second_response.result}"))

            third_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin="7777",
                ),
                session_id=session_token,
            )
            print(flow_text(f"3차 PIN 실패 응답={third_response.result}"))

            followup_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin="1234",
                ),
                session_id=session_token,
            )
            print(flow_text(f"종료 후 후속 요청 응답={followup_response.error_message}"))
        finally:
            server.terminate()
            server.wait(timeout=5)

        self.assertIsNone(first_response.error_code)
        self.assertFalse(first_response.result["succeeded"])
        self.assertEqual(
            "PIN_FAILED_RETRYABLE",
            first_response.result["status_code"],
        )
        self.assertEqual(
            "PIN이 올바르지 않습니다. 3회 실패 시 세션이 종료되고 카드 사용이 중단됩니다. 남은 시도 2회.",
            first_response.result["message"],
        )
        self.assertEqual(
            SessionState.CARD_INSERTED,
            first_response.result["session_state"],
        )
        self.assertFalse(first_response.result["session_closed"])
        self.assertEqual(2, first_response.result["remaining_pin_attempts"])

        self.assertIsNone(second_response.error_code)
        self.assertFalse(second_response.result["succeeded"])
        self.assertEqual("PIN_FAILED_RETRYABLE", second_response.result["status_code"])
        self.assertEqual(
            "PIN이 올바르지 않습니다. 3회 실패 시 세션이 종료되고 카드 사용이 중단됩니다. 남은 시도 1회.",
            second_response.result["message"],
        )
        self.assertEqual(SessionState.CARD_INSERTED, second_response.result["session_state"])
        self.assertFalse(second_response.result["session_closed"])
        self.assertEqual(1, second_response.result["remaining_pin_attempts"])

        self.assertIsNone(third_response.error_code)
        self.assertFalse(third_response.result["succeeded"])
        self.assertEqual("PIN_ATTEMPTS_EXCEEDED", third_response.result["status_code"])
        self.assertEqual(
            "PIN 입력을 3회 실패했습니다. 세션을 종료합니다. 카드 사용이 중단되었습니다.",
            third_response.result["message"],
        )
        self.assertEqual(SessionState.SESSION_CLOSED, third_response.result["session_state"])
        self.assertTrue(third_response.result["session_closed"])
        self.assertEqual(0, third_response.result["remaining_pin_attempts"])

        self.assertEqual("ControllerError", followup_response.error_code)
        self.assertEqual("이미 종료된 세션입니다", followup_response.error_message)

    def test_end_to_end_force_end_interrupts_flow_and_rejects_followup(self) -> None:
        print(spec_text("강제 종료는 절차를 중단하고 이후 요청을 거부해야 한다"))

        server = self.start_module("controller", self.test_root)
        try:
            insert_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.INSERT_CARD,
                    card_number="4000-1234-5678-0001",
                )
            )
            session_token = insert_response.result["session_token"]

            submit_pin_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin="1234",
                ),
                session_id=session_token,
            )
            account_id = submit_pin_response.result["available_account_ids"][0]
            self._dispatch(
                SessionCommand(
                    command_type=CommandType.SELECT_ACCOUNT,
                    session_token=session_token,
                    account_id=account_id,
                ),
                session_id=session_token,
            )

            force_end_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.FORCE_END_SESSION,
                    session_token=session_token,
                ),
                session_id=session_token,
            )
            print(flow_text(f"강제 종료 응답={force_end_response.result}"))

            followup_response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.REQUEST_BALANCE,
                    session_token=session_token,
                ),
                session_id=session_token,
            )
            print(flow_text(f"종료 후 후속 요청 응답={followup_response.error_message}"))
        finally:
            server.terminate()
            server.wait(timeout=5)

        self.assertEqual("SESSION_CLOSED", force_end_response.result["status_code"])
        self.assertEqual(
            "세션이 종료되었습니다. 카드를 회수해주세요.",
            force_end_response.result["message"],
        )
        self.assertEqual(True, force_end_response.result["session_closed"])
        self.assertEqual("ControllerError", followup_response.error_code)
        self.assertEqual("이미 종료된 세션입니다", followup_response.error_message)

    def _dispatch(
        self,
        command: SessionCommand,
        session_id: str | None = None,
    ):
        request_id = f"e2e-{next(self._request_sequence):03d}"
        transport = FileTransport(
            transport_root=self.test_root,
            poll_interval_seconds=0.01,
            timeout_seconds=3.0,
        )
        request = SessionRequestEnvelope(
            request_id=request_id,
            session_id=session_id,
            command=command,
        )
        return transport.dispatch(request)


if __name__ == "__main__":
    unittest.main(verbosity=2)
