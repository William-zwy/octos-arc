
# Stage 9 Evidence — ff7eaee7c526

## Confirmed

- Run `ff7eaee7c526`, task `hackathon--github-stage-1`, ended `FAILED`, score `0`, `0/30`.
- Generation exited normally in about 247 seconds, but the skeleton turn hit request budget 30 and was forced to finish; rehearsal repair hit request budget 10 and was also forced to finish.
- Deployment succeeded: frontend/backend were present, server started, and the template application was reachable on port 3000.
- The embedded Playwright report in the template ZIP records 30 failures: 28 timeouts in login/register/password-recovery UI paths and 2 failures because the navigation target `Acme Demo` was not found.
- `arc-project-context` was staged and loaded, but the final product still lacked the shared authentication/navigation surface.
- Submission `1e9d1b6074bd`; Agent ZIP SHA-256 `39880081A50C4C299AE36365269FFB0B02BDCB9A0B7A5D28E376584200A59F17`; Agent commit `3e858fc6bcc6535d7970623a3066ceb39764b67b`; requirements SHA `d5392c2c08f6e67b0de8640ba3d74333071e93ef9b3d15610d0b605f9ff7efd8`.

## Inferred

The strongest explanation is budget truncation combined with an incomplete-completion gate: the skeleton ended before the shared authentication and organization-navigation surface was implemented, the rehearsal repair was also cut short, and deployment readiness was treated as sufficient to continue. This is correlated evidence, not a single-variable causal proof.

The loaded skill improved context availability but cannot enforce completion. Deterministic Harness checks must own the decision to continue, mark a node implemented, or trigger bounded repair.

## Unknown

The terminal summary does not prove which exact files/routes were absent, whether `Acme Demo` was missing from the route table or only had an incorrect accessible name, or whether the repair turn observed the concrete failures. Those details require extracting `runner-events.jsonl`, `stdout.log`, checkpoints, and the final frontend files from `ff7eaee7c526-template.zip`.

## Corrective decision

P0 is not a larger global request cap. The next generic control should be:

```text
requirement compilation
→ skeleton
→ build/start/readiness
→ shared-surface smoke derived from the contract
→ one bounded targeted repair on failure
→ checkpoint and dependency blocking on repeated cap-hit
→ feature/vertical-slice execution
```

The smoke must derive route, role, and accessible name from the current requirement contract. It must not hardcode `Acme Demo`, login, or any Sheet-specific label. A passed smoke proves only that the public entry surface is present; it does not prove the full hidden suite.

## Priority changes

- P0: make request-budget exhaustion non-successful; require command/evidence-backed completion; run shared-surface smoke before feature expansion.
- P1: add contract-derived authentication/navigation entry checks and one visible next-state assertion; preserve `passed/failed/unknown` semantics.
- P1: record embedded template ZIP reports and runtime logs as post-run evidence sources.
- P2: add vertical-slice smoke for persistence, refresh/reopen, and error atomicity.
