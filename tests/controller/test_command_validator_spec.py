from __future__ import annotations

import unittest

from controller import (
    CommandType,
    CommandValidationError,
    CommandValidator,
    SessionCommand,
)
from tests.support.spec_support import TestRootSupport, spec_text


class CommandValidatorSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()

    def test_insert_card_requires_card_number(self) -> None:
        print(spec_text("INSERT_CARD 는 card_number 가 필요하다"))

        with self.assertRaisesRegex(CommandValidationError, "Missing field: card_number"):
            CommandValidator.validate({"command_type": CommandType.INSERT_CARD})

    def test_insert_card_forbids_session_token(self) -> None:
        print(spec_text("INSERT_CARD 는 session_token 을 받지 않는다"))

        with self.assertRaisesRegex(CommandValidationError, "Forbidden field: session_token"):
            CommandValidator.validate(
                {
                    "command_type": CommandType.INSERT_CARD,
                    "session_token": "session-001",
                    "card_number": "4000-1234-5678-0001",
                }
            )

    def test_submit_pin_requires_session_token_and_pin(self) -> None:
        print(spec_text("SUBMIT_PIN 은 session_token 과 pin 이 필요하다"))

        with self.assertRaisesRegex(CommandValidationError, "Missing field: session_token"):
            CommandValidator.validate({"command_type": CommandType.SUBMIT_PIN, "pin": "1234"})

    def test_select_account_requires_account_id(self) -> None:
        print(spec_text("SELECT_ACCOUNT 는 account_id 가 필요하다"))

        with self.assertRaisesRegex(CommandValidationError, "Missing field: account_id"):
            CommandValidator.validate(
                {"command_type": CommandType.SELECT_ACCOUNT, "session_token": "session-001"}
            )

    def test_request_balance_forbids_amount(self) -> None:
        print(spec_text("REQUEST_BALANCE 는 amount 를 받지 않는다"))

        with self.assertRaisesRegex(CommandValidationError, "Forbidden field: amount"):
            CommandValidator.validate(
                {
                    "command_type": CommandType.REQUEST_BALANCE,
                    "session_token": "session-001",
                    "amount": 100,
                }
            )

    def test_request_deposit_requires_positive_int_amount(self) -> None:
        print(spec_text("REQUEST_DEPOSIT 는 양수 정수 amount 가 필요하다"))

        with self.assertRaisesRegex(
            CommandValidationError,
            "Invalid value for amount: positive int required",
        ):
            CommandValidator.validate(
                {
                    "command_type": CommandType.REQUEST_DEPOSIT,
                    "session_token": "session-001",
                    "amount": 0,
                }
            )

    def test_request_withdraw_rejects_non_int_amount(self) -> None:
        print(spec_text("REQUEST_WITHDRAW 는 정수 amount 만 받는다"))

        with self.assertRaisesRegex(
            CommandValidationError,
            "Input should be a valid integer",
        ):
            CommandValidator.validate(
                {
                    "command_type": CommandType.REQUEST_WITHDRAW,
                    "session_token": "session-001",
                    "amount": "100",
                }
            )

    def test_valid_request_deposit_passes(self) -> None:
        print(spec_text("유효한 REQUEST_DEPOSIT 는 validator 를 통과한다"))

        command = SessionCommand(
            command_type=CommandType.REQUEST_DEPOSIT,
            session_token="session-001",
            amount=100,
        )

        validated = CommandValidator.validate(command)

        self.assertEqual(command, validated)


if __name__ == "__main__":
    unittest.main(verbosity=2)
