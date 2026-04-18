from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class SessionRecord:
    session_token: str
    card_id: str
    created_at: str


class SessionHistoryStore:
    def __init__(self, sessions_path: str | Path) -> None:
        self._sessions_path = Path(sessions_path)
        self._sessions_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._sessions_path.exists():
            self._write_all([])

    def issue_session(self, card_id: str) -> SessionRecord:
        record = SessionRecord(
            session_token=self._new_token(),
            card_id=card_id,
            created_at=self._utcnow().isoformat(),
        )
        sessions = self._read_all()
        sessions.append(record)
        self._write_all(sessions)
        return record

    def list_sessions(self) -> list[SessionRecord]:
        return self._read_all()

    def _read_all(self) -> list[SessionRecord]:
        payload = json.loads(self._sessions_path.read_text(encoding="utf-8"))
        return [SessionRecord(**item) for item in payload]

    def _write_all(self, sessions: list[SessionRecord]) -> None:
        payload = [asdict(session) for session in sessions]
        self._sessions_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _new_token() -> str:
        return secrets.token_urlsafe(24)

    @staticmethod
    def _utcnow() -> datetime:
        return datetime.now(UTC)
