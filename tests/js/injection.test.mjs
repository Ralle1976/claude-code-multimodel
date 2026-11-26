/**
 * Injection- und Integrations-Regressionstests fuer das context-compressor
 * Plugin.
 *
 * Der Kern: Nutzereingaben (Prompt/Zusammenfassung) duerfen niemals als
 * Shell-Kommando ausgewertet werden. Frueher wurde die Zusammenfassung per
 * execSync in eine Shell-Zeile interpoliert - hier wird geprueft, dass
 * Shell-Metazeichen als reine Daten ankommen.
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import {
  filesWithExtension,
  makeTempDir,
  pythonRunner,
  readText,
  repoRoot,
  run,
} from "./helpers.mjs";

const COMMAND_DIR = path.join(repoRoot, "plugins", "context-compressor", "commands");
const SESSION_SAVE = path.join(COMMAND_DIR, "session-save.cjs");
const SESSION_LOAD = path.join(COMMAND_DIR, "session-load.cjs");
const COMPRESS = path.join(COMMAND_DIR, "compress.cjs");

// Erzwingt den regelbasierten Fallback: kein Modell-Download, kein Netzwerk.
const OFFLINE_ENV = { CLAUDE_DISABLE_LLMLINGUA: "1" };

function envFor(memoryDir, extra = {}) {
  return {
    ...OFFLINE_ENV,
    CLAUDE_MEMORY_DIR: memoryDir,
    ...extra,
  };
}

function shellPayloads(markerDir) {
  const markers = {
    subst: path.join(markerDir, "pwned-subst"),
    backtick: path.join(markerDir, "pwned-backtick"),
    quote: path.join(markerDir, "pwned-quote"),
    amp: path.join(markerDir, "pwned-amp"),
    single: path.join(markerDir, "pwned-single"),
  };

  const payloads = [
    { name: "command substitution", marker: markers.subst, text: `$(touch ${markers.subst})` },
    { name: "backticks", marker: markers.backtick, text: "`touch " + markers.backtick + "`" },
    { name: "double quote escape", marker: markers.quote, text: `"; touch ${markers.quote}; echo "` },
    { name: "windows command chaining", marker: markers.amp, text: `x" & echo pwned > ${markers.amp} & rem "` },
    { name: "single quote escape", marker: markers.single, text: `'; touch ${markers.single}; echo '` },
  ];

  return payloads;
}

test("session-save never executes shell metacharacters", async (t) => {
  const python = await pythonRunner.resolvePython();
  if (!python) {
    t.skip("no Python interpreter available");
    return;
  }

  const temp = makeTempDir("ccm-inject-");
  const memoryDir = path.join(temp, "memory");
  const markerDir = path.join(temp, "markers");
  fs.mkdirSync(markerDir, { recursive: true });

  for (const payload of shellPayloads(markerDir)) {
    const result = run(process.execPath, [SESSION_SAVE], {
      input: JSON.stringify({ summary: payload.text }),
      env: envFor(memoryDir),
    });

    assert.equal(
      result.code,
      0,
      `session-save failed for ${payload.name}: ${result.stderr}`
    );
    assert.equal(
      fs.existsSync(payload.marker),
      false,
      `shell payload was executed (${payload.name})`
    );

    const parsed = JSON.parse(result.stdout);
    assert.equal(parsed.success, true, `session-save reported an error for ${payload.name}`);

    const stored = fs.readFileSync(
      path.join(memoryDir, "session_summary.md"),
      "utf8"
    );
    assert.ok(
      stored.includes(payload.text),
      `${payload.name} payload was not stored literally`
    );
  }
});

test("compress keeps shell metacharacters as data", async (t) => {
  const python = await pythonRunner.resolvePython();
  if (!python) {
    t.skip("no Python interpreter available");
    return;
  }

  const temp = makeTempDir("ccm-compress-");
  const memoryDir = path.join(temp, "memory");
  const marker = path.join(temp, "pwned-compress");
  const text = "Bitte komprimiere das. $(touch " + marker + ") ``` ; rm -rf /tmp/xyz ; " +
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor " +
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam quis nostrud.";

  const result = run(process.execPath, [COMPRESS], {
    input: JSON.stringify({ text }),
    env: envFor(memoryDir),
  });

  assert.equal(result.code, 0, `compress failed: ${result.stderr}`);
  assert.equal(fs.existsSync(marker), false, "compress executed a shell payload");

  const parsed = JSON.parse(result.stdout);
  assert.equal(parsed.success, true, `compress reported an error: ${result.stdout}`);
});

test("session save/load round trip survives UTF-8 (emoji, CJK)", async (t) => {
  const python = await pythonRunner.resolvePython();
  if (!python) {
    t.skip("no Python interpreter available");
    return;
  }

  const temp = makeTempDir("ccm-roundtrip-");
  const memoryDir = path.join(temp, "memory");
  const summary = "Session mit Emoji 🚀 und CJK 日本語 sowie Umlauten äöüß";

  const save = run(process.execPath, [SESSION_SAVE], {
    input: JSON.stringify({ summary }),
    env: envFor(memoryDir),
  });
  assert.equal(save.code, 0);
  assert.equal(JSON.parse(save.stdout).success, true);

  const load = run(process.execPath, [SESSION_LOAD], {
    input: "",
    env: envFor(memoryDir),
  });
  assert.equal(load.code, 0, `session-load failed: ${load.stderr}`);

  const parsed = JSON.parse(load.stdout);
  assert.equal(parsed.success, true);
  assert.equal(parsed.exists, true);
  assert.ok(
    parsed.content.includes(summary),
    "UTF-8 payload did not survive the round trip"
  );
});

test("session-load reports missing memory gracefully", async (t) => {
  const python = await pythonRunner.resolvePython();
  if (!python) {
    t.skip("no Python interpreter available");
    return;
  }

  const temp = makeTempDir("ccm-empty-");
  const memoryDir = path.join(temp, "memory-neu");

  const load = run(process.execPath, [SESSION_LOAD], {
    input: "",
    env: envFor(memoryDir),
  });
  assert.equal(load.code, 0, `session-load failed: ${load.stderr}`);

  const parsed = JSON.parse(load.stdout);
  assert.equal(parsed.success, true);
  assert.equal(parsed.exists, false);
});

test("malformed INPUT JSON is reported, not crashed", async (t) => {
  const python = await pythonRunner.resolvePython();
  if (!python) {
    t.skip("no Python interpreter available");
    return;
  }

  const temp = makeTempDir("ccm-badjson-");
  const memoryDir = path.join(temp, "memory");

  const result = run(process.execPath, [COMPRESS], {
    input: "{not json",
    env: envFor(memoryDir),
  });

  assert.equal(result.code, 0, "the command must not crash on invalid stdin JSON");
  const parsed = JSON.parse(result.stdout);
  assert.equal(parsed.success, false);
  assert.equal(parsed.error, "missing_text");
});

test("no shell-invoking child_process APIs in plugin/script code", () => {
  const files = filesWithExtension([".cjs", ".mjs", ".js", ".ts"]).filter(
    (rel) => !rel.startsWith("tests/")
  );

  const offenders = [];
  for (const rel of files) {
    const text = readText(rel);
    if (text === null) continue;
    if (/\bexecSync\s*\(/.test(text)) offenders.push(`${rel}: execSync(`);
    if (/\bexec\s*\(\s*`/.test(text)) offenders.push(`${rel}: exec(\`…\`)`);
    if (/shell\s*:\s*true/.test(text)) offenders.push(`${rel}: shell: true`);
    if (/\bchild_process\.execSync\b/.test(text)) offenders.push(`${rel}: child_process.execSync`);
  }

  assert.deepEqual(offenders, [], `shell-based process APIs found:\n${offenders.join("\n")}`);
});
