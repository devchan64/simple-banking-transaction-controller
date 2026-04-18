from __future__ import annotations

import unittest
from pathlib import Path

from banking_session_controller import SessionHistoryStore
from spec_support import TestRootSupport, spec_text


class SessionHistoryStoreSpec(TestRootSupport, unittest.TestCase):
    def setUp(self) -> None:
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
