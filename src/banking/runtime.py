from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BankingRuntimePaths:
    runtime_root: Path
    mock_db_root: Path
    cards_path: Path
    accounts_path: Path
    session_history_path: Path
    active_sessions_path: Path


def prepare_banking_runtime(runtime_root: str | Path) -> BankingRuntimePaths:
    root = Path(runtime_root)
    mock_db_root = root / "mock-db"
    mock_db_root.mkdir(parents=True, exist_ok=True)

    cards_path = mock_db_root / "cards.json"
    accounts_path = mock_db_root / "accounts.json"
    if not cards_path.exists():
        shutil.copy(Path("mock-db/cards.json"), cards_path)
    if not accounts_path.exists():
        shutil.copy(Path("mock-db/accounts.json"), accounts_path)

    session_history_path = root / "session-history.json"
    active_sessions_path = root / "active-sessions.json"
    _ensure_json_list_file(session_history_path)
    _ensure_json_list_file(active_sessions_path)

    return BankingRuntimePaths(
        runtime_root=root,
        mock_db_root=mock_db_root,
        cards_path=cards_path,
        accounts_path=accounts_path,
        session_history_path=session_history_path,
        active_sessions_path=active_sessions_path,
    )


def _ensure_json_list_file(path: Path) -> None:
    if path.exists():
        return
    path.write_text(json.dumps([], ensure_ascii=True, indent=2), encoding="utf-8")
