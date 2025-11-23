#!/usr/bin/env node

/**
 * session-save.cjs - Speichert Session-Zusammenfassung
 *
 * Eingabe (JSON):
 *   { "summary": "Text der Zusammenfassung", "metadata": {...} }
 *
 * Speichert die Zusammenfassung in ~/.claude-memory/session_summary.md
 * Diese wird beim naechsten Claude-Start automatisch geladen.
 */

const { execSync } = require("node:child_process");
const path = require("path");

const SCRIPT_DIR = path.dirname(__dirname);
const PYTHON_SCRIPT = path.join(SCRIPT_DIR, "context_compressor.py");

async function readStdinJson() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  if (!chunks.length) return {};
  try {
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  } catch (err) {
    return {};
  }
}

async function main() {
  const payload = await readStdinJson();
  const summary = payload.summary || "";

  if (!summary) {
    console.log(JSON.stringify({
      success: false,
      error: "missing_summary",
      message: "Bitte Zusammenfassung angeben: {\"summary\": \"Text...\"}"
    }, null, 2));
    return;
  }

  try {
    const result = execSync(
      `python3 "${PYTHON_SCRIPT}" save-session "${summary.replace(/"/g, '\\"')}"`,
      { encoding: "utf8", timeout: 30000 }
    );
    console.log(result);
  } catch (error) {
    console.log(JSON.stringify({
      success: false,
      error: "save_failed",
      message: error.message
    }, null, 2));
  }
}

main().catch(console.error);
