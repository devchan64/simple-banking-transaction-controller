from __future__ import annotations

import unittest

from controller import SessionResult, SessionState, TransactionType
from tests.support.spec_support import TestRootSupport, spec_text


class SessionResultSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()

    def test_session_result_requires_core_fields(self) -> None:
        print(spec_text("SessionResult 는 핵심 필드를 반드시 포함해야 한다"))

        result = SessionResult(
            succeeded=True,
            status_code="AUTHENTICATED",
            session_state=SessionState.AUTHENTICATED,
            message="PIN이 확인되었습니다.",
            session_closed=False,
        )

        self.assertTrue(result.succeeded)
        self.assertEqual("AUTHENTICATED", result.status_code)
        self.assertEqual(SessionState.AUTHENTICATED, result.session_state)
        self.assertEqual("PIN이 확인되었습니다.", result.message)
        self.assertFalse(result.session_closed)

    def test_session_result_accepts_account_list_after_authentication(self) -> None:
        print(spec_text("인증 직후 결과는 계좌 목록을 포함할 수 있다"))

        result = SessionResult(
            succeeded=True,
            status_code="ACCOUNT_LIST_READY",
            session_state=SessionState.AUTHENTICATED,
            session_token="session-001",
            message="계좌를 선택해주세요.",
            available_account_ids=["account-001", "account-002"],
            session_closed=False,
            remaining_pin_attempts=3,
        )

        self.assertEqual(["account-001", "account-002"], result.available_account_ids)
        self.assertEqual("session-001", result.session_token)
        self.assertEqual(3, result.remaining_pin_attempts)

    def test_session_result_accepts_transaction_fields(self) -> None:
        print(spec_text("거래 결과는 transaction_type, amount, balance 를 포함할 수 있다"))

        result = SessionResult(
            succeeded=True,
            status_code="WITHDRAW_COMPLETED",
            session_state=SessionState.TRANSACTION_EXECUTED,
            session_token="session-001",
            message="출금이 완료되었습니다.",
            selected_account_id="account-001",
            balance=900,
            transaction_type=TransactionType.WITHDRAW,
            requested_amount=100,
            session_closed=False,
        )

        self.assertEqual(TransactionType.WITHDRAW, result.transaction_type)
        self.assertEqual(100, result.requested_amount)
        self.assertEqual(900, result.balance)

    def test_session_result_rejects_non_int_balance(self) -> None:
        print(spec_text("SessionResult 는 balance 에 정수만 허용한다"))

        with self.assertRaisesRegex(Exception, "Input should be a valid integer"):
            SessionResult(
                succeeded=True,
                status_code="BALANCE_READY",
                session_state=SessionState.TRANSACTION_EXECUTED,
                message="잔액을 안내했습니다.",
                balance="900",  # type: ignore[arg-type]
                session_closed=False,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
