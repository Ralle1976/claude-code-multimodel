# 🚀 Quick Start - Multi-Provider CLI Chat Plugin

Schnelleinstieg für die Verwendung von OpenAI und Gemini über Claude Code.

---

## ⚡ Installation (einmalig)

```bash
# 1. Commands installieren
$HOME/claude-code-multimodel/install-commands.sh

# 2. Shell-Integration aktivieren (optional, aber empfohlen)
$HOME/claude-code-multimodel/setup-shell-integration.sh
source ~/.bashrc

# 3. Neue Claude-Session starten
exit
claude
```

---

## 💻 Verwendung

### OpenAI Commands

#### Beste Qualität (komplexe Aufgaben)
```bash
/openai-cli {
  "prompt": "Entwirf eine skalierbare Microservices-Architektur für ein E-Commerce-System",
  "model": "gpt-5.1-codex",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

#### Schnelle Code-Generierung
```bash
/openai-cli {
  "prompt": "Schreibe eine Python-Funktion für Quicksort mit Unit-Tests",
  "model": "gpt-5.1-codex-mini"
}
```

#### Allgemeine Fragen
```bash
/openai-cli {
  "prompt": "Erkläre mir den Unterschied zwischen REST und GraphQL",
  "model": "gpt-5.1"
}
```

---

### Gemini Commands

#### Höchste Intelligenz (1M Token Context)
```bash
/gemini-cli {
  "prompt": "Analysiere diese gesamte Codebase und gib mir eine detaillierte Architektur-Bewertung",
  "model": "gemini-3-pro-preview-11-2025",
  "approval_mode": "yolo"
}
```

#### Mit sichtbarem Reasoning
```bash
/gemini-cli {
  "prompt": "Löse dieses komplexe Dynamic Programming Problem und zeige mir deinen Denkprozess Schritt für Schritt",
  "model": "gemini-3-pro-preview-11-2025-thinking"
}
```

#### Ultra-schnelle Antworten
```bash
/gemini-cli {
  "prompt": "Quick: Was ist der Big-O von Binary Search?",
  "model": "gemini-3.0-flash",
  "yolo": true
}
```

---

## 🎯 Modell-Empfehlungen

### Für Coding

| Anforderung | OpenAI | Gemini |
|-------------|--------|--------|
| **Beste Qualität** | `gpt-5.1-codex` | `gemini-3-pro-preview-11-2025` |
| **Beste Speed** | `gpt-5.1-codex-mini` | `gemini-3.0-flash` |
| **Große Codebases** | - | `gemini-3-pro-preview-11-2025` (1M context) |
| **Debugging** | `gpt-5.1-codex-mini` | `gemini-3-pro-preview-11-2025-thinking` |

### Für Allgemein

| Anforderung | OpenAI | Gemini |
|-------------|--------|--------|
| **Balanced** | `gpt-5.1` | `gemini-2.5-pro` |
| **Höchste Intelligenz** | `gpt-5.1-codex` | `gemini-3-pro-preview-11-2025` |
| **Schnellste Antworten** | `gpt-5.1-codex-mini` | `gemini-3.0-flash` |

---

## 🔐 Authentifizierung

### OpenAI (einmalig)
```bash
codex login
```

### Gemini (einmalig)
```bash
# Folge dem Login-Flow der Gemini CLI
gemini --help
```

---

## 🛠️ Hilfsbefehle (Shell-Aliase)

Nach Installation der Shell-Integration:

```bash
# Commands prüfen
claude-commands-verify

# Commands neu installieren
claude-commands-install

# Gesamtes Plugin-Setup prüfen
claude-plugins-check
```

---

## ❓ Häufige Fragen

### Commands nicht verfügbar?
```bash
# 1. Prüfen
ls -la ~/.claude/commands/

# 2. Falls leer
claude-commands-install

# 3. Neue Claude-Session starten
exit && claude
```

### "Error: not logged in"?
```bash
# OpenAI
codex login

# Gemini
gemini  # Folge Login-Anweisungen
```

### "Rate limit reached"?
Nutze den anderen Provider:
- OpenAI limit → Nutze Gemini
- Gemini limit → Nutze OpenAI

---

## 📚 Weitere Dokumentation

- **Vollständige Modell-Info**: `MODEL_UPDATES_2025.md`
- **Persistenz-Guide**: `PERSISTENCE_GUIDE.md`
- **Troubleshooting**: `PLUGIN_TROUBLESHOOTING.md`
- **Plugin README**: `plugins/multi-provider-cli-chat/README.md`

---

## 🎉 Beispiel-Session

```bash
# Starte Claude
claude

# Frage Claude etwas
"Kannst du mir helfen, eine REST API zu designen?"

# Cross-Check mit OpenAI
/openai-cli {
  "prompt": "Designvorschläge für eine REST API mit User-Management",
  "model": "gpt-5.1-codex"
}

# Cross-Check mit Gemini
/gemini-cli {
  "prompt": "Was sind die Best Practices für REST API Design?",
  "model": "gemini-3-pro-preview-11-2025"
}

# Vergleiche alle drei Antworten
```

---

*Viel Erfolg! 🚀*
