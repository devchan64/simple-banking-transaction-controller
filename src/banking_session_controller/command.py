from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, StrictInt, ValidationError
from .contracts import (
    CommandType,
)


class CommandValidationError(RuntimeError):
    pass


class SessionCommand(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    command_type: CommandType
    session_token: str | None = None
    card_number: str | None = None
    pin: str | None = None
    account_id: str | None = None
    amount: StrictInt | None = None


class CommandValidator:
    @classmethod
    def validate(cls, payload: SessionCommand | dict[str, Any]) -> SessionCommand:
        try:
            command = (
                payload
                if isinstance(payload, SessionCommand)
                else SessionCommand.model_validate(payload)
            )
        except ValidationError as exc:
            raise CommandValidationError(cls._first_error_message(exc)) from exc

        if command.command_type == CommandType.INSERT_CARD:
            cls._require_present(command.card_number, "card_number")
            cls._require_absent(command.session_token, "session_token")
            cls._require_absent(command.pin, "pin")
            cls._require_absent(command.account_id, "account_id")
            cls._require_absent(command.amount, "amount")
            return command

        cls._require_present(command.session_token, "session_token")

        if command.command_type == CommandType.SUBMIT_PIN:
            cls._require_present(command.pin, "pin")
            cls._require_absent(command.card_number, "card_number")
            cls._require_absent(command.account_id, "account_id")
            cls._require_absent(command.amount, "amount")
            return command

        if command.command_type == CommandType.SELECT_ACCOUNT:
            cls._require_present(command.account_id, "account_id")
            cls._require_absent(command.card_number, "card_number")
            cls._require_absent(command.pin, "pin")
            cls._require_absent(command.amount, "amount")
            return command

        if command.command_type == CommandType.REQUEST_BALANCE:
            cls._require_absent(command.card_number, "card_number")
            cls._require_absent(command.pin, "pin")
            cls._require_absent(command.account_id, "account_id")
            cls._require_absent(command.amount, "amount")
            return command

        if command.command_type in {
            CommandType.REQUEST_DEPOSIT,
            CommandType.REQUEST_WITHDRAW,
        }:
            cls._require_present(command.amount, "amount")
            cls._require_positive_int(command.amount, "amount")
            cls._require_absent(command.card_number, "card_number")
            cls._require_absent(command.pin, "pin")
            cls._require_absent(command.account_id, "account_id")
            return command

        if command.command_type == CommandType.END_SESSION:
            cls._require_absent(command.card_number, "card_number")
            cls._require_absent(command.pin, "pin")
            cls._require_absent(command.account_id, "account_id")
            cls._require_absent(command.amount, "amount")
            return command

        raise CommandValidationError(f"Unsupported command_type: {command.command_type}")

    @staticmethod
    def _require_present(value: object, field_name: str) -> None:
        if value is None:
            raise CommandValidationError(f"Missing field: {field_name}")

    @staticmethod
    def _require_absent(value: object, field_name: str) -> None:
        if value is not None:
            raise CommandValidationError(f"Forbidden field: {field_name}")

    @staticmethod
    def _require_positive_int(value: object, field_name: str) -> None:
        if value <= 0:
            raise CommandValidationError(
                f"Invalid value for {field_name}: positive int required"
            )

    @staticmethod
    def _first_error_message(exc: ValidationError) -> str:
        error = exc.errors(include_url=False)[0]
        return str(error["msg"])
