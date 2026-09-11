# Octos ARC Runtime

Independent downstream repository for ARC coding experiments, established on 2026-09-10.
The original Octos and ARC adapter repositories remain unchanged. This repository preserves
their Git history; it is not a GitHub fork-network repository.

## Fixed starting point

- Octos repository: `octos-org/octos`
- Octos commit: `8558a3bff41f43838130808a1fa6cf0299e0bc40`
- Baseline tag: `arc-base-20260910`
- Cargo.lock SHA-256: `9761e8904a0949aa0cff189cdd75b6a5f0b00daf7c968a883cdf39786bbd3088`
- `main` contains the Octos source and downstream provenance documents.
- `legacy` preserves the existing adapter at `b0999c95f7875c8d4ff3e58e733fb2c5abc8caf7`,
  plus its original locally submitted ZIP and provenance.
- `legacy-adapter-20260910` names the preserved legacy snapshot.

The upstream README describes upstream capabilities, not completed ARC modifications.
At this checkpoint there are no kernel behavior changes, compiled downstream releases,
new ARC submissions, or new evaluation scores.

## Release and submission policy

`arc-runtime-lock.json` records the fixed source baseline. It is not yet a runnable
release manifest: build, model, and submission fields are deliberately null.
Do not submit this source-only checkpoint as a finished agent.

Before submitting a future modified runtime:

1. Record its full downstream source commit and exact build toolchain, target, and features.
2. Build with the committed Cargo.lock, then record each binary's SHA-256.
3. Publish a versioned artifact and record its URL and archive SHA-256.
4. Verify the downloaded bytes before execution; reject mismatches without fallback.
5. Record the actual model identifier, endpoint, generation settings, and execution budget.
   Credentials must come from the execution environment and must not enter Git.
6. Include the adapter source commit and this manifest in each submission's provenance.

Never use a `latest` release URL, a moving branch reference, or an unverified binary
from PATH as the selected ARC runtime. If the pinned artifact is unavailable, stop.
Changing a pin requires an explicit new version; do not silently replace an existing artifact.

## Repository isolation

GitHub Actions is disabled on this new repository. Inherited upstream workflows remain
in the source history but must not run upstream deployments or publish upstream packages.
Add and review a dedicated downstream build workflow before selectively enabling automation.

The `legacy` branch is historical reference only. Its old downloader and execution
behavior have intentionally not been modernized; it is not the new competition runtime.

## Next phase, not started

Use the official ARC Counter task first, then its Evolution task with the prior generated
project as input. Implement honest execution evidence and incremental changes before
building and submitting the fixed downstream runtime. Do not fabricate test results.
