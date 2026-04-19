from __future__ import annotations

"""controller 활성 세션 저장소.

이 모듈 역시 완성된 세션 계층이라고 보기는 어렵다.
토큰 발급, 만료, 갱신, 정리(cleanup), 세션 이력과의 정합성 보장까지 포함한
전체 세션 시스템을 제공하지는 못하고,
현재는 controller 상태머신이 참조할 활성 세션 스냅샷을 파일로 저장하는 역할에 가깝다.

그래도 구현의 의미가 완전히 사라진 것은 아니다.

- controller 가 절차 상태를 메모리 밖에 유지하는 최소 저장소 역할을 한다
- ``CARD_INSERTED -> AUTHENTICATED -> ACCOUNT_SELECTED -> SESSION_CLOSED`` 같은
  상태 전이를 파일 기반으로 검증할 수 있게 해 준다
- 별도 프로세스나 서버 실행 환경에서도 controller 상태를 다시 읽을 수 있는
  가장 단순한 지속성 경계를 제공한다

즉 현재 구조는 세션 시스템의 완성형이라기보다,
controller 상태를 파일에 고정해 보려는 실험적 중간 구현으로 보는 편이 맞다.
"""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from .contracts import SessionState


class StoredSession(BaseModel):
    """controller 가 다루는 활성 세션의 최소 상태 표현."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_token: str
    card_id: str
    card_number: str
    session_state: SessionState
    selected_account_id: str | None = None


class SessionStoreError(RuntimeError):
    """활성 세션 저장소 접근 실패를 나타내는 예외."""

    pass


class JsonSessionStore:
    """활성 세션 스냅샷을 JSON 파일로 읽고 쓰는 최소 저장소."""

    def __init__(self, sessions_path: str | Path) -> None:
        self._sessions_path = Path(sessions_path)
        self._sessions_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._sessions_path.exists():
            self._write_all([])

    def create_session(self, session_token: str, card_id: str, card_number: str) -> StoredSession:
        """새 활성 세션 레코드를 생성한다."""
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
        """세션 토큰에 해당하는 현재 활성 세션을 조회한다."""
        for session in self._read_all():
            if session.session_token == session_token:
                return session
        raise SessionStoreError(f"알 수 없는 세션 토큰입니다: {session_token}")

    def save_session(self, updated_session: StoredSession) -> StoredSession:
        """기존 활성 세션을 새 상태로 덮어쓴다."""
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
                f"알 수 없는 세션 토큰입니다: {updated_session.session_token}"
            )

        self._write_all(sessions)
        return updated_session

    def replace_session(
        self, current_session_token: str, updated_session: StoredSession
    ) -> StoredSession:
        """기존 세션을 새 토큰을 가진 세션으로 교체한다."""
        sessions = []
        found = False
        for session in self._read_all():
            if session.session_token == current_session_token:
                sessions.append(updated_session)
                found = True
            else:
                sessions.append(session)

        if not found:
            raise SessionStoreError(
                f"알 수 없는 세션 토큰입니다: {current_session_token}"
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
