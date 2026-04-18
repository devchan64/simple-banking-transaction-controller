from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path


class ModuleProcessSupport:
    @staticmethod
    def repo_root() -> Path:
        return Path(__file__).resolve().parents[2]

    @classmethod
    def python_env(cls) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"src{os.pathsep}.{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(
            os.pathsep
        )
        return env

    @classmethod
    def run_module(cls, module_name: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-m", module_name, *map(str, args)],
            cwd=cls.repo_root(),
            env=cls.python_env(),
            text=True,
            capture_output=True,
            check=False,
        )

    @classmethod
    def start_module(cls, module_name: str, *args: str) -> subprocess.Popen[str]:
        return subprocess.Popen(
            ["python3", "-m", module_name, *map(str, args)],
            cwd=cls.repo_root(),
            env=cls.python_env(),
            text=True,
        )

    @staticmethod
    def wait_for_file(path: Path, timeout_seconds: float = 3.0) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if path.exists():
                return
            time.sleep(0.01)
        raise TimeoutError(f"Timed out waiting for file: {path}")
