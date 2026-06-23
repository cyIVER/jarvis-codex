# Product Readiness Review

This review applies the PM command-library discovery, prioritization, and roadmap workflow to the current Jarvis Codex platform state.

## Product Outcome

Jarvis Codex should be a local-first operating layer for Codex work that preserves continuity, exposes review surfaces, and keeps side effects behind explicit gates.

## Target Users

- Primary: the local operator coordinating Codex, Worktrunk, state, and review workflows from WSL.
- Secondary: future specialist agents that need deterministic context, routing, and acceptance gates before acting.

## Current Release Slice

The current release is a governed local operating substrate:

- state, memory, approval, handoff, hardware, doctor, and plan-viewer CLI surfaces
- project-local Codex governance agents and skills
- portable governance validator and `doctor --governance`
- read-only doctor inspection
- local plan viewer with planning queue boundaries
- static local plan viewer tooling
- notification pack hint routing
- read-only lane scoring and WorkerContract planning records
- approval-gated autonomous loop planning artifacts
- local-only Remotion review asset scaffold

## Prioritized Assumptions

| Assumption | Risk | Evidence Now | Next Validation |
| --- | --- | --- | --- |
| Local-first state plus review UI is enough to coordinate the next Codex work loop. | Medium | CLI, plan viewer, tests, and docs exist. | Run a real user workflow from capture to plan selection to handoff. |
| Explicit planning queues prevent accidental execution better than free-form displayed commands. | Medium | Queue entries include non-execution authority language and tests. | Add a safe handoff or execution-gateway design before any command runner. |
| Governance validator plus doctor summary will catch project-local agent/skill drift. | Low | Validator passes with 156 checks; doctor is opt-in and read-only. | Add checks only when trial runs reveal routing noise. |
| Local Remotion review assets improve review and handoff quality without adding hosted risk. | Medium | Typecheck, render, audit, and scaffold tests pass. | Review generated asset with the operator and decide whether it belongs in release artifacts. |
| Lane scoring can guide Worktrunk cleanup without implying mutation authority. | Medium | Read-only lane tests pass and docs say mutation is approval-gated. | Exercise lane scoring against multiple real worktrees before adding lane CLI commands. |

## Prioritized Backlog

| Rank | Initiative | Why Now | Confidence | Do Next |
| ---: | --- | --- | --- | --- |
| 1 | End-to-end local workflow rehearsal | Proves the platform works as a user-facing loop, not just components. | High | Run capture, approval, handoff, plan viewer, doctor, and Remotion review as one scripted checklist. |
| 2 | Safe handoff / execution gateway design | Converts planning queue into controlled action proposals without weakening governance. | Medium | Read-only queue handoff is implemented; do not add a runner without a separate PRD. |
| 3 | Plan viewer browser smoke automation | Existing tests cover package/static behavior; browser rendering should be checked before UI-heavy release claims. | Medium | Add a Playwright or lightweight browser smoke only if dependency policy is approved. |
| 4 | Worktrunk lane CLI design | Lane scoring exists, but CLI mutation must remain gated. | Medium | Write PRD/acceptance criteria before adding `lane` subcommands. |
| 5 | Voice ingress and Codex App Server bridge | Important product direction, but higher runtime and approval risk. | Low | Keep as discovery until state, queue, and handoff loop is proven. |

## Release Acceptance Criteria

- `git status --short` is clean except ignored runtime artifacts.
- `uv run pytest` passes.
- `python3 scripts/validate-jarvis-codex-phase1.py` reports `PASS`, 156 checks, zero warnings, and zero failures.
- `jarvis-codex doctor --governance` returns compact governance status and does not create state directories.
- Loop planning YAML parses successfully.
- Remotion `npm run typecheck`, `npm audit --audit-level=high`, `npm run still`, and `npm run render` pass.
- `tests/test_workflow_rehearsal.py` proves the local loop can capture state, record memory, request approval, write a handoff, report governance through doctor, select plan steps, approve a planning queue, and render continuity from temp state.
- Global architecture validation has zero errors.

## Unresolved Product Decisions

- Whether to push the 17 local commits to `origin/main`.
- Whether generated Remotion PNG/MP4 files should be copied to a release artifact location or remain local ignored outputs.
- Whether the next package should be a safe handoff gateway, browser smoke automation, or Worktrunk lane CLI design.
- Whether project-local `skills.config` should remain deferred until more routing evidence appears.

## Recommendation

Treat the platform as production-ready for local governed review and planning workflows. Do not claim autonomous execution readiness. The end-to-end local workflow rehearsal is covered by `tests/test_workflow_rehearsal.py`; the safe handoff gateway PRD is implemented as a read-only queue summary, not a command runner.
