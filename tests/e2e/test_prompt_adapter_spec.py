from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from tests.support.process_support import ModuleProcessSupport
from tests.support.spec_support import TestRootSupport, flow_text, spec_text


class PromptAdapterE2ESpec(ModuleProcessSupport, TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        self.test_root = Path(".test-run/e2e") / self._testMethodName
        self.reset_test_root(self.test_root, "e2e test_root")
        self.transport_root = self.test_root / "transport"
        self.controller_root = self.test_root / "controller"
        self.banking_root = self.test_root / "banking"

    def test_prompt_adapter_guides_human_balance_flow(self) -> None:
        print(spec_text("Prompt Adapter가 카드 입력부터 잔액 조회까지 한글로 안내한다"))

        banking_server, controller_server = self._start_servers()
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "prompt_adapter", str(self.transport_root)],
                cwd=self.repo_root(),
                env=self.python_env(),
                text=True,
                input="\n".join(
                    [
                        "4000-1234-5678-0001",
                        "1234",
                        "1",
                        "1",
                        "q",
                        "q",
                    ]
                )
                + "\n",
                capture_output=True,
                check=False,
                timeout=10,
            )
        finally:
            self._stop_servers(controller_server, banking_server)

        print(flow_text(f"prompt adapter stdout=\n{completed.stdout}"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("ATM CLI Prompt Adapter", completed.stdout)
        self.assertIn("카드를 확인했습니다. PIN을 입력해주세요.", completed.stdout)
        self.assertIn("PIN이 확인되었습니다. 계좌를 선택해주세요.", completed.stdout)
        self.assertIn("계좌가 선택되었습니다. 거래를 선택해주세요.", completed.stdout)
        self.assertIn("현재 잔액을 안내했습니다.", completed.stdout)
        self.assertIn("[잔액] 1200원", completed.stdout)
        self.assertIn("세션이 종료되었습니다. 카드를 회수해주세요.", completed.stdout)

    def test_prompt_adapter_allows_deposit_after_balance_lookup(self) -> None:
        print(spec_text("Prompt Adapter가 잔액 조회 후 입금 절차를 이어서 진행하게 한다"))

        banking_server, controller_server = self._start_servers()
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "prompt_adapter", str(self.transport_root)],
                cwd=self.repo_root(),
                env=self.python_env(),
                text=True,
                input="\n".join(
                    [
                        "4000-1234-5678-0001",
                        "1234",
                        "1",
                        "1",
                        "",
                        "2",
                        "300",
                        "q",
                        "q",
                    ]
                )
                + "\n",
                capture_output=True,
                check=False,
                timeout=10,
            )
        finally:
            self._stop_servers(controller_server, banking_server)

        print(flow_text(f"prompt adapter stdout=\n{completed.stdout}"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("현재 잔액을 안내했습니다.", completed.stdout)
        self.assertIn("[잔액] 1200원", completed.stdout)
        self.assertIn("입금이 완료되었습니다.", completed.stdout)
        self.assertIn("[잔액] 1500원", completed.stdout)
        self.assertIn("[요청 금액] 300원", completed.stdout)
        self.assertIn("세션이 종료되었습니다. 카드를 회수해주세요.", completed.stdout)

    def test_prompt_adapter_shows_pin_retry_feedback_loop(self) -> None:
        print(spec_text("Prompt Adapter가 잘못된 PIN의 재시도 안내를 사람에게 보여준다"))

        banking_server, controller_server = self._start_servers()
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "prompt_adapter", str(self.transport_root)],
                cwd=self.repo_root(),
                env=self.python_env(),
                text=True,
                input="\n".join(
                    [
                        "4000-1234-5678-0001",
                        "9999",
                        "8888",
                        "1234",
                        "1",
                        "4",
                        "q",
                    ]
                )
                + "\n",
                capture_output=True,
                check=False,
                timeout=10,
            )
        finally:
            self._stop_servers(controller_server, banking_server)

        print(flow_text(f"prompt adapter stdout=\n{completed.stdout}"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(
            "PIN이 올바르지 않습니다. 3회 실패 시 세션이 종료되고 카드 사용이 중단됩니다. 남은 시도 2회.",
            completed.stdout,
        )
        self.assertIn(
            "PIN이 올바르지 않습니다. 3회 실패 시 세션이 종료되고 카드 사용이 중단됩니다. 남은 시도 1회.",
            completed.stdout,
        )
        self.assertIn("PIN이 확인되었습니다. 계좌를 선택해주세요.", completed.stdout)
        self.assertIn("세션이 종료되었습니다. 카드를 회수해주세요.", completed.stdout)

    def test_prompt_adapter_guides_human_deposit_flow(self) -> None:
        print(spec_text("Prompt Adapter가 입금 절차와 결과 금액을 한글로 안내한다"))

        banking_server, controller_server = self._start_servers()
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "prompt_adapter", str(self.transport_root)],
                cwd=self.repo_root(),
                env=self.python_env(),
                text=True,
                input="\n".join(
                    [
                        "4000-1234-5678-0001",
                        "1234",
                        "1",
                        "2",
                        "300",
                        "q",
                        "q",
                    ]
                )
                + "\n",
                capture_output=True,
                check=False,
                timeout=10,
            )
        finally:
            self._stop_servers(controller_server, banking_server)

        print(flow_text(f"prompt adapter stdout=\n{completed.stdout}"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("입금이 완료되었습니다.", completed.stdout)
        self.assertIn("[요청 금액] 300원", completed.stdout)
        self.assertIn("[잔액] 1500원", completed.stdout)
        self.assertIn("세션이 종료되었습니다. 카드를 회수해주세요.", completed.stdout)

    def test_prompt_adapter_guides_human_withdraw_failure_feedback_loop(self) -> None:
        print(spec_text("Prompt Adapter가 잔액 부족 출금 오류를 사람에게 안내한다"))

        banking_server, controller_server = self._start_servers()
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "prompt_adapter", str(self.transport_root)],
                cwd=self.repo_root(),
                env=self.python_env(),
                text=True,
                input="\n".join(
                    [
                        "4000-1234-5678-0004",
                        "1357",
                        "1",
                        "3",
                        "100",
                        "q",
                    ]
                )
                + "\n",
                capture_output=True,
                check=False,
                timeout=10,
            )
        finally:
            self._stop_servers(controller_server, banking_server)

        print(flow_text(f"prompt adapter stdout=\n{completed.stdout}"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("[오류:ControllerError] 잔액이 부족합니다: account-006", completed.stdout)

    def test_prompt_adapter_closes_session_after_third_invalid_pin(self) -> None:
        print(spec_text("Prompt Adapter가 PIN 3회 실패 후 세션 종료와 카드 중단을 안내한다"))

        banking_server, controller_server = self._start_servers()
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "prompt_adapter", str(self.transport_root)],
                cwd=self.repo_root(),
                env=self.python_env(),
                text=True,
                input="\n".join(
                    [
                        "4000-1234-5678-0001",
                        "9999",
                        "8888",
                        "7777",
                        "q",
                    ]
                )
                + "\n",
                capture_output=True,
                check=False,
                timeout=10,
            )
        finally:
            self._stop_servers(controller_server, banking_server)

        print(flow_text(f"prompt adapter stdout=\n{completed.stdout}"))

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn(
            "PIN 입력을 3회 실패했습니다. 세션을 종료합니다. 카드 사용이 중단되었습니다.",
            completed.stdout,
        )
        self.assertIn("ATM CLI를 종료합니다.", completed.stdout)

    def _start_servers(self):
        banking_server = self.start_module("banking", self.banking_root)
        controller_server = self.start_module(
            "controller",
            self.transport_root,
            "--runtime-root",
            self.controller_root,
            "--banking-root",
            self.banking_root,
        )
        return banking_server, controller_server

    @staticmethod
    def _stop_servers(controller_server, banking_server) -> None:
        controller_server.terminate()
        controller_server.wait(timeout=5)
        banking_server.terminate()
        banking_server.wait(timeout=5)
