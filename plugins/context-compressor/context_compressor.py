#!/usr/bin/env python3
"""
Context Compressor - LLMLingua-basierte Kontext-Komprimierung fuer Claude Code

Funktionen:
1. compress - Komprimiert Text mit LLMLingua (bis 20x)
2. save-session - Speichert Session-Zusammenfassung
3. load-session - Laedt letzte Session-Zusammenfassung
4. status - Zeigt Komprimierungsstatistiken

Verwendung:
  python3 context_compressor.py compress "Langer Text hier..."
  python3 context_compressor.py save-session "Zusammenfassung der Session"
  python3 context_compressor.py load-session
  python3 context_compressor.py status

Das Tool verwendet LLMLingua von Microsoft Research fuer intelligente
Token-Reduktion ohne signifikanten Bedeutungsverlust.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Session Memory Pfade
MEMORY_DIR = Path.home() / ".claude-memory"
SESSION_FILE = MEMORY_DIR / "session_summary.md"
HISTORY_FILE = MEMORY_DIR / "session_history.jsonl"
STATS_FILE = MEMORY_DIR / "compression_stats.json"

# LLMLingua Konfiguration
DEFAULT_COMPRESSION_RATE = 0.5  # 50% der Tokens behalten
DEFAULT_TARGET_TOKENS = 2000   # Ziel-Token-Anzahl


def ensure_memory_dir():
    """Erstellt Memory-Verzeichnis falls noetig."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_llmlingua():
    """Laedt LLMLingua Kompressor (lazy loading)."""
    try:
        from llmlingua import PromptCompressor
        return PromptCompressor(
            model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
            use_llmlingua2=True,
            device_map="cpu"  # CPU fuer WSL-Kompatibilitaet
        )
    except ImportError:
        return None
    except Exception as e:
        print(f"LLMLingua Ladefehler: {e}", file=sys.stderr)
        return None


def simple_compress(text: str, target_ratio: float = 0.5) -> str:
    """
    Einfache regelbasierte Komprimierung ohne ML-Modell.
    Entfernt redundante Phrasen und verkuerzt Saetze.
    """
    import re

    # Entferne ueberfluessige Whitespaces
    text = re.sub(r'\s+', ' ', text).strip()

    # Entferne gaengige Fuellwoerter (Deutsch + Englisch)
    filler_patterns = [
        r'\b(also|eigentlich|sozusagen|quasi|praktisch|grundsaetzlich|prinzipiell)\b',
        r'\b(basically|actually|literally|essentially|fundamentally)\b',
        r'\b(ich denke|ich glaube|ich meine|meiner Meinung nach)\b',
        r'\b(I think|I believe|I mean|in my opinion)\b',
    ]
    for pattern in filler_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Entferne doppelte Leerzeichen nach dem Entfernen
    text = re.sub(r'\s+', ' ', text).strip()

    # Falls noch zu lang, kuerze auf target_ratio
    words = text.split()
    target_words = int(len(words) * target_ratio)
    if len(words) > target_words and target_words > 50:
        # Behalte Anfang und Ende (wichtigste Teile)
        keep_start = target_words * 2 // 3
        keep_end = target_words - keep_start
        text = ' '.join(words[:keep_start]) + ' [...] ' + ' '.join(words[-keep_end:])

    return text


def compress_text(text: str, target_ratio: float = DEFAULT_COMPRESSION_RATE, use_llmlingua: bool = True) -> dict:
    """
    Komprimiert Text mit LLMLingua oder Fallback.

    Args:
        text: Zu komprimierender Text
        target_ratio: Anteil der zu behaltenden Tokens (0.0-1.0)
        use_llmlingua: Wenn False, wird nur einfache Komprimierung verwendet

    Returns:
        dict mit compressed_text, original_tokens, compressed_tokens, ratio
    """
    if not text or len(text.strip()) < 100:
        return {
            "success": True,
            "compressed_text": text,
            "original_tokens": len(text.split()),
            "compressed_tokens": len(text.split()),
            "compression_ratio": 1.0,
            "skipped": True,
            "reason": "Text zu kurz fuer Komprimierung"
        }

    # Versuche LLMLingua wenn gewuenscht
    compressor = None
    if use_llmlingua:
        compressor = load_llmlingua()

    if not compressor:
        # Fallback: Einfache regelbasierte Komprimierung
        original_tokens = len(text.split())
        compressed = simple_compress(text, target_ratio)
        compressed_tokens = len(compressed.split())

        save_compression_stat(original_tokens, compressed_tokens)

        return {
            "success": True,
            "compressed_text": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(compressed_tokens / original_tokens, 3) if original_tokens > 0 else 1.0,
            "tokens_saved": original_tokens - compressed_tokens,
            "method": "simple" if use_llmlingua else "simple_only",
            "note": "Einfache Komprimierung (LLMLingua nicht verfuegbar)" if use_llmlingua else "Einfache Komprimierung"
        }

    try:
        # Komprimiere mit LLMLingua
        result = compressor.compress_prompt(
            text,
            rate=target_ratio,
            force_tokens=['\n', '.', '!', '?', ','],  # Behalte wichtige Zeichen
            drop_consecutive=True
        )

        compressed = result["compressed_prompt"]
        original_tokens = result.get("origin_tokens", len(text.split()))
        compressed_tokens = result.get("compressed_tokens", len(compressed.split()))

        # Speichere Statistik
        save_compression_stat(original_tokens, compressed_tokens)

        return {
            "success": True,
            "compressed_text": compressed,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": round(compressed_tokens / original_tokens, 3) if original_tokens > 0 else 1.0,
            "tokens_saved": original_tokens - compressed_tokens
        }

    except Exception as e:
        return {
            "success": False,
            "error": "compression_failed",
            "message": f"Komprimierung fehlgeschlagen: {str(e)}"
        }


def save_compression_stat(original: int, compressed: int):
    """Speichert Komprimierungsstatistik."""
    ensure_memory_dir()

    stats = {"total_original": 0, "total_compressed": 0, "compressions": 0}
    if STATS_FILE.exists():
        try:
            stats = json.loads(STATS_FILE.read_text())
        except:
            pass

    stats["total_original"] += original
    stats["total_compressed"] += compressed
    stats["compressions"] += 1
    stats["last_compression"] = datetime.now().isoformat()

    STATS_FILE.write_text(json.dumps(stats, indent=2))


def save_session_summary(summary: str, metadata: dict = None):
    """
    Speichert Session-Zusammenfassung fuer naechsten Start.

    Args:
        summary: Zusammenfassungstext
        metadata: Optionale Metadaten (Projekt, Kontext, etc.)
    """
    ensure_memory_dir()

    # Erstelle strukturierte Zusammenfassung
    content = f"""# Claude Session Memory
Letzte Aktualisierung: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Kontext der letzten Session

{summary}
"""

    if metadata:
        content += "\n## Metadaten\n"
        for key, value in metadata.items():
            content += f"- **{key}**: {value}\n"

    SESSION_FILE.write_text(content)

    # Fuege zur History hinzu
    history_entry = {
        "timestamp": datetime.now().isoformat(),
        "summary_length": len(summary),
        "metadata": metadata
    }

    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(history_entry) + "\n")

    return {
        "success": True,
        "message": "Session-Zusammenfassung gespeichert.",
        "file": str(SESSION_FILE),
        "summary_length": len(summary)
    }


def load_session_summary() -> dict:
    """Laedt die letzte Session-Zusammenfassung."""
    if not SESSION_FILE.exists():
        return {
            "success": True,
            "exists": False,
            "message": "Keine vorherige Session-Zusammenfassung gefunden."
        }

    content = SESSION_FILE.read_text()

    return {
        "success": True,
        "exists": True,
        "content": content,
        "file": str(SESSION_FILE),
        "last_modified": datetime.fromtimestamp(SESSION_FILE.stat().st_mtime).isoformat()
    }


def get_compression_stats() -> dict:
    """Gibt Komprimierungsstatistiken zurueck."""
    ensure_memory_dir()

    stats = {
        "total_original": 0,
        "total_compressed": 0,
        "compressions": 0,
        "average_ratio": 0,
        "total_saved": 0
    }

    if STATS_FILE.exists():
        try:
            saved_stats = json.loads(STATS_FILE.read_text())
            stats.update(saved_stats)

            if stats["total_original"] > 0:
                stats["average_ratio"] = round(stats["total_compressed"] / stats["total_original"], 3)
                stats["total_saved"] = stats["total_original"] - stats["total_compressed"]
        except:
            pass

    # Session-Info
    stats["session_file_exists"] = SESSION_FILE.exists()
    if SESSION_FILE.exists():
        stats["session_file_size"] = SESSION_FILE.stat().st_size

    # History-Info
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE) as f:
            stats["total_sessions"] = sum(1 for _ in f)
    else:
        stats["total_sessions"] = 0

    return {
        "success": True,
        "stats": stats,
        "memory_dir": str(MEMORY_DIR)
    }


def create_auto_summary(conversation_text: str) -> dict:
    """
    Erstellt automatisch eine Zusammenfassung fuer Session-Memory.
    Nutzt LLMLingua fuer intelligente Komprimierung.
    """
    # Zuerst komprimieren
    compressed = compress_text(conversation_text, target_ratio=0.3)

    if not compressed.get("success"):
        # Fallback: Einfache Kuerzung
        words = conversation_text.split()
        if len(words) > 500:
            summary = " ".join(words[:200]) + "\n...\n" + " ".join(words[-200:])
        else:
            summary = conversation_text

        return save_session_summary(summary)

    return save_session_summary(compressed["compressed_text"], {
        "compression_ratio": compressed.get("compression_ratio"),
        "original_tokens": compressed.get("original_tokens"),
        "compressed_tokens": compressed.get("compressed_tokens")
    })


def main():
    if len(sys.argv) < 2:
        print("""
Context Compressor - LLMLingua Integration fuer Claude Code

Befehle:
  compress <text>      - Komprimiert Text mit LLMLingua
  save-session <text>  - Speichert Session-Zusammenfassung
  load-session         - Laedt letzte Session
  status               - Zeigt Statistiken
  auto-summary <text>  - Erstellt automatische Zusammenfassung

Beispiele:
  python3 context_compressor.py compress "Langer Konversationstext..."
  python3 context_compressor.py save-session "User arbeitet an STT-Plugin"
  python3 context_compressor.py load-session
""")
        return

    action = sys.argv[1].lower()

    if action == "compress":
        if len(sys.argv) < 3:
            # Lese von stdin
            text = sys.stdin.read()
        else:
            text = " ".join(sys.argv[2:])

        result = compress_text(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "save-session":
        if len(sys.argv) < 3:
            text = sys.stdin.read()
        else:
            text = " ".join(sys.argv[2:])

        result = save_session_summary(text)
        print(json.dumps(result, indent=2))

    elif action == "load-session":
        result = load_session_summary()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif action == "status":
        result = get_compression_stats()
        print(json.dumps(result, indent=2))

    elif action == "auto-summary":
        if len(sys.argv) < 3:
            text = sys.stdin.read()
        else:
            text = " ".join(sys.argv[2:])

        result = create_auto_summary(text)
        print(json.dumps(result, indent=2))

    else:
        print(json.dumps({
            "success": False,
            "error": "invalid_action",
            "message": f"Unbekannte Aktion: {action}. Verfuegbar: compress, save-session, load-session, status, auto-summary"
        }))


if __name__ == "__main__":
    main()
