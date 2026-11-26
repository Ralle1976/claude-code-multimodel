# 🤖 Multi-Provider CLI Chat Plugin für Claude Code

**Version**: 0.1.0 | **Stand**: 21.11.2025

Ermöglicht Claude Code die Verwendung von **OpenAI** (gpt-5.1-codex, gpt-5.1-codex-mini, gpt-5.1) und **Google Gemini** (Gemini 3) über deren offizielle CLIs.

---

## ✅ Status: INSTALLIERT & PERMANENT

Die Commands sind jetzt **permanent installiert** und bleiben nach Neustarts erhalten! 🎉

**Warum?**
- ✅ Symlink-basierte Installation (keine Kopien)
- ✅ Shell-Integration mit Auto-Verification
- ✅ Management-Scripts für Wartung

---

## 🚀 Quick Start

### Verwendung

```bash
# OpenAI - Beste Qualität
/openai-cli {"prompt": "Entwirf eine Microservices-Architektur", "model": "gpt-5.1-codex"}

# OpenAI - Schnelles Coding
/openai-cli {"prompt": "Schreibe Quicksort in Python", "model": "gpt-5.1-codex-mini"}

# Gemini - Höchste Intelligenz (1M Token Context)
/gemini-cli {"prompt": "Analysiere diese Codebase", "model": "gemini-3-pro-preview-11-2025"}

# Gemini - Ultra-schnell
/gemini-cli {"prompt": "Was ist Binary Search?", "model": "gemini-3.0-flash", "yolo": true}
```

### Hilfsbefehle

```bash
claude-commands-verify    # Prüft Command-Status
claude-commands-install   # Repariert Commands
claude-plugins-check      # Prüft gesamtes Setup
```

---

## 📚 Dokumentation

| Datei | Beschreibung |
|-------|--------------|
| **[QUICK_START.md](QUICK_START.md)** | 🚀 Schnelleinstieg & Beispiele |
| **[MODEL_UPDATES_2025.md](MODEL_UPDATES_2025.md)** | 📊 Alle 2025-Modelle, Benchmarks |
| **[PERSISTENCE_GUIDE.md](PERSISTENCE_GUIDE.md)** | 🔒 Warum es permanent bleibt |
| **[PLUGIN_TROUBLESHOOTING.md](PLUGIN_TROUBLESHOOTING.md)** | 🔧 Fehlerdiagnose |

---

## 🎯 Top-Modelle 2025

### OpenAI (Codex CLI)
- **gpt-5.1-codex** (Nov 2025) - Optimiert für Codex, beste Coding-Performance
- **gpt-5.1-codex-mini** (Nov 2025) - Schneller & günstiger
- **gpt-5.1** (Aug 2025) - Default, general purpose

### Google Gemini
- **gemini-3-pro-preview-11-2025** (Nov 2025) - 1501 Elo, 1M Token Context
- **gemini-3.0-flash** - Sub-Sekunden-Antworten
- **gemini-2.5-pro** - Stabil & bewährt

---

## 🛠️ Wartung

### Commands prüfen
```bash
claude-commands-verify
```

### Commands reparieren
```bash
claude-commands-install
```

### Vollständiger Check
```bash
claude-plugins-check
```

### Offline-Verifikation (Tests)
```bash
# Ein Befehl, echte Exit-Codes, kein Netzwerk:
node tests/run-all.mjs

# Einzeln:
node --test tests/js                                      # Syntax, Manifeste, Public-Guards, Injection
python -m unittest discover -s tests/py -t tests/py        # Python-Logik
```

Geprüft wird vollständig offline: Shell-/Python-/JavaScript-/TypeScript-/
PowerShell-Syntax, JSON- und Plugin-Manifeste, Secret-/PII-/Pfad-Guards,
Command-Injection-Regressionen sowie der Security-Hook (inkl. Path-Traversal).
`CLAUDE_DISABLE_LLMLINGUA=1` verhindert Modell-Downloads in den Tests.

---

## ⚠️ Falls Commands fehlen

```bash
# 1. Installation überprüfen
ls -la ~/.claude/commands/

# 2. Falls leer, neu installieren
claude-commands-install

# 3. Neue Claude-Session starten
exit && claude
```

---

## 📂 Projektstruktur

```
claude-code-multimodel/
├── PROJECT_README.md                  # Diese Datei
├── QUICK_START.md                     # Schnelleinstieg
├── MODEL_UPDATES_2025.md              # Modell-Info
├── PERSISTENCE_GUIDE.md               # Persistenz-Guide
├── PLUGIN_TROUBLESHOOTING.md          # Troubleshooting
│
├── install-commands.sh                # ⚙️ Installiert Commands
├── verify-commands.sh                 # 🔍 Prüft Commands
├── reload-plugins.sh                  # 🔄 Prüft Setup
├── setup-shell-integration.sh         # 🐚 Shell-Integration
│
└── plugins/
    └── multi-provider-cli-chat/       # Das Plugin
        ├── commands/
        │   ├── openai-cli.cjs
        │   └── gemini-cli.cjs
        └── README.md
```

---

**Happy Coding! 🚀**

*Für Details siehe die verlinkten Dokumentationen.*
