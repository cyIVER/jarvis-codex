# Remotion Review Gate

Remotion is a local-only review asset path under `video/remotion`. It is isolated from the Python package and is used to generate local walkthrough assets for review, not hosted publishing or runtime execution.

## Current Scaffold

- Dependencies are pinned and project-local in `video/remotion/package.json` and `video/remotion/package-lock.json`.
- Generated videos, frames, browser caches, and temporary render artifacts stay outside Git through `video/remotion/.gitignore`.
- The default composition is `JarvisCodexPlan`.
- Docker and GPU paths are optional and approval-gated.
- `npm run studio`, `npm run still`, `npm run render`, `npm run render:gpu`, and Docker Compose commands must be treated as explicit local runtime commands, not ambient agent permissions.

## Candidate Assets

| Asset | Purpose | Gate |
| --- | --- | --- |
| Short plan walkthrough | Show the current Jarvis Codex operating loop | Local-only render approval |
| Lane reconciliation clip | Explain planning-lane states | Local-only render approval; lane mutation remains separately gated |
| Hardware boundary clip | Show CUDA/NPU/Docker routing | Runtime execution approval before any GPU or Docker command |

## Acceptance Checks

- `npm ci` installs from the lockfile.
- `npm run typecheck` passes.
- `npm audit --audit-level=high` reports no high or critical vulnerabilities.
- `npm run still` and `npm run render` write only under ignored `video/remotion/out/`.
- `tests/test_remotion_scaffold.py` confirms private/local package settings, deterministic Docker install, ignored outputs, approval-gated docs, and current planning-lane copy.
- No hosted publish path is added without explicit approval.
