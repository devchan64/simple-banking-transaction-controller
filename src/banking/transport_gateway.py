from __future__ import annotations

"""온보딩 메모: controller 와 banking 사이의 파일 통신 어댑터.

이 파일을 처음 읽을 때는 ``banking`` 내부 도메인 코드라기보다,
controller 가 banking 서버를 호출하기 위해 끼워 넣은 통합 어댑터로 이해하는 편이
더 정확하다.

한 줄 요약
---------
- 실제 전송 수단은 file transport 이다
- 하지만 controller 에서는 transport 를 직접 다루지 않고
  ``FileTransportBankGateway`` 메서드를 호출한다
- 그래서 이 타입은 bank gateway 이면서도, 동시에 bank 서버용 로컬 SDK/Client 처럼 보인다

형성 과정
--------
- 초기에는 bank 기능을 함수 호출에 가까운 방식으로 다루던 흐름이 있었다
- 이후 controller 와 banking 을 독립 프로세스로 분리하고,
  file transport 로 request/response 를 주고받는 구조로 옮겨 갔다
- 이 전환 과정에서 transport 경계를 직접 노출하기보다
  ``BankGateway`` 프로토콜을 유지한 채 런타임 구현만 file transport 기반으로
  바꿔 끼우는 방식이 선택되었다
- 그 결과 남은 것이 이 모듈이다

왜 이름과 위치가 헷갈리는가
-------------------------
- 역할만 보면 ``FileTransportBankGateway`` 는 ``Gateway`` 라기보다
  ``Sdk`` 나 ``Client`` 에 더 가깝다
- 또 controller 와 banking 의 통합 과정에서 생긴 어댑터인데
  ``banking`` 네임스페이스 안에 놓여 있다
- 그래서 bank 도메인 코드, 서버 엔트리, IPC 클라이언트 어댑터의 경계가
  처음 보는 사람에게는 함께 섞여 보일 수 있다

그래도 남아 있는 구현 의미
------------------------
- controller 서버가 banking 서버를 별도 프로세스로 두고 통신할 수 있다
- ``BankGateway`` 프로토콜을 바꾸지 않고도 런타임에서 file transport 구현을 주입할 수 있다
- bank 응답의 성공/실패를 controller 쪽 Python 객체와 예외로 다시 매핑할 수 있다

읽는 방법
--------
- 도메인 규칙은 이 파일이 아니라 ``bank_gateway.py`` 와 ``server.py`` 쪽에서 본다
- 이 파일은 "bank 기능을 어떻게 계산하는가"보다
  "banking 서버에 어떻게 요청을 보내고 결과를 받는가"에 집중해서 읽는다
- 따라서 이 모듈은 완성된 경계 설계의 결과라기보다,
  함수 호출 중심 접근에서 file transport 기반 통합으로 넘어가는 과정에서
  남은 어댑터라고 이해하면 온보딩에 가장 도움이 된다
"""

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
    """banking 서버와 파일 transport 로 통신하는 ``BankGateway`` 구현체."""

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
        """요청 파일을 쓰고 응답 파일을 기다린 뒤 bank 예외 모델로 변환한다."""
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
