#!/usr/bin/env bash
# Portable launcher for security_reminder_hook.py.
#
# The interpreter is called `python3` on Linux/macOS but usually `python` on
# Windows, so a hardcoded `python3` in hooks.json silently fails for Windows
# users. This wrapper picks the first working interpreter and forwards stdin,
# stdout, stderr and the exit code unchanged (exit code 2 = block the tool).

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/security_reminder_hook.py"

for candidate in "${CLAUDE_PYTHON:-}" python3 python; do
    [ -n "$candidate" ] || continue
    command -v "$candidate" >/dev/null 2>&1 || continue
    # 'command -v' reicht nicht: unter Windows liefert die Microsoft-Store-
    # Alias "python3" einen Treffer, der beim Start mit Fehlercode abbricht.
    if "$candidate" --version >/dev/null 2>&1; then
        exec "$candidate" "$HOOK_SCRIPT"
    fi
done

# Kein Python gefunden: Hook darf den Workflow nicht blockieren.
echo "security-guidance: no Python interpreter found (set CLAUDE_PYTHON)" >&2
exit 0
