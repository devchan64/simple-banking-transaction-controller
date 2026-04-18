from __future__ import annotations

from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt

from .contracts import SessionState, TransactionType


class SessionResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    succeeded: StrictBool
    status_code: str
    session_state: SessionState
    message: str
    session_closed: StrictBool
    session_token: str | None = None
    available_account_ids: list[str] | None = None
    selected_account_id: str | None = None
    balance: StrictInt | None = None
    transaction_type: TransactionType | None = None
    requested_amount: StrictInt | None = None
    remaining_pin_attempts: StrictInt | None = None
