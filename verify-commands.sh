#!/bin/bash
# Multi-Provider CLI Chat Plugin - Command Verification
# Prüft ob die Commands noch installiert sind und repariert sie falls nötig
#
# Alle Pfade werden relativ zum Repo-Root aufgeloest; es gibt keine
# hartkodierten Benutzerverzeichnisse.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_DIR="$HOME/.claude/commands"
PLUGIN_DIR="$SCRIPT_DIR/plugins/multi-provider-cli-chat"

echo "🔍 Multi-Provider CLI Chat - Command Verification"
echo "=================================================="
echo ""

# Funktion: Prüfe einzelnen Command
# Rückgabe: 0 = alles ok, 1 = mindestens ein Problem
check_command() {
    local cmd_name=$1
    local issues=0

    echo "Prüfe $cmd_name..."

    if [ ! -L "$COMMANDS_DIR/$cmd_name" ]; then
        echo "  ❌ Symlink fehlt: $cmd_name"
        issues=$((issues + 1))
    elif [ ! -e "$COMMANDS_DIR/$cmd_name" ]; then
        echo "  ❌ Symlink ist broken: $cmd_name"
        issues=$((issues + 1))
    else
        echo "  ✓ Symlink OK: $cmd_name"
    fi

    if [ ! -f "$COMMANDS_DIR/$cmd_name.md" ]; then
        echo "  ❌ Dokumentation fehlt: $cmd_name.md"
        issues=$((issues + 1))
    else
        echo "  ✓ Dokumentation OK: $cmd_name.md"
    fi

    if [ "$issues" -gt 0 ]; then
        return 1
    fi
    return 0
}

# Prüfe Plugin-Quellen und beide Commands
total_issues=0

if [ ! -f "$PLUGIN_DIR/commands/openai-cli.cjs" ]; then
    echo "  ❌ Plugin-Quellen fehlen: $PLUGIN_DIR/commands/openai-cli.cjs"
    echo "     (Git-Link ohne Inhalt; dieses Repo hat keine .gitmodules-Datei)"
    total_issues=$((total_issues + 1))
fi

check_command "openai-cli" || total_issues=$((total_issues + 1))
check_command "gemini-cli" || total_issues=$((total_issues + 1))

echo ""

# Falls Probleme gefunden wurden, biete Reparatur an
if [ "$total_issues" -gt 0 ]; then
    echo "⚠️  Es wurden $total_issues Problem(e) gefunden!"
    echo ""
    echo "Möchtest du die Commands automatisch reparieren? (j/n)"
    # Ohne TTY (z.B. in einem Cronjob) bricht read mit Fehler ab -> Default n
    read -r answer || answer="n"

    if [ "$answer" = "j" ] || [ "$answer" = "J" ]; then
        echo ""
        echo "🔧 Repariere Commands..."
        "$SCRIPT_DIR/install-commands.sh"
    else
        echo ""
        echo "ℹ️  Zum manuellen Reparieren führe aus:"
        echo "   $SCRIPT_DIR/install-commands.sh"
    fi
else
    echo "✅ Alle Commands sind korrekt installiert!"
    echo ""
    echo "📋 Installierte Commands:"
    ls -lh "$COMMANDS_DIR" | grep -E "openai-cli|gemini-cli" || true
fi

echo ""
echo "=================================================="
