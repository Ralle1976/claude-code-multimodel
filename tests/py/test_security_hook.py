"""Offline-Tests fuer den Security-Reminder-Hook (State, Path Traversal, Regeln)."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "plugins" / "security-guidance" / "hooks"
HOOK_SCRIPT = HOOKS_DIR / "security_reminder_hook.py"
sys.path.insert(0, str(HOOKS_DIR))

import security_patterns  # noqa: E402
import security_reminder_hook as hook  # noqa: E402
import security_state  # noqa: E402


class StateDirTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ccm-hook-"))
        self._env_backup = {
            key: os.environ.get(key)
            for key in ("CLAUDE_SECURITY_STATE_DIR", "CLAUDE_SECURITY_LOG", "ENABLE_SECURITY_REMINDER")
        }
        os.environ["CLAUDE_SECURITY_STATE_DIR"] = str(self.tmp / "state")
        os.environ["CLAUDE_SECURITY_LOG"] = str(self.tmp / "debug.log")

    def tearDown(self):
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        shutil.rmtree(self.tmp, ignore_errors=True)


class SanitizeSessionIdTest(StateDirTest):
    def test_plain_id_is_kept(self):
        self.assertEqual(security_state.sanitize_session_id("abc-123_X"), "abc-123_X")

    def test_non_string_falls_back(self):
        for value in (None, 42, [], {}):
            self.assertEqual(security_state.sanitize_session_id(value), "default")

    def test_empty_falls_back(self):
        self.assertEqual(security_state.sanitize_session_id(""), "default")

    def test_traversal_is_stripped(self):
        self.assertEqual(security_state.sanitize_session_id("../../etc/passwd"), "etcpasswd")

    def test_separators_are_stripped(self):
        self.assertEqual(security_state.sanitize_session_id("a/b\\c"), "abc")

    def test_windows_drive_is_stripped(self):
        self.assertEqual(security_state.sanitize_session_id("C:\\Windows\\x"), "CWindowsx")

    def test_only_dots_falls_back(self):
        self.assertEqual(security_state.sanitize_session_id(".."), "default")

    def test_long_id_is_truncated(self):
        result = security_state.sanitize_session_id("a" * 500)
        self.assertEqual(len(result), security_state.MAX_STATE_ID_LENGTH)


class StateFilePathTest(StateDirTest):
    def test_state_file_stays_inside_state_dir(self):
        state_dir = security_state.state_dir().resolve()
        for hostile in ("../../evil", "..", "/etc/passwd", "a/../../b", "C:\\temp\\x"):
            path = security_state.get_state_file(hostile).resolve()
            self.assertEqual(
                path.parent,
                state_dir,
                f"{hostile!r} escaped the state directory: {path}"
            )


class StatePersistenceTest(StateDirTest):
    def test_roundtrip(self):
        security_state.save_state("s1", {"warn-a", "warn-b"})
        self.assertEqual(security_state.load_state("s1"), {"warn-a", "warn-b"})

    def test_missing_file_returns_empty_set(self):
        self.assertEqual(security_state.load_state("nope"), set())

    def test_corrupt_file_returns_empty_set(self):
        path = security_state.get_state_file("broken")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{kaputt", encoding="utf-8")
        self.assertEqual(security_state.load_state("broken"), set())

    def test_non_list_returns_empty_set(self):
        path = security_state.get_state_file("obj")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"a": 1}', encoding="utf-8")
        self.assertEqual(security_state.load_state("obj"), set())

    def test_cleanup_removes_only_old_state_files(self):
        state_dir = security_state.state_dir()
        state_dir.mkdir(parents=True, exist_ok=True)

        old = state_dir / f"{security_state.STATE_PREFIX}old.json"
        old.write_text("[]", encoding="utf-8")
        stale = (datetime.now() - timedelta(days=40)).timestamp()
        os.utime(old, (stale, stale))

        fresh = state_dir / f"{security_state.STATE_PREFIX}fresh.json"
        fresh.write_text("[]", encoding="utf-8")

        unrelated = state_dir / "settings.json"
        unrelated.write_text("{}", encoding="utf-8")

        security_state.cleanup_old_state_files()

        self.assertFalse(old.exists(), "old state file must be removed")
        self.assertTrue(fresh.exists(), "fresh state file must survive")
        self.assertTrue(unrelated.exists(), "unrelated files must survive")


class PatternTest(unittest.TestCase):
    def test_workflow_path_is_flagged(self):
        rule, reminder = security_patterns.check_patterns(".github/workflows/ci.yml", "")
        self.assertEqual(rule, "github_actions_workflow")
        self.assertIn("Command Injection", reminder)

    def test_leading_slash_path_is_normalised(self):
        rule, _ = security_patterns.check_patterns("/.github/workflows/ci.yaml", "")
        self.assertEqual(rule, "github_actions_workflow")

    def test_eval_is_flagged(self):
        rule, _ = security_patterns.check_patterns("src/app.js", "const x = eval('1+1');")
        self.assertEqual(rule, "eval_injection")

    def test_child_process_exec_is_flagged(self):
        rule, _ = security_patterns.check_patterns("src/a.js", "exec(`ls ${x}`)")
        self.assertEqual(rule, "child_process_exec")

    def test_benign_content_is_not_flagged(self):
        rule, reminder = security_patterns.check_patterns("src/app.js", "const x = 1;")
        self.assertIsNone(rule)
        self.assertIsNone(reminder)

    def test_empty_content_with_safe_path_is_not_flagged(self):
        self.assertEqual(security_patterns.check_patterns("README.md", ""), (None, None))


class ExtractContentTest(unittest.TestCase):
    def test_write_uses_content(self):
        self.assertEqual(
            hook.extract_content_from_input("Write", {"content": "eval(1)"}),
            "eval(1)"
        )

    def test_edit_uses_new_string(self):
        self.assertEqual(
            hook.extract_content_from_input("Edit", {"new_string": "eval(1)"}),
            "eval(1)"
        )

    def test_multiedit_joins_edits(self):
        result = hook.extract_content_from_input(
            "MultiEdit", {"edits": [{"new_string": "a"}, {"new_string": "b"}]}
        )
        self.assertEqual(result, "a b")

    def test_unknown_tool_and_bad_input(self):
        self.assertEqual(hook.extract_content_from_input("Read", {"content": "x"}), "")
        self.assertEqual(hook.extract_content_from_input("Write", "kaputt"), "")


class HookProcessTest(StateDirTest):
    """End-to-end: echter Prozessaufruf mit JSON auf stdin."""

    def _run_hook(self, payload, extra_env=None):
        env = dict(os.environ)
        env.update({
            "CLAUDE_SECURITY_STATE_DIR": str(self.tmp / "state"),
            "CLAUDE_SECURITY_LOG": str(self.tmp / "debug.log"),
        })
        env.pop("ENABLE_SECURITY_REMINDER", None)
        env.update(extra_env or {})

        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env,
            timeout=60,
        )

    def test_first_warning_blocks_and_second_allows(self):
        payload = {
            "session_id": "sess-1",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/a.js", "content": "eval('x')"},
        }

        first = self._run_hook(payload)
        self.assertEqual(first.returncode, 2, "first warning must block the tool")
        self.assertIn(b"eval", first.stderr.lower())

        second = self._run_hook(payload)
        self.assertEqual(second.returncode, 0, "repeated warning must not block again")

    def test_safe_edit_is_allowed(self):
        payload = {
            "session_id": "sess-1",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/a.js", "new_string": "const x = 1;"},
        }
        self.assertEqual(self._run_hook(payload).returncode, 0)

    def test_non_file_tool_is_ignored(self):
        payload = {"session_id": "s", "tool_name": "Bash", "tool_input": {"command": "eval(1)"}}
        self.assertEqual(self._run_hook(payload).returncode, 0)

    def test_invalid_json_is_ignored(self):
        env = dict(os.environ)
        env["CLAUDE_SECURITY_STATE_DIR"] = str(self.tmp / "state")
        result = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=b"{kein json",
            capture_output=True,
            env=env,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0)

    def test_disabled_by_env(self):
        payload = {
            "session_id": "sess-2",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/a.js", "content": "eval('x')"},
        }
        result = self._run_hook(payload, {"ENABLE_SECURITY_REMINDER": "0"})
        self.assertEqual(result.returncode, 0)

    def test_hostile_session_id_cannot_write_outside_state_dir(self):
        payload = {
            "session_id": "../../pwned",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/a.js", "content": "eval('x')"},
        }
        result = self._run_hook(payload)
        self.assertEqual(result.returncode, 2)

        state_dir = (self.tmp / "state").resolve()
        for path in state_dir.glob("*.json"):
            self.assertEqual(path.resolve().parent, state_dir)

        # Nichts ausserhalb des State-Verzeichnisses anlegen
        self.assertEqual(list(self.tmp.glob("*.json")), [])
        self.assertEqual(list(Path(tempfile.gettempdir()).glob("pwned*")), [])


if __name__ == "__main__":
    unittest.main()