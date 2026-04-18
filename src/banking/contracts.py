from __future__ import annotations

from enum import StrEnum


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


ERROR_INVALID_PIN = "Invalid PIN"
