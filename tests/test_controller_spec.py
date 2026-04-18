from __future__ import annotations

import shutil
import unittest
from pathlib import Path

from banking import JsonBankGateway, SessionHistoryStore
from controller import (
    BankingSessionController,
    CommandType,
    ControllerError,
    JsonSessionStore,
    SessionState,
    TransactionType,
)
from spec_support import TestRootSupport, spec_text


class BankingSessionControllerSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/controller") / self._testMethodName
        print(f"[초기화] controller test_root 삭제={self.test_root}")
        shutil.rmtree(self.test_root, ignore_errors=True)
        self.test_root.mkdir(parents=True, exist_ok=True)

        self.cards_path = self.test_root / "cards.json"
        self.accounts_path = self.test_root / "accounts.json"
        self.session_history_path = self.test_root / "session-history.json"
        self.active_sessions_path = self.test_root / "active-sessions.json"

        shutil.copy(Path("mock-db/cards.json"), self.cards_path)
        shutil.copy(Path("mock-db/accounts.json"), self.accounts_path)

        bank_gateway = JsonBankGateway(self.cards_path, self.accounts_path)
        session_history_store = SessionHistoryStore(self.session_history_path)
        session_store = JsonSessionStore(self.active_sessions_path)
        self.controller = BankingSessionController(
            bank_gateway=bank_gateway,
            session_history_store=session_history_store,
            session_store=session_store,
        )

    def test_insert_card_starts_session(self) -> None:
        print(spec_text("INSERT_CARD 는 세션을 시작하고 토큰을 반환한다"))

        result = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )

        self.assertEqual(SessionState.CARD_INSERTED, result.session_state)
        self.assertTrue(result.session_token)
        self.assertFalse(result.session_closed)

    def test_submit_pin_returns_available_accounts(self) -> None:
        print(spec_text("SUBMIT_PIN 성공 후 계좌 목록을 반환한다"))

        session = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )
        result = self.controller.handle(
            {
                "command_type": CommandType.SUBMIT_PIN,
                "session_token": session.session_token,
                "pin": "1234",
            }
        )

        self.assertEqual(SessionState.AUTHENTICATED, result.session_state)
        self.assertEqual(["account-001", "account-002"], result.available_account_ids)

    def test_select_account_before_authentication_fails(self) -> None:
        print(spec_text("인증 전 SELECT_ACCOUNT 는 실패한다"))

        session = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )

        with self.assertRaisesRegex(ControllerError, "Invalid session state"):
            self.controller.handle(
                {
                    "command_type": CommandType.SELECT_ACCOUNT,
                    "session_token": session.session_token,
                    "account_id": "account-001",
                }
            )

    def test_request_balance_requires_selected_account(self) -> None:
        print(spec_text("계좌 선택 전 REQUEST_BALANCE 는 실패한다"))

        session = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )
        authenticated = self.controller.handle(
            {
                "command_type": CommandType.SUBMIT_PIN,
                "session_token": session.session_token,
                "pin": "1234",
            }
        )

        with self.assertRaisesRegex(ControllerError, "Invalid session state"):
            self.controller.handle(
                {
                    "command_type": CommandType.REQUEST_BALANCE,
                    "session_token": authenticated.session_token,
                }
            )

    def test_balance_flow_reports_result(self) -> None:
        print(spec_text("정상 잔액 조회 흐름은 RESULT_REPORTED 로 끝난다"))

        session = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )
        authenticated = self.controller.handle(
            {
                "command_type": CommandType.SUBMIT_PIN,
                "session_token": session.session_token,
                "pin": "1234",
            }
        )
        selected = self.controller.handle(
            {
                "command_type": CommandType.SELECT_ACCOUNT,
                "session_token": authenticated.session_token,
                "account_id": "account-001",
            }
        )
        result = self.controller.handle(
            {
                "command_type": CommandType.REQUEST_BALANCE,
                "session_token": selected.session_token,
            }
        )

        self.assertEqual(SessionState.RESULT_REPORTED, result.session_state)
        self.assertEqual(TransactionType.BALANCE, result.transaction_type)
        self.assertEqual(1200, result.balance)
        self.assertEqual("account-001", result.selected_account_id)

    def test_withdraw_flow_updates_balance_and_allows_end_session(self) -> None:
        print(spec_text("출금 후 결과를 보고하고 END_SESSION 으로 종료할 수 있다"))

        session = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )
        authenticated = self.controller.handle(
            {
                "command_type": CommandType.SUBMIT_PIN,
                "session_token": session.session_token,
                "pin": "1234",
            }
        )
        selected = self.controller.handle(
            {
                "command_type": CommandType.SELECT_ACCOUNT,
                "session_token": authenticated.session_token,
                "account_id": "account-001",
            }
        )
        withdraw = self.controller.handle(
            {
                "command_type": CommandType.REQUEST_WITHDRAW,
                "session_token": selected.session_token,
                "amount": 100,
            }
        )
        closed = self.controller.handle(
            {
                "command_type": CommandType.END_SESSION,
                "session_token": withdraw.session_token,
            }
        )

        self.assertEqual(SessionState.RESULT_REPORTED, withdraw.session_state)
        self.assertEqual(TransactionType.WITHDRAW, withdraw.transaction_type)
        self.assertEqual(1100, withdraw.balance)
        self.assertEqual(SessionState.SESSION_CLOSED, closed.session_state)
        self.assertTrue(closed.session_closed)

    def test_closed_session_rejects_followup_command(self) -> None:
        print(spec_text("종료된 세션은 이후 입력을 거부한다"))

        session = self.controller.handle(
            {
                "command_type": CommandType.INSERT_CARD,
                "card_number": "4000-1234-5678-0001",
            }
        )
        closed = self.controller.handle(
            {
                "command_type": CommandType.END_SESSION,
                "session_token": session.session_token,
            }
        )

        self.assertTrue(closed.session_closed)

        with self.assertRaisesRegex(ControllerError, "Session already closed"):
            self.controller.handle(
                {
                    "command_type": CommandType.SUBMIT_PIN,
                    "session_token": session.session_token,
                    "pin": "1234",
                }
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
