#!/bin/bash
# Multi-Provider CLI Chat Plugin - Reload Script
# Stellt sicher, dass Plugins nach Neustart verfügbar sind
#
# Alle Pfade werden relativ zum Repo-Root aufgeloest; es gibt keine
# hartkodierten Benutzerverzeichnisse.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_PATH="$SCRIPT_DIR/plugins/multi-provider-cli-chat"

echo "🔄 Multi-Provider CLI Chat Plugin - Reload Script"
echo "=================================================="
echo ""

# 1. Prüfe Claude-Config
echo "✓ Prüfe Claude-Konfiguration..."
if [ ! -f "$HOME/.claude/settings.json" ]; then
    echo "❌ FEHLER: $HOME/.claude/settings.json nicht gefunden!"
    exit 1
fi

# 2. Prüfe Plugin-Pfad inkl. Inhalt
#    (ein Git-Link-Ordner existiert auch dann, wenn der Inhalt fehlt)
echo "✓ Prüfe Plugin-Verzeichnis..."
if [ ! -d "$PLUGIN_PATH" ]; then
    echo "❌ FEHLER: Plugin-Verzeichnis nicht gefunden: $PLUGIN_PATH"
    exit 1
fi

if [ ! -f "$PLUGIN_PATH/commands/openai-cli.cjs" ] || [ ! -f "$PLUGIN_PATH/commands/gemini-cli.cjs" ]; then
    echo "❌ FEHLER: Plugin-Verzeichnis ist leer (Git-Link ohne Inhalt): $PLUGIN_PATH"
    echo "   Dieses Repo enthält keine .gitmodules-Datei, 'git submodule update'"
    echo "   kann den Ordner daher nicht holen. Klone das Plugin-Repo direkt nach:"
    echo "   $PLUGIN_PATH"
    exit 1
fi
echo "✓ Plugin-Verzeichnis gefunden: $PLUGIN_PATH"

# 3. Prüfe CLI-Binaries
echo ""
echo "✓ Prüfe CLI-Verfügbarkeit..."
if ! command -v codex &> /dev/null; then
    echo "⚠️  WARNUNG: 'codex' CLI nicht im PATH gefunden!"
    echo "   Installation: npm install -g @openai/codex"
else
    echo "  ✓ codex CLI: $(codex --version)"
fi

if ! command -v gemini &> /dev/null; then
    echo "⚠️  WARNUNG: 'gemini' CLI nicht im PATH gefunden!"
    echo "   Installation siehe: https://github.com/google/generative-ai-cli"
else
    echo "  ✓ gemini CLI: $(gemini --version)"
fi

# 4. Validiere Settings JSON
echo ""
echo "✓ Validiere Claude Settings..."
if ! node -e "JSON.parse(require('fs').readFileSync(process.argv[1], 'utf8'))" "$HOME/.claude/settings.json" 2>/dev/null; then
    echo "❌ FEHLER: settings.json ist nicht valide!"
    exit 1
fi
echo "  ✓ settings.json ist valides JSON"

# 5. Prüfe Plugin-Registrierung
echo ""
echo "✓ Prüfe Plugin-Registrierung..."
if grep -q "multi-provider-cli-chat" "$HOME/.claude/settings.json"; then
    echo "  ✓ Plugin ist in settings.json registriert"
else
    echo "  ❌ Plugin ist NICHT registriert!"
    echo ""
    echo "  Füge folgendes zu ~/.claude/settings.json hinzu:"
    echo '  "plugins": {'
    echo '    "local": ['
    echo '      {'
    echo "        \"path\": \"$PLUGIN_PATH\","
    echo '        "enabled": true'
    echo '      }'
    echo '    ]'
    echo '  }'
    exit 1
fi

# 6. Test Commands
#    Ein fehlschlagender Test ist erwartbar (nicht eingeloggt) und darf unter
#    `set -e` nicht das ganze Skript abbrechen -> Auswertung per if.
echo ""
echo "✓ Teste Commands..."
if echo '{"prompt":"test"}' | node "$PLUGIN_PATH/commands/openai-cli.cjs" > /dev/null 2>&1; then
    echo "  ✓ openai-cli.cjs ist ausführbar"
else
    echo "  ⚠️  openai-cli.cjs gibt Fehler zurück (erwartet, wenn nicht eingeloggt)"
fi

if echo '{"prompt":"test"}' | node "$PLUGIN_PATH/commands/gemini-cli.cjs" > /dev/null 2>&1; then
    echo "  ✓ gemini-cli.cjs ist ausführbar"
else
    echo "  ⚠️  gemini-cli.cjs gibt Fehler zurück (erwartet, wenn nicht eingeloggt)"
fi

# 7. Zeige Verwendung
echo ""
echo "=================================================="
echo "✓ Plugin-Setup ist vollständig!"
echo ""
echo "📚 Verwendung:"
echo "  /openai-cli {\"prompt\": \"Erkläre Quicksort\", \"model\": \"gpt-5.1-codex-mini\"}"
echo "  /gemini-cli {\"prompt\": \"Was ist Python?\", \"model\": \"gemini-2.5-pro\"}"
echo ""
echo "🔐 Authentifizierung:"
echo "  Codex:  codex login"
echo "  Gemini: gemini --help (siehe Login-Flow)"
echo ""
echo "⚠️  WICHTIG: Neue Claude-Session starten, um Plugins zu laden!"
echo "=================================================="
