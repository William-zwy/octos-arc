# Stage 9 Evidence — e27e2a94d089 + ae836343d76a

## Confirmed evidence

### e27e2a94d089 — hackathon--sheet

- Result: `FAILED`, score `0`, `0/100`, feature `0/24`.
- Submission: `9243c227e8b4`; uploaded ZIP SHA-256: `07c1d0a529abb297aac3fd248848b0f82c0d54c48ac4d0cb193ebf901db16ffd`.
- Agent commit from identity log: `3dd11aa43893c3920e0d664ecfe75905674a69d9`.
- Requirements SHA: `b3f5f6a681f47085757dfd7309a8c535a0a431ddc9366b6e80d36bc5681987d9`.
- Generation completed, but guard forced-to-finish occurred 66 times; `REQ-4-1-2` had `wrote=False` and remained inconclusive.
- Deployment postflight passed.
- Template ZIP contains `.arc/playwright-report.json`; report stats are `unexpected=100`, `timedOut=100`, `failed=0`.
- Extracted failures are dominated by `getByRole('button', {name: 'New blank workbook'})` count `0`, with five click timeouts. This identifies a missing shared entry control, not a static-resource 404.

### ae836343d76a — hackathon--github-stage-1

- Result: `FAILED`; deployment readiness failed before tests, `0/0`.
- Submission: `9243c227e8b4`; uploaded ZIP is the same as e27.
- Agent commit from identity log: `f55492a05b672916561f1696a647238ac30a56e5`.
- Requirements SHA: `d5392c2c08f6e67b0de8640ba3d74333071e93ef9b3d15610d0b605f9ff7efd8`.
- Generation exited normally, but 42 guard forced-to-finish events occurred; 8 nodes exhausted request budget and several nodes had no deployable source change.
- Frontend build completed, but backend startup failed with `SyntaxError: Unexpected token ']'` at `backend/server.js:1722`; no official tests ran and no Playwright report exists.
- Template ZIP contains `.arc/run-identity.json`, `.arc/runner-events.jsonl`, and `.arc/stdout.log`, proving deployment evidence can be recovered from the bundle even when platform result endpoints are incomplete.

## Evidence boundaries

- e27's missing `New blank workbook` button is directly supported by the embedded report and template source; the causal contribution of the 66 budget truncations is strongly associated but not single-variable proof.
- ae836's syntax error is a confirmed deployment blocker. It is not an official test failure because tests never started.
- ZIP-embedded reports and runtime files must be inspected before declaring platform details unavailable.

## Branch recommendations

### Integration branch `codex/hkt-runtime-compat-3307814`

1. Keep requirement compilation and capability judge shadow-only.
2. Add a truthful-completion gate requiring recorded build, start, and request evidence before a slice can be accepted; `wrote=True` alone is insufficient.
3. Add a generic high-fanout entry smoke derived from the contract. It should validate the first visible action (for Sheet, `New blank workbook`) and core semantic surface, without hardcoding Sheet into the Agent.
4. On repeated budget exhaustion or `wrote=False`, write a checkpoint and prevent dependent slices from claiming completion; do not simply raise the global request cap.
5. Add syntax/start preflight that runs the generated backend before readiness polling and records the first parse error with file and line.

### Main branch `main`

1. Retain the static-asset closure gate already added for the dc failure mode.
2. Add template-bundle evidence extraction as a post-run analysis utility, separate from the Agent ZIP contract.
3. Add app-level smoke requirements: homepage, first task action, core route, and one visible semantic element; fail closed before advanced feature checks.
4. Keep generated-app validation separate from Agent packaging so task-specific UI requirements do not pollute the generic bundle contract.

## Priority

P0: syntax/start preflight; truthful command evidence; embedded report extraction; first-action semantic smoke.
P1: dependency-aware checkpointing after guard exhaustion; refresh/reopen and error atomicity smoke.
P2: broader capability scheduling and full requirement-only browser scenario generation.