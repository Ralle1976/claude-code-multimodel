"use strict";

/**
 * python-runner.cjs - Locates a usable Python interpreter and runs
 * context_compressor.py without a shell.
 *
 * Why this module exists:
 * - `python3` does not exist on every platform (notably Windows, where the
 *   interpreter is usually `python`). Hardwiring `python3` made every command
 *   fail with ENOENT.
 * - Text from the user (prompt/summary) must never be interpolated into a
 *   shell command line. We only ever spawn with an argv array and pass the
 *   payload over stdin.
 */

const { spawn } = require("node:child_process");

const PROBE_TIMEOUT_MS = 5000;
const DEFAULT_TIMEOUT_MS = 120000;

// Order matters: explicit override first, then the POSIX name, then the
// Windows name. Missing candidates are skipped by the probe.
function candidateCommands() {
  return [process.env.CLAUDE_PYTHON, "python3", "python"].filter(Boolean);
}

function probeCommand(cmd) {
  return new Promise((resolve) => {
    let child;
    let settled = false;

    const finish = (ok) => {
      if (settled) return;
      settled = true;
      resolve(ok);
    };

    try {
      child = spawn(cmd, ["--version"], {
        stdio: ["ignore", "pipe", "pipe"],
        windowsHide: true,
      });
    } catch {
      finish(false);
      return;
    }

    const timer = setTimeout(() => {
      try {
        child.kill();
      } catch {
        // process already gone
      }
      finish(false);
    }, PROBE_TIMEOUT_MS);

    child.on("error", () => {
      clearTimeout(timer);
      finish(false);
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      finish(code === 0);
    });
  });
}

let cachedPython = null;

/**
 * Resolve the first interpreter whose `--version` succeeds.
 * @returns {Promise<string|null>} command name, or null if none works
 */
async function resolvePython() {
  if (cachedPython) return cachedPython;

  for (const cmd of candidateCommands()) {
    if (await probeCommand(cmd)) {
      cachedPython = cmd;
      return cachedPython;
    }
  }
  return null;
}

/**
 * Run a Python script with argv passed as a real argument vector.
 *
 * @param {string} scriptPath absolute path to the .py file
 * @param {string[]} argv arguments after the script path
 * @param {{input?: string, timeoutMs?: number}} [options]
 * @returns {Promise<{code: number|null, stdout: string, stderr: string, timedOut: boolean}>}
 */
async function runPython(scriptPath, argv = [], options = {}) {
  const python = await resolvePython();
  if (!python) {
    return {
      code: null,
      stdout: "",
      stderr:
        "No Python interpreter found. Install Python 3 or set CLAUDE_PYTHON to its path.",
      timedOut: false,
      missingInterpreter: true,
    };
  }

  const timeoutMs = options.timeoutMs || DEFAULT_TIMEOUT_MS;

  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    let settled = false;

    const child = spawn(python, [scriptPath, ...argv], {
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });

    const timer = setTimeout(() => {
      timedOut = true;
      try {
        child.kill();
      } catch {
        // process already gone
      }
    }, timeoutMs);

    const finish = (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ code, stdout, stderr, timedOut });
    };

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    // A closed pipe must not surface as an unhandled stream error.
    child.stdin.on("error", () => {});

    child.on("error", (err) => {
      stderr += String(err && err.message ? err.message : err);
      finish(null);
    });
    child.on("close", (code) => finish(code));

    if (options.input === undefined) {
      child.stdin.end();
    } else {
      child.stdin.end(options.input);
    }
  });
}

module.exports = { resolvePython, runPython, candidateCommands };
