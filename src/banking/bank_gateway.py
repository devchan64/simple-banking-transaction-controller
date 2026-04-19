from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .contracts import (
    CardStatus,
    ERROR_ACCOUNT_LOCKED,
    ERROR_BANK_MAINTENANCE,
    ERROR_INVALID_PIN,
    ERROR_PIN_ATTEMPTS_EXCEEDED,
)


class BankGatewayError(RuntimeError):
    pass


class PinVerificationError(BankGatewayError):
    def __init__(
        self,
        message: str,
        *,
        remaining_attempts: int,
        card_locked: bool,
    ) -> None:
        super().__init__(message)
        self.remaining_attempts = remaining_attempts
        self.card_locked = card_locked


@dataclass(frozen=True)
class BankingSession:
    session_token: str
    card_id: str
    expires_at: str


class BankGateway(Protocol):
    def create_session(self, card_id: str) -> BankingSession: ...

    def get_session(self, session_token: str) -> BankingSession: ...

    def refresh_session(self, session_token: str) -> BankingSession: ...

    def get_card_by_number(self, card_number: str) -> "CardRecord": ...

    def get_card_by_id(self, card_id: str) -> "CardRecord": ...

    def verify_pin(self, card_number: str, pin: str) -> "CardRecord": ...

    def list_accounts(self, card_id: str) -> list[str]: ...

    def get_balance(self, account_id: str) -> int: ...

    def deposit(self, account_id: str, amount: int) -> int: ...

    def withdraw(self, account_id: str, amount: int) -> int: ...


@dataclass(frozen=True)
class CardRecord:
    card_id: str
    card_number: str
    cardholder_name: str
    expires_at: str
    status: str
    pin: str
    account_ids: list[str]
    pin_failure_count: int = 0


@dataclass(frozen=True)
class AccountRecord:
    account_id: str
    balance: int


class JsonBankGateway:
    def __init__(
        self,
        cards_path: str | Path,
        accounts_path: str | Path,
        maintenance_enabled: bool = False,
    ) -> None:
        self._cards_path = Path(cards_path)
        self._accounts_path = Path(accounts_path)
        self._maintenance_enabled = maintenance_enabled

    def get_card_by_number(self, card_number: str) -> CardRecord:
        for card in self._read_cards():
            if card.card_number == card_number:
                return card
        raise BankGatewayError(f"알 수 없는 카드 번호입니다: {card_number}")

    def create_session(self, card_id: str) -> BankingSession:
        raise BankGatewayError("세션 생성은 아직 구현되지 않았습니다")

    def get_session(self, session_token: str) -> BankingSession:
        raise BankGatewayError("세션 조회는 아직 구현되지 않았습니다")

    def refresh_session(self, session_token: str) -> BankingSession:
        raise BankGatewayError("세션 갱신은 아직 구현되지 않았습니다")

    def get_card_by_id(self, card_id: str) -> CardRecord:
        for card in self._read_cards():
            if card.card_id == card_id:
                return card
        raise BankGatewayError(f"알 수 없는 카드 ID입니다: {card_id}")

    def verify_pin(self, card_number: str, pin: str) -> CardRecord:
        self._require_service_available()
        card = self.get_card_by_number(card_number)
        self._require_available_card(card)
        self._verify_pin_or_update_card(card, pin)
        if card.pin_failure_count != 0:
            card = self._save_card(
                card,
                pin_failure_count=0,
            )
        return card

    def list_accounts(self, card_id: str) -> list[str]:
        self._require_service_available()
        return self.get_card_by_id(card_id).account_ids

    def get_balance(self, account_id: str) -> int:
        self._require_service_available()
        return self._get_account(account_id).balance

    def deposit(self, account_id: str, amount: int) -> int:
        self._require_service_available()
        self._require_positive_amount(amount)
        account = self._get_account(account_id)
        updated = AccountRecord(
            account_id=account.account_id, balance=account.balance + amount
        )
        self._save_account(updated)
        return updated.balance

    def withdraw(self, account_id: str, amount: int) -> int:
        self._require_service_available()
        self._require_positive_amount(amount)
        account = self._get_account(account_id)
        if account.balance < amount:
            raise BankGatewayError(f"잔액이 부족합니다: {account_id}")
        updated = AccountRecord(
            account_id=account.account_id, balance=account.balance - amount
        )
        self._save_account(updated)
        return updated.balance

    def _get_account(self, account_id: str) -> AccountRecord:
        for account in self._read_accounts():
            if account.account_id == account_id:
                return account
        raise BankGatewayError(f"알 수 없는 계좌입니다: {account_id}")

    def _save_account(self, updated_account: AccountRecord) -> None:
        accounts = []
        found = False
        for account in self._read_accounts():
            if account.account_id == updated_account.account_id:
                accounts.append(updated_account)
                found = True
            else:
                accounts.append(account)
        if not found:
            raise BankGatewayError(
                f"알 수 없는 계좌입니다: {updated_account.account_id}"
            )
        self._write_accounts(accounts)

    def _save_card(self, card: CardRecord, **updates: object) -> CardRecord:
        updated_card = CardRecord(
            card_id=card.card_id,
            card_number=card.card_number,
            cardholder_name=card.cardholder_name,
            expires_at=card.expires_at,
            status=updates.get("status", card.status),
            pin=card.pin,
            account_ids=card.account_ids,
            pin_failure_count=updates.get(
                "pin_failure_count",
                card.pin_failure_count,
            ),
        )

        cards = []
        found = False
        for current_card in self._read_cards():
            if current_card.card_id == updated_card.card_id:
                cards.append(updated_card)
                found = True
            else:
                cards.append(current_card)

        if not found:
            raise BankGatewayError(f"알 수 없는 카드 ID입니다: {updated_card.card_id}")

        self._write_cards(cards)
        return updated_card

    def _read_cards(self) -> list[CardRecord]:
        payload = json.loads(self._cards_path.read_text(encoding="utf-8"))
        return [CardRecord(**item) for item in payload]

    def _write_cards(self, cards: list[CardRecord]) -> None:
        payload = [
            {
                "card_id": card.card_id,
                "card_number": card.card_number,
                "cardholder_name": card.cardholder_name,
                "expires_at": card.expires_at,
                "status": card.status,
                "pin": card.pin,
                "account_ids": card.account_ids,
                "pin_failure_count": card.pin_failure_count,
            }
            for card in cards
        ]
        self._cards_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _read_accounts(self) -> list[AccountRecord]:
        payload = json.loads(self._accounts_path.read_text(encoding="utf-8"))
        return [AccountRecord(**item) for item in payload]

    def _write_accounts(self, accounts: list[AccountRecord]) -> None:
        payload = [
            {"account_id": account.account_id, "balance": account.balance}
            for account in accounts
        ]
        self._accounts_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _require_available_card(card: CardRecord) -> None:
        if card.status == CardStatus.LOCKED:
            raise BankGatewayError(ERROR_ACCOUNT_LOCKED)
        if card.status != CardStatus.ACTIVE:
            raise BankGatewayError(f"비활성 카드입니다: {card.card_id}")

    def _require_service_available(self) -> None:
        if self._maintenance_enabled:
            raise BankGatewayError(ERROR_BANK_MAINTENANCE)

    def _verify_pin_or_update_card(self, card: CardRecord, pin: str) -> None:
        if card.pin != pin:
            failure_count = card.pin_failure_count + 1
            remaining_attempts = max(0, 3 - failure_count)
            if failure_count >= 3:
                self._save_card(
                    card,
                    status=CardStatus.LOCKED,
                    pin_failure_count=3,
                )
                raise PinVerificationError(
                    ERROR_PIN_ATTEMPTS_EXCEEDED,
                    remaining_attempts=0,
                    card_locked=True,
                )

            self._save_card(
                card,
                pin_failure_count=failure_count,
            )
            raise PinVerificationError(
                ERROR_INVALID_PIN,
                remaining_attempts=remaining_attempts,
                card_locked=False,
            )

    @staticmethod
    def _require_positive_amount(amount: int) -> None:
        if amount <= 0:
            raise BankGatewayError(f"올바르지 않은 금액입니다: {amount}")
