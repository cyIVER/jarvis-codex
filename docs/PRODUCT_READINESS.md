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
- static local plan viewer tooling with headless browser smoke coverage
- notification pack hint routing
- read-only lane scoring, JSON lane CLI review, and WorkerContract planning records
- read-only release artifact manifest for local review surfaces and generated Remotion asset decisions
- GitHub CI for Python tests, Codex governance validation, and Remotion static validation
- approval-gated autonomous loop planning artifacts
- local-only Remotion review asset scaffold

## Prioritized Assumptions

| Assumption | Risk | Evidence Now | Next Validation |
| --- | --- | --- | --- |
| Local-first state plus review UI is enough to coordinate the next Codex work loop. | Low | CLI, plan viewer, browser smoke, workflow rehearsal, tests, and docs exist. | Run operator review on generated Remotion and plan-viewer surfaces before publishing release notes. |
| Explicit planning queues prevent accidental execution better than free-form displayed commands. | Low | Queue entries include non-execution authority language, safe handoff output, and tests. | Keep command runners out of scope until a separate runner PRD is approved. |
| Governance validator plus doctor summary will catch project-local agent/skill drift. | Low | Validator passes with 156 checks; doctor is opt-in and read-only. | Add checks only when trial runs reveal routing noise. |
| GitHub-side validation catches drift outside the local shell. | Low | CI workflow runs Python tests, project-local governance validation, and Remotion typecheck/audit without rendering or publishing artifacts. | Observe the first remote run after push and tighten only if it finds environment drift. |
| Local Remotion review assets improve review and handoff quality without adding hosted risk. | Low | Typecheck, render, audit, scaffold tests, and the read-only release manifest pass. | Review generated asset with the operator before any copy, publication, or tracked release bundle. |
| Lane scoring can guide Worktrunk cleanup without implying mutation authority. | Low | Read-only lane tests pass, docs say mutation is approval-gated, `jarvis-codex lane list --json` plus `lane score --json` expose review-only CLI output, and an isolated real-worktree fixture covers multiple worktrees. | Exercise manually on operator-selected real worktrees before any mutation PRD. |

## Prioritized Backlog

| Rank | Initiative | Why Now | Confidence | Do Next |
| ---: | --- | --- | --- | --- |
| 1 | End-to-end local workflow rehearsal | Proves the platform works as a user-facing loop, not just components. | High | Run capture, approval, handoff, plan viewer, doctor, and Remotion review as one scripted checklist. |
| 2 | Safe handoff / execution gateway design | Converts planning queue into controlled action proposals without weakening governance. | Medium | Read-only queue handoff is implemented; do not add a runner without a separate PRD. |
| 3 | Plan viewer browser smoke automation | Existing package/static tests are now backed by a headless Chromium render smoke. | High | Keep browser smoke in the dev test suite; do not add browser-launching automation to production commands. |
| 4 | Worktrunk lane CLI review | Read-only `lane list --json` and `lane score --json` are implemented and covered by an isolated real-worktree fixture; mutation remains out of scope. | High | Manual operator review on real worktrees can happen before considering any mutation PRD. |
| 5 | Release artifact packaging | Read-only manifest is implemented; generated assets still require operator approval before packaging. | High | Keep the manifest as review-only until the operator approves a specific artifact copy/publish step. |
| 6 | GitHub CI and review templates | CI and templates are present and validation-only. | High | Watch the first remote CI result after push; do not add publish/release jobs without approval. |
| 7 | Voice ingress and Codex App Server bridge | Important product direction, but higher runtime and approval risk. | Low | Keep as discovery until state, queue, handoff, and lane review loops are proven. |

## Release Acceptance Criteria

- `git status --short` is clean except ignored runtime artifacts.
- `uv run pytest` passes.
- `python3 scripts/validate-jarvis-codex-phase1.py` reports `PASS`, 156 checks, zero warnings, and zero failures.
- `jarvis-codex doctor --governance` returns compact governance status and does not create state directories.
- Loop planning YAML parses successfully.
- Remotion `npm run typecheck`, `npm audit --audit-level=high`, `npm run still`, and `npm run render` pass.
- `tests/test_workflow_rehearsal.py` proves the local loop can capture state, record memory, request approval, write a handoff, report governance through doctor, select plan steps, approve a planning queue, and render continuity from temp state.
- `tests/test_static_plan_viewer_browser.py` renders the static viewer in headless Chromium without using `--open` or executing displayed commands.
- `tests/test_worktrunk_lane_cli_prd.py` keeps the lane CLI PRD read-only-first and mutation-gated.
- `tests/test_cli.py` covers read-only JSON lane list and score commands.
- `tests/test_lanes.py` covers read-only lane inventory across an isolated temporary git repo with multiple worktrees.
- `tests/test_release.py` covers the read-only release manifest and generated asset approval labels.
- `tests/test_github_ci.py` covers the validation-only CI and review-template guardrails.
- Global architecture validation has zero errors.

## Unresolved Product Decisions

- Whether future PM loop commits should be pushed immediately after validation or batched for release review.
- Whether generated Remotion PNG/MP4 files should be copied to a release artifact location or remain local ignored outputs after operator review.
- Whether the next package should start voice ingress discovery, release publication planning, or broader release readiness review.
- Whether project-local `skills.config` should remain deferred until more routing evidence appears.

## Recommendation

Treat the platform as production-ready for local governed review and planning workflows. Do not claim autonomous execution readiness. The end-to-end local workflow rehearsal is covered by `tests/test_workflow_rehearsal.py`, the safe handoff gateway PRD is implemented as a read-only queue summary, the static plan viewer has headless browser smoke coverage, Worktrunk lane CLI review is read-only JSON output with isolated real-worktree coverage, and release artifact review is manifest-only until a specific copy or publication action is approved.
