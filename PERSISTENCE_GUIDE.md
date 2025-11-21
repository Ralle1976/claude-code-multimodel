# 🔒 Persistenz-Guide - Multi-Provider CLI Chat Plugin

**Problem**: Commands verschwinden nach Neustart/Session-Wechsel
**Lösung**: Symlink-basierte Installation mit Auto-Verification

---

## ✅ Warum es JETZT permanent bleibt

### 1. **Symlinks statt Kopien**

Wir verwenden **symbolische Links**, nicht kopierte Dateien:

```bash
~/.claude/commands/openai-cli -> /home/ralle/.../openai-cli.cjs
~/.claude/commands/gemini-cli -> /home/ralle/.../gemini-cli.cjs
```

**Vorteile**:
- ✅ Zeigt immer auf die Original-Dateien
- ✅ Updates im Plugin-Verzeichnis werden automatisch übernommen
- ✅ Bleibt bestehen, solange das Plugin-Verzeichnis existiert
- ✅ Keine Sync-Probleme zwischen Kopien

### 2. **Shell-Integration mit Auto-Verification**

Die Shell-Integration (`.bashrc`) prüft bei **jedem Shell-Start**, ob die Commands noch da sind:

```bash
# Bei Shell-Start automatisch:
if [ ! -L "$HOME/.claude/commands/openai-cli" ]; then
    echo "⚠️  Commands fehlen! Führe aus: claude-commands-install"
fi
```

**Vorteile**:
- ✅ Warnt dich sofort, wenn Commands fehlen
- ✅ Keine bösen Überraschungen
- ✅ Erinnert dich an die Reparatur

### 3. **Drei Management-Scripts**

#### install-commands.sh
- **Zweck**: Erstellt/repariert alle Commands
- **Wann**: Erste Installation oder nach Problemen
- **Führt aus**:
  - Erstellt `~/.claude/commands/` Verzeichnis
  - Erstellt Symlinks
  - Generiert Dokumentationen
  - Validiert Installation

#### verify-commands.sh
- **Zweck**: Prüft ob Commands noch korrekt sind
- **Wann**: Bei Verdacht auf Probleme oder regelmäßig
- **Prüft**:
  - Symlinks vorhanden?
  - Symlinks nicht broken?
  - Dokumentationen vorhanden?
  - Bietet automatische Reparatur an

#### reload-plugins.sh
- **Zweck**: Prüft gesamtes Plugin-Setup (CLIs, Settings, etc.)
- **Wann**: Nach Neustart oder bei generellen Problemen

---

## 🛡️ Szenarien & Lösungen

### Szenario 1: Neustart / Neue WSL-Session

**Was passiert**:
- Symlinks bleiben bestehen ✅
- Shell-Integration lädt automatisch ✅
- Commands sind sofort verfügbar ✅

**Keine Aktion nötig!**

### Szenario 2: `~/.claude/commands/` wurde gelöscht

**Was passiert**:
- Shell-Start zeigt: `⚠️ Commands fehlen!`
- Commands sind nicht verfügbar ❌

**Lösung**:
```bash
claude-commands-install
# Oder direkt:
/home/ralle/claude-code-multimodel/install-commands.sh
```

### Szenario 3: Plugin-Verzeichnis wurde verschoben

**Was passiert**:
- Symlinks sind broken (zeigen ins Leere)
- Shell-Start zeigt Warnung
- Commands funktionieren nicht ❌

**Lösung**:
1. Plugin-Verzeichnis zurück verschieben, ODER
2. Symlinks aktualisieren:
```bash
rm ~/.claude/commands/openai-cli ~/.claude/commands/gemini-cli
# Install-Script passt Pfade automatisch an
claude-commands-install
```

### Szenario 4: Neue Claude-Version installiert

**Was passiert**:
- `~/.claude/` Verzeichnis könnte zurückgesetzt werden
- Commands könnten fehlen

**Lösung**:
```bash
claude-commands-verify  # Prüft Status
claude-commands-install # Falls nötig
```

### Szenario 5: Backup/Restore von System

**Was passiert**:
- Falls `~/.claude/commands/` im Backup enthalten: Funktioniert ✅
- Falls nicht: Commands fehlen

**Lösung**:
```bash
claude-commands-install
```

---

## 📋 Checkliste: Ist alles persistent?

Führe diese Checks aus, um sicherzustellen, dass alles permanent eingerichtet ist:

### ✅ Check 1: Symlinks vorhanden?
```bash
ls -la ~/.claude/commands/ | grep -E "openai-cli|gemini-cli"
```

**Erwartet**:
```
lrwxrwxrwx ... openai-cli -> /home/ralle/.../openai-cli.cjs
lrwxrwxrwx ... gemini-cli -> /home/ralle/.../gemini-cli.cjs
-rw------- ... openai-cli.md
-rw------- ... gemini-cli.md
```

### ✅ Check 2: Shell-Integration aktiv?
```bash
grep "Claude Multi-Provider Plugin Integration" ~/.bashrc
```

**Erwartet**: Zeigt die Integration-Zeile

### ✅ Check 3: Aliase verfügbar?
```bash
alias | grep claude
```

**Erwartet**:
```
alias claude-commands-install='...'
alias claude-commands-verify='...'
alias claude-plugins-check='...'
```

### ✅ Check 4: Commands in neuer Session verfügbar?
```bash
# Öffne neues Terminal
claude
# Dann:
/help
```

**Erwartet**: `/openai-cli` und `/gemini-cli` in der Liste

---

## 🔧 Manuelle Reparatur (falls Scripts nicht funktionieren)

### Schritt 1: Verzeichnis erstellen
```bash
mkdir -p ~/.claude/commands
```

### Schritt 2: Symlinks erstellen
```bash
ln -sf /home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/openai-cli.cjs \
       ~/.claude/commands/openai-cli

ln -sf /home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/gemini-cli.cjs \
       ~/.claude/commands/gemini-cli
```

### Schritt 3: Dokumentationen erstellen
```bash
cat > ~/.claude/commands/openai-cli.md << 'EOF'
# OpenAI CLI Command
Sendet Prompts an OpenAI über die Codex CLI.

## Usage
/openai-cli {"prompt": "Deine Anfrage", "model": "gpt-5.1-codex"}

## Modelle
- gpt-5.1-codex, gpt-5.1-codex-mini, gpt-5.1
EOF

cat > ~/.claude/commands/gemini-cli.md << 'EOF'
# Gemini CLI Command
Sendet Prompts an Google Gemini CLI.

## Usage
/gemini-cli {"prompt": "Deine Anfrage", "model": "gemini-3-pro-preview-11-2025"}

## Modelle
- gemini-3-pro-preview-11-2025, gemini-3.0-flash, gemini-2.5-pro
EOF
```

### Schritt 4: Validieren
```bash
ls -la ~/.claude/commands/
```

### Schritt 5: Neue Claude-Session starten
```bash
exit
claude
```

---

## 🚨 Troubleshooting

### Problem: "Command not found: /openai-cli"

**Diagnose**:
```bash
ls -la ~/.claude/commands/openai-cli
```

**Mögliche Ursachen**:
1. Symlink fehlt → `claude-commands-install`
2. Symlink broken → Plugin-Verzeichnis prüfen
3. Alte Claude-Session → Neue Session starten

### Problem: "Permission denied"

**Diagnose**:
```bash
ls -l ~/.claude/commands/openai-cli
file ~/.claude/commands/openai-cli
```

**Lösung**:
```bash
chmod +x /home/ralle/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/*.cjs
```

### Problem: Commands zeigen kein Output

**Diagnose**:
```bash
# Test direkt
echo '{"prompt":"test"}' | ~/.claude/commands/openai-cli
```

**Mögliche Ursachen**:
1. CLI nicht eingeloggt → `codex login` / Gemini-Login
2. CLI nicht installiert → `which codex gemini`
3. Script-Fehler → Siehe stderr

### Problem: Shell-Integration funktioniert nicht

**Diagnose**:
```bash
grep "Claude Multi-Provider" ~/.bashrc
```

**Lösung**:
```bash
# Erneut ausführen
/home/ralle/claude-code-multimodel/setup-shell-integration.sh
source ~/.bashrc
```

---

## 📚 Weitere Schritte für absolute Persistenz

### 1. Zu Backup-Strategie hinzufügen

Füge diese Dateien/Verzeichnisse zu deinem Backup hinzu:

```
~/.claude/commands/          # Die Command-Links
~/.claude/settings.json      # Claude-Konfiguration
~/.bashrc                    # Shell-Integration
/home/ralle/claude-code-multimodel/plugins/  # Plugin-Verzeichnis
```

### 2. Systemd-Service für Auto-Verification (Optional)

Für absolute Sicherheit könnte man einen systemd-Service erstellen, der bei jedem Boot prüft:

```bash
# /etc/systemd/system/claude-commands-verify.service
[Unit]
Description=Verify Claude Commands
After=multi-user.target

[Service]
Type=oneshot
User=ralle
ExecStart=/home/ralle/claude-code-multimodel/verify-commands.sh

[Install]
WantedBy=multi-user.target
```

### 3. Cron-Job für regelmäßige Verification (Optional)

```bash
# Täglich um 08:00 Uhr prüfen
0 8 * * * /home/ralle/claude-code-multimodel/verify-commands.sh
```

---

## ✅ Erfolgskriterien für Persistenz

Die Installation ist **wirklich persistent**, wenn:

- ✅ Symlinks zeigen auf existierende Dateien
- ✅ Shell-Integration in `.bashrc` vorhanden
- ✅ Aliase funktionieren in neuen Shells
- ✅ Commands erscheinen in **jeder neuen** Claude-Session
- ✅ Nach System-Neustart immer noch verfügbar
- ✅ Warnung bei Shell-Start, falls Commands fehlen

---

## 🎯 Quick Reference

```bash
# Installation/Reparatur
claude-commands-install

# Verification
claude-commands-verify

# Full Plugin Check
claude-plugins-check

# Manuelle Links prüfen
ls -la ~/.claude/commands/

# Neue Claude-Session starten
exit && claude
```

---

*Erstellt: 21.11.2025*
*Letzte Aktualisierung: 21.11.2025*
*Plugin-Version: 0.1.0*
