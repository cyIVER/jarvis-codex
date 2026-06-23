# Swarm And Loop Operation

Jarvis supports autonomous-loop planning and governed swarm lifecycle records after an approved plan.

## Default Loop

`/loop` defaults to a delivery loop:

```text
plan -> implement -> test -> review -> fix -> validate -> commit -> push -> monitor -> continue
```

The loop must keep:

- Objective.
- Active phase.
- Editable surfaces.
- Locked evaluators.
- Append-only run log.
- Keep/discard decisions.
- Current risk level.
- Next action.

## Default Swarm

`/swarm` uses orchestrator-worker behavior.

Roles are dynamic and risk-scaled:

- Codex executor.
- Antigravity planner.
- Architecture adversary.
- Security adversary.
- QA adversary.
- Product adversary.
- Codeburn telemetry reviewer.

Small work may use only main thread plus executor. High-risk or production work requires multiple challengers before commit or push.

Current runtime support is intentionally state-first:

- `swarm.plan` records planned lane assignments.
- `swarm.start` records an approved lifecycle start for a plan.
- `swarm.stop` records an approved lifecycle stop for a recorded swarm event.
- `loop.start`, `loop.pause`, `loop.resume`, and `loop.stop` record approved loop lifecycle state for a session.

These records do not launch agents, start PTYs, mutate Worktrunk, run shell commands, execute runtime workflows, or grant execution authority.

The HUD exposes matching loop lifecycle controls. The controls can request approval and record approved lifecycle state, but they do not start autonomous loop execution.

## Bounded Loop Runner

`jarvis-codex loop run-once --allow-validation --json` runs one bounded product-readiness loop iteration.

The runner executes only fixed built-in validators/readiness collectors and fixed no-shell Codeburn telemetry:

- Phase 1 Codex governance validation.
- Loop readiness validation.
- Runtime readiness summary.
- Fixed Codeburn telemetry status.

It writes a loop-run JSON record under the selected `--state` directory and appends `logs/loop-runs.jsonl`.

It does not accept arbitrary command strings, launch services, probe the network, mutate Git, mutate Worktrunk, start agents, start PTYs, or run runtime workflows.

## Risk-Scaled Spawning

Risk factors:

- Security-sensitive files.
- Runtime services.
- Git/worktree mutation.
- Public exposure.
- Voice or microphone changes.
- Database migrations.
- Hardware/GPU/Docker execution.
- Large diff size.
- Failing tests.
- Ambiguous requirements.

Swarm size increases as risk increases.

## Codeburn Integration

Codeburn runs as a first-class pane and telemetry source.

It should report:

- Provider/model usage.
- Cost or token trend where available.
- Task and tool distribution.
- Session yield or optimization hints.

Codeburn data informs loop budgets but does not override safety gates.

## Worktree Policy

Use the hybrid write substrate:

- Small single-lane edits may happen in the current repo.
- Parallel or high-risk write-heavy work uses Worktrunk worktrees after approval.
- Docker is reserved for isolated runtime/test workloads.

## Promotion Gates

Before commit or push:

- Required tests pass.
- Governance validator passes when governance files are affected.
- Relevant adversary lanes pass or document accepted risk.
- Diff is scoped.
- User-facing docs are updated when behavior changes.

## Acceptance Criteria

- `/loop` can run a delivery phase with a durable event trail.
- `/loop` lifecycle methods can record approved state without starting execution.
- `loop run-once` can execute fixed validators and record a bounded loop-run event.
- `/swarm` can record role-labeled lifecycle state with scoped approvals.
- Actual role-labeled pane spawning remains a future implementation gate.
- High-risk work triggers adversarial review.
- Commit/push steps are visible, logged, and policy-gated.
