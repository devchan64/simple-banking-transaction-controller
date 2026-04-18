from __future__ import annotations

import argparse
from itertools import count
from pathlib import Path

from controller import CommandType, SessionCommand
from transport import FileTransport, SessionRequestEnvelope, SessionResponseEnvelope


class PromptAdapter:
    def __init__(self, transport_root: str | Path) -> None:
        self._transport = FileTransport(
            transport_root=transport_root,
            poll_interval_seconds=0.01,
            timeout_seconds=3.0,
        )
        self._request_sequence = count(1)

    def run(self) -> int:
        self._print_header()

        while True:
            card_number = input("카드 번호를 입력하세요 (`q` 종료): ").strip()
            if self._is_quit(card_number):
                print("ATM CLI를 종료합니다.")
                return 0
            if not card_number:
                print("카드 번호를 입력해주세요.")
                continue

            response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.INSERT_CARD,
                    card_number=card_number,
                )
            )
            if not self._print_response(response):
                continue

            result = response.result
            session_token = result["session_token"]

            if not self._run_pin_step(session_token):
                continue

    def _run_pin_step(self, session_token: str) -> bool:
        while True:
            pin = input("PIN을 입력하세요 (`q` 카드 반환): ").strip()
            if self._is_quit(pin):
                self._force_end_session(session_token)
                return False
            if not pin:
                print("PIN을 입력해주세요.")
                continue

            response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SUBMIT_PIN,
                    session_token=session_token,
                    pin=pin,
                ),
                session_id=session_token,
            )
            if not self._print_response(response):
                return False

            result = response.result
            if result["succeeded"]:
                available_account_ids = result["available_account_ids"]
                return self._run_account_step(session_token, available_account_ids)

            if result["session_closed"]:
                return False

    def _run_account_step(
        self,
        session_token: str,
        available_account_ids: list[str],
    ) -> bool:
        while True:
            print("계좌 목록:")
            for index, account_id in enumerate(available_account_ids, start=1):
                print(f"  {index}. {account_id}")

            account_input = input(
                "계좌 번호 또는 계좌 ID를 입력하세요 (`q` 카드 반환): "
            ).strip()
            if self._is_quit(account_input):
                self._force_end_session(session_token)
                return False

            account_id = self._resolve_account_id(account_input, available_account_ids)
            if account_id is None:
                print("올바른 계좌를 선택해주세요.")
                continue

            response = self._dispatch(
                SessionCommand(
                    command_type=CommandType.SELECT_ACCOUNT,
                    session_token=session_token,
                    account_id=account_id,
                ),
                session_id=session_token,
            )
            if not self._print_response(response):
                return False

            return self._run_transaction_step(session_token)

    def _run_transaction_step(self, session_token: str) -> bool:
        while True:
            print("거래 메뉴:")
            print("  1. 잔액 조회")
            print("  2. 입금")
            print("  3. 출금")
            print("  4. 카드 반환")

            choice = input("선택하세요: ").strip()
            if choice == "1":
                response = self._dispatch(
                    SessionCommand(
                        command_type=CommandType.REQUEST_BALANCE,
                        session_token=session_token,
                    ),
                    session_id=session_token,
                )
                return self._finish_transaction(session_token, response)

            if choice == "2":
                amount = self._prompt_amount("입금할 금액을 입력하세요")
                if amount is None:
                    self._force_end_session(session_token)
                    return False
                response = self._dispatch(
                    SessionCommand(
                        command_type=CommandType.REQUEST_DEPOSIT,
                        session_token=session_token,
                        amount=amount,
                    ),
                    session_id=session_token,
                )
                return self._finish_transaction(session_token, response)

            if choice == "3":
                amount = self._prompt_amount("출금할 금액을 입력하세요")
                if amount is None:
                    self._force_end_session(session_token)
                    return False
                response = self._dispatch(
                    SessionCommand(
                        command_type=CommandType.REQUEST_WITHDRAW,
                        session_token=session_token,
                        amount=amount,
                    ),
                    session_id=session_token,
                )
                return self._finish_transaction(session_token, response)

            if choice == "4":
                self._force_end_session(session_token)
                return False

            print("메뉴 번호 1~4 중에서 선택해주세요.")

    def _finish_transaction(
        self,
        session_token: str,
        response: SessionResponseEnvelope,
    ) -> bool:
        if not self._print_response(response):
            return False

        while True:
            next_step = input(
                "엔터를 누르면 거래 메뉴로 돌아갑니다 (`q` 카드 반환): "
            ).strip()
            if not next_step:
                return self._run_transaction_step(session_token)
            if self._is_quit(next_step):
                self._force_end_session(session_token)
                return False
            print("엔터 또는 `q` 중에서 선택해주세요.")

    def _force_end_session(self, session_token: str) -> None:
        response = self._dispatch(
            SessionCommand(
                command_type=CommandType.FORCE_END_SESSION,
                session_token=session_token,
            ),
            session_id=session_token,
        )
        self._print_response(response)

    def _dispatch(
        self,
        command: SessionCommand,
        session_id: str | None = None,
    ) -> SessionResponseEnvelope:
        request_id = f"cli-{next(self._request_sequence):03d}"
        request = SessionRequestEnvelope(
            request_id=request_id,
            session_id=session_id,
            command=command,
        )
        return self._transport.dispatch(request)

    @staticmethod
    def _is_quit(value: str) -> bool:
        return value.lower() in {"q", "quit", "exit"}

    @staticmethod
    def _resolve_account_id(
        user_input: str,
        available_account_ids: list[str],
    ) -> str | None:
        if user_input in available_account_ids:
            return user_input
        if user_input.isdigit():
            index = int(user_input) - 1
            if 0 <= index < len(available_account_ids):
                return available_account_ids[index]
        return None

    @staticmethod
    def _prompt_amount(prompt: str) -> int | None:
        while True:
            raw = input(f"{prompt} (`q` 카드 반환): ").strip()
            if PromptAdapter._is_quit(raw):
                return None
            if not raw:
                print("금액을 입력해주세요.")
                continue
            if not raw.isdigit():
                print("금액은 숫자로 입력해주세요.")
                continue

            amount = int(raw)
            if amount <= 0:
                print("금액은 0보다 커야 합니다.")
                continue
            return amount

    @staticmethod
    def _print_header() -> None:
        print("ATM CLI Prompt Adapter")
        print("사람이 손으로 controller 절차를 점검하는 테스트 도구입니다.")
        print("")

    @staticmethod
    def _print_response(response: SessionResponseEnvelope) -> bool:
        if response.error_code is not None:
            print(f"[오류:{response.error_code}] {response.error_message}")
            return False

        result = response.result
        print(f"[안내] {result['message']}")

        if result.get("available_account_ids"):
            joined = ", ".join(result["available_account_ids"])
            print(f"[계좌] {joined}")
        if result.get("selected_account_id"):
            print(f"[선택 계좌] {result['selected_account_id']}")
        if result.get("balance") is not None:
            print(f"[잔액] {result['balance']}원")
        if result.get("requested_amount") is not None:
            print(f"[요청 금액] {result['requested_amount']}원")
        if result.get("remaining_pin_attempts") is not None:
            print(f"[남은 PIN 시도] {result['remaining_pin_attempts']}회")
        print("")
        return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a lightweight ATM CLI prompt adapter for controller testing."
    )
    parser.add_argument(
        "transport_root",
        nargs="?",
        default=".transport",
        help="Controller transport root directory.",
    )
    args = parser.parse_args(argv)

    adapter = PromptAdapter(args.transport_root)
    return adapter.run()
