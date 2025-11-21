#!/bin/bash
# Multi-Provider CLI Chat Plugin - Reload Script
# Stellt sicher, dass Plugins nach Neustart verfügbar sind

set -e

echo "🔄 Multi-Provider CLI Chat Plugin - Reload Script"
echo "=================================================="
echo ""

# 1. Prüfe Claude-Config
echo "✓ Prüfe Claude-Konfiguration..."
if [ ! -f ~/.claude/settings.json ]; then
    echo "❌ FEHLER: ~/.claude/settings.json nicht gefunden!"
    exit 1
fi

# 2. Prüfe Plugin-Pfad
PLUGIN_PATH="/home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat"
if [ ! -d "$PLUGIN_PATH" ]; then
    echo "❌ FEHLER: Plugin-Verzeichnis nicht gefunden: $PLUGIN_PATH"
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
if ! python3 -m json.tool ~/.claude/settings.json > /dev/null 2>&1; then
    echo "❌ FEHLER: settings.json ist nicht valide!"
    exit 1
fi

# 5. Prüfe Plugin-Registrierung
echo ""
echo "✓ Prüfe Plugin-Registrierung..."
if grep -q "multi-provider-cli-chat" ~/.claude/settings.json; then
    echo "  ✓ Plugin ist in settings.json registriert"
else
    echo "  ❌ Plugin ist NICHT registriert!"
    echo ""
    echo "  Füge folgendes zu ~/.claude/settings.json hinzu:"
    echo '  "plugins": {'
    echo '    "local": ['
    echo '      {'
    echo '        "path": "/home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat",'
    echo '        "enabled": true'
    echo '      }'
    echo '    ]'
    echo '  }'
    exit 1
fi

# 6. Test Commands
echo ""
echo "✓ Teste Commands..."
echo '{"prompt":"test"}' | node "$PLUGIN_PATH/commands/openai-cli.cjs" > /dev/null 2>&1
if [ $? -eq 1 ]; then
    echo "  ⚠️  openai-cli.cjs gibt Fehler zurück (erwartet, wenn nicht eingeloggt)"
else
    echo "  ✓ openai-cli.cjs ist ausführbar"
fi

echo '{"prompt":"test"}' | node "$PLUGIN_PATH/commands/gemini-cli.cjs" > /dev/null 2>&1
if [ $? -eq 1 ]; then
    echo "  ⚠️  gemini-cli.cjs gibt Fehler zurück (erwartet, wenn nicht eingeloggt)"
else
    echo "  ✓ gemini-cli.cjs ist ausführbar"
fi

# 7. Zeige Verwendung
echo ""
echo "=================================================="
echo "✓ Plugin-Setup ist vollständig!"
echo ""
echo "📚 Verwendung:"
echo "  /openai-cli {\"prompt\": \"Erkläre Quicksort\", \"model\": \"o3-mini\"}"
echo "  /gemini-cli {\"prompt\": \"Was ist Python?\", \"model\": \"gemini-2.5-pro\"}"
echo ""
echo "🔐 Authentifizierung:"
echo "  Codex:  codex login"
echo "  Gemini: gemini --help (siehe Login-Flow)"
echo ""
echo "⚠️  WICHTIG: Neue Claude-Session starten, um Plugins zu laden!"
echo "=================================================="
