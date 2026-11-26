"""
Tests fuer den portablen Hook-Launcher (run-security-hook.sh).

hooks.json ruft dieses Shell-Skript auf. Es muss stdin/stdout/stderr und den
Exit-Code unveraendert weiterreichen - insbesondere Exit 2 (blockieren) - und
darf auch dann nicht blockieren, wenn kein Python installiert ist.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "plugins" / "security-guidance" / "hooks"
LAUNCHER = HOOKS_DIR / "run-security-hook.sh"


class HookLauncherTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ccm-launcher-"))
        self.env = dict(os.environ)
        self.env["CLAUDE_SECURITY_STATE_DIR"] = str(self.tmp / "state")
        self.env["CLAUDE_SECURITY_LOG"] = str(self.tmp / "debug.log")
        self.env.pop("ENABLE_SECURITY_REMINDER", None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, payload, env=None):
        return subprocess.run(
            ["bash", str(LAUNCHER)],
            input=json.dumps(payload).encode("utf-8"),
            capture_output=True,
            env=env or self.env,
            timeout=60,
        )

    def _require_bash(self):
        if not LAUNCHER.exists():
            self.skipTest("launcher missing")
        if shutil.which("bash") is None:
            self.skipTest("bash not available")

    def test_blocking_exit_code_is_forwarded(self):
        self._require_bash()
        payload = {
            "session_id": "launcher",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/a.js", "content": "eval('x')"},
        }

        # Exit 2 = block. Ein fehlender Interpreter wuerde 0 liefern und den
        # Hook stillschweigend wirkungslos machen.
        result = self._run(payload)
        self.assertEqual(
            result.returncode,
            2,
            f"launcher did not block: {result.stderr.decode('utf-8', 'replace')}"
        )

    def test_safe_payload_exits_zero(self):
        self._require_bash()
        payload = {
            "session_id": "launcher",
            "tool_name": "Write",
            "tool_input": {"file_path": "src/a.js", "content": "const x = 1;"},
        }
        self.assertEqual(self._run(payload).returncode, 0)

    def test_state_file_is_written_to_configured_dir(self):
        self._require_bash()
        payload = {
            "session_id": "launcher-state",
            "tool_name": "Edit",
            "tool_input": {"file_path": "src/a.js", "new_string": "eval('x')"},
        }
        self._run(payload)

        state_files = list((self.tmp / "state").glob("*.json"))
        self.assertEqual(len(state_files), 1)
        self.assertEqual(json.loads(state_files[0].read_text(encoding="utf-8")),
                         ["src/a.js-eval_injection"])


if __name__ == "__main__":
    unittest.main()
