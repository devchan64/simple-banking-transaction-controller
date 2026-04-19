from __future__ import annotations

import unittest
from pathlib import Path

from banking import BankingSessionStore, SessionExpiredError, SessionHistoryStore
from tests.support.spec_support import TestRootSupport, spec_text


class SessionHistoryStoreSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        test_root = Path(".test-run/session") / self._testMethodName
        self.reset_test_root(test_root, "session test_root")
        self.sessions_path = test_root / "sessions.json"
        self.store = SessionHistoryStore(self.sessions_path)

    def test_issue_session_creates_token_and_records_history(self) -> None:
        # 세션 모듈은 토큰을 발급하고 생성 이력만 기록해야 한다.
        print(spec_text("세션 토큰을 발급하고 생성 이력을 기록한다"))

        session = self.store.issue_session("card-001")

        print(spec_text(f"세션={session}"))
        self.assertEqual("card-001", session.card_id)
        self.assertTrue(session.session_token)
        self.assertTrue(self.sessions_path.exists())
        self.assertEqual(1, len(self.store.list_sessions()))

    def test_issue_session_appends_history(self) -> None:
        # 세션 생성 이력은 append-only 형태로 쌓여야 한다.
        print(spec_text("세션 생성 이력을 append-only로 누적한다"))

        first = self.store.issue_session("card-001")
        second = self.store.issue_session("card-002")
        history = self.store.list_sessions()

        print(spec_text(f"첫 번째 세션={first}"))
        print(spec_text(f"두 번째 세션={second}"))
        print(spec_text(f"누적 이력 수={len(history)}"))

        self.assertEqual(2, len(history))
        self.assertEqual("card-001", history[0].card_id)
        self.assertEqual("card-002", history[1].card_id)
        self.assertNotEqual(first.session_token, second.session_token)


class BankingSessionStoreSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
        self.print_test_header()
        test_root = Path(".test-run/banking-session") / self._testMethodName
        self.reset_test_root(test_root, "banking session test_root")
        self.history_path = test_root / "session-history.json"
        self.active_sessions_path = test_root / "active-sessions.json"
        self.history_store = SessionHistoryStore(self.history_path)
        self.store = BankingSessionStore(
            self.active_sessions_path,
            self.history_store,
            session_ttl_seconds=300,
        )

    def test_create_session_persists_active_session_and_history(self) -> None:
        print(spec_text("banking session store 는 활성 세션과 이력을 함께 남긴다"))

        session = self.store.create_session("card-001")

        self.assertEqual("card-001", session.card_id)
        self.assertTrue(session.session_token)
        self.assertTrue(session.expires_at)
        self.assertEqual(1, len(self.store.list_sessions()))
        self.assertEqual(1, len(self.history_store.list_sessions()))

    def test_get_session_returns_non_expired_session(self) -> None:
        print(spec_text("만료되지 않은 세션은 조회할 수 있다"))

        created = self.store.create_session("card-001")
        loaded = self.store.get_session(created.session_token)

        self.assertEqual(created, loaded)

    def test_get_session_rejects_expired_session(self) -> None:
        print(spec_text("만료된 세션 조회는 실패한다"))
        expired_store = BankingSessionStore(
            self.active_sessions_path,
            self.history_store,
            session_ttl_seconds=-1,
        )
        session = expired_store.create_session("card-001")

        with self.assertRaisesRegex(SessionExpiredError, "세션이 만료되었습니다"):
            expired_store.get_session(session.session_token)

    def test_refresh_session_rotates_token_and_extends_expiration(self) -> None:
        print(spec_text("refresh 는 새 토큰을 발급하고 기존 토큰을 교체한다"))

        created = self.store.create_session("card-001")
        refreshed = self.store.refresh_session(created.session_token)

        self.assertEqual("card-001", refreshed.card_id)
        self.assertNotEqual(created.session_token, refreshed.session_token)
        self.assertEqual(1, len(self.store.list_sessions()))
        self.assertEqual(2, len(self.history_store.list_sessions()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
