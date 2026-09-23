#!/usr/bin/env node
'use strict';
/* ARC Run Log Collector — collect & classify all logs of an ARC-Bench run.
 * stdin : {run_dir, source, run_name?, run_log?, output_base?}
 * stdout: {ok, output_dir, collected, analysis}   (single JSON line)
 * Never modifies the run workspace; only reads and copies. */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const EXCLUDED = /node_modules|\\dist\\|^dist$|\.git|__pycache__|skill-output/;

function err(msg) { console.log(JSON.stringify({ ok: false, error: msg })); process.exit(1); }

function readLines(file) {
  try { return fs.readFileSync(file, 'utf8').split(/\r?\n/).filter(Boolean); }
  catch { return []; }
}
function readJsonl(file) {
  const out = [];
  for (const line of readLines(file)) {
    try { out.push(JSON.parse(line)); } catch { /* skip malformed */ }
  }
  return out;
}
function copyTree(src, dst) {
  if (!fs.existsSync(src)) return 0;
  let n = 0;
  fs.mkdirSync(dst, { recursive: true });
  for (const ent of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, ent.name), d = path.join(dst, ent.name);
    if (EXCLUDED.test(ent.name)) continue;
    if (ent.isDirectory()) n += copyTree(s, d);
    else { fs.mkdirSync(path.dirname(d), { recursive: true }); fs.copyFileSync(s, d); n++; }
  }
  return n;
}
function copyFile(src, dst) {
  if (!fs.existsSync(src)) return false;
  fs.mkdirSync(path.dirname(dst), { recursive: true });
  fs.copyFileSync(src, dst);
  return true;
}
function gitLog(cwd) {
  try {
    const top = execSync('git rev-parse --show-toplevel', { cwd, encoding: 'utf8', windowsHide: true }).trim();
    if (path.resolve(top) !== path.resolve(cwd)) return []; // only when the run workspace IS the repo root
    return execSync('git log --oneline -30', { cwd, encoding: 'utf8', windowsHide: true }).split(/\r?\n/).filter(Boolean);
  } catch { return []; }
}
function classifyError(text) {
  const t = String(text || '');
  const rules = [
    ['build', /npm run build|failed to build|build error|ERR!|Module not found|SyntaxError|Unable to resolve|build failed/i],
    ['startup', /npm start|EADDRINUSE|EACCES|cannot find module|require is not defined|server\.listen|started|startup|rehearsal/i],
    ['playwright-timeout', /timeout|timed out|TimeoutError|waited long|not stable/i],
    ['locator', /locator|strict mode|resolved to \d+ elements|getByRole|getByLabel|getByText|multiple elements|no element/i],
    ['assertion', /expect\(|toEqual|toBe|toHaveText|Expected|Received|assertion/i],
    ['api', /\/api\/|fetch|429|401|403|502|503|rate limit|unauthorized|proxy/i],
    ['infrastructure', /infrastructure error|WinError|Traceback|OSError|PermissionError|ENOENT|E2BIG/i],
  ];
  for (const [cat, re] of rules) if (re.test(t)) return cat;
  return 'other';
}

function main() {
  let input = {};
  try {
    const arg = process.argv[2];
    if (arg) {
      input = JSON.parse(fs.existsSync(arg)
        ? fs.readFileSync(arg, 'utf8').replace(/^\uFEFF/, '')
        : arg);
    } else {
      input = JSON.parse(fs.readFileSync(0, 'utf8').replace(/^\uFEFF/, ''));
    }
  } catch { err('stdin or argv[2] must be one JSON object'); }
  let finalVerdict = null, finalMessage = '';
  const runDir = path.resolve(input.run_dir || '');
  const source = input.source === 'cloud' ? 'cloud' : 'local';
  const runName = input.run_name || path.basename(runDir);
  const runLog = input.run_log ? path.resolve(input.run_log) : null;
  const outputBase = path.resolve(input.output_base || process.env.ARC_SKILL_OUTPUT || path.resolve(runDir, '..', '..', 'skill-output'));

  if (!fs.existsSync(runDir)) err(`run_dir not found: ${runDir}`);

  const bundle = path.join(outputBase, source, runName);
  const logsDir = path.join(bundle, 'logs');
  const codeDir = path.join(bundle, 'code');
  const anaDir = path.join(bundle, 'analysis');

  /* ---- collect raw logs ---- */
  const collected = { files: 0, dirs: [] };
  const arcDir = path.join(runDir, '.arc');
  const copies = [
    [path.join(arcDir, 'octos-events.jsonl'), path.join(logsDir, 'octos-events.jsonl')],
    [path.join(arcDir, 'runner-events.jsonl'), path.join(logsDir, 'runner-events.jsonl')],
    [path.join(arcDir, 'llm-usage.jsonl'), path.join(logsDir, 'llm-usage.jsonl')],
  ];
  for (const [s, d] of copies) if (copyFile(s, d)) collected.files++;
  if (fs.existsSync(path.join(arcDir, 'traceability'))) {
    collected.files += copyTree(path.join(arcDir, 'traceability'), path.join(logsDir, 'traceability'));
    collected.dirs.push('traceability');
  }
  if (runLog && copyFile(runLog, path.join(logsDir, 'run.log'))) collected.files++;
  if (source === 'cloud') {
    /* platform archives (evidence/arc-bench/runs/<id>) hold diagnostic/handoff
       files instead of a workspace: snapshot the whole archive as logs. */
    for (const ent of fs.readdirSync(runDir, { withFileTypes: true })) {
      if (EXCLUDED.test(ent.name) || ent.name === '.arc') continue;
      const s = path.join(runDir, ent.name), d = path.join(logsDir, ent.name);
      if (ent.isDirectory()) collected.files += copyTree(s, d);
      else { fs.mkdirSync(path.dirname(d), { recursive: true }); fs.copyFileSync(s, d); collected.files++; }
    }
    const pr = path.join(runDir, 'phase4-result.json');
    if (fs.existsSync(pr)) {
      try {
        const j = JSON.parse(fs.readFileSync(pr, 'utf8'));
        finalVerdict = j.PHASE4_RESULT || j.status || j.state || finalVerdict;
        const taskPart = j.task_key ? `task=${j.task_key}` : '';
        const runPart = j.run_id ? `run_id=${j.run_id}` : '';
        finalMessage = [taskPart, runPart, j.summary || j.message || ''].filter(Boolean).join('; ') || finalMessage;
      } catch { /* keep defaults */ }
    }
  }
  for (const part of ['frontend', 'backend']) {
    const n = copyTree(path.join(runDir, part), path.join(codeDir, part));
    if (n > 0) { collected.files += n; collected.dirs.push(part); }
  }
  collected.dirs.push('logs', 'analysis', 'code');

  /* ---- analysis: events ---- */
  const events = readJsonl(path.join(arcDir, 'runner-events.jsonl'));
  const nodes = {};
  for (const ev of events) {
    if (ev.type === 'runner_state') { finalVerdict = ev.state; finalMessage = ev.message || ''; }
    if (ev.type === 'requirement_state' && ev.node_id) {
      const k = String(ev.node_id);
      nodes[k] = nodes[k] || {};
      if (ev.phase && ev.status) nodes[k][ev.phase] = { status: ev.status, message: ev.message || '', ts: ev.timestamp || '' };
    }
  }
  const nodeSummary = Object.entries(nodes).map(([id, s]) => ({
    node: id,
    design: s.design?.status || null,
    implement: s.implement?.status || null,
    test: s.test?.status || null,
    testMessage: s.test?.message || '',
  }));

  /* ---- analysis: usage ---- */
  const usage = { requests: 0, prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 };
  for (const rec of readJsonl(path.join(arcDir, 'llm-usage.jsonl'))) {
    usage.requests++;
    usage.prompt_tokens += rec.prompt_tokens || 0;
    usage.completion_tokens += rec.completion_tokens || 0;
    usage.total_tokens += rec.total_tokens || 0;
  }

  /* ---- analysis: generated code ---- */
  const codeFiles = [];
  for (const part of ['frontend', 'backend']) {
    const root = path.join(runDir, part);
    if (!fs.existsSync(root)) continue;
    const walk = (dir, rel) => {
      for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
        if (EXCLUDED.test(ent.name)) continue;
        const s = path.join(dir, ent.name), r = path.join(rel, ent.name);
        if (ent.isDirectory()) walk(s, r);
        else { const st = fs.statSync(s); codeFiles.push({ file: r.replace(/\\/g, '/'), bytes: st.size, mtime: st.mtime.toISOString() }); }
      }
    };
    walk(root, part);
  }
  codeFiles.sort((a, b) => a.file.localeCompare(b.file));

  /* ---- analysis: git chain ---- */
  const commits = gitLog(runDir);

  /* ---- analysis: errors ---- */
  const errorEvents = [];
  for (const ev of events) {
    if (ev.type === 'requirement_state' && ev.phase === 'test' && ev.status === 'failed' && ev.message) {
      errorEvents.push({ node: String(ev.node_id), phase: 'test', round: null, message: String(ev.message).slice(0, 400), ts: ev.timestamp || '' });
    }
  }
  const runLogLines = runLog ? readLines(runLog) : [];
  for (let i = 0; i < runLogLines.length; i++) {
    const line = runLogLines[i];
    const acc = line.match(/\[acceptance\]\s+(\S+)\s+round\s+(\d+):\s+(\d+)\/(\d+)/);
    if (acc) {
      if (Number(acc[3]) < Number(acc[4])) {
        errorEvents.push({ node: acc[1], phase: 'acceptance', round: Number(acc[2]), message: `${acc[3]}/${acc[4]} passed`, ts: '' });
      }
      continue;
    }
    const m = line.match(/\[(?:acceptance|flow)\]\s+.*?(infrastructure error|failed|FAILED|Traceback|Error|WinError|Timeout|OOM|killed)[^|]{0,300}/i);
    if (m && /acceptance|flow|postflight|guard/.test(line)) {
      errorEvents.push({ node: null, phase: 'run', round: null, message: line.slice(0, 400), ts: '' });
    }
  }
  const classified = errorEvents.map((e) => ({ ...e, category: classifyError(e.message) }));
  const byCategory = {};
  for (const e of classified) { byCategory[e.category] = (byCategory[e.category] || 0) + 1; }

  /* ---- analysis: summary.md ---- */
  const lines = [];
  lines.push(`# Run Log Summary — ${runName}`);
  lines.push('');
  lines.push(`- source: **${source}** (bundle: ${path.join(outputBase, source, runName)})`);
  lines.push(`- run workspace: ${runDir}`);
  lines.push(`- final runner state: **${finalVerdict}**${finalMessage ? ' — ' + finalMessage : ''}`);
  lines.push(`- LLM usage: ${usage.requests} request(s), ${usage.prompt_tokens} prompt / ${usage.completion_tokens} completion = ${usage.total_tokens} tokens`);
  lines.push(`- generated files: ${codeFiles.length}`);
  lines.push(`- commits: ${commits.length ? commits[0] : '(none)'}`);
  lines.push('');
  lines.push('## Node verdicts');
  lines.push('');
  if (nodeSummary.length) {
    lines.push('| node | design | implement | test |');
    lines.push('|---|---|---|---|');
    for (const n of nodeSummary) lines.push(`| ${n.node} | ${n.design || '-'} | ${n.implement || '-'} | ${n.test || '-'} |`);
  } else lines.push('(no per-node requirement_state events found)');
  lines.push('');
  lines.push('## Errors by category');
  lines.push('');
  if (Object.keys(byCategory).length) {
    lines.push('| category | count |');
    lines.push('|---|---|');
    for (const [c, n] of Object.entries(byCategory).sort((a, b) => b[1] - a[1])) lines.push(`| ${c} | ${n} |`);
    lines.push('');
    lines.push('### Details');
    lines.push('');
    for (const e of classified) lines.push(`- [${e.category}] ${e.node || 'run'}${e.round !== null ? ` r${e.round}` : ''}: ${e.message.slice(0, 200)}`);
  } else lines.push('(no errors classified)');
  lines.push('');
  lines.push('## Commit chain');
  lines.push('');
  for (const c of commits) lines.push(`- \`${c}\``);
  const summaryMd = lines.join('\n');

  fs.mkdirSync(anaDir, { recursive: true });
  fs.writeFileSync(path.join(anaDir, 'summary.md'), summaryMd, 'utf8');
  fs.writeFileSync(path.join(anaDir, 'generated-code.json'), JSON.stringify({ run: runName, source, files: codeFiles }, null, 2), 'utf8');
  fs.writeFileSync(path.join(anaDir, 'error-analysis.json'), JSON.stringify({ run: runName, source, by_category: byCategory, errors: classified }, null, 2), 'utf8');

  console.log(JSON.stringify({
    ok: true,
    output_dir: bundle,
    collected,
    analysis: {
      final_verdict: finalVerdict,
      final_message: finalMessage,
      nodes: nodeSummary,
      usage,
      code_files: codeFiles.length,
      errors: classified.length,
      by_category: byCategory,
      commits: commits.length,
    },
  }));
}

main();
