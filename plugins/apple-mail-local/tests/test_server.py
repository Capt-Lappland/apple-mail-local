from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PLUGIN_ROOT / "scripts" / "server.py"
JXA_PATH = PLUGIN_ROOT / "scripts" / "mail_automation.jxa"

spec = importlib.util.spec_from_file_location("apple_mail_server", SERVER_PATH)
server = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(server)


class FakeRunner:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def run(self, operation, arguments):
        self.calls.append((operation, arguments))
        return json.loads(json.dumps(self.response))


class ToolCatalogTests(unittest.TestCase):
    def test_default_catalog_is_read_only(self):
        tools = server.available_tools(False)
        self.assertEqual(
            [tool["name"] for tool in tools],
            ["mail_list_accounts", "mail_list_mailboxes", "mail_search_messages", "mail_get_message"],
        )
        self.assertTrue(all(tool["annotations"]["readOnlyHint"] for tool in tools))

    def test_draft_tool_requires_opt_in(self):
        tools = server.available_tools(True)
        draft = next(tool for tool in tools if tool["name"] == "mail_create_reply_draft")
        self.assertFalse(draft["annotations"]["readOnlyHint"])
        self.assertFalse(draft["annotations"]["destructiveHint"])

    def test_draft_tool_requires_confirmation(self):
        ref = server.encode_message_ref(
            {"account_id": "a", "mailbox_path": ["Inbox"], "message_id": "7"}
        )
        with self.assertRaisesRegex(server.ToolError, "confirm_create_draft"):
            server.validate_and_prepare(
                "mail_create_reply_draft",
                {"message_ref": ref, "body": "Draft text", "confirm_create_draft": False},
                enable_drafts=True,
            )


class ValidationTests(unittest.TestCase):
    def test_message_ref_round_trip(self):
        locator = {"account_id": "账户", "mailbox_path": ["收件箱"], "message_id": "42"}
        self.assertEqual(server.decode_message_ref(server.encode_message_ref(locator)), locator)

    def test_search_requires_account_for_mailbox_path(self):
        with self.assertRaisesRegex(server.ToolError, "account_id"):
            server.validate_and_prepare(
                "mail_search_messages", {"mailbox_path": ["Inbox"]}, enable_drafts=False
            )

    def test_unknown_arguments_are_rejected(self):
        with self.assertRaisesRegex(server.ToolError, "Unknown argument"):
            server.validate_and_prepare("mail_list_accounts", {"send": True}, enable_drafts=False)

    def test_search_results_get_opaque_refs(self):
        locator = {"account_id": "a", "mailbox_path": ["Inbox"], "message_id": "9"}
        runner = FakeRunner({"messages": [{"subject": "Hello", "_locator": locator}]})
        result, _ = server.call_tool(
            "mail_search_messages", {}, enable_drafts=False, runner=runner
        )
        message = result["messages"][0]
        self.assertNotIn("_locator", message)
        self.assertEqual(server.decode_message_ref(message["message_ref"]), locator)


class SafetyTests(unittest.TestCase):
    def test_jxa_has_no_forbidden_mail_actions(self):
        source = JXA_PATH.read_text(encoding="utf-8")
        forbidden = ["Mail.send(", "Mail.delete(", "Mail.move(", ".readStatus =", ".flaggedStatus ="]
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_manifest_and_mcp_config(self):
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin" / "plugin.json").read_text())
        mcp = json.loads((PLUGIN_ROOT / ".mcp.json").read_text())
        self.assertEqual(manifest["name"], "apple-mail-local")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")
        self.assertEqual(mcp["mcpServers"]["apple_mail"]["command"], "/usr/bin/python3")


class ProtocolTests(unittest.TestCase):
    def test_jxa_bridge_healthcheck(self):
        completed = subprocess.run(
            ["/usr/bin/osascript", "-l", "JavaScript", str(JXA_PATH)],
            input=json.dumps({"operation": "healthcheck", "arguments": {}}),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=True,
        )
        self.assertEqual(json.loads(completed.stdout), {"ok": True})

    def test_stdio_initialize_and_tool_list(self):
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            },
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        ]
        payload = "".join(json.dumps(item) + "\n" for item in requests)
        completed = subprocess.run(
            [sys.executable, str(SERVER_PATH)],
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(responses[0]["result"]["serverInfo"]["name"], "apple-mail-local")
        self.assertEqual(len(responses[1]["result"]["tools"]), 4)


if __name__ == "__main__":
    unittest.main()
