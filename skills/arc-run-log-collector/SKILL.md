---
name: arc-run-log-collector
description: Collect all logs (generated code + error-cause analysis) after an ARC-Bench run, organized under skill-output/ with local/cloud separation.
version: 1.0.0
author: octos
---

# ARC Run Log Collector

Collect and classify every log produced by an ARC-Bench agent run — the generated
code, the acceptance/traceability events, the LLM usage, and the error causes —
into a single organized bundle under `skill-output/`.

## When to use

After any ARC-Bench run, local or cloud:

- Local runs (this machine): `arc/arc-output/<run-name>/` (e.g. `try1`, `dice1`)
- Cloud runs (platform archives): `evidence/arc-bench/runs/<run-id>/`

## Tool

You have a `log_collect` tool (Node.js, `index.js` in this skill dir). It reads
one JSON object from stdin and returns JSON on stdout:

```
stdin:  {"run_dir": "arc/arc-output/dice1", "source": "local", "run_name": "dice1", "run_log": "dice1-run.log"}
stdout: {"ok": true, "output_dir": "...", "collected": {...}, "analysis": {...}}
```

### Parameters

| Field | Required | Description |
|---|---|---|
| `run_dir` | Yes | Absolute path to the run workspace (contains `.arc/`, `frontend/`, `backend/`) |
| `source` | Yes | `"local"` for this machine's runs, `"cloud"` for platform archives |
| `run_name` | No | Output folder name (default: the run_dir's directory name) |
| `run_log` | No | Absolute path to the captured stdout log of the run (used for error-cause analysis) |
| `output_base` | No | Root for collected bundles (default: `$env:ARC_SKILL_OUTPUT` or the `skill-output/` dir beside `arc-output/`) |

## Output layout (classification rules — keep exactly)

Collected bundles go under `skill-output/` with **local and cloud runs kept in
separate trees**:

```
<output_base>/skill-output/
  local/<run_name>/            # source=local  (this machine's arc/arc-output runs)
  cloud/<run_name>/            # source=cloud  (platform evidence/arc-bench runs)
```

Each bundle contains:

```
<run_name>/
  logs/                        # raw logs, verbatim copies
    octos-events.jsonl         # octos session events
    runner-events.jsonl        # five-step closed-loop events
    llm-usage.jsonl            # per-request usage (tokens/cost basis)
    traceability/              # node_states, requirements, scenarios, tests
    run.log                    # stdout log of the run (when run_log given)
  code/                        # generated application code snapshot
    frontend/                  # copy of frontend sources (src/, package.json)
    backend/                   # copy of backend sources
  analysis/                    # classified analysis (the deliverable)
    summary.md                 # human-readable run summary
    generated-code.json        # per-node generated files (path, bytes, mtime, node)
    error-analysis.json        # error causes classified by category/round/node
```

## Analysis rules

1. **Generated code**: enumerate `frontend/` and `backend/` source files; attach
   each to its requirement node when the git log / events identify one; record
   path, bytes and mtime.
2. **Error classification**: scan `runner-events.jsonl` and the optional run log
   for acceptance failures; classify each failure by cause category
   (`build`, `startup`, `playwright-timeout`, `locator`, `assertion`, `infrastructure`,
   `api`, `other`) and attach node id, round and the observed message.
3. **Verdict**: read the terminal `runner_state` (e.g. `completed: all
   requirement nodes implemented and verified`) and each node's `test` phase
   status; report the pass/fail matrix.
4. **Usage**: sum `llm-usage.jsonl` (requests, prompt/completion tokens).
5. **Git**: capture `git log --oneline` of the run workspace as the commit chain.

## Best practices

- Prefer `source=local` + `run_name` matching the `--name` used with
  `run-task-local.py` so local and cloud bundles never collide.
- Pass `run_log` when available (e.g. the `Tee-Object`-captured stdout) — the
  error classification is far richer with it.
- Never modify the run workspace; the tool only reads and copies.
