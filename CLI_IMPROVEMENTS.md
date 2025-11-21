# 🚀 CLI Session & Context Management - Verbesserungsvorschläge

**Erstellt**: 21. November 2025
**Status**: Design-Phase

## 🎯 Zentrale Frage: Context-Sharing-Strategie

### Problem
Wenn Claude Aufgaben an Codex/Gemini delegiert:
- Sollten sie die CLAUDE.md Anweisungen sehen?
- Wie viel Projekt-Context ist nötig?
- Wie vermeiden wir Token-Verschwendung?

---

## 📋 Option-Analyse

### Option A: Voller Context (CLAUDE.md komplett)
```javascript
// Bei jedem Aufruf
const fullPrompt = `
${CLAUDE_MD_CONTENT}

Task: ${userTask}
`;
```

**Pros**:
- ✅ Maximale Konsistenz
- ✅ Alle AIs verstehen Projekt-Regeln
- ✅ Einheitlicher Code-Stil

**Cons**:
- ❌ Hoher Token-Verbrauch (~5000+ Tokens/Request)
- ❌ Claude-spezifische Regeln verwirren andere AIs
- ❌ Unnötige Informationen (z.B. "no Claude signatures")

**Bewertung**: ⚠️ Zu aufwendig, nicht optimal

---

### Option B: Provider-spezifische Instruction Files

```
.claude/
├── CLAUDE.md        # Claude-spezifisch
├── CODEX.md         # Codex-spezifisch
├── GEMINI.md        # Gemini-spezifisch
└── SHARED.md        # Gemeinsame Regeln
```

**CODEX.md Beispiel**:
```markdown
# Codex Instructions

## Project: Multi-Provider CLI Chat Plugin

### Code Style
- Use Node.js best practices
- Prefer async/await over callbacks
- Add JSDoc comments for complex functions

### Security Rules
- Never expose API keys
- Validate all inputs
- Use proper error handling

### Task Context
This is a CLI plugin that routes between Claude, Codex, and Gemini.
When implementing features, ensure cross-compatibility.
```

**Pros**:
- ✅ Optimiert für jeden Provider
- ✅ Keine verwirrenden Provider-spezifischen Regeln
- ✅ Moderater Token-Verbrauch

**Cons**:
- ❌ Maintenance-Overhead (3 Dateien pflegen)
- ❌ Risiko von Inkonsistenzen
- ❌ Duplikation von Shared Rules

**Bewertung**: ⭐⭐⭐ Gut, aber Overhead

---

### Option C: Minimal Context (Task-only)

```javascript
// Nur die spezifische Aufgabe
/openai-cli {
  "prompt": "Review this code for bugs: [code]"
}
```

**Pros**:
- ✅ Minimaler Token-Verbrauch
- ✅ Fokussierte Prompts
- ✅ Schnelle Antworten

**Cons**:
- ❌ Inkonsistente Ergebnisse
- ❌ Keine Projekt-Context-Awareness
- ❌ Unterschiedliche Code-Stile

**Bewertung**: ⚠️ Zu minimal für Quality-Sicherung

---

### Option D: Hybrid - Core Rules + Task Context ⭐ **EMPFOHLEN**

```markdown
# CORE_RULES.md (klein, ~500 tokens)

## Essential Project Rules

### Security
- Never expose credentials
- Validate all inputs
- Use proper error handling

### Code Style
- Modern JavaScript (ES6+)
- Async/await pattern
- Clear error messages

### Output Format
- Structured JSON responses
- Include error_type field
- Add retryable flag

### Context
This is a multi-provider CLI plugin for Claude Code.
When implementing features, ensure compatibility with all providers.
```

**Verwendung**:
```javascript
// Auto-inject bei wichtigen Tasks
const prompt = `
${CORE_RULES}

Specific Task: ${userTask}

Additional Context: ${relevantCode}
`;
```

**Pros**:
- ✅ Balance zwischen Konsistenz & Effizienz
- ✅ Core Rules (~500 tokens) statt Full CLAUDE.md (~5000)
- ✅ Flexibel erweiterbar mit Task-Context
- ✅ Eine zentrale Datei für Shared Rules

**Cons**:
- ⚠️ Muss definieren was "Core" ist
- ⚠️ Manuelle Pflege bei Rule-Updates

**Bewertung**: ⭐⭐⭐⭐⭐ OPTIMAL

---

## 🔧 Implementierungsstrategie

### Phase 1: CORE_RULES.md erstellen

```markdown
# Multi-Provider CLI Plugin - Core Rules

## Security (CRITICAL)
1. Never expose API keys or credentials
2. Validate all user inputs
3. Use proper error handling with structured responses

## Error Handling Pattern
```javascript
{
  provider: "codex" | "gemini",
  success: false,
  error_type: "auth" | "limit" | "missing" | "error" | "circuit_breaker",
  retryable: false,  // CRITICAL: Prevent retry loops
  message: "Clear user-facing message"
}
```

## Code Style
- Node.js with async/await
- No callbacks (use Promises)
- JSDoc for complex functions
- Clear variable names

## Context
Multi-provider CLI plugin routing tasks between Claude, OpenAI Codex, and Google Gemini.
Goal: Consistent behavior, robust error handling, no retry loops.
```

### Phase 2: Smart Context Injection

```javascript
// commands/context-injector.js
const fs = require('fs');
const path = require('path');

const CORE_RULES = fs.readFileSync(
  path.join(__dirname, '../CORE_RULES.md'),
  'utf8'
);

function buildPrompt(task, options = {}) {
  const parts = [];

  // Always include core rules for code tasks
  if (options.includeRules !== false) {
    parts.push(CORE_RULES);
    parts.push('\n---\n');
  }

  // Add task-specific context if provided
  if (options.context) {
    parts.push(`Context:\n${options.context}\n\n`);
  }

  // Add the actual task
  parts.push(`Task:\n${task}`);

  return parts.join('');
}

module.exports = { buildPrompt };
```

### Phase 3: Automatic vs Manual

**Automatic Injection** (für Code-Tasks):
```javascript
// Bei /openai-cli oder /gemini-cli
if (taskType === 'code_review' || taskType === 'implementation') {
  prompt = buildPrompt(userPrompt, { includeRules: true });
}
```

**Manual Injection** (für spezielle Fälle):
```javascript
// Claude kann explizit entscheiden
/openai-cli {
  "prompt": "[CORE_RULES]\n\nReview this code...",
  "model": "gpt-5.1-codex"
}
```

---

## 🎨 CLI-Session-Verbesserungen

### 1. Context-Aware Commands

**Aktuell**:
```bash
/openai-cli {"prompt": "Long prompt here..."}
```

**Verbessert**:
```bash
# Kurze Syntax mit auto-context
/openai-cli --with-context "Review current file"

# Oder explizit
/openai-cli --core-rules "Implement circuit breaker"
```

### 2. Session-State-Management

```javascript
// .claude/session-state.json
{
  "last_provider": "codex",
  "circuit_breaker_states": {
    "codex": { "failures": [], "last_success": 1700000000 },
    "gemini": { "failures": [], "last_success": 1700000000 }
  },
  "recent_tasks": [
    { "provider": "codex", "task": "code review", "success": true },
    { "provider": "gemini", "task": "documentation", "success": true }
  ]
}
```

### 3. Intelligente Provider-Auswahl

```javascript
// Auto-Routing basierend auf Task-Typ
function selectProvider(task) {
  if (task.includes('code') || task.includes('implement')) {
    return 'codex';  // Codex besser für Coding
  }
  if (task.includes('analyze') || task.includes('explain')) {
    return 'gemini';  // Gemini besser für Reasoning
  }
  return 'claude';  // Default
}
```

### 4. Verbose-Mode für Debugging

```bash
# Zeigt was tatsächlich gesendet wird
export DEBUG_CLAUDE_PLUGIN=true

/openai-cli {"prompt": "test"}
# Output:
# [DEBUG] Injecting CORE_RULES (523 tokens)
# [DEBUG] Final prompt: 1456 tokens
# [DEBUG] Checking circuit breaker: OK
# [DEBUG] Sending to codex...
```

---

## 📊 Token-Vergleich

| Ansatz | Tokens/Request | Konsistenz | Wartung |
|--------|----------------|------------|---------|
| **Full CLAUDE.md** | ~5000 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Provider-spezifisch** | ~2000 | ⭐⭐⭐⭐ | ⭐⭐ |
| **Minimal** | ~100 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Hybrid (CORE_RULES)** | ~500 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Kosteneinsparung mit Hybrid**:
- Full CLAUDE.md: 5000 tokens × $0.01/1K = $0.05/request
- Hybrid CORE_RULES: 500 tokens × $0.01/1K = $0.005/request
- **90% Einsparung** bei fast gleicher Konsistenz!

---

## 🚀 Nächste Schritte

1. **Warte auf Gemini's strategische Analyse** zur Context-Sharing-Strategie
2. **Warte auf Codex's Circuit-Breaker-Implementation** für gemini-cli
3. **Erstelle CORE_RULES.md** basierend auf Feedback
4. **Implementiere Context-Injector** in beiden CLI-Scripts
5. **Teste mit verschiedenen Task-Typen**
6. **Dokumentiere Best Practices** für Manual vs. Auto-Injection

---

## 💡 Offene Fragen für Gemini & Codex

1. **Für Gemini**: Welche Approach-Empfehlung basierend auf AI-System-Design?
2. **Für Codex**: Technische Umsetzbarkeit des Context-Injectors?
3. **Beide**: Wie handhaben andere Multi-AI-Systeme dieses Problem?

---

*Warten auf AI-Feedback vor finaler Implementation...*
