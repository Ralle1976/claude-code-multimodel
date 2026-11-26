#!/usr/bin/env node

/**
 * session-load.cjs - Laedt Session-Zusammenfassung
 *
 * Eingabe: Keine (leeres JSON oder {})
 *
 * Gibt die gespeicherte Session-Zusammenfassung zurueck,
 * falls vorhanden.
 */

const path = require("path");
const { runPython } = require("../lib/python-runner.cjs");

const SCRIPT_DIR = path.dirname(__dirname);
const PYTHON_SCRIPT = path.join(SCRIPT_DIR, "context_compressor.py");

function printJson(payload) {
  console.log(JSON.stringify(payload, null, 2));
}

async function main() {
  const result = await runPython(PYTHON_SCRIPT, ["load-session"], {
    timeoutMs: 10000,
  });

  if (result.timedOut) {
    printJson({
      success: false,
      error: "timeout",
      message: "Laden hat das Zeitlimit ueberschritten.",
    });
    return;
  }

  if (result.code !== 0) {
    printJson({
      success: false,
      error: "load_failed",
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

// stdin wird konsumiert, aber inhaltlich ignoriert
let started = false;
function start() {
  if (started) return;
  started = true;
  main().catch((error) => {
    printJson({
      success: false,
      error: "unexpected_error",
      message: String(error && error.message ? error.message : error),
    });
  });
}

process.stdin.resume();
process.stdin.on("end", start);
process.stdin.on("close", start);
process.stdin.on("error", start);
