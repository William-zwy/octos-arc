# Build Record: urgent-bookstack-contract-fix-r2-unverified

- Status: `platform_unverified`
- Build ID: `urgent-bookstack-contract-fix-r2-unverified`
- Built: 2026-09-29
- Source repository: `octos-p` (`git@github.com:William-zwy/octos-p.git`)
- Source branch: `codex/urgent-bookstack-contract-fix-r2`
- Source commit: `dc5a848d4b6a7d1775ffb360548649bdb9105608`
- Packaging script: `arc/pack.ps1` with its checked-in `$Inputs` allowlist; script exit code `0`
- ZIP: `octos-arc-bundle_urgent-bookstack-contract-fix-r2-platform-unverified.zip`
- ZIP size: `333727` bytes
- ZIP SHA-256: `9F8EE636363A5BCA75EA9E15E4403C83401965443EB0BC0941BBE6E09ADD890E`
- Shape check: `492` entries; required agent files at ZIP root; no `arc/` prefix, `__pycache__`, or `.pyc` entries; passed

## Verification

| Check | Result | Exit code |
|---|---:|---:|
| `python -m py_compile main.py tests/test_main_helpers.py` (`arc/`) | Passed | 0 |
| Targeted `CreateResultContractTests` + `WorkflowStateContractTests` | 10/10 passed | 0 |
| `node tests/ui_scope_locator_regression.cjs` with system Chrome `154.0.8037.58` and preinstalled Playwright | Passed against synthetic DOM only | 0 |
| `python -m unittest discover -s tests` (`arc/`) | 101 tests; 3 failures + 1 error | 1 |
| `git diff --check` | Passed | 0 |

The full-suite failures match the recorded Windows baseline shape: npm cache path assertion, two POSIX path-separator assertions, and a temporary `.git/objects` permission error during test cleanup. The recorded pre-change suite had 97 tests with the same 3 failures + 1 error; no new failing test was observed.

This build record and synthetic-DOM smoke do not establish behavior in an Agent-generated application. No official platform upload or Run was performed. Platform ZIP/build/task-snapshot identity and score impact remain unverified.
