from __future__ import annotations

"""controller 상태머신 구현.

이 모듈은 현재 ATM 절차의 핵심 상태 전이를 담당하지만,
세션 설계 관점에서는 마무리되지 못한 과도기 구현의 성격도 함께 가진다.

배경
----
- 초기 목표 중 하나는 서버가 세션 토큰을 발급하고,
  controller 는 그 토큰을 바탕으로 인증된 세션 흐름을 처리하며,
  이후 만료, 갱신(refresh), 추가 검증 같은 세션 규칙까지 한 흐름으로
  정리하는 것이었다.
- 하지만 실제 구현은 그 목표를 끝까지 밀어붙이지 못했다.
  그 결과 토큰 발급 이력과 활성 세션 상태가 서로 다른 저장소로 분리되어 있고,
  서버와 controller 사이의 세션 책임도 충분히 정리되지 않은 채 남아 있다.

현재 구조의 한계
----------------
- 세션 토큰 발급은 ``SessionHistoryStore`` 가 담당한다.
- 현재 활성 세션 상태와 상태 전이는 ``JsonSessionStore`` 가 담당한다.
- 서버는 controller 와 저장소를 조립해 요청을 전달하지만,
  세션 만료/리프레시/추가 인증 같은 상위 세션 정책은 제공하지 않는다.

즉 현재 구현은 "controller 상태머신"은 제공하지만,
"완성된 세션 시스템"까지는 제공하지 못한다.

향후 정리 시 반영되면 좋은 점
---------------------------
- 세션 토큰의 발급 주체와 검증 주체를 더 명확히 나눌 것
- 세션 이력과 활성 세션 상태의 단일 진실 원천을 정할 것
- 만료 시각, 갱신 시각, 추가 인증 문맥 같은 세션 메타데이터를
  어느 계층이 관리할지 결정할 것
- 서버와 controller 가 각각 세션을 따로 들고 있는 모양이 아니라,
  하나의 세션 생명주기를 공유하도록 정리할 것

따라서 이 모듈을 읽을 때는 현재 동작하는 상태 전이 로직과 별개로,
세션 책임 분리가 아직 완료되지 않은 코드라는 점을 함께 염두에 둘 필요가 있다.
"""

from banking import (
    BankGateway,
    BankGatewayError,
    ERROR_PIN_ATTEMPTS_EXCEEDED,
    PinVerificationError,
)

from .command import CommandValidationError, CommandValidator, SessionCommand
from .contracts import CommandType, SessionState, TransactionType
from .result import SessionResult
from .session_store import JsonSessionStore, SessionStoreError, StoredSession


class ControllerError(RuntimeError):
    """controller 계층에서 외부로 노출하는 공통 예외."""

    pass


class BankingFlowController:
    """ATM 절차를 상태머신으로 처리하는 controller.

    현재는 세션 상태 전이와 명령 검증 이후의 흐름 제어를 담당한다.
    다만 세션 토큰 발급, 활성 세션 저장, 서버 조립 책임이 완전히 하나로
    정리된 상태는 아니므로, 장기적으로는 더 명확한 세션 경계 정리가
    필요한 controller 로 보는 편이 맞다.
    """

    def __init__(
        self,
        bank_gateway: BankGateway,
        session_store: JsonSessionStore,
    ) -> None:
        self._bank_gateway = bank_gateway
        self._session_store = session_store

    def handle(self, payload: SessionCommand | dict[str, object]) -> SessionResult:
        """명령을 검증하고 현재 세션 상태에 맞는 절차 처리기로 위임한다."""
        try:
            command = CommandValidator.validate(payload)
        except CommandValidationError as exc:
            raise ControllerError(str(exc)) from exc

        if command.command_type == CommandType.INSERT_CARD:
            return self._handle_insert_card(command)

        session = self._load_session(command.session_token)
        self._require_not_closed(session)

        if command.command_type == CommandType.SUBMIT_PIN:
            return self._handle_submit_pin(session, command)
        if command.command_type == CommandType.SELECT_ACCOUNT:
            return self._handle_select_account(session, command)
        if command.command_type == CommandType.REQUEST_BALANCE:
            return self._handle_balance(session)
        if command.command_type == CommandType.REQUEST_DEPOSIT:
            return self._handle_deposit(session, command)
        if command.command_type == CommandType.REQUEST_WITHDRAW:
            return self._handle_withdraw(session, command)
        if command.command_type == CommandType.FORCE_END_SESSION:
            return self._handle_end_session(session)

        raise ControllerError(f"Unsupported command_type: {command.command_type}")

    def _handle_insert_card(self, command: SessionCommand) -> SessionResult:
        """카드 입력으로 새 세션을 시작한다.

        세션 생성은 banking 에 위임하고,
        controller 는 banking 이 발급한 토큰으로 로컬 상태를 시작한다.
        """
        card = self._bank_gateway.get_card_by_number(command.card_number)
        session = self._bank_gateway.create_session(card.card_id)
        self._session_store.create_session(
            session.session_token,
            card.card_id,
            card.card_number,
        )
        return SessionResult(
            succeeded=True,
            status_code="SESSION_STARTED",
            session_state=SessionState.CARD_INSERTED,
            session_token=session.session_token,
            message="카드를 확인했습니다. PIN을 입력해주세요.",
            session_closed=False,
        )

    def _handle_submit_pin(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        """PIN 인증을 처리하고 인증 이후 상태로 전이한다."""
        self._require_state(session, SessionState.CARD_INSERTED)
        try:
            card = self._bank_gateway.verify_pin(session.card_number, command.pin)
            account_ids = self._bank_gateway.list_accounts(card.card_id)
        except PinVerificationError as exc:
            if exc.card_locked or str(exc) == ERROR_PIN_ATTEMPTS_EXCEEDED:
                closed_session = session.model_copy(
                    update={"session_state": SessionState.SESSION_CLOSED}
                )
                self._session_store.save_session(closed_session)
                return SessionResult(
                    succeeded=False,
                    status_code="PIN_ATTEMPTS_EXCEEDED",
                    session_state=SessionState.SESSION_CLOSED,
                    session_token=closed_session.session_token,
                    message="PIN 입력을 3회 실패했습니다. 세션을 종료합니다. 카드 사용이 중단되었습니다.",
                    session_closed=True,
                    remaining_pin_attempts=0,
                )

            if str(exc) == "PIN이 올바르지 않습니다.":
                return SessionResult(
                    succeeded=False,
                    status_code="PIN_FAILED_RETRYABLE",
                    session_state=SessionState.CARD_INSERTED,
                    session_token=session.session_token,
                    message=(
                        "PIN이 올바르지 않습니다. "
                        "3회 실패 시 세션이 종료되고 카드 사용이 중단됩니다. "
                        f"남은 시도 {exc.remaining_attempts}회."
                    ),
                    session_closed=False,
                    remaining_pin_attempts=exc.remaining_attempts,
                )
            raise ControllerError(str(exc)) from exc
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(update={"session_state": SessionState.AUTHENTICATED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="PIN_VERIFIED",
            session_state=SessionState.AUTHENTICATED,
            session_token=updated_session.session_token,
            message="PIN이 확인되었습니다. 계좌를 선택해주세요.",
            available_account_ids=account_ids,
            session_closed=False,
            remaining_pin_attempts=3,
        )

    def _handle_select_account(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        """인증된 세션에서 계좌를 선택한다."""
        self._require_state(session, SessionState.AUTHENTICATED)
        try:
            account_ids = self._bank_gateway.list_accounts(session.card_id)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        if command.account_id not in account_ids:
            raise ControllerError(f"알 수 없는 계좌입니다: {command.account_id}")

        updated_session = session.model_copy(
            update={
                "session_state": SessionState.ACCOUNT_SELECTED,
                "selected_account_id": command.account_id,
            }
        )
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="ACCOUNT_SELECTED",
            session_state=SessionState.ACCOUNT_SELECTED,
            session_token=updated_session.session_token,
            message="계좌가 선택되었습니다. 거래를 선택해주세요.",
            selected_account_id=updated_session.selected_account_id,
            session_closed=False,
        )

    def _handle_balance(self, session: StoredSession) -> SessionResult:
        """선택된 계좌의 잔액을 조회한다."""
        self._require_state(session, SessionState.ACCOUNT_SELECTED)
        try:
            balance = self._bank_gateway.get_balance(session.selected_account_id)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(
            update={"session_state": SessionState.ACCOUNT_SELECTED}
        )
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="BALANCE_REPORTED",
            session_state=SessionState.RESULT_REPORTED,
            session_token=updated_session.session_token,
            message="현재 잔액을 안내했습니다.",
            selected_account_id=updated_session.selected_account_id,
            balance=balance,
            transaction_type=TransactionType.BALANCE,
            session_closed=False,
        )

    def _handle_deposit(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        """선택된 계좌에 입금을 수행한다."""
        self._require_state(session, SessionState.ACCOUNT_SELECTED)
        try:
            balance = self._bank_gateway.deposit(session.selected_account_id, command.amount)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(
            update={"session_state": SessionState.ACCOUNT_SELECTED}
        )
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="DEPOSIT_REPORTED",
            session_state=SessionState.RESULT_REPORTED,
            session_token=updated_session.session_token,
            message="입금이 완료되었습니다.",
            selected_account_id=updated_session.selected_account_id,
            balance=balance,
            transaction_type=TransactionType.DEPOSIT,
            requested_amount=command.amount,
            session_closed=False,
        )

    def _handle_withdraw(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        """선택된 계좌에서 출금을 수행한다."""
        self._require_state(session, SessionState.ACCOUNT_SELECTED)
        try:
            balance = self._bank_gateway.withdraw(session.selected_account_id, command.amount)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(
            update={"session_state": SessionState.ACCOUNT_SELECTED}
        )
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="WITHDRAW_REPORTED",
            session_state=SessionState.RESULT_REPORTED,
            session_token=updated_session.session_token,
            message="출금이 완료되었습니다.",
            selected_account_id=updated_session.selected_account_id,
            balance=balance,
            transaction_type=TransactionType.WITHDRAW,
            requested_amount=command.amount,
            session_closed=False,
        )

    def _handle_end_session(self, session: StoredSession) -> SessionResult:
        """현재 세션을 종료 상태로 전이한다."""
        updated_session = session.model_copy(update={"session_state": SessionState.SESSION_CLOSED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="SESSION_CLOSED",
            session_state=SessionState.SESSION_CLOSED,
            session_token=updated_session.session_token,
            message="세션이 종료되었습니다. 카드를 회수해주세요.",
            selected_account_id=updated_session.selected_account_id,
            session_closed=True,
        )

    def _load_session(self, session_token: str | None) -> StoredSession:
        """세션 토큰으로 활성 세션 저장소에서 현재 세션을 읽어온다."""
        try:
            return self._session_store.get_session(session_token)
        except SessionStoreError as exc:
            raise ControllerError(str(exc)) from exc

    @staticmethod
    def _require_not_closed(session: StoredSession) -> None:
        """이미 종료된 세션에는 후속 명령을 허용하지 않는다."""
        if session.session_state == SessionState.SESSION_CLOSED:
            raise ControllerError("이미 종료된 세션입니다")

    @staticmethod
    def _require_state(session: StoredSession, expected_state: SessionState) -> None:
        """세션이 기대한 상태에 있을 때만 다음 절차를 허용한다."""
        if session.session_state != expected_state:
            raise ControllerError(
                f"Invalid session state: expected {expected_state}, got {session.session_state}"
            )
