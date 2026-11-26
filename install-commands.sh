#!/bin/bash
# Multi-Provider CLI Chat Plugin - Command Installation
# Installiert die Slash-Commands für Claude Code
#
# Alle Pfade werden relativ zum Repo-Root aufgeloest; es gibt keine
# hartkodierten Benutzerverzeichnisse.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/plugins/multi-provider-cli-chat"
COMMANDS_DIR="$HOME/.claude/commands"

echo "🔧 Multi-Provider CLI Chat Plugin - Command Installation"
echo "=========================================================="
echo ""

# 0. Prüfe Plugin-Quellen (der Plugin-Ordner ist ein Git-Link, dessen Inhalt
#    ohne .gitmodules nicht mitgeklont wird)
echo "✓ Prüfe Plugin-Quellen..."
missing=0
for command_file in openai-cli.cjs gemini-cli.cjs; do
    if [ ! -f "$PLUGIN_DIR/commands/$command_file" ]; then
        echo "  ❌ Fehlt: $PLUGIN_DIR/commands/$command_file"
        missing=1
    fi
done
if [ "$missing" -eq 1 ]; then
    echo ""
    echo "❌ Plugin-Quellen fehlen in: $PLUGIN_DIR"
    echo "   Der Ordner ist ein Git-Link (Submodul), für den dieses Repo keine"
    echo "   .gitmodules-Datei enthält - 'git submodule update' kann ihn daher"
    echo "   nicht holen. Klone das Plugin-Repo direkt nach:"
    echo "   $PLUGIN_DIR"
    exit 1
fi
echo "  ✓ Plugin-Quellen vorhanden"

# 1. Erstelle Commands-Verzeichnis
echo "✓ Erstelle $COMMANDS_DIR Verzeichnis..."
mkdir -p "$COMMANDS_DIR"

# 2. Erstelle Symlinks zu Command-Scripts
echo "✓ Erstelle Symlinks zu Command-Scripts..."
ln -sfn "$PLUGIN_DIR/commands/openai-cli.cjs" "$COMMANDS_DIR/openai-cli"
ln -sfn "$PLUGIN_DIR/commands/gemini-cli.cjs" "$COMMANDS_DIR/gemini-cli"

# 3. Erstelle Command-Dokumentationen
echo "✓ Erstelle Command-Dokumentationen..."

cat > "$COMMANDS_DIR/openai-cli.md" << 'EOF'
# OpenAI CLI Command

Sendet Prompts an OpenAI über die Codex CLI (Account-basierte Auth, keine API-Keys).

## Usage

Der Command erwartet ein JSON-Objekt als Input:

```json
{
  "prompt": "Deine Anfrage hier",
  "model": "gpt-5.1-codex",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

## Verfügbare Modelle (2025)

- `gpt-5.1-codex` - Most capable reasoning model (beste Qualität)
- `gpt-5.1-codex-mini` - Fast reasoning model (Coding optimiert)
- `o3-mini` - Smaller o3 model (schneller)
- `gpt-5.1` - Latest GPT flagship
- `gpt-4.1` - Previous generation

## Beispiele

### Komplexe Software-Entwicklung
```bash
/openai-cli {
  "prompt": "Entwirf eine skalierbare Microservices-Architektur",
  "model": "gpt-5.1-codex",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

### Schnelle Code-Generierung
```bash
/openai-cli {
  "prompt": "Schreibe eine Python Binary Search Funktion",
  "model": "gpt-5.1-codex-mini"
}
```

## Auth

```bash
codex login
```
EOF

cat > "$COMMANDS_DIR/gemini-cli.md" << 'EOF'
# Gemini CLI Command

Sendet Prompts an Google Gemini über die Gemini CLI (Account-basierte Auth, keine API-Keys).

## Usage

Der Command erwartet ein JSON-Objekt als Input:

```json
{
  "prompt": "Deine Anfrage hier",
  "model": "gemini-3-pro-preview-11-2025",
  "approval_mode": "yolo"
}
```

## Verfügbare Modelle (2025)

- `gemini-3-pro-preview-11-2025` - Latest (1M Token Context, 1501 Elo)
- `gemini-3-pro-preview-11-2025-thinking` - Mit sichtbarem Reasoning
- `gemini-3.0-flash` - Fast (Sub-Sekunden)
- `gemini-2.5-pro` - Previous generation (stabil)

## Beispiele

### Große Codebase-Analyse
```bash
/gemini-cli {
  "prompt": "Analysiere diese gesamte Codebase",
  "model": "gemini-3-pro-preview-11-2025",
  "approval_mode": "yolo"
}
```

### Ultra-schnelle Responses
```bash
/gemini-cli {
  "prompt": "Quick: Unterschied Array vs Linked List?",
  "model": "gemini-3.0-flash",
  "yolo": true
}
```
EOF

# 4. Validierung
echo ""
echo "✓ Validiere Installation..."
if [ -L "$COMMANDS_DIR/openai-cli" ] && [ -L "$COMMANDS_DIR/gemini-cli" ]; then
    echo "  ✓ Symlinks erfolgreich erstellt"
else
    echo "  ❌ FEHLER: Symlinks fehlen!"
    exit 1
fi

if [ ! -e "$COMMANDS_DIR/openai-cli" ] || [ ! -e "$COMMANDS_DIR/gemini-cli" ]; then
    echo "  ❌ FEHLER: Symlinks zeigen ins Leere!"
    exit 1
fi

if [ -f "$COMMANDS_DIR/openai-cli.md" ] && [ -f "$COMMANDS_DIR/gemini-cli.md" ]; then
    echo "  ✓ Dokumentationen erfolgreich erstellt"
else
    echo "  ❌ FEHLER: Dokumentationen fehlen!"
    exit 1
fi

# 5. Zeige installierte Commands
echo ""
echo "=========================================================="
echo "✅ Installation erfolgreich!"
echo ""
echo "📋 Installierte Commands:"
# grep liefert Exit 1, wenn nichts matcht - unter `set -e` würde das Skript
# hier sonst mit Fehlercode abbrechen.
ls -lh "$COMMANDS_DIR" | grep -E "openai-cli|gemini-cli" || true
echo ""
echo "🚀 Verwendung:"
echo "  1. Starte eine NEUE Claude-Session (wichtig!)"
echo "  2. Teste mit: /openai-cli {\"prompt\": \"test\"}"
echo "  3. Oder mit:   /gemini-cli {\"prompt\": \"test\"}"
echo ""
echo "📚 Dokumentation:"
echo "  - /openai-cli -> siehe $COMMANDS_DIR/openai-cli.md"
echo "  - /gemini-cli -> siehe $COMMANDS_DIR/gemini-cli.md"
echo ""
echo "🔐 Auth erforderlich:"
echo "  - OpenAI: codex login"
echo "  - Gemini: gemini --help (siehe Login-Flow)"
echo ""
echo "⚠️  WICHTIG: Commands sind nur in NEUEN Claude-Sessions verfügbar!"
echo "=========================================================="
