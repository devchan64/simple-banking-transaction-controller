from __future__ import annotations

from enum import StrEnum


class CardStatus(StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    LOCKED = "LOCKED"


ERROR_INVALID_PIN = "PIN이 올바르지 않습니다."
ERROR_ACCOUNT_LOCKED = "계정이 잠겨 있습니다. 은행에 문의해주세요."
ERROR_BANK_MAINTENANCE = "현재 은행 점검 중입니다. 잠시 후 다시 시도해주세요."
ERROR_PIN_ATTEMPTS_EXCEEDED = (
    "PIN 입력을 3회 실패하여 카드 사용이 중단되었습니다. 은행에 문의해주세요."
)
