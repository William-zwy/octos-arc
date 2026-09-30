---
name: arc-project-context
description: Build a compact project map and cached source excerpts for agent work, avoiding repeated scans and duplicate file reads without assuming a particular domain.
---

# ARC Project Context

Use this skill when an agent needs to understand an unfamiliar workspace or
re-read source/spec files during an iterative run. It provides two bounded
tools:

- `project_map`: enumerate a compact, stable map of project files and likely
  entry points.
- `source_read`: read a line-bounded excerpt and cache it by file SHA, range,
  and size limit.

The tools are deliberately domain-neutral. Do not encode task names, entity
names, requirement IDs, locators, or a particular frontend/backend framework
in calls or assumptions.

## Use and boundaries

Call `project_map` once near the start of a run, then reuse its returned paths.
Call `source_read` for a targeted range instead of repeatedly loading an entire
file. The tool returns a short excerpt, a SHA-256 fingerprint, cache status,
and omitted-range metadata. A changed file automatically invalidates old
entries.

The cache is stored under `<workspace>/.arc/context-cache/`. It contains only
derived metadata and excerpts; it is not a source-of-truth for implementation
state. Do not use this skill for quota decisions, checkpoints, budget ledgers,
repair termination, official-test verdicts, or cross-machine resume. Those
controls belong to the runtime.

Never ask this skill to dump a full transcript or an unbounded file. Keep the
returned context small and follow the caller's token budget.

## Protocol

The entrypoint is `index.js`. Pass the tool name as argv[2] and one JSON object
on stdin. The result is one JSON line; `output` contains the compact JSON
payload for hosts that expect the standard skill protocol.

```text
node skills/arc-project-context/index.js project_map < input.json
node skills/arc-project-context/index.js source_read < input.json
```

`workspace_root` may be absolute or relative to the process working directory.
`source_read.path` may be absolute or workspace-relative, but paths outside the
workspace (including symlinks resolving outside it) are rejected.
