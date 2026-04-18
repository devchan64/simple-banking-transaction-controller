from __future__ import annotations

import json
import unittest
from pathlib import Path

from banking_session_controller import (
    BankGatewayError,
    CardStatus,
    ERROR_INVALID_PIN,
    JsonBankGateway,
)
from spec_support import TestRootSupport, spec_text


class JsonBankGatewaySpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
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

    def test_get_balance_returns_current_balance(self) -> None:
        # 계좌 잔액을 현재 값 그대로 반환해야 한다.
        print(spec_text("계좌 잔액을 조회한다"))

        balance = self.gateway.get_balance("account-002")

        print(spec_text(f"잔액={balance}"))
        self.assertEqual(5400, balance)

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

    def test_verify_pin_rejects_inactive_card(self) -> None:
        # 비활성 카드면 PIN이 맞아도 인증을 실패해야 한다.
        print(spec_text("비활성 카드면 PIN 인증을 거부한다"))
        cards = json.loads(self.cards_path.read_text(encoding="utf-8"))
        cards[0]["status"] = CardStatus.INACTIVE
        self.cards_path.write_text(
            json.dumps(cards, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(BankGatewayError, "Inactive card"):
            self.gateway.verify_pin("4000-1234-5678-0001", "1234")

    def test_deposit_rejects_non_positive_amount(self) -> None:
        # 금액이 0 이하이면 입금을 거부해야 한다.
        print(spec_text("0 이하 금액 입금을 거부한다"))

        with self.assertRaisesRegex(BankGatewayError, "Invalid amount"):
            self.gateway.deposit("account-001", 0)

    def test_withdraw_rejects_non_positive_amount(self) -> None:
        # 금액이 0 이하이면 출금을 거부해야 한다.
        print(spec_text("0 이하 금액 출금을 거부한다"))

        with self.assertRaisesRegex(BankGatewayError, "Invalid amount"):
            self.gateway.withdraw("account-001", -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
