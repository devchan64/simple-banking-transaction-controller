from __future__ import annotations

import shutil
from pathlib import Path

RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"


def _tag(color: str, label: str) -> str:
    return f"{color}[{label}]{RESET}"


def init_text(message: str) -> str:
    return f"{_tag(YELLOW, '초기화')} {message}"


def spec_text(message: str) -> str:
    return f"{_tag(GREEN, '스펙')} {message}"


def flow_text(message: str) -> str:
    return f"{_tag(BLUE, '흐름')} {message}"


class TestRootSupport:
    def print_test_header(self) -> None:
        print(
            f"\n{_tag(MAGENTA, '테스트')} "
            f"{self.__class__.__name__}.{self._testMethodName}"
        )

    def reset_test_root(self, test_root: Path, label: str = "test_root") -> Path:
        print(init_text(f"{label} 삭제={test_root}"))
        shutil.rmtree(test_root, ignore_errors=True)
        test_root.mkdir(parents=True, exist_ok=True)
        return test_root
