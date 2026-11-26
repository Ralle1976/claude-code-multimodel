"""
State- und Log-Verwaltung des Security-Reminder-Hooks.

Sicherheitsrelevante Punkte:
- Session-IDs kommen aus dem Hook-Input und werden gefiltert, damit sie
  keinen Pfadtrenner oder ".." enthalten (kein Path Traversal).
- State-Files werden ohne Symlink-Follow und mit restriktiven Rechten
  geschrieben.
- Das Debug-Log nutzt das Plattform-Temp-Verzeichnis statt eines
  hartkodierten /tmp.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

STATE_DIR_ENV = "CLAUDE_SECURITY_STATE_DIR"
DEFAULT_STATE_DIRNAME = ".claude"
STATE_PREFIX = "security_warnings_state_"

SAFE_STATE_CHARS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
)
MAX_STATE_ID_LENGTH = 128

NOFOLLOW = getattr(os, "O_NOFOLLOW", 0)


def state_dir() -> Path:
    """Verzeichnis fuer die State-Files (per Env ueberschreibbar fuer Tests)."""
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return Path(override)
    return Path.home() / DEFAULT_STATE_DIRNAME


def debug_log_path() -> Path:
    """Pfad des Debug-Logs."""
    override = os.environ.get("CLAUDE_SECURITY_LOG")
    if override:
        return Path(override)
    return Path(tempfile.gettempdir()) / "security-warnings-log.txt"


def _open_no_follow(path: Path, flags: int, mode: int = 0o600) -> int:
    """os.open mit O_NOFOLLOW, damit ein Symlink nicht als Ziel dient."""
    return os.open(str(path), flags | NOFOLLOW, mode)


def debug_log(message):
    """Haengt eine Debug-Zeile mit Zeitstempel an das Log an."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        fd = _open_no_follow(debug_log_path(), flags)
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except (OSError, ValueError):
        # Logging darf den Hook niemals blockieren.
        pass


def sanitize_session_id(session_id) -> str:
    """
    Macht aus einem beliebigen Session-Namen einen sicheren Dateinamen-Teil.

    Der Wert kommt aus dem Hook-Input und ist damit nicht vertrauenswuerdig:
    ohne Filterung koennte "../../x" das State-File ausserhalb des
    State-Verzeichnisses schreiben.
    """
    if not isinstance(session_id, str) or not session_id:
        return "default"

    cleaned = "".join(char for char in session_id if char in SAFE_STATE_CHARS)
    if not cleaned:
        return "default"

    return cleaned[:MAX_STATE_ID_LENGTH]


def get_state_file(session_id) -> Path:
    """Pfad des session-spezifischen State-Files (immer im State-Verzeichnis)."""
    return state_dir() / f"{STATE_PREFIX}{sanitize_session_id(session_id)}.json"


def cleanup_old_state_files():
    """Loescht State-Files, die aelter als 30 Tage sind."""
    directory = state_dir()
    if not directory.is_dir():
        return

    thirty_days_ago = datetime.now().timestamp() - (30 * 24 * 60 * 60)

    try:
        entries = list(directory.iterdir())
    except OSError:
        return

    for entry in entries:
        try:
            if not entry.name.startswith(STATE_PREFIX) or not entry.name.endswith(".json"):
                continue
            # Nur echte Dateien loeschen - keine Symlinks oder Verzeichnisse.
            if entry.is_symlink() or not entry.is_file():
                continue
            if entry.stat().st_mtime < thirty_days_ago:
                entry.unlink()
        except OSError:
            continue  # Fehler bei einzelnen Dateien ignorieren


def load_state(session_id) -> set:
    """Laedt die bereits gezeigten Warnungen einer Session."""
    path = get_state_file(session_id)
    if not path.exists():
        return set()

    try:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return set()

    if not isinstance(loaded, list):
        return set()

    return {item for item in loaded if isinstance(item, str)}


def save_state(session_id, shown_warnings):
    """Schreibt die bereits gezeigten Warnungen einer Session."""
    path = get_state_file(session_id)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        fd = _open_no_follow(path, flags)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(sorted(shown_warnings), f)
    except OSError as e:
        debug_log(f"Failed to save state file: {e}")
