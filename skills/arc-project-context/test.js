'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'arc-project-context-'));
const skill = path.join(__dirname, 'index.js');
const write = (name, value) => {
  const file = path.join(root, name);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, value, 'utf8');
};
const call = (tool, input) => {
  const proc = spawnSync(process.execPath, [skill, tool], { input: JSON.stringify(input), encoding: 'utf8' });
  assert.strictEqual(proc.status, 0, proc.stderr || proc.stdout);
  return JSON.parse(proc.stdout);
};

write('src/main.js', `${'const first = 1;\n'.repeat(30)}const final = 3;\n`);
write('src/routes/home.js', 'route');
write('package.json', '{}');
write('node_modules/noise.js', 'noise');
write('dist/noise.js', 'noise');

const firstMap = call('project_map', { workspace_root: root });
assert.strictEqual(firstMap.cache_hit, false);
assert.ok(firstMap.project_map_hash);
assert.ok(firstMap.files.some((item) => item.path === 'src/main.js'));
assert.ok(!firstMap.files.some((item) => item.path.includes('node_modules')));
const secondMap = call('project_map', { workspace_root: root });
assert.strictEqual(secondMap.cache_hit, true);
assert.strictEqual(secondMap.project_map_hash, firstMap.project_map_hash);

const firstRead = call('source_read', { workspace_root: root, path: 'src/main.js', max_chars: 256 });
assert.strictEqual(firstRead.cache_hit, false);
assert.strictEqual(firstRead.truncated, true);
assert.ok(firstRead.omitted.chars > 0);
const secondRead = call('source_read', { workspace_root: root, path: 'src/main.js', max_chars: 256 });
assert.strictEqual(secondRead.cache_hit, true);
assert.strictEqual(secondRead.sha256, firstRead.sha256);

write('src/main.js', 'const changed = true;\n');
const changedRead = call('source_read', { workspace_root: root, path: 'src/main.js', max_chars: 12000 });
assert.strictEqual(changedRead.cache_hit, false);
assert.notStrictEqual(changedRead.sha256, firstRead.sha256);

const escaped = spawnSync(process.execPath, [skill, 'source_read'], {
  input: JSON.stringify({ workspace_root: root, path: '../outside.txt' }), encoding: 'utf8'
});
assert.notStrictEqual(escaped.status, 0);
assert.match(escaped.stdout, /outside|not found/);

console.log('arc-project-context: 8 assertions passed');
