/**
 * Shared helpers for the offline test suite.
 *
 * Everything here is deterministic and network-free: files come from the git
 * index (plus untracked, non-ignored files) and processes are started with an
 * argv array (never a shell).
 */

import { execFileSync, spawnSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  "..",
  ".."
);

export const requireCjs = createRequire(import.meta.url);
export const pythonRunner = requireCjs(
  "../../plugins/context-compressor/lib/python-runner.cjs"
);

/** Files tracked by git plus untracked-but-not-ignored files. */
export function listRepoFiles() {
  const output = execFileSync(
    "git",
    ["ls-files", "--cached", "--others", "--exclude-standard"],
    { cwd: repoRoot, encoding: "utf8" }
  );
  return [...new Set(output.split(/\r?\n/).filter(Boolean))].sort();
}

/** Repository files that are regular files on disk (git links are skipped). */
export function listRegularFiles() {
  return listRepoFiles().filter((rel) => {
    try {
      return fs.statSync(path.join(repoRoot, rel)).isFile();
    } catch {
      return false;
    }
  });
}

/** Reads a repo file as UTF-8, or null for binary files. */
export function readText(rel) {
  const absolute = path.join(repoRoot, rel);
  const buffer = fs.readFileSync(absolute);
  if (buffer.includes(0)) return null;
  return buffer.toString("utf8");
}

export function readJson(rel) {
  return JSON.parse(fs.readFileSync(path.join(repoRoot, rel), "utf8"));
}

export function fileExists(rel) {
  try {
    return fs.statSync(path.join(repoRoot, rel)).isFile();
  } catch {
    return false;
  }
}

/** Runs a command without a shell and returns {code, stdout, stderr}. */
export function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    env: { ...process.env, ...(options.env || {}) },
    input: options.input,
    timeout: options.timeout || 120000,
    windowsHide: true,
  });
  return {
    code: result.status,
    stdout: result.stdout || "",
    stderr: result.stderr || "",
    error: result.error ? String(result.error.message) : null,
  };
}

export function makeTempDir(prefix = "ccm-test-") {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

/**
 * Paths recorded as git links (mode 160000) in the index.
 *
 * Such directories exist but are empty in a plain checkout; they must not be
 * mistaken for real plugin directories.
 */
export function gitlinkPaths() {
  const output = execFileSync("git", ["ls-files", "--stage"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  const paths = [];
  for (const line of output.split(/\r?\n/)) {
    const match = /^160000\s+[0-9a-f]+\s+\d+\t(.+)$/.exec(line);
    if (match) paths.push(match[1]);
  }
  return paths;
}

/** Minimal glob: returns repo-relative files matching a suffix. */
export function filesWithExtension(extensions) {
  return listRegularFiles().filter((rel) =>
    extensions.includes(path.extname(rel).toLowerCase())
  );
}
