from __future__ import annotations

from banking import BankGatewayError, JsonBankGateway, SessionHistoryStore

from .command import CommandValidationError, CommandValidator, SessionCommand
from .contracts import CommandType, SessionState, TransactionType
from .result import SessionResult
from .session_store import JsonSessionStore, SessionStoreError, StoredSession


class ControllerError(RuntimeError):
    pass


class BankingFlowController:
    def __init__(
        self,
        bank_gateway: JsonBankGateway,
        session_history_store: SessionHistoryStore,
        session_store: JsonSessionStore,
    ) -> None:
        self._bank_gateway = bank_gateway
        self._session_history_store = session_history_store
        self._session_store = session_store

    def handle(self, payload: SessionCommand | dict[str, object]) -> SessionResult:
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
        card = self._bank_gateway.get_card_by_number(command.card_number)
        record = self._session_history_store.issue_session(card.card_id)
        self._session_store.create_session(record.session_token, card.card_id, card.card_number)
        return SessionResult(
            succeeded=True,
            status_code="SESSION_STARTED",
            session_state=SessionState.CARD_INSERTED,
            session_token=record.session_token,
            message="Card accepted. Enter PIN.",
            session_closed=False,
        )

    def _handle_submit_pin(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        self._require_state(session, SessionState.CARD_INSERTED)
        try:
            card = self._bank_gateway.verify_pin(session.card_number, command.pin)
            account_ids = self._bank_gateway.list_accounts(card.card_id)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(update={"session_state": SessionState.AUTHENTICATED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="PIN_VERIFIED",
            session_state=SessionState.AUTHENTICATED,
            session_token=updated_session.session_token,
            message="PIN verified. Select account.",
            available_account_ids=account_ids,
            session_closed=False,
        )

    def _handle_select_account(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        self._require_state(session, SessionState.AUTHENTICATED)
        try:
            account_ids = self._bank_gateway.list_accounts(session.card_id)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        if command.account_id not in account_ids:
            raise ControllerError(f"Unknown account id: {command.account_id}")

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
            message="Account selected. Choose transaction.",
            selected_account_id=updated_session.selected_account_id,
            session_closed=False,
        )

    def _handle_balance(self, session: StoredSession) -> SessionResult:
        self._require_state(session, SessionState.ACCOUNT_SELECTED)
        try:
            balance = self._bank_gateway.get_balance(session.selected_account_id)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(update={"session_state": SessionState.RESULT_REPORTED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="BALANCE_REPORTED",
            session_state=SessionState.RESULT_REPORTED,
            session_token=updated_session.session_token,
            message="Balance reported.",
            selected_account_id=updated_session.selected_account_id,
            balance=balance,
            transaction_type=TransactionType.BALANCE,
            session_closed=False,
        )

    def _handle_deposit(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        self._require_state(session, SessionState.ACCOUNT_SELECTED)
        try:
            balance = self._bank_gateway.deposit(session.selected_account_id, command.amount)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(update={"session_state": SessionState.RESULT_REPORTED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="DEPOSIT_REPORTED",
            session_state=SessionState.RESULT_REPORTED,
            session_token=updated_session.session_token,
            message="Deposit completed.",
            selected_account_id=updated_session.selected_account_id,
            balance=balance,
            transaction_type=TransactionType.DEPOSIT,
            requested_amount=command.amount,
            session_closed=False,
        )

    def _handle_withdraw(
        self, session: StoredSession, command: SessionCommand
    ) -> SessionResult:
        self._require_state(session, SessionState.ACCOUNT_SELECTED)
        try:
            balance = self._bank_gateway.withdraw(session.selected_account_id, command.amount)
        except BankGatewayError as exc:
            raise ControllerError(str(exc)) from exc

        updated_session = session.model_copy(update={"session_state": SessionState.RESULT_REPORTED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="WITHDRAW_REPORTED",
            session_state=SessionState.RESULT_REPORTED,
            session_token=updated_session.session_token,
            message="Withdrawal completed.",
            selected_account_id=updated_session.selected_account_id,
            balance=balance,
            transaction_type=TransactionType.WITHDRAW,
            requested_amount=command.amount,
            session_closed=False,
        )

    def _handle_end_session(self, session: StoredSession) -> SessionResult:
        updated_session = session.model_copy(update={"session_state": SessionState.SESSION_CLOSED})
        self._session_store.save_session(updated_session)
        return SessionResult(
            succeeded=True,
            status_code="SESSION_CLOSED",
            session_state=SessionState.SESSION_CLOSED,
            session_token=updated_session.session_token,
            message="Session ended. Please remove card.",
            selected_account_id=updated_session.selected_account_id,
            session_closed=True,
        )

    def _load_session(self, session_token: str | None) -> StoredSession:
        try:
            return self._session_store.get_session(session_token)
        except SessionStoreError as exc:
            raise ControllerError(str(exc)) from exc

    @staticmethod
    def _require_not_closed(session: StoredSession) -> None:
        if session.session_state == SessionState.SESSION_CLOSED:
            raise ControllerError("Session already closed")

    @staticmethod
    def _require_state(session: StoredSession, expected_state: SessionState) -> None:
        if session.session_state != expected_state:
            raise ControllerError(
                f"Invalid session state: expected {expected_state}, got {session.session_state}"
            )
