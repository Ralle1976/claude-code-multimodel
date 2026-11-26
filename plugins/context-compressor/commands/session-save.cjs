#!/usr/bin/env node

/**
 * session-save.cjs - Speichert Session-Zusammenfassung
 *
 * Eingabe (JSON):
 *   { "summary": "Text der Zusammenfassung", "metadata": {...} }
 *
 * Speichert die Zusammenfassung in ~/.claude-memory/session_summary.md
 * (bzw. unter $CLAUDE_MEMORY_DIR). Wird beim naechsten Claude-Start geladen.
 *
 * Der Text geht ausschliesslich ueber stdin an das Python-Skript: keine
 * Shell, keine Argument-Interpolation, kein Laengenlimit.
 */

const path = require("path");
const { runPython } = require("../lib/python-runner.cjs");

const SCRIPT_DIR = path.dirname(__dirname);
const PYTHON_SCRIPT = path.join(SCRIPT_DIR, "context_compressor.py");

async function readStdinJson() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  try {
    const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function printJson(payload) {
  console.log(JSON.stringify(payload, null, 2));
}

async function main() {
  const payload = await readStdinJson();
  const summary = typeof payload.summary === "string" ? payload.summary : "";

  if (!summary) {
    printJson({
      success: false,
      error: "missing_summary",
      message: "Bitte Zusammenfassung angeben: {\"summary\": \"Text...\"}",
    });
    return;
  }

  const result = await runPython(PYTHON_SCRIPT, ["save-session"], {
    input: summary,
    timeoutMs: 30000,
  });

  if (result.timedOut) {
    printJson({
      success: false,
      error: "timeout",
      message: "Speichern hat das Zeitlimit ueberschritten.",
    });
    return;
  }

  if (result.code !== 0) {
    printJson({
      success: false,
      error: "save_failed",
      message: (result.stderr || "Unbekannter Fehler").trim(),
    });
    return;
  }

  try {
    printJson(JSON.parse(result.stdout));
  } catch {
    console.log(result.stdout);
  }
}

main().catch((error) => {
  printJson({
    success: false,
    error: "unexpected_error",
    message: String(error && error.message ? error.message : error),
  });
});
