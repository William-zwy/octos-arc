# Stage 9 Evidence — d69748b0603b

## Confirmed

- Run `d69748b0603b`, task `hackathon--sheet`, ended `FAILED`, score `0`, `0/100`, feature `0/24`.
- Agent commit: `3d93bcdb7c69b1c53b3100ecc0e92a390f08cc5c`.
- Agent ZIP SHA-256: `39880081A50C4C299AE36365269FFB0B02BDCB9A0B7A5D28E376584200A59F17`; submission `1e9d1b6074bd`.
- Requirements SHA: `b3f5f6a681f47085757dfd7309a8c535a0a431ddc9366b6e80d36bc5681987d9`.
- Generation exited, but skeleton hit request budget 30 and rehearsal repair 1/2 each hit request budget 10. Both repair attempts were truncated.
- Deployment succeeded: server started and was reachable on port 3000; no readiness failure was reported.
- The embedded Playwright report records `0/100`, all 100 tests timed out. Failure clusters were 95 missing `Create` buttons and 5 missing visible `Import CSV` dialogs.
- The same generic ZIP was reused across ff7 and d697; task identity and requirements differed, so the runs are not a clean budget-only experiment.
- `arc-project-context` was staged and loaded, but the observable Sheet UI remained incomplete.

## Inferred

The direct product failure is a missing shared Sheet surface, not deployment: the application was reachable, but the workbook workflow lacked the first high-fanout controls. The repeated budget truncation is a strong contributing factor because the run completed in roughly 386 seconds with low usage, but it is not proof of sole causality.

The ff7 and d697 results establish a cross-task invariant:

```text
server reachable != shared entry present != vertical user journey complete
```

The current smoke must therefore validate task-derived semantic entry controls after foundation readiness and before feature expansion. It must not hardcode `Create`, `Import CSV`, `New blank workbook`, or any other task label.

## Unknown

- Whether `Create` was absent from the DOM, rendered with a different accessible name, or never wired to a route.
- Whether `Import CSV` backend/API support existed independently of the missing dialog.
- Which exact nodes were truncated versus merely incomplete.
- Whether the rehearsal repair saw the embedded report and applied a targeted fix.

## Corrective priority

P0: fail closed on cap-hit/no-evidence completion; run contract-derived shared-surface smoke after build/start/readiness; write `.arc/shared-surface-smoke.json`; block dependent nodes on failure.

P1: add a minimal vertical Sheet contract check: entry action -> workbook/sheet state -> grid/formula surface -> visible result; keep it generic and derived from requirements.

P1: preserve embedded ZIP evidence extraction as the preferred fallback when platform report endpoints return no tests or 404.

P2: use bounded, targeted repair with a reserved validation budget instead of increasing the global request cap.
