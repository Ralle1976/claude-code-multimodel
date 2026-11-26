#!/usr/bin/env node

/**
 * Offline-Gesamtverifikation — ein Befehl, echte Exit-Codes.
 *
 *   node tests/run-all.mjs
 *
 * Fuehrt die JS-Tests (node --test) und die Python-Tests (unittest) aus.
 * Es werden keine Pakete installiert, keine Live-APIs aufgerufen und keine
 * Modelle geladen (CLAUDE_DISABLE_LLMLINGUA=1).
 */

import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import path from "node:path";

const require = createRequire(import.meta.url);
const { resolvePython } = require("../plugins/context-compressor/lib/python-runner.cjs");

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function runStep(label, command, args, env) {
  process.stdout.write(`\n=== ${label} ===\n`);

  const started = Date.now();
  const result = spawnSync(command, args, {
    cwd: repoRoot,
    stdio: "inherit",
    env: { ...process.env, CLAUDE_DISABLE_LLMLINGUA: "1", ...(env || {}) },
    timeout: 15 * 60 * 1000,
    windowsHide: true,
  });
  const duration = ((Date.now() - started) / 1000).toFixed(1);

  const code = result.status === null ? 1 : result.status;
  console.log(`--- ${label}: exit ${code} (${duration}s)`);
  return code;
}

async function main() {
  const results = [];

  results.push({
    label: "JS/Node-Checks (node --test)",
    code: runStep("JS/Node-Checks", process.execPath, ["--test", "tests/js"]),
  });

  const python = await resolvePython();
  if (!python) {
    console.error("Kein Python-Interpreter gefunden - Python-Tests uebersprungen.");
    results.push({ label: "Python-Checks (unittest)", code: 1 });
  } else {
    results.push({
      label: "Python-Checks (unittest)",
      code: runStep("Python-Checks", python, [
        "-m",
        "unittest",
        "discover",
        "-s",
        path.join("tests", "py"),
        "-t",
        path.join("tests", "py"),
        "-v",
      ]),
    });
  }

  console.log("\n=== Zusammenfassung ===");
  for (const entry of results) {
    console.log(`${entry.code === 0 ? "PASS" : "FAIL"}  ${entry.label}  (exit ${entry.code})`);
  }

  const failed = results.filter((entry) => entry.code !== 0).length;
  console.log(
    failed === 0
      ? `\nAlle Checks gruen (${results.length} Stufen).`
      : `\n${failed} von ${results.length} Stufen fehlgeschlagen.`
  );

  process.exit(failed === 0 ? 0 : 1);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
