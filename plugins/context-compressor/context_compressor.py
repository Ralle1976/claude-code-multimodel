#!/usr/bin/env python3
"""
Context Compressor - LLMLingua-basierte Kontext-Komprimierung fuer Claude Code

Dies ist der dokumentierte CLI-Einstiegspunkt. Die Implementierung liegt im
Paket `ccompressor` (compress / storage / cli), damit einzelne Dateien klein
und fokussiert bleiben.

Verwendung:
  python3 context_compressor.py compress "Langer Text hier..."
  python3 context_compressor.py save-session "Zusammenfassung der Session"
  python3 context_compressor.py load-session
  python3 context_compressor.py status

Das Tool verwendet LLMLingua von Microsoft Research fuer intelligente
Token-Reduktion ohne signifikanten Bedeutungsverlust.
"""

import sys

from ccompressor import (
    DEFAULT_COMPRESSION_RATE,
    DEFAULT_TARGET_TOKENS,
    HELP_TEXT,
    compress_text,
    create_auto_summary,
    ensure_memory_dir,
    get_compression_stats,
    load_session_summary,
    main,
    memory_dir,
    save_compression_stat,
    save_session_summary,
    simple_compress,
)

__all__ = [
    "DEFAULT_COMPRESSION_RATE",
    "DEFAULT_TARGET_TOKENS",
    "HELP_TEXT",
    "compress_text",
    "create_auto_summary",
    "ensure_memory_dir",
    "get_compression_stats",
    "load_session_summary",
    "main",
    "memory_dir",
    "save_compression_stat",
    "save_session_summary",
    "simple_compress",
]


if __name__ == "__main__":
    sys.exit(main())
