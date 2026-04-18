from __future__ import annotations

import unittest
from pathlib import Path

from banking import (
    BankGatewayError,
    CardStatus,
    ERROR_ACCOUNT_LOCKED,
    ERROR_INVALID_PIN,
    ERROR_PIN_ATTEMPTS_EXCEEDED,
    JsonBankGateway,
    PinVerificationError,
)
from tests.support.spec_support import TestRootSupport, spec_text


class JsonBankGatewaySpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/bank-gateway") / self._testMethodName
        # 이전 테스트 산출물을 지워서 매 테스트가 같은 JSON 상태에서 시작되게 한다.
        self.reset_test_root(self.test_root)

        self.cards_path = self.test_root / "cards.json"
        self.accounts_path = self.test_root / "accounts.json"
        self.cards_path.write_text(
            Path("mock-db/cards.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.accounts_path.write_text(
            Path("mock-db/accounts.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        self.gateway = JsonBankGateway(self.cards_path, self.accounts_path)

    def test_verify_pin_returns_card_when_card_number_and_pin_match(self) -> None:
        # 카드 번호와 PIN이 맞으면 인증된 카드 정보를 돌려줘야 한다.
        print(spec_text("카드 번호와 PIN이 맞으면 카드 정보를 반환한다"))

        card = self.gateway.verify_pin("4000-1234-5678-0001", "1234")

        print(spec_text(f"카드={card}"))
        self.assertEqual("card-001", card.card_id)
        self.assertEqual(["account-001", "account-002"], card.account_ids)

    def test_list_accounts_returns_account_ids_for_card(self) -> None:
        # 카드에 연결된 계좌 목록을 읽을 수 있어야 한다.
        print(spec_text("카드에 연결된 계좌 목록을 반환한다"))

        accounts = self.gateway.list_accounts("card-003")

        print(spec_text(f"계좌 목록={accounts}"))
        self.assertEqual(["account-004", "account-005"], accounts)

    def test_list_accounts_returns_single_account_for_new_fixture_card(self) -> None:
        # fixture 에 추가된 단일 계좌 카드도 그대로 읽을 수 있어야 한다.
        print(spec_text("단일 계좌 카드 fixture 도 계좌 목록을 반환한다"))

        accounts = self.gateway.list_accounts("card-007")

        print(spec_text(f"계좌 목록={accounts}"))
        self.assertEqual(["account-009"], accounts)

    def test_get_balance_returns_current_balance(self) -> None:
        # 계좌 잔액을 현재 값 그대로 반환해야 한다.
        print(spec_text("계좌 잔액을 조회한다"))

        balance = self.gateway.get_balance("account-002")

        print(spec_text(f"잔액={balance}"))
        self.assertEqual(5400, balance)

    def test_get_balance_returns_zero_for_empty_balance_fixture(self) -> None:
        # 0원 계좌 fixture 도 그대로 조회되어야 한다.
        print(spec_text("0원 계좌 fixture 의 잔액을 조회한다"))

        balance = self.gateway.get_balance("account-007")

        print(spec_text(f"잔액={balance}"))
        self.assertEqual(0, balance)

    def test_deposit_updates_account_balance(self) -> None:
        # 입금 후에는 accounts.json의 잔액도 함께 갱신되어야 한다.
        print(spec_text("입금 후 accounts.json 잔액을 갱신한다"))

        balance = self.gateway.deposit("account-001", 300)

        print(spec_text(f"입금 후 잔액={balance}"))
        self.assertEqual(1500, balance)
        self.assertEqual(1500, self.gateway.get_balance("account-001"))

    def test_withdraw_updates_account_balance(self) -> None:
        # 출금 후에는 accounts.json의 잔액도 함께 갱신되어야 한다.
        print(spec_text("출금 후 accounts.json 잔액을 갱신한다"))

        balance = self.gateway.withdraw("account-004", 900)

        print(spec_text(f"출금 후 잔액={balance}"))
        self.assertEqual(8000, balance)
        self.assertEqual(8000, self.gateway.get_balance("account-004"))

    def test_withdraw_rejects_insufficient_balance(self) -> None:
        # 잔액이 부족하면 출금을 거부해야 한다.
        print(spec_text("잔액 부족이면 출금을 거부한다"))

        with self.assertRaises(BankGatewayError):
            self.gateway.withdraw("account-006", 100)

    def test_verify_pin_rejects_invalid_pin(self) -> None:
        # PIN이 틀리면 인증을 실패해야 한다.
        print(spec_text("PIN이 틀리면 인증을 실패한다"))

        with self.assertRaisesRegex(BankGatewayError, ERROR_INVALID_PIN):
            self.gateway.verify_pin("4000-1234-5678-0002", "0000")

        card = self.gateway.get_card_by_number("4000-1234-5678-0002")
        self.assertEqual(CardStatus.ACTIVE, card.status)
        self.assertEqual(1, card.pin_failure_count)

    def test_verify_pin_locks_card_after_third_invalid_attempt(self) -> None:
        print(spec_text("PIN 3회 실패 시 bank 가 카드를 사용중단 상태로 만든다"))

        for invalid_pin in ("0000", "1111"):
            with self.assertRaisesRegex(BankGatewayError, ERROR_INVALID_PIN):
                self.gateway.verify_pin("4000-1234-5678-0002", invalid_pin)

        with self.assertRaisesRegex(BankGatewayError, ERROR_PIN_ATTEMPTS_EXCEEDED):
            self.gateway.verify_pin("4000-1234-5678-0002", "2222")

        card = self.gateway.get_card_by_number("4000-1234-5678-0002")
        self.assertEqual(CardStatus.LOCKED, card.status)
        self.assertEqual(3, card.pin_failure_count)

    def test_verify_pin_reports_remaining_attempts(self) -> None:
        print(spec_text("PIN 실패 시 bank 는 남은 시도 횟수를 함께 제공한다"))

        with self.assertRaises(PinVerificationError) as exc_info:
            self.gateway.verify_pin("4000-1234-5678-0002", "0000")

        self.assertEqual(2, exc_info.exception.remaining_attempts)
        self.assertFalse(exc_info.exception.card_locked)

    def test_verify_pin_rejects_inactive_card(self) -> None:
        # fixture 상 비활성 카드면 PIN이 맞아도 인증을 실패해야 한다.
        print(spec_text("비활성 카드면 PIN 인증을 거부한다"))

        with self.assertRaisesRegex(BankGatewayError, "비활성 카드입니다"):
            self.gateway.verify_pin("4000-1234-5678-0006", "8888")

    def test_verify_pin_rejects_locked_card(self) -> None:
        # fixture 상 잠긴 카드는 사용자 안내 메시지로 인증을 실패해야 한다.
        print(spec_text("잠긴 카드 fixture 는 안내 메시지로 PIN 인증을 거부한다"))

        with self.assertRaisesRegex(BankGatewayError, ERROR_ACCOUNT_LOCKED):
            self.gateway.verify_pin("4000-1234-5678-0005", "7777")

    def test_deposit_rejects_non_positive_amount(self) -> None:
        # 금액이 0 이하이면 입금을 거부해야 한다.
        print(spec_text("0 이하 금액 입금을 거부한다"))

        with self.assertRaisesRegex(BankGatewayError, "올바르지 않은 금액입니다"):
            self.gateway.deposit("account-001", 0)

    def test_withdraw_rejects_non_positive_amount(self) -> None:
        # 금액이 0 이하이면 출금을 거부해야 한다.
        print(spec_text("0 이하 금액 출금을 거부한다"))

        with self.assertRaisesRegex(BankGatewayError, "올바르지 않은 금액입니다"):
            self.gateway.withdraw("account-001", -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
