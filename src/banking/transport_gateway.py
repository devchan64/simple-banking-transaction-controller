from __future__ import annotations

import json
import time
import uuid
from pathlib import Path

from .bank_gateway import (
    BankGateway,
    BankGatewayError,
    CardRecord,
    PinVerificationError,
)
from .protocol import BankAction, BankRequest, BankResponse


class FileTransportBankGateway(BankGateway):
    def __init__(
        self,
        transport_root: str | Path,
        poll_interval_seconds: float = 0.01,
        timeout_seconds: float = 3.0,
    ) -> None:
        self._root = Path(transport_root)
        self._requests_dir = self._root / "requests"
        self._responses_dir = self._root / "responses"
        self._poll_interval_seconds = poll_interval_seconds
        self._timeout_seconds = timeout_seconds
        self._requests_dir.mkdir(parents=True, exist_ok=True)
        self._responses_dir.mkdir(parents=True, exist_ok=True)

    def get_card_by_number(self, card_number: str) -> CardRecord:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.GET_CARD_BY_NUMBER,
                card_number=card_number,
            )
        )
        return CardRecord(**payload)

    def get_card_by_id(self, card_id: str) -> CardRecord:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.GET_CARD_BY_ID,
                card_id=card_id,
            )
        )
        return CardRecord(**payload)

    def verify_pin(self, card_number: str, pin: str) -> CardRecord:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.VERIFY_PIN,
                card_number=card_number,
                pin=pin,
            )
        )
        return CardRecord(**payload)

    def list_accounts(self, card_id: str) -> list[str]:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.LIST_ACCOUNTS,
                card_id=card_id,
            )
        )
        return payload["account_ids"]

    def get_balance(self, account_id: str) -> int:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.GET_BALANCE,
                account_id=account_id,
            )
        )
        return payload["balance"]

    def deposit(self, account_id: str, amount: int) -> int:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.DEPOSIT,
                account_id=account_id,
                amount=amount,
            )
        )
        return payload["balance"]

    def withdraw(self, account_id: str, amount: int) -> int:
        payload = self._dispatch(
            BankRequest(
                request_id=self._request_id(),
                action=BankAction.WITHDRAW,
                account_id=account_id,
                amount=amount,
            )
        )
        return payload["balance"]

    def _dispatch(self, request: BankRequest) -> dict[str, object]:
        self._write_request(request)
        response = self._wait_for_response(request.request_id)
        if response.error_code is None:
            return response.payload

        if response.error_code == "PinVerificationError":
            details = response.error_details or {}
            raise PinVerificationError(
                response.error_message,
                remaining_attempts=int(details.get("remaining_attempts", 0)),
                card_locked=bool(details.get("card_locked", False)),
            )

        raise BankGatewayError(response.error_message)

    def _write_request(self, request: BankRequest) -> None:
        request_path = self._requests_dir / f"{request.request_id}.json"
        request_path.write_text(
            json.dumps(request.model_dump(mode="json"), ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    def _wait_for_response(self, request_id: str) -> BankResponse:
        response_path = self._responses_dir / f"{request_id}.json"
        deadline = time.monotonic() + self._timeout_seconds
        while time.monotonic() < deadline:
            if response_path.exists():
                return BankResponse.model_validate(
                    json.loads(response_path.read_text(encoding="utf-8"))
                )
            time.sleep(self._poll_interval_seconds)
        raise BankGatewayError(f"Timed out waiting for bank response: {request_id}")

    @staticmethod
    def _request_id() -> str:
        return f"bank-{uuid.uuid4().hex}"
