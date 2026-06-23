# Swarm And Loop Operation

Jarvis supports autonomous loops and dynamic swarms after an approved plan.

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
- `/swarm` can spawn role-labeled panes.
- High-risk work triggers adversarial review.
- Commit/push steps are visible, logged, and policy-gated.

