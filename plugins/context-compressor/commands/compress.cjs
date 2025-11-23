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
 * Verwendet LLMLingua fuer intelligente Komprimierung
 * ohne signifikanten Bedeutungsverlust.
 */

const { execSync, spawn } = require("node:child_process");
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
  const text = payload.text || "";

  if (!text) {
    console.log(JSON.stringify({
      success: false,
      error: "missing_text",
      message: "Bitte Text angeben: {\"text\": \"Langer Text...\"}"
    }, null, 2));
    return;
  }

  try {
    // Use spawn to handle large text via stdin
    const child = spawn("python3", [PYTHON_SCRIPT, "compress"], {
      stdio: ["pipe", "pipe", "pipe"],
      timeout: 120000
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (data) => {
      stdout += data.toString();
    });

    child.stderr.on("data", (data) => {
      stderr += data.toString();
    });

    child.stdin.write(text);
    child.stdin.end();

    await new Promise((resolve, reject) => {
      child.on("close", (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Process exited with code ${code}: ${stderr}`));
        }
      });
      child.on("error", reject);
    });

    // Try to parse as JSON, otherwise return raw
    try {
      const result = JSON.parse(stdout);
      console.log(JSON.stringify(result, null, 2));
    } catch {
      console.log(stdout);
    }

  } catch (error) {
    console.log(JSON.stringify({
      success: false,
      error: "compression_failed",
      message: error.message
    }, null, 2));
  }
}

main().catch(console.error);
