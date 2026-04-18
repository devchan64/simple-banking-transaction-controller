from __future__ import annotations

from enum import StrEnum


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class CommandType(StrEnum):
    INSERT_CARD = "INSERT_CARD"
    SUBMIT_PIN = "SUBMIT_PIN"
    SELECT_ACCOUNT = "SELECT_ACCOUNT"
    REQUEST_BALANCE = "REQUEST_BALANCE"
    REQUEST_DEPOSIT = "REQUEST_DEPOSIT"
    REQUEST_WITHDRAW = "REQUEST_WITHDRAW"
    END_SESSION = "END_SESSION"


class FieldName(StrEnum):
    COMMAND_TYPE = "command_type"
    STATUS = "status"


class ResultStatus(StrEnum):
    OK = "ok"


ERROR_INVALID_STATE = "invalid state"
ERROR_INVALID_PIN = "Invalid PIN"
