"""Opt-in live smoke test; it reports counts only and never reads message bodies."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import unittest


SERVER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "server.py"
spec = importlib.util.spec_from_file_location("apple_mail_server_live", SERVER_PATH)
server = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(server)


@unittest.skipUnless(os.environ.get("APPLE_MAIL_LIVE_TESTS") == "1", "set APPLE_MAIL_LIVE_TESTS=1")
class LiveSmokeTest(unittest.TestCase):
    def test_list_accounts_and_mailboxes(self):
        runner = server.AutomationRunner()
        accounts = runner.run("list_accounts", {})
        self.assertIsInstance(accounts.get("accounts"), list)
        mailboxes = runner.run("list_mailboxes", {})
        self.assertIsInstance(mailboxes.get("mailboxes"), list)


if __name__ == "__main__":
    unittest.main()
