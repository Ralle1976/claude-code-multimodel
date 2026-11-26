# 🚀 Model Updates 2025 - Multi-Provider CLI Chat Plugin

**Letzte Aktualisierung**: 21. November 2025

> ⚠️ **WICHTIG - Tatsächlich verfügbare Modelle im Codex CLI**:
>
> Die in diesem Dokument recherchierten Modelle (o3-pro, o4-mini, etc.) sind **NICHT** direkt im Codex CLI verfügbar.
>
> **Tatsächlich verfügbare Modelle** (Stand November 2025):
> - `gpt-5.1-codex` - Optimized for codex (EMPFOHLEN für Coding)
> - `gpt-5.1-codex-mini` - Optimized for codex, cheaper & faster
> - `gpt-5.1` - (default) Broad world knowledge, general reasoning
>
> Die folgenden Abschnitte dienen als Hintergrundinformation zu OpenAI's Modell-Entwicklung.

## 📊 OpenAI Modell-Entwicklung 2025 (Hintergrundinformation)

### 🔵 OpenAI Models

#### o3-pro (Released: Juni 2025)
- **Modell-Name**: `o3-pro`
- **Typ**: Reasoning Model
- **Hauptmerkmale**:
  - Most capable reasoning model von OpenAI
  - Denkt länger und liefert zuverlässigste Antworten
  - 20% weniger schwere Fehler als o1
  - **Spezialisierung**: Programming, Business/Consulting, Creative Ideation
- **Benchmark-Highlights**:
  - SWE-bench Verified: 71.7% (vs. 48.9% bei o1)
  - Codeforces Elo: 2727 (vs. 1891 bei o1)
- **Empfohlen für**:
  - ✅ Komplexe Coding-Aufgaben
  - ✅ Software Engineering (höchste SWE-bench-Score)
  - ✅ Kritische Aufgaben, bei denen Zuverlässigkeit wichtiger als Speed ist
- **Hinweis**: Längere Response-Time (Background-Mode empfohlen)

#### o4-mini (Released: April 2025)
- **Modell-Name**: `o4-mini`
- **Typ**: Fast Reasoning Model
- **Hauptmerkmale**:
  - Erstes o4-Modell
  - Verbesserte Performance gegenüber o3-mini in allen Key-Benchmarks
  - Optimiert für Math, Coding, Visual Tasks
  - **Beste Kosten-Performance für technische Tasks**
- **Empfohlen für**:
  - ✅ Schnelle Coding-Aufgaben
  - ✅ Math/Science-Probleme
  - ✅ Wenn Speed wichtig ist
  - ✅ Budget-bewusste Projekte

#### gpt-5.1 (Released: August 2025)
- **Modell-Name**: `gpt-5.1`
- **Typ**: Flagship GPT Model
- **Hauptmerkmale**:
  - Neuestes GPT-Generation-Modell
  - Default für alle logged-in/out User
  - Verbesserte Coding-Personality & Code-Qualität
  - Entwickelt in Zusammenarbeit mit: Cursor, Cognition, Augment Code, Factory, Warp
- **Empfohlen für**:
  - ✅ Allgemeine Aufgaben
  - ✅ Conversational AI
  - ✅ Code-Generierung mit gutem Stil
  - ✅ Balanced Performance

---

### 🟢 Google Gemini Models

#### gemini-3-pro-preview-11-2025 (Released: November 2025)
- **Modell-Name**: `gemini-3-pro-preview-11-2025`
- **Typ**: Most Intelligent Gemini Model
- **Hauptmerkmale**:
  - **Erste KI mit >1500 Elo auf LMArena** (1501 Elo)
  - 1 Million Token Input Context
  - 64k Token Output
  - Knowledge Cutoff: Januar 2025
  - State-of-the-art Reasoning + Multimodal Understanding + Agentic Capabilities
- **Benchmark-Highlights**:
  - Erster 1500+ Elo Score in der AI-Geschichte
  - Record-breaking Benchmark-Scores
- **Empfohlen für**:
  - ✅ Höchste Intelligenz-Anforderungen
  - ✅ Sehr große Contexts (bis 1M Token)
  - ✅ Multimodale Aufgaben
  - ✅ Agentic Workflows
  - ✅ Complex Reasoning

#### gemini-3-pro-preview-11-2025-thinking (Released: November 2025)
- **Modell-Name**: `gemini-3-pro-preview-11-2025-thinking`
- **Typ**: Gemini 3 mit Reasoning-Visualisierung
- **Hauptmerkmale**:
  - Gleiche Capabilities wie Gemini 3 Pro
  - **Zeigt Denkprozess sichtbar an**
  - "Generative Interfaces" - Model wählt beste Output-Form
- **Empfohlen für**:
  - ✅ Debugging komplexer Logik
  - ✅ Verständnis des AI-Reasoning
  - ✅ Educational Use Cases
  - ✅ Transparenz-Anforderungen

#### gemini-3.0-flash (Released: November 2025)
- **Modell-Name**: `gemini-3.0-flash`
- **Typ**: Fast Gemini 3 Variant
- **Hauptmerkmale**:
  - Distilled, latency-focused Version
  - **Sub-Sekunden Response-Times**
  - Hohe Capability bei extremer Geschwindigkeit
- **Empfohlen für**:
  - ✅ Latenz-kritische Anwendungen
  - ✅ Real-time Interactions
  - ✅ High-throughput Scenarios
  - ✅ Schnelle Prototyping-Iterationen

---

## 📈 Modell-Vergleich & Use-Case-Matrix

### Coding-Aufgaben

| Use Case | Beste Wahl | Alternative | Begründung |
|----------|-----------|-------------|------------|
| **Komplexe Software Engineering** | `o3-pro` | `gemini-3-pro-preview` | Höchste SWE-bench-Score (71.7%) |
| **Schnelle Code-Generierung** | `o4-mini` | `gemini-3.0-flash` | Optimiert für Speed + Quality |
| **Code-Review & Refactoring** | `gemini-3-pro-preview` | `o3-pro` | 1M Token Context für große Codebases |
| **Bug-Fixing** | `o4-mini` | `gpt-5.1` | Schnelle Iteration wichtig |
| **Architecture Design** | `o3-pro` | `gemini-3-pro-preview-thinking` | Komplexes Reasoning erforderlich |

### Allgemeine Aufgaben

| Use Case | Beste Wahl | Alternative | Begründung |
|----------|-----------|-------------|------------|
| **Conversational AI** | `gpt-5.1` | `gemini-3-pro-preview` | Beste Personality |
| **Dokumentation** | `gemini-3-pro-preview` | `gpt-5.1` | 1M Context für große Docs |
| **Schnelle Q&A** | `gemini-3.0-flash` | `o4-mini` | Sub-Sekunden-Antworten |
| **Complex Reasoning** | `o3-pro` | `gemini-3-pro-preview` | Höchste Reasoning-Qualität |
| **Multimodal Tasks** | `gemini-3-pro-preview` | - | Native Multimodal Support |

### Performance vs. Quality

```
Höchste Qualität (langsamer):
  o3-pro > gemini-3-pro-preview > o3-mini > gpt-5.1

Beste Balance:
  o4-mini > gemini-3.0-flash > gpt-5.1 > gemini-2.5-pro

Höchste Geschwindigkeit:
  gemini-3.0-flash > o4-mini > gpt-5.1 > o3-mini
```

---

## 🎯 Praktische Verwendungsbeispiele

### OpenAI/Codex Commands

#### Hochkomplexe Software-Entwicklung
```bash
/openai-cli {
  "prompt": "Entwirf eine skalierbare Microservices-Architektur für ein E-Commerce-System mit Event Sourcing",
  "model": "o3-pro",
  "sandbox": "danger-full-access",
  "approval_policy": "never"
}
```

#### Schnelle Code-Generierung
```bash
/openai-cli {
  "prompt": "Schreibe eine Python-Funktion für Binary Search mit Tests",
  "model": "o4-mini",
  "sandbox": "workspace-write",
  "approval_policy": "on-failure"
}
```

#### Allgemeine Aufgaben
```bash
/openai-cli {
  "prompt": "Erkläre mir REST vs GraphQL für eine API-Entscheidung",
  "model": "gpt-5.1"
}
```

---

### Gemini Commands

#### Große Codebase-Analyse
```bash
/gemini-cli {
  "prompt": "Analysiere diese gesamte Codebase und identifiziere Verbesserungspotential",
  "model": "gemini-3-pro-preview-11-2025",
  "approval_mode": "yolo"
}
```

#### Reasoning mit Transparenz
```bash
/gemini-cli {
  "prompt": "Löse dieses komplexe Algorithm-Problem und zeige deinen Denkprozess",
  "model": "gemini-3-pro-preview-11-2025-thinking",
  "approval_mode": "default"
}
```

#### Ultra-schnelle Responses
```bash
/gemini-cli {
  "prompt": "Quick: Was ist der Unterschied zwischen Array und Linked List?",
  "model": "gemini-3.0-flash",
  "yolo": true
}
```

---

## 🔄 Migration von älteren Modellen

### Von o3-mini zu o4-mini
**Warum wechseln?**
- o4-mini übertrifft o3-mini in allen Key-Benchmarks
- Bessere Performance bei ähnlicher Geschwindigkeit
- April 2025 Release, neuere Technologie

**Breaking Changes**: Keine - Drop-in Replacement

### Von gemini-2.5-pro zu gemini-3-pro-preview
**Warum wechseln?**
- Deutlich höhere Intelligenz (1501 Elo vs. ~1400 Elo)
- 1M Token Context (vs. typisch 128k)
- Bessere multimodale Capabilities
- Agentic Features

**Breaking Changes**:
- Modell-Name ändert sich
- Längerer Name für Preview-Version

**Migration**:
```bash
# Alt
"model": "gemini-2.5-pro"

# Neu
"model": "gemini-3-pro-preview-11-2025"
```

---

## 💡 Best Practices 2025

### 1. Model-Auswahl-Strategie

**Faustregel**:
- **Quality > Speed**: `o3-pro` oder `gemini-3-pro-preview`
- **Speed > Quality**: `o4-mini` oder `gemini-3.0-flash`
- **Balanced**: `gpt-5.1` oder `gemini-2.5-pro`

### 2. Context-Management

**Große Contexts (>100k tokens)**:
- Nutze `gemini-3-pro-preview-11-2025` (1M Token)
- Vermeide o3-pro (höhere Latenz bei großen Inputs)

### 3. Cost-Optimization

**Budget-freundlich**:
1. `o4-mini` - Beste Kosten/Performance für Coding
2. `gemini-3.0-flash` - Schnellste Antworten, günstig
3. `o3-mini` - Wenn o4-mini nicht verfügbar

**Premium-Performance** (höhere Kosten akzeptabel):
1. `o3-pro` - Wenn Qualität kritisch ist
2. `gemini-3-pro-preview` - Für multimodale Tasks

### 4. Debugging & Transparenz

**Wenn du den Denkprozess sehen willst**:
- Nutze `gemini-3-pro-preview-11-2025-thinking`
- Ideal für:
  - Verständnis komplexer AI-Entscheidungen
  - Debugging von fehlerhaften Antworten
  - Learning & Education

---

## 🚨 Bekannte Limitierungen (Stand Nov 2025)

### o3-pro
- ⚠️ Längere Response-Times (Background-Mode empfohlen)
- ⚠️ Keine Image-Generation Support
- ⚠️ Timeout-Risiko bei Standard-Mode

### Gemini 3 Preview
- ⚠️ Preview-Status - API kann sich ändern
- ⚠️ Modell-Name ist temporär (wird zu `gemini-3-pro` stabilisiert)
- ⚠️ Knowledge Cutoff: Januar 2025

### gpt-5.1
- ℹ️ Noch keine offizielle Deprecation von GPT-4 angekündigt
- ℹ️ Legacy-Code könnte noch GPT-4-Namen verwenden

---

## 📚 Weitere Ressourcen

### Offizielle Dokumentation
- **OpenAI o3**: https://openai.com/index/introducing-o3-and-o4-mini/
- **GPT-5.1**: https://help.openai.com/en/articles/11909943-gpt-5-in-chatgpt
- **Gemini 3**: https://blog.google/products/gemini/gemini-3/
- **Gemini 3 Developers**: https://blog.google/technology/developers/gemini-3-developers/

### Benchmarks & Vergleiche
- **LMArena Leaderboard**: https://lmarena.ai (Gemini 3: 1501 Elo)
- **SWE-bench**: https://www.swebench.com (o3-pro: 71.7%)
- **OpenAI Model Comparison**: https://platform.openai.com/docs/models

### Plugin-Dokumentation
- **README**: `$HOME/claude-code-multimodel/plugins/multi-provider-cli-chat/README.md`
- **CLAUDE.md Integration**: `~/.claude/CLAUDE.md` (Zeile 151-185)
- **Troubleshooting**: `$HOME/claude-code-multimodel/PLUGIN_TROUBLESHOOTING.md`

---

## 🔄 Update-Historie

- **21.11.2025**: Initial documentation mit allen 2025 Model-Releases
  - OpenAI: o3-pro, o4-mini, gpt-5.1
  - Gemini: gemini-3-pro-preview, gemini-3.0-flash
  - Use-Case-Matrix und Best Practices hinzugefügt

---

*Für Aktualisierungen dieser Datei siehe: Web-Recherche zu neuesten Model-Releases*
*Plugin-Version: 0.1.0*
