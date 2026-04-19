from __future__ import annotations

"""session 이력 저장소.

이 모듈은 완성된 세션 시스템을 제공하지는 않는다.
현재 구조만 놓고 보면 토큰 발급 이력과 생성 시각을 남기는 최소 저장소에 가깝고,
만료, 갱신, 무효화, 활성 세션 검증 같은 본격적인 세션 정책은 다루지 않는다.

그래도 구현의 의미가 완전히 없는 것은 아니다.

- 카드 기준으로 세션 토큰이 언제 발급되었는지 기록하는 최소 이력 저장소 역할을 한다
- controller 상태머신 실험에서 "새 세션을 발급한다"는 동작을 분리해서 표현한다
- 이후 세션 생명주기를 정교하게 만들 때 출발점이 될 수 있는
  ``session_token``, ``card_id``, ``created_at`` 구조를 남겨 둔다

즉 현재는 세션 관리자의 완성형이라기보다,
세션 발급 이력이라는 한 조각을 독립시켜 본 흔적과 중간 구현으로 이해하는 편이 맞다.
"""

import json
import secrets
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class SessionRecord:
    """토큰 발급 시점의 최소 세션 이력 레코드."""

    session_token: str
    card_id: str
    created_at: str


class SessionHistoryStore:
    """세션 발급 이력을 파일에 append 하는 최소 저장소."""

    def __init__(self, sessions_path: str | Path) -> None:
        self._sessions_path = Path(sessions_path)
        self._sessions_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._sessions_path.exists():
            self._write_all([])

    def issue_session(self, card_id: str) -> SessionRecord:
        """새 토큰을 발급하고 이력에 남긴다."""
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
        """기록된 세션 발급 이력을 모두 반환한다."""
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
