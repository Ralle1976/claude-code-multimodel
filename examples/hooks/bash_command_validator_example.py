#!/usr/bin/env python3
"""
Claude Code Hook: Bash Command Validator
=========================================
This hook runs as a PreToolUse hook for the Bash tool.
It validates bash commands against a set of rules before execution.
In this case it changes grep calls to using rg.

Read more about hooks here: https://docs.anthropic.com/en/docs/claude-code/hooks

Make sure to change your path to your actual script.

{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/claude-code/examples/hooks/bash_command_validator_example.py"
          }
        ]
      }
    ]
  }
}

"""

import json
import re
import sys

# Define validation rules as a list of (regex pattern, message) tuples
_VALIDATION_RULES = [
    (
        r"^grep\b(?!.*\|)",
        "Use 'rg' (ripgrep) instead of 'grep' for better performance and features",
    ),
    (
        r"^find\s+\S+\s+-name\b",
        "Use 'rg --files | rg pattern' or 'rg --files -g pattern' instead of 'find -name' for better performance",
    ),
]

# Payloads groesser als das hier werden nicht geprueft (Hook darf nicht haengen).
MAX_INPUT_BYTES = 10 * 1024 * 1024


def _validate_command(command: str) -> list:
    issues = []
    for pattern, message in _VALIDATION_RULES:
        if re.search(pattern, command):
            issues.append(message)
    return issues


def _read_stdin() -> bytes:
    """Liest den Payload als Bytes; json.loads erkennt das Encoding selbst."""
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is not None:
        return buffer.read(MAX_INPUT_BYTES + 1)
    return sys.stdin.read(MAX_INPUT_BYTES + 1).encode("utf-8", errors="replace")


def main():
    try:
        raw_input = _read_stdin()
    except (OSError, ValueError) as e:
        print(f"Error: Could not read hook input: {e}", file=sys.stderr)
        sys.exit(1)

    if len(raw_input) > MAX_INPUT_BYTES:
        # Zu gross: nicht pruefen, aber den Tool-Call auch nicht blockieren.
        sys.exit(0)

    try:
        input_data = json.loads(raw_input)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        # Exit code 1 shows stderr to the user but not to Claude
        sys.exit(1)

    if not isinstance(input_data, dict):
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command:
        sys.exit(0)

    issues = _validate_command(command)
    if issues:
        for message in issues:
            print(f"• {message}", file=sys.stderr)
        # Exit code 2 blocks tool call and shows stderr to Claude
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
