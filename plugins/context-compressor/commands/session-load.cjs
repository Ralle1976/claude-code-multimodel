#!/usr/bin/env node

/**
 * session-load.cjs - Laedt Session-Zusammenfassung
 *
 * Eingabe: Keine (leeres JSON oder {})
 *
 * Gibt die gespeicherte Session-Zusammenfassung zurueck,
 * falls vorhanden.
 */

const { execSync } = require("node:child_process");
const path = require("path");

const SCRIPT_DIR = path.dirname(__dirname);
const PYTHON_SCRIPT = path.join(SCRIPT_DIR, "context_compressor.py");

async function main() {
  try {
    const result = execSync(
      `python3 "${PYTHON_SCRIPT}" load-session`,
      { encoding: "utf8", timeout: 10000 }
    );
    console.log(result);
  } catch (error) {
    console.log(JSON.stringify({
      success: false,
      error: "load_failed",
      message: error.message
    }, null, 2));
  }
}

// Consume stdin but ignore it
process.stdin.resume();
process.stdin.on("end", () => main().catch(console.error));
