#!/usr/bin/env node
'use strict';

/*
 * Project context helper. It only reads workspace files and writes a small
 * derived cache under .arc/context-cache; it never executes project code.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const CACHE_DIR_NAME = path.join('.arc', 'context-cache');
const CACHE_FILE = 'cache.json';
const SKIP_DIRS = new Set([
  '.git', '.hg', '.svn', '.arc', 'node_modules', 'dist', 'build', 'coverage',
  '.next', '.nuxt', 'target', '__pycache__', '.pytest_cache', 'skill-output',
  'context-cache'
]);
const DEFAULT_MAX_FILES = 2000;
const DEFAULT_MAX_CHARS = 12000;
const MAX_MAX_CHARS = 60000;

function fail(message) {
  process.stdout.write(JSON.stringify({ ok: false, success: false, error: String(message) }) + '\n');
  process.exitCode = 1;
}

function hashBuffer(value) {
  return crypto.createHash('sha256').update(value).digest('hex');
}

function hashText(value) {
  return hashBuffer(Buffer.from(value, 'utf8'));
}

function jsonStable(value) {
  return JSON.stringify(value);
}

function output(tool, result) {
  const payload = { ok: true, success: true, tool, ...result };
  payload.output = JSON.stringify(result);
  process.stdout.write(JSON.stringify(payload) + '\n');
}

function readInput() {
  try {
    const raw = fs.readFileSync(0, 'utf8').replace(/^\uFEFF/, '');
    return JSON.parse(raw || '{}');
  } catch (err) {
    throw new Error(`stdin must contain one JSON object: ${err.message}`);
  }
}

function resolveRoot(input) {
  const root = path.resolve(String(input.workspace_root || input.root || process.cwd()));
  if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
    throw new Error(`workspace_root is not a directory: ${root}`);
  }
  return fs.realpathSync(root);
}

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative));
}

function resolveFile(root, requested) {
  if (!requested) throw new Error('path is required');
  const candidate = path.resolve(root, String(requested));
  if (!fs.existsSync(candidate)) throw new Error(`file not found: ${requested}`);
  const realRoot = fs.realpathSync(root);
  const realFile = fs.realpathSync(candidate);
  if (!isWithin(realRoot, realFile)) throw new Error('path resolves outside workspace_root');
  const stat = fs.statSync(realFile);
  if (!stat.isFile()) throw new Error(`path is not a regular file: ${requested}`);
  return { realRoot, realFile, stat };
}

function rel(root, file) {
  return path.relative(root, file).replace(/\\/g, '/');
}

function statFingerprint(stat) {
  return { size: stat.size, mtime_ns: stat.mtimeNs ? String(stat.mtimeNs) : String(Math.floor(stat.mtimeMs * 1e6)) };
}

function cachePath(root) {
  return path.join(root, CACHE_DIR_NAME, CACHE_FILE);
}

function loadCache(root) {
  const file = cachePath(root);
  try {
    const parsed = JSON.parse(fs.readFileSync(file, 'utf8'));
    if (parsed && parsed.version === 1) return parsed;
  } catch (_) { /* cache is advisory; rebuild it when malformed or absent */ }
  return { version: 1, reads: {}, maps: {} };
}

function saveCache(root, cache) {
  const dir = path.dirname(cachePath(root));
  fs.mkdirSync(dir, { recursive: true });
  const target = cachePath(root);
  const temporary = `${target}.${process.pid}.${Date.now()}.tmp`;
  fs.writeFileSync(temporary, JSON.stringify(cache), 'utf8');
  fs.renameSync(temporary, target);
}

function isSkipped(name) {
  return SKIP_DIRS.has(name.toLowerCase());
}

function collectMap(root, maxFiles) {
  const files = [];
  const dirs = [];
  const walk = (directory) => {
    let entries;
    try { entries = fs.readdirSync(directory, { withFileTypes: true }); }
    catch (_) { return; }
    let directoryStat;
    try { directoryStat = fs.statSync(directory); } catch (_) { return; }
    dirs.push({ path: rel(root, directory), ...statFingerprint(directoryStat) });
    entries.sort((a, b) => a.name.localeCompare(b.name));
    for (const entry of entries) {
      if (entry.isDirectory()) {
        if (!isSkipped(entry.name)) walk(path.join(directory, entry.name));
        continue;
      }
      if (!entry.isFile() || files.length >= maxFiles) continue;
      const file = path.join(directory, entry.name);
      try {
        const stat = fs.statSync(file);
        files.push({ path: rel(root, file), ...statFingerprint(stat) });
      } catch (_) { /* a concurrent deletion is simply absent from this map */ }
    }
  };
  walk(root);
  files.sort((a, b) => a.path.localeCompare(b.path));
  dirs.sort((a, b) => a.path.localeCompare(b.path));

  const entrypoints = files.filter((item) => /(^|\/)(index|main|app|server|start|cli)\.(js|cjs|mjs|ts|tsx|jsx|py|rs|go|java|rb|php)$/i.test(item.path)).map((item) => item.path);
  const manifests = files.filter((item) => /(^|\/)(package\.json|pyproject\.toml|cargo\.toml|requirements\.txt|dockerfile|compose\.ya?ml|manifest\.json|go\.mod)$/i.test(item.path)).map((item) => item.path);
  const routeHints = files.filter((item) => /(^|\/)(routes?|api|controllers?|pages?|views?)(\/|\.|$)/i.test(item.path)).map((item) => item.path).slice(0, 100);
  const modelHints = files.filter((item) => /(model|schema|migration|fixture|seed|database|store)/i.test(item.path)).map((item) => item.path).slice(0, 100);
  const truncated = files.length >= maxFiles;
  const map = { files, dirs, entrypoints, manifests, route_hints: routeHints, model_hints: modelHints, files_truncated: truncated };
  // The cache directory is created after the first scan, so root mtime alone
  // cannot be used for validation. Keep a cheap root-entry signature instead.
  map.root_entries = fs.readdirSync(root, { withFileTypes: true })
    .filter((entry) => !isSkipped(entry.name))
    .map((entry) => `${entry.name}:${entry.isDirectory() ? 'd' : 'f'}`)
    .sort();
  const projectMapHash = hashText(jsonStable(map));
  return { ...map, project_map_hash: projectMapHash };
}

function mapStillValid(root, cached) {
  if (!cached || !Array.isArray(cached.files) || !Array.isArray(cached.dirs)) return false;
  for (const item of cached.dirs) {
    if (!item.path) continue; // root mtime changes when the cache directory is created
    const directory = item.path ? path.join(root, item.path) : root;
    try {
      const stat = fs.statSync(directory);
      const current = statFingerprint(stat);
      if (current.size !== item.size || current.mtime_ns !== item.mtime_ns) return false;
    } catch (_) { return false; }
  }
  const currentRootEntries = fs.readdirSync(root, { withFileTypes: true })
    .filter((entry) => !isSkipped(entry.name))
    .map((entry) => `${entry.name}:${entry.isDirectory() ? 'd' : 'f'}`)
    .sort();
  if (JSON.stringify(currentRootEntries) !== JSON.stringify(cached.root_entries || [])) return false;
  for (const item of cached.files) {
    try {
      const current = statFingerprint(fs.statSync(path.join(root, item.path)));
      if (current.size !== item.size || current.mtime_ns !== item.mtime_ns) return false;
    } catch (_) { return false; }
  }
  return true;
}

function projectMap(input) {
  const root = resolveRoot(input);
  const requestedMax = Number.isInteger(input.max_files) ? input.max_files : DEFAULT_MAX_FILES;
  const maxFiles = Math.max(1, Math.min(10000, requestedMax));
  const cache = loadCache(root);
  const key = `${root}|${maxFiles}`;
  const cached = cache.maps[key];
  if (cached && mapStillValid(root, cached)) {
    return { workspace_root: root, cache_hit: true, ...cached };
  }
  const map = collectMap(root, maxFiles);
  cache.maps[key] = map;
  saveCache(root, cache);
  return { workspace_root: root, cache_hit: false, ...map };
}

function omittedFor(lines, startLine, firstIncluded, lastIncluded, totalChars, maxChars) {
  const omittedLines = [];
  const omittedStart = firstIncluded + (lastIncluded < lines.length ? 1 : 0);
  if (omittedStart <= lines.length) omittedLines.push({ start: startLine + omittedStart - 1, end: startLine + lines.length - 1 });
  return {
    lines: omittedLines,
    chars: Math.max(0, totalChars - maxChars),
    reason: totalChars > maxChars ? 'max_chars' : null
  };
}

function sourceRead(input) {
  const root = resolveRoot(input);
  const target = resolveFile(root, input.path);
  const content = fs.readFileSync(target.realFile, 'utf8');
  const sha256 = hashText(content);
  const allLines = content.split(/\r?\n/);
  const startLine = Math.max(1, Number.isInteger(input.start_line) ? input.start_line : 1);
  const requestedEnd = Number.isInteger(input.end_line) ? input.end_line : allLines.length;
  const endLine = Math.max(startLine, Math.min(allLines.length, requestedEnd));
  const maxChars = Math.max(256, Math.min(MAX_MAX_CHARS, Number.isInteger(input.max_chars) ? input.max_chars : DEFAULT_MAX_CHARS));
  const cache = loadCache(root);
  const key = `${rel(root, target.realFile)}|${sha256}|${startLine}|${endLine}|${maxChars}`;
  const cached = cache.reads[key];
  if (cached) return { workspace_root: root, path: rel(root, target.realFile), sha256, cache_hit: true, ...cached };

  const selected = allLines.slice(startLine - 1, endLine);
  const selectedText = selected.join('\n');
  const excerpt = selectedText.length > maxChars ? selectedText.slice(0, maxChars) : selectedText;
  let includedLines = selected.length;
  if (selectedText.length > maxChars) {
    const prefix = selectedText.slice(0, maxChars);
    includedLines = prefix.split('\n').length;
  }
  const result = {
    total_lines: allLines.length,
    requested_line_range: { start: startLine, end: endLine },
    returned_line_range: { start: startLine, end: startLine + includedLines - 1 },
    excerpt,
    truncated: selectedText.length > maxChars,
    omitted: omittedFor(selected, startLine, 1, includedLines, selectedText.length, maxChars)
  };
  cache.reads[key] = result;
  saveCache(root, cache);
  return { workspace_root: root, path: rel(root, target.realFile), sha256, cache_hit: false, ...result };
}

function main() {
  try {
    const tool = process.argv[2];
    const input = readInput();
    if (tool === 'project_map') output(tool, projectMap(input));
    else if (tool === 'source_read') output(tool, sourceRead(input));
    else throw new Error(`unknown tool: ${tool || '(missing)'}`);
  } catch (err) {
    fail(err.message || err);
  }
}

main();
