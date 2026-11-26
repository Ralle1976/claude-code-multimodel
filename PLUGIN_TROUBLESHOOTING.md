# Multi-Provider CLI Chat Plugin - Troubleshooting Guide

## 🔍 Symptom: Plugin "verschwindet" nach Neustart/Sitzungswechsel

### Ursachenanalyse

#### 1. Lokaler Plugin-Pfad nicht persistent eingetragen

**Problem**: Claude Code sucht Plugins über `~/.claude/settings.json` oder projektbezogene `.claude/settings.json`.

**Diagnose**:
```bash
cat ~/.claude/settings.json | grep -A 5 "plugins"
```

**Erwartete Ausgabe**:
```json
"plugins": {
  "local": [
    {
      "path": "$HOME/claude-code-multimodel/plugins/multi-provider-cli-chat",
      "enabled": true
    }
  ]
}
```

**Lösung**: Falls fehlt oder Pfad falsch, Settings korrigieren:
```bash
# Backup erstellen
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Dann manuell editieren oder mit jq:
jq '.plugins.local += [{"path": "$HOME/claude-code-multimodel/plugins/multi-provider-cli-chat", "enabled": true}]' \
  ~/.claude/settings.json > ~/.claude/settings.json.tmp && \
  mv ~/.claude/settings.json.tmp ~/.claude/settings.json
```

---

#### 2. CLIs fehlen im neuen Shell-Environment (PATH/Installation)

**Problem**: Neue Sessions oder frische Container haben oft kein global installiertes CLI oder ein anderes PATH-Setup.

**Diagnose**:
```bash
which codex
which gemini
echo $PATH
```

**Lösung bei fehlenden CLIs**:
```bash
# OpenAI Codex CLI
npm install -g @openai/codex

# Gemini CLI (Installation je nach System)
# Siehe: https://github.com/google/generative-ai-cli
```

**Lösung bei PATH-Problemen**:
```bash
# Prüfe wo node-global-packages installiert sind
npm config get prefix

# Füge zu ~/.bashrc hinzu:
export PATH="$PATH:$(npm config get prefix)/bin"
export PATH="$PATH:$HOME/.nvm/versions/node/$(node --version)/bin"

# Reload
source ~/.bashrc
```

---

#### 3. Abgelaufene oder fehlende CLI-Sessions

**Problem**: Die Authentifizierung läuft vollständig über die jeweiligen CLIs; bei abgelaufenen Logins melden die Commands `error_type: "auth"`.

**Diagnose**:
```bash
# Test OpenAI Codex Login
codex exec "test" --skip-git-repo-check

# Test Gemini Login
gemini "test"
```

**Erwartete Fehler bei fehlender Auth**:
- Codex: `"Please run codex login"`
- Gemini: `"Not logged in"` oder ähnliche Auth-Meldung

**Lösung**:
```bash
# Codex Login (öffnet Browser)
codex login

# Gemini Login (folge CLI-Anweisungen)
gemini --help  # Zeigt Login-Flow
```

---

#### 4. Rate-Limits oder Kontingent erschöpft

**Problem**: Bei Limit-Fehlern liefern die Commands `error_type: "limit"`.

**Diagnose**:
```bash
# Test mit direktem CLI-Aufruf
codex exec "Hello" 2>&1 | grep -i "rate\|limit\|quota"
gemini "Hello" 2>&1 | grep -i "rate\|limit\|quota"
```

**Lösung**:
- OpenAI: Warte oder upgrade Kontingent auf platform.openai.com
- Gemini: Prüfe Quota auf Google AI Studio
- Temporär anderen Provider nutzen (Claude direkt)

---

## 🛠️ Automatisierte Checks

### Check-Script ausführen

```bash
$HOME/claude-code-multimodel/reload-plugins.sh
```

Dieses Script prüft:
- ✓ Claude-Config existiert
- ✓ Plugin-Pfad korrekt
- ✓ CLI-Binaries im PATH
- ✓ Settings JSON valide
- ✓ Plugin registriert
- ✓ Commands ausführbar

### Shell-Integration installieren

```bash
$HOME/claude-code-multimodel/setup-shell-integration.sh
source ~/.bashrc
```

Danach zeigt jede neue Shell:
```
✓ Claude Multi-Provider CLI Plugin verfügbar
  Commands: /openai-cli, /gemini-cli
  CLIs: codex ✓ | gemini ✓
```

---

## 📋 Schritt-für-Schritt Fehlerbehebung

### Szenario 1: Neue WSL-Session / VM-Neustart

1. **Prüfe Settings**:
   ```bash
   cat ~/.claude/settings.json | python3 -m json.tool
   ```

2. **Prüfe CLIs**:
   ```bash
   which codex gemini
   codex --version
   gemini --version
   ```

3. **Falls CLIs fehlen**:
   ```bash
   # PATH erweitern in ~/.bashrc
   export PATH="$PATH:$HOME/.nvm/versions/node/v22.16.0/bin"
   source ~/.bashrc
   ```

4. **Teste Authentifizierung**:
   ```bash
   codex exec "test" --skip-git-repo-check
   gemini "test"
   ```

5. **Falls Auth-Fehler**:
   ```bash
   codex login
   # Gemini: folge CLI-Login-Flow
   ```

6. **Starte neue Claude-Session**:
   ```bash
   claude  # Plugins werden beim Start geladen
   ```

### Szenario 2: Plugin erscheint nicht in /help

**Problem**: Commands werden nicht als verfügbar angezeigt.

**Ursache**: Plugins werden nur beim Start der Claude-Session geladen.

**Lösung**:
1. Claude-Session komplett beenden (nicht nur Tab)
2. Neue Session starten
3. Prüfe mit `/help` oder direkt testen:
   ```
   /openai-cli {"prompt": "test"}
   ```

### Szenario 3: "Plugin reagiert nicht" / Keine Antwort

**Diagnose**:
```bash
# Teste Command direkt
echo '{"prompt":"test"}' | \
  node $HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/openai-cli.cjs
```

**Mögliche Ausgaben**:

1. **Auth-Fehler**:
   ```json
   {
     "provider": "codex",
     "success": false,
     "error_type": "auth",
     "message": "Please run codex login"
   }
   ```
   → Lösung: `codex login`

2. **Missing CLI**:
   ```json
   {
     "error_type": "missing",
     "message": "The `codex` CLI is not available on PATH"
   }
   ```
   → Lösung: PATH erweitern oder CLI installieren

3. **Rate Limit**:
   ```json
   {
     "error_type": "limit",
     "message": "Quota appears to be reached"
   }
   ```
   → Lösung: Warten oder anderen Provider nutzen

---

## 🔐 Wichtige Hinweise zur Sicherheit

- **Keine API-Keys im Plugin**: Das Plugin speichert KEINE Credentials
- **Account-basierte Auth**: Verwendet bestehende CLI-Logins
- **Session-Management**: CLIs verwalten Sessions eigenständig
- **Keine Rate-Limit-Umgehung**: Plugin respektiert Provider-Limits

---

## 📚 Verwendungsbeispiele (wenn alles funktioniert)

### OpenAI/Codex (gpt-5.1-codex-mini)
```
/openai-cli {
  "prompt": "Erkläre Quicksort in Python",
  "model": "gpt-5.1-codex-mini",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

### Gemini (2.5-pro)
```
/gemini-cli {
  "prompt": "Was ist Merge Sort?",
  "model": "gemini-2.5-pro",
  "approval_mode": "yolo"
}
```

### Cross-Check zwischen Providern
```
# Frage Claude (default)
"Erkläre Binary Search"

# Vergleiche mit OpenAI
/openai-cli {"prompt": "Erkläre Binary Search", "model": "gpt-5.1-codex-mini"}

# Vergleiche mit Gemini
/gemini-cli {"prompt": "Erkläre Binary Search", "model": "gemini-2.5-pro"}
```

---

## 🆘 Wenn nichts hilft

### Debug-Log erstellen

```bash
# Sammle alle relevanten Informationen
cat > /tmp/plugin-debug.log << EOF
=== Claude Settings ===
$(cat ~/.claude/settings.json)

=== Plugin-Struktur ===
$(ls -laR $HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/)

=== CLI-Versionen ===
codex: $(codex --version 2>&1)
gemini: $(gemini --version 2>&1)

=== PATH ===
$PATH

=== Test OpenAI CLI ===
$(echo '{"prompt":"test"}' | node $HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/openai-cli.cjs 2>&1)

=== Test Gemini CLI ===
$(echo '{"prompt":"test"}' | node $HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/commands/gemini-cli.cjs 2>&1)
EOF

cat /tmp/plugin-debug.log
```

### Plugin-Repository kontaktieren

Falls alle Lösungen fehlschlagen, öffne ein Issue mit dem Debug-Log:
- Repository: `$HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/.git`
- Include: Debug-Log, Fehlermeldungen, Schritte zur Reproduktion

---

## ✅ Erfolgskriterien

Das Plugin funktioniert korrekt, wenn:

- ✓ `reload-plugins.sh` ohne Fehler durchläuft
- ✓ Beide CLIs (`codex`, `gemini`) im PATH verfügbar sind
- ✓ Auth funktioniert (keine `error_type: "auth"`)
- ✓ Direkte Command-Tests liefern JSON-Responses
- ✓ Commands in neuer Claude-Session verwendbar sind

---

*Erstellt: 2025-11-21*
*Plugin-Version: 0.1.0*
*Für Fragen siehe: `$HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/README.md`*
