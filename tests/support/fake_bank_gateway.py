from __future__ import annotations

from pathlib import Path
from typing import Callable

from banking import AccountRecord, CardRecord, JsonBankGateway


class FakeBankGateway:
    def __init__(
        self,
        cards_path: str | Path,
        accounts_path: str | Path,
        maintenance_enabled: bool = False,
    ) -> None:
        self._delegate = JsonBankGateway(
            cards_path,
            accounts_path,
            maintenance_enabled=maintenance_enabled,
        )
        self.on_get_card_by_number: Callable[[str], CardRecord] | None = None
        self.on_get_card_by_id: Callable[[str], CardRecord] | None = None
        self.on_verify_pin: Callable[[str, str], CardRecord] | None = None
        self.on_list_accounts: Callable[[str], list[str]] | None = None
        self.on_get_balance: Callable[[str], int] | None = None
        self.on_deposit: Callable[[str, int], int] | None = None
        self.on_withdraw: Callable[[str, int], int] | None = None

    def get_card_by_number(self, card_number: str) -> CardRecord:
        if self.on_get_card_by_number is not None:
            return self.on_get_card_by_number(card_number)
        return self._delegate.get_card_by_number(card_number)

    def get_card_by_id(self, card_id: str) -> CardRecord:
        if self.on_get_card_by_id is not None:
            return self.on_get_card_by_id(card_id)
        return self._delegate.get_card_by_id(card_id)

    def verify_pin(self, card_number: str, pin: str) -> CardRecord:
        if self.on_verify_pin is not None:
            return self.on_verify_pin(card_number, pin)
        return self._delegate.verify_pin(card_number, pin)

    def list_accounts(self, card_id: str) -> list[str]:
        if self.on_list_accounts is not None:
            return self.on_list_accounts(card_id)
        return self._delegate.list_accounts(card_id)

    def get_balance(self, account_id: str) -> int:
        if self.on_get_balance is not None:
            return self.on_get_balance(account_id)
        return self._delegate.get_balance(account_id)

    def deposit(self, account_id: str, amount: int) -> int:
        if self.on_deposit is not None:
            return self.on_deposit(account_id, amount)
        return self._delegate.deposit(account_id, amount)

    def withdraw(self, account_id: str, amount: int) -> int:
        if self.on_withdraw is not None:
            return self.on_withdraw(account_id, amount)
        return self._delegate.withdraw(account_id, amount)

    def get_account(self, account_id: str) -> AccountRecord:
        return self._delegate._get_account(account_id)
