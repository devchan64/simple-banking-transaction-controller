from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class BankAction(StrEnum):
    GET_CARD_BY_NUMBER = "GET_CARD_BY_NUMBER"
    GET_CARD_BY_ID = "GET_CARD_BY_ID"
    VERIFY_PIN = "VERIFY_PIN"
    LIST_ACCOUNTS = "LIST_ACCOUNTS"
    GET_BALANCE = "GET_BALANCE"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


class BankRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    request_id: str
    action: BankAction
    card_number: str | None = None
    card_id: str | None = None
    pin: str | None = None
    account_id: str | None = None
    amount: int | None = None


class BankResponse(BaseModel):
    request_id: str
    payload: dict[str, object] | None = None
    error_code: str | None = None
    error_message: str | None = None
