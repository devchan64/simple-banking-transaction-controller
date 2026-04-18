from __future__ import annotations

import shutil
from pathlib import Path


class TestRootSupport:
    def reset_test_root(self, test_root: Path, label: str = "test_root") -> Path:
        print(f"[초기화] {label} 삭제={test_root}")
        shutil.rmtree(test_root, ignore_errors=True)
        test_root.mkdir(parents=True, exist_ok=True)
        return test_root
