---
name: jarvis-gate-stabilization
description: Stabilize Jarvis gate checks, approval gates, verification state, gate failures, gate reports, readiness criteria, stabilization reviews, and Gate 2 governance. Use only for Jarvis gate and approval-governance work, not for general CI or unrelated repositories.
---

# Purpose

Stabilize Jarvis gate checks, approval gates, and verification state without assuming permission to edit files or run mutating workflows.

# When to use

Use this skill for Jarvis gate failures, gate reports, readiness criteria, stabilization reviews, approval gate reviews, and Gate 2 governance.

Reference targets include `AGENTS.md`, `pyproject.toml`, `scripts/`, `tests/`, and `plans/`.

# When not to use

Do not use this skill for general CI debugging, unrelated repositories, deployment triage, package upgrades, or direct implementation work unless a separate approval explicitly allows writes.

# Tool expectations

Read files, inspect scripts and tests, and propose validation commands. Do not write files, install packages, launch services, or mutate git state unless separately approved.

# Workflow

1. Identify the specific gate, report, script, or readiness criterion under review.
2. Inspect the relevant local references and current gate artifacts.
3. Separate confirmed failures from missing evidence and inferred risks.
4. Propose the smallest non-destructive validation commands first.
5. If fixes are needed, produce an approval-ready change plan instead of editing.

# Expected output

Return: gate reviewed, files inspected, current evidence, confirmed blockers, likely causes, proposed validation commands, approval gates, residual risk, and next action.

# Guardrails

Keep scope Jarvis-specific. Preserve read-only behavior by default. Do not treat failed gates as permission to rewrite gate scripts or bypass approvals.

# Validation

Confirm each recommendation points to an inspected file, a specific missing artifact, or a concrete validation command. Mark speculation clearly.
