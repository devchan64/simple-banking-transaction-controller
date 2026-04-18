from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .contracts import CardStatus, ERROR_INVALID_PIN


class BankGatewayError(RuntimeError):
    pass


@dataclass(frozen=True)
class CardRecord:
    card_id: str
    card_number: str
    cardholder_name: str
    expires_at: str
    status: str
    pin: str
    account_ids: list[str]


@dataclass(frozen=True)
class AccountRecord:
    account_id: str
    balance: int


class JsonBankGateway:
    def __init__(self, cards_path: str | Path, accounts_path: str | Path) -> None:
        self._cards_path = Path(cards_path)
        self._accounts_path = Path(accounts_path)

    def get_card_by_number(self, card_number: str) -> CardRecord:
        for card in self._read_cards():
            if card.card_number == card_number:
                return card
        raise BankGatewayError(f"Unknown card number: {card_number}")

    def get_card_by_id(self, card_id: str) -> CardRecord:
        for card in self._read_cards():
            if card.card_id == card_id:
                return card
        raise BankGatewayError(f"Unknown card id: {card_id}")

    def verify_pin(self, card_number: str, pin: str) -> CardRecord:
        card = self.get_card_by_number(card_number)
        self._require_active_card(card)
        self._require_matching_pin(card, pin)
        return card

    def list_accounts(self, card_id: str) -> list[str]:
        return self.get_card_by_id(card_id).account_ids

    def get_balance(self, account_id: str) -> int:
        return self._get_account(account_id).balance

    def deposit(self, account_id: str, amount: int) -> int:
        self._require_positive_amount(amount)
        account = self._get_account(account_id)
        updated = AccountRecord(
            account_id=account.account_id, balance=account.balance + amount
        )
        self._save_account(updated)
        return updated.balance

    def withdraw(self, account_id: str, amount: int) -> int:
        self._require_positive_amount(amount)
        account = self._get_account(account_id)
        if account.balance < amount:
            raise BankGatewayError(f"Insufficient balance: {account_id}")
        updated = AccountRecord(
            account_id=account.account_id, balance=account.balance - amount
        )
        self._save_account(updated)
        return updated.balance

    def _get_account(self, account_id: str) -> AccountRecord:
        for account in self._read_accounts():
            if account.account_id == account_id:
                return account
        raise BankGatewayError(f"Unknown account id: {account_id}")

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
            raise BankGatewayError(f"Unknown account id: {updated_account.account_id}")
        self._write_accounts(accounts)

    def _read_cards(self) -> list[CardRecord]:
        payload = json.loads(self._cards_path.read_text(encoding="utf-8"))
        return [CardRecord(**item) for item in payload]

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
    def _require_active_card(card: CardRecord) -> None:
        if card.status != CardStatus.ACTIVE:
            raise BankGatewayError(f"Inactive card: {card.card_id}")

    @staticmethod
    def _require_matching_pin(card: CardRecord, pin: str) -> None:
        if card.pin != pin:
            raise BankGatewayError(ERROR_INVALID_PIN)

    @staticmethod
    def _require_positive_amount(amount: int) -> None:
        if amount <= 0:
            raise BankGatewayError(f"Invalid amount: {amount}")
