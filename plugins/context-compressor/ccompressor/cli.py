"""
CLI fuer den Context Compressor: Argument-Parsing und Dispatch.

Alle Nutzereingaben kommen aus argv oder stdin; es wird nie ein Shell-String
gebaut.
"""

import json
import sys

from .compress import DEFAULT_COMPRESSION_RATE, compress_text
from .storage import (
    get_compression_stats,
    load_session_summary,
    save_session_summary,
)
from .storage import ENCODING

HELP_TEXT = """
Context Compressor - LLMLingua Integration fuer Claude Code

Befehle:
  compress [--ratio R] <text>  - Komprimiert Text mit LLMLingua
  save-session <text>          - Speichert Session-Zusammenfassung
  load-session                 - Laedt letzte Session
  status                       - Zeigt Statistiken
  auto-summary <text>          - Erstellt automatische Zusammenfassung

Ohne <text> wird von stdin gelesen (UTF-8).

Beispiele:
  python3 context_compressor.py compress "Langer Konversationstext..."
  python3 context_compressor.py save-session "User arbeitet an STT-Plugin"
  python3 context_compressor.py load-session
"""


def read_utf8_stdin() -> str:
    """
    Liest stdin als UTF-8, unabhaengig von der Plattform-Codepage.

    Ohne das schlaegt sys.stdin.read() auf Windows (cp1252) bei Emojis oder
    CJK-Zeichen fehl.
    """
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is not None:
        try:
            return buffer.read().decode(ENCODING, errors="replace")
        except (OSError, ValueError):
            return ""
    try:
        return sys.stdin.read()
    except (OSError, ValueError, UnicodeDecodeError):
        return ""


def parse_ratio(args: list) -> tuple:
    """
    Entfernt ein optionales --ratio aus den Argumenten.

    Returns:
        (ratio, restliche_args)
    """
    ratio = DEFAULT_COMPRESSION_RATE
    remaining = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--ratio" and index + 1 < len(args):
            try:
                ratio = float(args[index + 1])
            except ValueError:
                remaining.extend([arg, args[index + 1]])
            index += 2
            continue
        if arg.startswith("--ratio="):
            try:
                ratio = float(arg.split("=", 1)[1])
            except ValueError:
                remaining.append(arg)
            index += 1
            continue
        remaining.append(arg)
        index += 1
    return ratio, remaining


def collect_text(args: list) -> str:
    """Nutzt die Argumente als Text, sonst stdin."""
    if args:
        return " ".join(args)
    return read_utf8_stdin()


def create_auto_summary(conversation_text: str) -> dict:
    """Komprimiert einen Gespraechsverlauf und speichert ihn als Session-Memory."""
    compressed = compress_text(conversation_text, target_ratio=0.3)

    if not compressed.get("success"):
        words = conversation_text.split()
        if len(words) > 500:
            summary = " ".join(words[:200]) + "\n...\n" + " ".join(words[-200:])
        else:
            summary = conversation_text
        return save_session_summary(summary)

    return save_session_summary(compressed["compressed_text"], {
        "compression_ratio": compressed.get("compression_ratio"),
        "original_tokens": compressed.get("original_tokens"),
        "compressed_tokens": compressed.get("compressed_tokens"),
    })


def _emit(result: dict) -> int:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("success") else 1


def main(argv=None) -> int:
    """
    CLI-Einstiegspunkt.

    Returns:
        Exit-Code: 0 bei Erfolg, 1 bei Fehlern.
    """
    if argv is None:
        argv = sys.argv

    if len(argv) < 2:
        print(HELP_TEXT)
        return 0

    action = argv[1].lower()
    rest = argv[2:]

    if action == "compress":
        ratio, text_args = parse_ratio(rest)
        return _emit(compress_text(collect_text(text_args), target_ratio=ratio))

    if action == "save-session":
        return _emit(save_session_summary(collect_text(rest)))

    if action == "load-session":
        return _emit(load_session_summary())

    if action == "status":
        return _emit(get_compression_stats())

    if action == "auto-summary":
        return _emit(create_auto_summary(collect_text(rest)))

    print(json.dumps({
        "success": False,
        "error": "invalid_action",
        "message": f"Unbekannte Aktion: {action}. Verfuegbar: compress, save-session, load-session, status, auto-summary"
    }, ensure_ascii=False))
    return 1
