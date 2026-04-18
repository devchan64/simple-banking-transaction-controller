from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .contracts import SessionState


class StoredSession(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session_token: str
    card_id: str
    card_number: str
    session_state: SessionState
    selected_account_id: str | None = None


class SessionStoreError(RuntimeError):
    pass


class JsonSessionStore:
    def __init__(self, sessions_path: str | Path) -> None:
        self._sessions_path = Path(sessions_path)
        self._sessions_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._sessions_path.exists():
            self._write_all([])

    def create_session(self, session_token: str, card_id: str, card_number: str) -> StoredSession:
        session = StoredSession(
            session_token=session_token,
            card_id=card_id,
            card_number=card_number,
            session_state=SessionState.CARD_INSERTED,
        )
        sessions = self._read_all()
        sessions.append(session)
        self._write_all(sessions)
        return session

    def get_session(self, session_token: str) -> StoredSession:
        for session in self._read_all():
            if session.session_token == session_token:
                return session
        raise SessionStoreError(f"Unknown session token: {session_token}")

    def save_session(self, updated_session: StoredSession) -> StoredSession:
        sessions = []
        found = False
        for session in self._read_all():
            if session.session_token == updated_session.session_token:
                sessions.append(updated_session)
                found = True
            else:
                sessions.append(session)

        if not found:
            raise SessionStoreError(
                f"Unknown session token: {updated_session.session_token}"
            )

        self._write_all(sessions)
        return updated_session

    def _read_all(self) -> list[StoredSession]:
        payload = json.loads(self._sessions_path.read_text(encoding="utf-8"))
        return [StoredSession.model_validate(item) for item in payload]

    def _write_all(self, sessions: list[StoredSession]) -> None:
        payload = [session.model_dump(mode="json") for session in sessions]
        self._sessions_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
