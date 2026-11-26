#!/bin/bash
# Setup Shell Integration für Multi-Provider CLI Chat Plugin
#
# Der Repo-Pfad wird beim Setup ermittelt und in die ~/.bashrc geschrieben
# (statt eines hartkodierten Benutzerverzeichnisses).

BASHRC="$HOME/.bashrc"
MARKER="# Claude Multi-Provider Plugin Integration"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! grep -q "$MARKER" "$BASHRC" 2>/dev/null; then
    echo ""
    echo "Füge Shell-Integration zu ~/.bashrc hinzu..."
    # Unquotiertes Heredoc: $SCRIPT_DIR wird jetzt eingesetzt, alle
    # Laufzeit-Variablen der Ziel-Shell sind mit \$ escaped.
    cat >> "$BASHRC" << EOF

# Claude Multi-Provider Plugin Integration
# Zeigt Plugin-Status bei Shell-Start an
CLAUDE_MULTIPROVIDER_ROOT="$SCRIPT_DIR"
export CLAUDE_MULTIPROVIDER_ROOT
if [ -d "\$CLAUDE_MULTIPROVIDER_ROOT/plugins/multi-provider-cli-chat" ]; then
    echo "✓ Claude Multi-Provider CLI Plugin verfügbar"
    echo "  Commands: /openai-cli, /gemini-cli"

    # Prüfe CLI-Verfügbarkeit
    if command -v codex >/dev/null 2>&1 && command -v gemini >/dev/null 2>&1; then
        echo "  CLIs: codex ✓ | gemini ✓"
    else
        command -v codex >/dev/null 2>&1 || echo "  ⚠️  codex CLI fehlt: npm install -g @openai/codex"
        command -v gemini >/dev/null 2>&1 || echo "  ⚠️  gemini CLI fehlt"
    fi
fi

# Alias für Plugin-Management
alias claude-plugins-check='"\$CLAUDE_MULTIPROVIDER_ROOT/reload-plugins.sh"'
alias claude-commands-verify='"\$CLAUDE_MULTIPROVIDER_ROOT/verify-commands.sh"'
alias claude-commands-install='"\$CLAUDE_MULTIPROVIDER_ROOT/install-commands.sh"'

# Auto-Verification bei Shell-Start (silent)
if [ ! -L "\$HOME/.claude/commands/openai-cli" ] || [ ! -L "\$HOME/.claude/commands/gemini-cli" ]; then
    echo "  ⚠️  Commands fehlen! Führe aus: claude-commands-install"
fi

EOF
    echo "✓ Integration hinzugefügt!"
    echo ""
    echo "Starte neue Shell oder führe aus: source ~/.bashrc"
else
    echo "✓ Integration bereits vorhanden"
    echo ""
    echo "ℹ️  Falls der Repo-Pfad umgezogen ist: Block '$MARKER' in ~/.bashrc"
    echo "   entfernen und dieses Skript erneut ausführen."
fi
