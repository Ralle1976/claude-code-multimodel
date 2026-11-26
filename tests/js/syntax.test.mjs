/**
 * Offline syntax validation for every script type in the repository.
 *
 * No network, no package installation, no build step: shell scripts go through
 * `bash -n`, Python through `compile()`, JavaScript through `node --check`,
 * TypeScript through Node's type stripping, PowerShell through the real
 * PowerShell parser when it is available.
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import {
  filesWithExtension,
  pythonRunner,
  readText,
  repoRoot,
  run,
} from "./helpers.mjs";

function haveCommand(command, args = ["--version"]) {
  const result = run(command, args, { timeout: 15000 });
  return result.code === 0;
}

test("all JSON files parse", () => {
  const files = filesWithExtension([".json"]);
  assert.ok(files.length > 0, "expected at least one JSON file");

  for (const rel of files) {
    const text = readText(rel);
    assert.ok(text !== null, `${rel} must be a text file`);
    try {
      JSON.parse(text);
    } catch (error) {
      assert.fail(`${rel} is not valid JSON: ${error.message}`);
    }
  }
});

test("all shell scripts pass 'bash -n'", (t) => {
  const files = filesWithExtension([".sh"]);
  if (!haveCommand("bash", ["--version"])) {
    t.skip("bash not available");
    return;
  }
  assert.ok(files.length > 0, "expected at least one shell script");

  for (const rel of files) {
    const result = run("bash", ["-n", path.join(repoRoot, rel)]);
    assert.equal(
      result.code,
      0,
      `${rel} has a shell syntax error:\n${result.stderr}`
    );
  }
});

test("all Python files compile", async (t) => {
  const files = filesWithExtension([".py"]);
  const python = await pythonRunner.resolvePython();
  if (!python) {
    t.skip("no Python interpreter available");
    return;
  }
  assert.ok(files.length > 0, "expected at least one Python file");

  const script = [
    "import pathlib, sys",
    "failed = []",
    "for name in sys.argv[1:]:",
    "    try:",
    // compile() statt py_compile: schreibt keine __pycache__-Artefakte
    "        source = pathlib.Path(name).read_text(encoding='utf-8')",
    "        compile(source, name, 'exec')",
    "    except (SyntaxError, UnicodeDecodeError) as exc:",
    "        failed.append(f'{name}: {exc}')",
    "print('\\n'.join(failed))",
    "sys.exit(1 if failed else 0)",
  ].join("\n");

  const direct = run(
    python,
    ["-c", script, ...files.map((rel) => path.join(repoRoot, rel))],
    { timeout: 60000 }
  );
  assert.equal(
    direct.code,
    0,
    `Python syntax errors:\n${direct.stdout}\n${direct.stderr}`
  );
});

test("all CommonJS/ESM modules pass 'node --check'", () => {
  const files = filesWithExtension([".cjs", ".mjs", ".js"]);
  assert.ok(files.length > 0, "expected at least one JS module");

  for (const rel of files) {
    const result = run(process.execPath, ["--check", path.join(repoRoot, rel)]);
    assert.equal(
      result.code,
      0,
      `${rel} has a JS syntax error:\n${result.stderr}`
    );
  }
});

test("all TypeScript scripts are syntactically valid", async (t) => {
  const files = filesWithExtension([".ts"]);
  if (files.length === 0) {
    t.skip("no TypeScript files");
    return;
  }

  let stripTypeScriptTypes;
  try {
    ({ stripTypeScriptTypes } = await import("node:module"));
  } catch {
    stripTypeScriptTypes = undefined;
  }
  if (typeof stripTypeScriptTypes !== "function") {
    t.skip("Node build has no module.stripTypeScriptTypes");
    return;
  }

  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "ccm-ts-"));

  for (const rel of files) {
    const source = readText(rel);
    assert.ok(source !== null, `${rel} must be a text file`);

    let stripped;
    try {
      stripped = stripTypeScriptTypes(source, { mode: "strip" });
    } catch (error) {
      assert.fail(`${rel} cannot be type-stripped: ${error.message}`);
    }

    const tempFile = path.join(tempDir, `${path.basename(rel)}.mjs`);
    fs.writeFileSync(tempFile, stripped, "utf8");

    const result = run(process.execPath, ["--check", tempFile]);
    assert.equal(
      result.code,
      0,
      `${rel} has a TypeScript syntax error:\n${result.stderr}`
    );
  }
});

test("PowerShell scripts parse", (t) => {
  const files = filesWithExtension([".ps1"]);
  if (files.length === 0) {
    t.skip("no PowerShell files");
    return;
  }
  if (!haveCommand("powershell", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.Major"])) {
    t.skip("PowerShell not available");
    return;
  }

  const command = [
    "$ErrorActionPreference='Stop'",
    "$errors=$null",
    "$null=[System.Management.Automation.Language.Parser]::ParseFile($env:CCM_PS_FILE,[ref]$null,[ref]$errors)",
    "if ($errors) { $errors | ForEach-Object { Write-Output $_.Message }; exit 1 }",
  ].join("; ");

  for (const rel of files) {
    const result = run(
      "powershell",
      ["-NoProfile", "-NonInteractive", "-Command", command],
      { env: { CCM_PS_FILE: path.join(repoRoot, rel) }, timeout: 60000 }
    );
    assert.equal(
      result.code,
      0,
      `${rel} has a PowerShell syntax error:\n${result.stdout}\n${result.stderr}`
    );
  }
});

test("hook handlers emit valid JSON", (t) => {
  const handlers = ["plugins/explanatory-output-style/hooks-handlers/session-start.sh",
    "plugins/learning-output-style/hooks-handlers/session-start.sh"];

  if (!haveCommand("bash", ["--version"])) {
    t.skip("bash not available");
    return;
  }

  for (const rel of handlers) {
    const result = run("bash", [path.join(repoRoot, rel)]);
    assert.equal(result.code, 0, `${rel} exited with ${result.code}`);
    let parsed;
    try {
      parsed = JSON.parse(result.stdout);
    } catch (error) {
      assert.fail(`${rel} did not emit JSON: ${error.message}`);
    }
    assert.ok(
      parsed.hookSpecificOutput,
      `${rel} must emit hookSpecificOutput`
    );
    assert.equal(typeof parsed.hookSpecificOutput.additionalContext, "string");
  }
});
