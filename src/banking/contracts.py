from __future__ import annotations

from enum import StrEnum


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


ERROR_INVALID_PIN = "Invalid PIN"
ERROR_ACCOUNT_LOCKED = "This account is locked. Please contact the bank."
ERROR_BANK_MAINTENANCE = (
    "Bank service is temporarily unavailable due to maintenance."
)
