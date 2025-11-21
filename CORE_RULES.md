# Multi-Provider CLI Plugin - Core Rules

Version: 1.0 | Last Updated: 2025-11-21

## Security (CRITICAL)

1. **Never expose API keys or credentials** in code, logs, or error messages
2. **Validate all user inputs** before processing
3. **Use proper error handling** with structured responses
4. **Always set `retryable: false`** in error responses to prevent retry loops

## Error Handling Pattern

All CLI commands MUST return structured JSON responses:

### Success Response
```json
{
  "provider": "codex" | "gemini",
  "success": true,
  "output": "Result text..."
}
```

### Error Response
```json
{
  "provider": "codex" | "gemini",
  "success": false,
  "error_type": "auth" | "limit" | "missing" | "error" | "circuit_breaker" | "server_error" | "timeout",
  "retryable": false,
  "message": "Clear user-facing message"
}
```

### Error Types

- **auth**: Authentication missing or invalid → User must run CLI login
- **limit**: Rate limit or quota reached → DO NOT RETRY, switch provider
- **missing**: CLI binary not installed → User must install CLI tool
- **error**: General CLI error → DO NOT RETRY
- **circuit_breaker**: Too many recent failures → System protection active
- **server_error**: API server error (500, 502, 503, 504) → DO NOT RETRY
- **timeout**: Request exceeded timeout → DO NOT RETRY

## Circuit Breaker Pattern

### Configuration
- **Threshold**: 3 failures within 5-minute window
- **Cooldown**: 10 minutes after threshold reached
- **State File**: `~/.claude-{provider}-cli-state.json`

### Behavior
1. Track all failures with timestamp
2. Remove failures older than 5 minutes
3. If 3+ failures in window → Open circuit for 10 minutes
4. Provide remaining cooldown time to user
5. Reset on first successful request

### Implementation Requirements
```javascript
const CIRCUIT_BREAKER_THRESHOLD = 3;
const CIRCUIT_BREAKER_WINDOW = 5 * 60 * 1000; // 5 minutes
const CIRCUIT_BREAKER_COOLDOWN = 10 * 60 * 1000; // 10 minutes
```

## Code Style

- **Node.js** with async/await (no callbacks)
- **ES6+** JavaScript syntax
- **Promise-based** error handling
- **JSDoc comments** for complex functions
- **Clear variable names** (descriptive, not abbreviated)

## Input Validation

- **Maximum input size**: 10MB
- **Required fields**: Validate presence and type
- **JSON parsing**: Always use try-catch
- **Timeout**: 5 minutes maximum per request

## CLI Integration

### OpenAI Codex CLI
```bash
codex [--sandbox MODE] [--ask-for-approval POLICY] [-m MODEL] exec "prompt"
```

**Available Models** (as of November 2025):
- `gpt-5.1-codex` - Optimized for coding (RECOMMENDED)
- `gpt-5.1-codex-mini` - Faster, cheaper coding model
- `gpt-5.1` - General knowledge and reasoning (default)

### Google Gemini CLI
```bash
gemini [-m MODEL] "prompt"
```

**Available Models** (as of November 2025):
- `gemini-3-pro-preview-11-2025` - Latest Pro, 1M context (RECOMMENDED)
- `gemini-3-pro-preview-11-2025-thinking` - With visible reasoning
- `gemini-3.0-flash` - Fast, low-latency variant
- `gemini-2.5-pro` - Previous generation Pro
- `gemini-2.0-pro` - Earlier Pro version
- `gemini-2.0-flash` - Earlier Flash version

## Context

This is a multi-provider CLI plugin for Claude Code that routes tasks between Claude, OpenAI Codex, and Google Gemini.

**Primary Goals**:
1. Consistent behavior across all providers
2. Robust error handling with no retry loops
3. Clear user feedback for all error states
4. Efficient token usage through minimal context injection

**Provider Selection Strategy**:
- Use Claude for primary analysis, planning, and code changes
- Use `/openai-cli` only when explicitly requested or for cross-checks
- Use `/gemini-cli` only when explicitly requested or for cross-checks
- Minimize external calls to reduce costs and latency

## Token Optimization

This CORE_RULES.md file is designed to be ~500 tokens, providing essential context without the overhead of full CLAUDE.md (~5000 tokens).

**Cost Savings**: 90% reduction in context injection costs while maintaining consistency.

---

*These rules apply to all CLI command implementations and should be injected into prompts for code-related tasks.*
