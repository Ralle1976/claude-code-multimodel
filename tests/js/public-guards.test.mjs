/**
 * PUBLIC-Repo-Guards: keine Secrets, keine persoenlichen Benutzerpfade,
 * keine privaten IPs, keine echten Kontaktadressen.
 *
 * Der Scan laeuft ueber alle Textdateien des Repos (getrackt + untracked,
 * ohne ignorierte Dateien) und ist vollkommen offline.
 */

import test from "node:test";
import assert from "node:assert/strict";

import { listRegularFiles, readText } from "./helpers.mjs";

// Endungen, die als Text geprueft werden. Binaerdateien (demo.gif) und der
// getrackte .pyc-Artefakt werden ausgelassen.
const TEXT_EXTENSIONS = new Set([
  "",
  ".md",
  ".json",
  ".yml",
  ".yaml",
  ".sh",
  ".py",
  ".cjs",
  ".mjs",
  ".js",
  ".ts",
  ".ps1",
  ".txt",
  ".gitignore",
  ".gitattributes",
]);

// Upstream-Anthropic-Kontaktadressen sind Teil des oeffentlichen
// Marketplace-Manifests und keine privaten PII.
const ALLOWED_EMAIL_DOMAINS = [
  "@anthropic.com",
  "@example.com",
  "@example.org",
  "@users.noreply.github.com",
];

// Platzhalter und Dienst-Benutzer, die in Container-/CI-Pfaden legitim sind.
const ALLOWED_HOME_USERS = new Set([
  "node",
  "me",
  "user",
  "username",
  "you",
  "vscode",
  "runner",
  "app",
  "ubuntu",
  "debian",
]);

function extensionOf(rel) {
  const match = /\.[A-Za-z0-9]+$/.exec(rel);
  return match ? match[0].toLowerCase() : "";
}

function textFiles() {
  return listRegularFiles()
    .filter((rel) => !rel.endsWith(".pyc"))
    .filter((rel) => TEXT_EXTENSIONS.has(extensionOf(rel)))
    .map((rel) => ({ rel, text: readText(rel) }))
    .filter((entry) => entry.text !== null);
}

function reportHits(hits) {
  return hits.map(({ rel, line, match }) => `${rel}:${line}: ${match}`).join("\n");
}

function scanLines(files, pattern) {
  const hits = [];
  for (const { rel, text } of files) {
    const lines = text.split(/\r?\n/);
    for (let index = 0; index < lines.length; index++) {
      const match = pattern.exec(lines[index]);
      if (match) {
        hits.push({ rel, line: index + 1, match: match[0] });
      }
    }
  }
  return hits;
}

const files = textFiles();

test("no API keys, tokens or private keys are committed", () => {
  const patterns = [
    /sk-[A-Za-z0-9]{16,}/,
    /sk-ant-[A-Za-z0-9_-]{16,}/,
    /gh[pous]_[A-Za-z0-9]{20,}/,
    /github_pat_[A-Za-z0-9_]{20,}/,
    /AKIA[0-9A-Z]{16}/,
    /AIza[0-9A-Za-z_-]{30,}/,
    /xox[baprs]-[A-Za-z0-9-]{10,}/,
    /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
    /Bearer\s+[A-Za-z0-9._-]{20,}/,
  ];

  const hits = [];
  for (const pattern of patterns) {
    hits.push(...scanLines(files, pattern));
  }

  assert.deepEqual(hits, [], `possible secrets found:\n${reportHits(hits)}`);
});

test("no absolute personal home directories", () => {
  const unixHome = /\/home\/([A-Za-z0-9._-]+)\//g;
  const macHome = /\/Users\/([A-Za-z0-9._-]+)\//g;
  const windowsHome = /[A-Za-z]:\\+Users\\+([A-Za-z0-9._-]+)/g;

  const hits = [];
  for (const { rel, text } of files) {
    const lines = text.split(/\r?\n/);
    lines.forEach((line, index) => {
      for (const pattern of [unixHome, macHome, windowsHome]) {
        pattern.lastIndex = 0;
        let match;
        while ((match = pattern.exec(line)) !== null) {
          const user = match[1];
          const isEnvVar = /^[$%]/.test(user);
          if (isEnvVar || ALLOWED_HOME_USERS.has(user)) continue;
          hits.push({ rel, line: index + 1, match: match[0] });
        }
      }
    });
  }

  assert.deepEqual(
    hits,
    [],
    `personal home directories must not be committed:\n${reportHits(hits)}`
  );
});

test("no private e-mail addresses are committed", () => {
  const email = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;

  const hits = [];
  for (const { rel, text } of files) {
    const lines = text.split(/\r?\n/);
    lines.forEach((line, index) => {
      email.lastIndex = 0;
      let match;
      while ((match = email.exec(line)) !== null) {
        const address = match[0].toLowerCase();
        if (ALLOWED_EMAIL_DOMAINS.some((domain) => address.endsWith(domain))) {
          continue;
        }
        hits.push({ rel, line: index + 1, match: match[0] });
      }
    });
  }

  assert.deepEqual(
    hits,
    [],
    `private e-mail addresses must not be committed:\n${reportHits(hits)}`
  );
});

test("no private network addresses are committed", () => {
  const privateIp = /\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b/;

  const hits = scanLines(files, privateIp);
  assert.deepEqual(
    hits,
    [],
    `private IP addresses must not be committed:\n${reportHits(hits)}`
  );
});

test("no .env files are tracked", () => {
  const tracked = listRegularFiles().filter((rel) =>
    /(^|\/)\.env(\.|$)/.test(rel)
  );
  assert.deepEqual(tracked, [], `env files must stay untracked: ${tracked.join(", ")}`);
});
