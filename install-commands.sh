#!/bin/bash
# Multi-Provider CLI Chat Plugin - Command Installation
# Installiert die Slash-Commands für Claude Code

set -e

echo "🔧 Multi-Provider CLI Chat Plugin - Command Installation"
echo "=========================================================="
echo ""

# 1. Erstelle Commands-Verzeichnis
echo "✓ Erstelle ~/.claude/commands/ Verzeichnis..."
mkdir -p ~/.claude/commands

# 2. Erstelle Symlinks zu Command-Scripts
echo "✓ Erstelle Symlinks zu Command-Scripts..."
ln -sf /home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/openai-cli.cjs \
       ~/.claude/commands/openai-cli

ln -sf /home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/gemini-cli.cjs \
       ~/.claude/commands/gemini-cli

# 3. Erstelle Command-Dokumentationen
echo "✓ Erstelle Command-Dokumentationen..."

cat > ~/.claude/commands/openai-cli.md << 'EOF'
# OpenAI CLI Command

Sendet Prompts an OpenAI über die Codex CLI (Account-basierte Auth, keine API-Keys).

## Usage

Der Command erwartet ein JSON-Objekt als Input:

```json
{
  "prompt": "Deine Anfrage hier",
  "model": "o3-pro",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

## Verfügbare Modelle (2025)

- `o3-pro` - Most capable reasoning model (beste Qualität)
- `o4-mini` - Fast reasoning model (Coding optimiert)
- `o3-mini` - Smaller o3 model (schneller)
- `gpt-5.1` - Latest GPT flagship
- `gpt-4.1` - Previous generation

## Beispiele

### Komplexe Software-Entwicklung
```bash
/openai-cli {
  "prompt": "Entwirf eine skalierbare Microservices-Architektur",
  "model": "o3-pro",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

### Schnelle Code-Generierung
```bash
/openai-cli {
  "prompt": "Schreibe eine Python Binary Search Funktion",
  "model": "o4-mini"
}
```

## Auth

```bash
codex login
```
EOF

cat > ~/.claude/commands/gemini-cli.md << 'EOF'
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
if [ -L ~/.claude/commands/openai-cli ] && [ -L ~/.claude/commands/gemini-cli ]; then
    echo "  ✓ Symlinks erfolgreich erstellt"
else
    echo "  ❌ FEHLER: Symlinks fehlen!"
    exit 1
fi

if [ -f ~/.claude/commands/openai-cli.md ] && [ -f ~/.claude/commands/gemini-cli.md ]; then
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
ls -lh ~/.claude/commands/ | grep -E "openai-cli|gemini-cli"
echo ""
echo "🚀 Verwendung:"
echo "  1. Starte eine NEUE Claude-Session (wichtig!)"
echo "  2. Teste mit: /openai-cli {\"prompt\": \"test\"}"
echo "  3. Oder mit:   /gemini-cli {\"prompt\": \"test\"}"
echo ""
echo "📚 Dokumentation:"
echo "  - /openai-cli -> siehe ~/.claude/commands/openai-cli.md"
echo "  - /gemini-cli -> siehe ~/.claude/commands/gemini-cli.md"
echo ""
echo "🔐 Auth erforderlich:"
echo "  - OpenAI: codex login"
echo "  - Gemini: gemini --help (siehe Login-Flow)"
echo ""
echo "⚠️  WICHTIG: Commands sind nur in NEUEN Claude-Sessions verfügbar!"
echo "=========================================================="
