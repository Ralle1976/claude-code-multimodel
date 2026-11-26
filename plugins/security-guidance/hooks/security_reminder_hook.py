#!/usr/bin/env python3
"""
Security Reminder Hook for Claude Code

PreToolUse-Hook fuer Edit/Write/MultiEdit: prueft Dateipfad und Inhalt gegen
einen Regelkatalog und blockt den Aufruf beim ersten Treffer pro Session.

Aufbau:
  security_patterns.py - Regelkatalog + check_patterns
  security_state.py    - Session-State, Pfad-Sanitisierung, Debug-Log
  dieses Modul         - Payload lesen, auswerten, Exit-Code setzen
"""

import json
import os
import random
import sys

from security_patterns import SECURITY_PATTERNS, check_patterns
from security_state import (
    cleanup_old_state_files,
    get_state_file,
    load_state,
    sanitize_session_id,
    save_state,
)

# Obergrenze fuer den Hook-Payload: schuetzt vor versehentlich riesigen
# Tool-Inputs (z.B. generierte Dateien) und vor Speicher-Erschoepfung.
MAX_INPUT_BYTES = 10 * 1024 * 1024

__all__ = [
    "MAX_INPUT_BYTES",
    "SECURITY_PATTERNS",
    "check_patterns",
    "cleanup_old_state_files",
    "extract_content_from_input",
    "get_state_file",
    "load_state",
    "main",
    "sanitize_session_id",
    "save_state",
]


def extract_content_from_input(tool_name, tool_input):
    """Extract content to check from tool input based on tool type."""
    if not isinstance(tool_input, dict):
        return ""

    if tool_name == "Write":
        return tool_input.get("content", "") or ""
    if tool_name == "Edit":
        return tool_input.get("new_string", "") or ""
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits", [])
        if isinstance(edits, list):
            return " ".join(
                edit.get("new_string", "") or ""
                for edit in edits
                if isinstance(edit, dict)
            )
        return ""

    return ""


def read_hook_input():
    """
    Liest den Hook-Payload als Bytes.

    Bytes statt str: json.loads erkennt das Encoding selbst, damit ein
    Nicht-UTF-8-Payload (Windows-Codepage) keinen UnicodeDecodeError ausloest.
    """
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is not None:
        return buffer.read(MAX_INPUT_BYTES + 1)
    return sys.stdin.read(MAX_INPUT_BYTES + 1).encode("utf-8", errors="replace")


def main():
    """Main hook function."""
    security_reminder_enabled = os.environ.get("ENABLE_SECURITY_REMINDER", "1")

    if security_reminder_enabled == "0":
        sys.exit(0)

    # Periodically clean up old state files (10% chance per run)
    if random.random() < 0.1:
        cleanup_old_state_files()

    try:
        raw_input = read_hook_input()
    except (OSError, ValueError):
        sys.exit(0)

    if len(raw_input) > MAX_INPUT_BYTES:
        sys.exit(0)  # Allow tool to proceed

    try:
        input_data = json.loads(raw_input)
    except (json.JSONDecodeError, UnicodeDecodeError):
        sys.exit(0)  # Allow tool to proceed if we can't parse input

    if not isinstance(input_data, dict):
        sys.exit(0)

    session_id = input_data.get("session_id", "default")
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ["Edit", "Write", "MultiEdit"]:
        sys.exit(0)  # Allow non-file tools to proceed

    if not isinstance(tool_input, dict):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not isinstance(file_path, str) or not file_path:
        sys.exit(0)  # Allow if no file path

    content = extract_content_from_input(tool_name, tool_input)

    rule_name, reminder = check_patterns(file_path, content)

    if rule_name and reminder:
        warning_key = f"{file_path}-{rule_name}"
        shown_warnings = load_state(session_id)

        if warning_key not in shown_warnings:
            shown_warnings.add(warning_key)
            save_state(session_id, shown_warnings)

            print(reminder, file=sys.stderr)
            sys.exit(2)  # Block tool execution (exit code 2 for PreToolUse hooks)

    # Allow tool to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
