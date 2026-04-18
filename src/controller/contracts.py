from __future__ import annotations

from enum import StrEnum


class CommandType(StrEnum):
    INSERT_CARD = "INSERT_CARD"
    SUBMIT_PIN = "SUBMIT_PIN"
    SELECT_ACCOUNT = "SELECT_ACCOUNT"
    REQUEST_BALANCE = "REQUEST_BALANCE"
    REQUEST_DEPOSIT = "REQUEST_DEPOSIT"
    REQUEST_WITHDRAW = "REQUEST_WITHDRAW"
    FORCE_END_SESSION = "FORCE_END_SESSION"


class FieldName(StrEnum):
    COMMAND_TYPE = "command_type"
    STATUS = "status"


class ResultStatus(StrEnum):
    OK = "ok"


class SessionState(StrEnum):
    IDLE = "IDLE"
    CARD_INSERTED = "CARD_INSERTED"
    AUTHENTICATED = "AUTHENTICATED"
    ACCOUNT_SELECTED = "ACCOUNT_SELECTED"
    TRANSACTION_EXECUTED = "TRANSACTION_EXECUTED"
    RESULT_REPORTED = "RESULT_REPORTED"
    SESSION_CLOSED = "SESSION_CLOSED"


class TransactionType(StrEnum):
    BALANCE = "BALANCE"
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


ERROR_INVALID_STATE = "invalid state"
