"""
Context Compressor - LLMLingua-basierte Kontext-Komprimierung fuer Claude Code.

Oeffentliche API. Die Implementierung liegt in den Untermodulen:
  ccompressor.compress - LLMLingua + regelbasierter Fallback
  ccompressor.storage  - Session-Memory und Statistiken
  ccompressor.cli      - CLI-Parsing und Dispatch
"""

from .cli import HELP_TEXT, collect_text, create_auto_summary, main, parse_ratio, read_utf8_stdin
from .compress import (
    DEFAULT_COMPRESSION_RATE,
    DEFAULT_TARGET_TOKENS,
    compress_text,
    load_llmlingua,
    simple_compress,
)
from .storage import (
    ensure_memory_dir,
    get_compression_stats,
    history_file,
    load_session_summary,
    load_stats_file,
    memory_dir,
    save_compression_stat,
    save_session_summary,
    session_file,
    stats_file,
)

__all__ = [
    "DEFAULT_COMPRESSION_RATE",
    "DEFAULT_TARGET_TOKENS",
    "HELP_TEXT",
    "collect_text",
    "compress_text",
    "create_auto_summary",
    "ensure_memory_dir",
    "get_compression_stats",
    "history_file",
    "load_llmlingua",
    "load_session_summary",
    "load_stats_file",
    "main",
    "memory_dir",
    "parse_ratio",
    "read_utf8_stdin",
    "save_compression_stat",
    "save_session_summary",
    "session_file",
    "simple_compress",
    "stats_file",
]
