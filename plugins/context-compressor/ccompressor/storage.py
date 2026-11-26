"""
Persistenz fuer den Context Compressor (Session-Memory + Statistiken).

Alle Pfade werden lazy aus der Umgebung aufgeloest, damit Tests mit
CLAUDE_MEMORY_DIR vollstaendig isoliert laufen koennen.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

# UTF-8 ueberall - der Windows-Default (cp1252) kann Emojis/CJK nicht schreiben.
ENCODING = "utf-8"
DEFAULT_MEMORY_DIRNAME = ".claude-memory"


def memory_dir() -> Path:
    """Wurzelverzeichnis fuer Session-Memory (per Env ueberschreibbar)."""
    override = os.environ.get("CLAUDE_MEMORY_DIR")
    if override:
        return Path(override)
    return Path.home() / DEFAULT_MEMORY_DIRNAME


def session_file() -> Path:
    return memory_dir() / "session_summary.md"


def history_file() -> Path:
    return memory_dir() / "session_history.jsonl"


def stats_file() -> Path:
    return memory_dir() / "compression_stats.json"


def ensure_memory_dir() -> Path:
    """Erstellt das Memory-Verzeichnis falls noetig."""
    target = memory_dir()
    target.mkdir(parents=True, exist_ok=True)
    return target


def read_text_file(path: Path) -> str:
    """Liest eine Datei als UTF-8 (Ersatzzeichen statt UnicodeDecodeError)."""
    return path.read_text(encoding=ENCODING, errors="replace")


def write_text_file(path: Path, content: str):
    """Schreibt eine Datei atomar als UTF-8."""
    ensure_memory_dir()
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=ENCODING) as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def empty_stats() -> dict:
    return {"total_original": 0, "total_compressed": 0, "compressions": 0}


def load_stats_file() -> dict:
    """
    Laedt die Statistikdatei und faengt kaputte oder falsch geformte Inhalte ab.

    Ungueltiges JSON oder ein JSON-Array ohne die erwarteten Keys darf das
    Skript nicht zum Absturz bringen.
    """
    path = stats_file()
    if not path.exists():
        return empty_stats()

    try:
        loaded = json.loads(read_text_file(path))
    except (json.JSONDecodeError, OSError):
        return empty_stats()

    if not isinstance(loaded, dict):
        return empty_stats()

    stats = empty_stats()
    for key in ("total_original", "total_compressed", "compressions"):
        value = loaded.get(key, 0)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        stats[key] = value

    if isinstance(loaded.get("last_compression"), str):
        stats["last_compression"] = loaded["last_compression"]

    return stats


def save_compression_stat(original: int, compressed: int):
    """Schreibt eine Komprimierung in die Statistikdatei."""
    stats = load_stats_file()
    stats["total_original"] += original
    stats["total_compressed"] += compressed
    stats["compressions"] += 1
    stats["last_compression"] = datetime.now().isoformat()

    try:
        write_text_file(stats_file(), json.dumps(stats, indent=2))
    except OSError:
        # Statistik ist Nice-to-have; ein Schreibfehler darf die
        # Komprimierung nicht kaputt machen.
        pass


def save_session_summary(summary: str, metadata: dict = None) -> dict:
    """
    Speichert eine Session-Zusammenfassung fuer den naechsten Start.

    Args:
        summary: Zusammenfassungstext
        metadata: Optionale Metadaten (Projekt, Kontext, ...)
    """
    ensure_memory_dir()

    content = f"""# Claude Session Memory
Letzte Aktualisierung: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Kontext der letzten Session

{summary}
"""

    if metadata:
        content += "\n## Metadaten\n"
        for key, value in metadata.items():
            content += f"- **{key}**: {value}\n"

    target = session_file()
    write_text_file(target, content)

    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "summary_length": len(summary),
        "metadata": metadata,
    }

    with open(history_file(), "a", encoding=ENCODING) as handle:
        handle.write(json.dumps(history_entry, default=str) + "\n")

    return {
        "success": True,
        "message": "Session-Zusammenfassung gespeichert.",
        "file": str(target),
        "summary_length": len(summary),
    }


def load_session_summary() -> dict:
    """Laedt die letzte Session-Zusammenfassung."""
    target = session_file()
    if not target.exists():
        return {
            "success": True,
            "exists": False,
            "message": "Keine vorherige Session-Zusammenfassung gefunden.",
        }

    return {
        "success": True,
        "exists": True,
        "content": read_text_file(target),
        "file": str(target),
        "last_modified": datetime.fromtimestamp(target.stat().st_mtime).isoformat(),
    }


def get_compression_stats() -> dict:
    """Aggregierte Komprimierungsstatistiken inkl. Session-Info."""
    ensure_memory_dir()

    stats = load_stats_file()
    stats.setdefault("average_ratio", 0)
    stats.setdefault("total_saved", 0)

    if stats["total_original"] > 0:
        stats["average_ratio"] = round(stats["total_compressed"] / stats["total_original"], 3)
        stats["total_saved"] = stats["total_original"] - stats["total_compressed"]

    session_path = session_file()
    stats["session_file_exists"] = session_path.exists()
    if session_path.exists():
        stats["session_file_size"] = session_path.stat().st_size

    history_path = history_file()
    if history_path.exists():
        try:
            with open(history_path, encoding=ENCODING, errors="replace") as handle:
                stats["total_sessions"] = sum(1 for _ in handle)
        except OSError:
            stats["total_sessions"] = 0
    else:
        stats["total_sessions"] = 0

    return {
        "success": True,
        "stats": stats,
        "memory_dir": str(memory_dir()),
    }
