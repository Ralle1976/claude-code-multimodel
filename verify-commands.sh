#!/bin/bash
# Multi-Provider CLI Chat Plugin - Command Verification
# Prüft ob die Commands noch installiert sind und repariert sie falls nötig

set -e

COMMANDS_DIR="$HOME/.claude/commands"
PLUGIN_DIR="/home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat"

echo "🔍 Multi-Provider CLI Chat - Command Verification"
echo "=================================================="
echo ""

# Funktion: Prüfe einzelnen Command
check_command() {
    local cmd_name=$1
    local issues=0

    echo "Prüfe $cmd_name..."

    # Prüfe Symlink
    if [ ! -L "$COMMANDS_DIR/$cmd_name" ]; then
        echo "  ❌ Symlink fehlt: $cmd_name"
        issues=$((issues + 1))
    elif [ ! -e "$COMMANDS_DIR/$cmd_name" ]; then
        echo "  ❌ Symlink ist broken: $cmd_name"
        issues=$((issues + 1))
    else
        echo "  ✓ Symlink OK: $cmd_name"
    fi

    # Prüfe Dokumentation
    if [ ! -f "$COMMANDS_DIR/$cmd_name.md" ]; then
        echo "  ❌ Dokumentation fehlt: $cmd_name.md"
        issues=$((issues + 1))
    else
        echo "  ✓ Dokumentation OK: $cmd_name.md"
    fi

    return $issues
}

# Prüfe beide Commands
total_issues=0
check_command "openai-cli" || total_issues=$((total_issues + $?))
check_command "gemini-cli" || total_issues=$((total_issues + $?))

echo ""

# Falls Probleme gefunden wurden, biete Reparatur an
if [ $total_issues -gt 0 ]; then
    echo "⚠️  Es wurden $total_issues Problem(e) gefunden!"
    echo ""
    echo "Möchtest du die Commands automatisch reparieren? (j/n)"
    read -r answer

    if [ "$answer" = "j" ] || [ "$answer" = "J" ]; then
        echo ""
        echo "🔧 Repariere Commands..."
        /home/ralle/claude-code-multimodel/install-commands.sh
    else
        echo ""
        echo "ℹ️  Zum manuellen Reparieren führe aus:"
        echo "   /home/ralle/claude-code-multimodel/install-commands.sh"
    fi
else
    echo "✅ Alle Commands sind korrekt installiert!"
    echo ""
    echo "📋 Installierte Commands:"
    ls -lh "$COMMANDS_DIR" | grep -E "openai-cli|gemini-cli"
fi

echo ""
echo "=================================================="
