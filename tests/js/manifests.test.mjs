/**
 * Manifest- und Struktur-Validierung: Plugin-Manifeste, Marketplace-Katalog
 * und Hook-Registrierungen muessen zum Inhalt auf der Platte passen.
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

import { fileExists, gitlinkPaths, readJson, repoRoot } from "./helpers.mjs";

const PLUGINS_DIR = path.join(repoRoot, "plugins");

function pluginDirectories() {
  const gitlinks = new Set(
    gitlinkPaths()
      .filter((rel) => rel.startsWith("plugins/"))
      .map((rel) => path.basename(rel))
  );

  return fs
    .readdirSync(PLUGINS_DIR, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    // Git-Link-Verzeichnisse sind in einem normalen Checkout leer und keine
    // eigenstaendigen Plugins dieses Repos.
    .filter((entry) => !gitlinks.has(entry.name))
    .map((entry) => entry.name)
    .sort();
}

test("every plugin ships a valid .claude-plugin/plugin.json", () => {
  const problems = [];

  for (const name of pluginDirectories()) {
    const manifestPath = path.join(PLUGINS_DIR, name, ".claude-plugin", "plugin.json");
    if (!fs.existsSync(manifestPath)) {
      problems.push(`${name}: .claude-plugin/plugin.json fehlt`);
      continue;
    }

    let manifest;
    try {
      manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    } catch (error) {
      problems.push(`${name}: plugin.json ist kein valides JSON (${error.message})`);
      continue;
    }

    if (manifest.name !== name) {
      problems.push(`${name}: manifest.name ist "${manifest.name}" statt "${name}"`);
    }
    if (typeof manifest.version !== "string" || !manifest.version) {
      problems.push(`${name}: version fehlt`);
    }
    if (typeof manifest.description !== "string" || !manifest.description) {
      problems.push(`${name}: description fehlt`);
    }
  }

  assert.deepEqual(problems, [], `plugin manifests:\n${problems.join("\n")}`);
});

test("marketplace entries point to existing plugins", () => {
  const marketplace = readJson(".claude-plugin/marketplace.json");
  assert.ok(Array.isArray(marketplace.plugins), "marketplace.plugins muss ein Array sein");

  const problems = [];
  for (const entry of marketplace.plugins) {
    if (!entry.name || !entry.source) {
      problems.push(`Eintrag ohne name/source: ${JSON.stringify(entry)}`);
      continue;
    }

    const relative = entry.source.replace(/^\.\//, "");
    const manifestPath = path.join(repoRoot, relative, ".claude-plugin", "plugin.json");
    if (!fs.existsSync(manifestPath)) {
      problems.push(`${entry.name}: source ${entry.source} hat kein plugin.json`);
      continue;
    }

    const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
    if (manifest.name !== entry.name) {
      problems.push(`${entry.name}: source zeigt auf Plugin "${manifest.name}"`);
    }
  }

  assert.deepEqual(problems, [], `marketplace:\n${problems.join("\n")}`);
});

test("hook registrations reference existing files", () => {
  const problems = [];

  for (const name of pluginDirectories()) {
    const hooksPath = path.join(PLUGINS_DIR, name, "hooks", "hooks.json");
    if (!fs.existsSync(hooksPath)) continue;

    let config;
    try {
      config = JSON.parse(fs.readFileSync(hooksPath, "utf8"));
    } catch (error) {
      problems.push(`${name}: hooks.json ist kein valides JSON (${error.message})`);
      continue;
    }

    if (!config.hooks || typeof config.hooks !== "object") {
      problems.push(`${name}: hooks.json hat kein hooks-Objekt`);
      continue;
    }

    for (const [eventName, entries] of Object.entries(config.hooks)) {
      if (!Array.isArray(entries)) {
        problems.push(`${name}: ${eventName} ist kein Array`);
        continue;
      }

      for (const entry of entries) {
        const registered = Array.isArray(entry.hooks) ? entry.hooks : [];
        if (registered.length === 0) {
          problems.push(`${name}: ${eventName} hat keinen Handler`);
        }

        for (const handler of registered) {
          if (handler.type !== "command") {
            problems.push(`${name}: ${eventName} nutzt unbekannten Handler-Typ ${handler.type}`);
          }
          if (typeof handler.command !== "string" || !handler.command) {
            problems.push(`${name}: ${eventName} hat kein command`);
            continue;
          }

          const resolved = handler.command.replace(
            /\$\{CLAUDE_PLUGIN_ROOT\}/g,
            path.join(PLUGINS_DIR, name)
          );
          if (!fs.existsSync(resolved)) {
            problems.push(`${name}: ${eventName} verweist auf fehlende Datei ${handler.command}`);
          }
        }
      }
    }
  }

  assert.deepEqual(problems, [], `hook registrations:\n${problems.join("\n")}`);
});

test("context-compressor package.json scripts point to real files", () => {
  const pluginDir = "plugins/context-compressor";
  const pkg = readJson(`${pluginDir}/package.json`);

  const problems = [];
  for (const [scriptName, command] of Object.entries(pkg.scripts || {})) {
    const match = /(?:node|python3?)\s+(\S+\.(?:cjs|js|py))/.exec(command);
    if (!match) continue;
    if (!fileExists(`${pluginDir}/${match[1]}`)) {
      problems.push(`${scriptName}: ${match[1]} fehlt`);
    }
  }

  assert.deepEqual(problems, [], `package.json scripts:\n${problems.join("\n")}`);
});

test("setup scripts verify plugin content, not just the directory", () => {
  // Ein Git-Link-Verzeichnis existiert auch ohne Inhalt - ein reiner
  // `-d`-Check haette den fehlenden Plugin-Code nie bemerkt.
  const requirements = {
    "install-commands.sh": ["commands/openai-cli.cjs", "commands/gemini-cli.cjs"],
    "reload-plugins.sh": ["commands/openai-cli.cjs", "commands/gemini-cli.cjs"],
    "verify-commands.sh": ["commands/openai-cli.cjs"],
    "upgrade-to-circuit-breaker.sh": ["openai-cli-improved.cjs"],
  };

  const problems = [];
  for (const [rel, needles] of Object.entries(requirements)) {
    const text = fs.readFileSync(path.join(repoRoot, rel), "utf8");
    for (const needle of needles) {
      if (!text.includes(needle)) {
        problems.push(`${rel}: prüft ${needle} nicht`);
      }
    }
  }

  assert.deepEqual(problems, [], problems.join("\n"));
});
