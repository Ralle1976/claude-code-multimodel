#!/bin/bash
# Setup Shell Integration für Multi-Provider CLI Chat Plugin

BASHRC="$HOME/.bashrc"
MARKER="# Claude Multi-Provider Plugin Integration"

if ! grep -q "$MARKER" "$BASHRC"; then
    echo ""
    echo "Füge Shell-Integration zu ~/.bashrc hinzu..."
    cat >> "$BASHRC" << 'EOF'

# Claude Multi-Provider Plugin Integration
# Zeigt Plugin-Status bei Shell-Start an
if [ -d "/home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat" ]; then
    echo "✓ Claude Multi-Provider CLI Plugin verfügbar"
    echo "  Commands: /openai-cli, /gemini-cli"

    # Prüfe CLI-Verfügbarkeit
    if command -v codex &> /dev/null && command -v gemini &> /dev/null; then
        echo "  CLIs: codex ✓ | gemini ✓"
    else
        [ ! command -v codex &> /dev/null ] && echo "  ⚠️  codex CLI fehlt: npm install -g @openai/codex"
        [ ! command -v gemini &> /dev/null ] && echo "  ⚠️  gemini CLI fehlt"
    fi
fi

# Alias für Plugin-Management
alias claude-plugins-check='/home/ralle/claude-code-multimodel/reload-plugins.sh'
alias claude-commands-verify='/home/ralle/claude-code-multimodel/verify-commands.sh'
alias claude-commands-install='/home/ralle/claude-code-multimodel/install-commands.sh'

# Auto-Verification bei Shell-Start (silent)
if [ ! -L "$HOME/.claude/commands/openai-cli" ] || [ ! -L "$HOME/.claude/commands/gemini-cli" ]; then
    echo "  ⚠️  Commands fehlen! Führe aus: claude-commands-install"
fi

EOF
    echo "✓ Integration hinzugefügt!"
    echo ""
    echo "Starte neue Shell oder führe aus: source ~/.bashrc"
else
    echo "✓ Integration bereits vorhanden"
fi
