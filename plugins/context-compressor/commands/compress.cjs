#!/usr/bin/env node

/**
 * compress.cjs - Komprimiert Text mit LLMLingua
 *
 * Eingabe (JSON):
 *   { "text": "Langer Text...", "ratio": 0.5 }
 *
 * ratio: Anteil der zu behaltenden Tokens (0.0-1.0)
 *        Standard: 0.5 (50% behalten)
 *
 * Der Text wird ausschliesslich ueber stdin an das Python-Skript uebergeben
 * (kein Shell-Aufruf, keine Argument-Interpolation).
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
  const text = typeof payload.text === "string" ? payload.text : "";

  if (!text) {
    printJson({
      success: false,
      error: "missing_text",
      message: "Bitte Text angeben: {\"text\": \"Langer Text...\"}",
    });
    return;
  }

  // ratio is optional; only forward it when it is a sane number so the
  // Python side never receives a value it would silently clamp.
  const args = ["compress"];
  const ratio = Number(payload.ratio);
  if (Number.isFinite(ratio) && ratio > 0 && ratio <= 1 && ratio !== 0.5) {
    args.push("--ratio", String(ratio));
  }

  const result = await runPython(PYTHON_SCRIPT, args, { input: text });

  if (result.timedOut) {
    printJson({
      success: false,
      error: "timeout",
      message: "Komprimierung hat das Zeitlimit ueberschritten.",
    });
    return;
  }

  if (result.code !== 0) {
    printJson({
      success: false,
      error: "compression_failed",
      message: (result.stderr || "Unbekannter Fehler").trim(),
    });
    return;
  }

  // Try to parse as JSON, otherwise return raw
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
