---
name: ipc-orchestration-review
description: Review Jarvis IPC and orchestration design safety boundaries for process coordination, queues, state, CLI-to-CLI orchestration, worker boundaries, and approval gates. Use for review and patch proposals, not direct IPC implementation.
---

# Purpose

Review Jarvis IPC and orchestration design for safety boundaries, approval handling, process isolation, and state integrity.

# When to use

Use this skill for IPC design review, worker coordination review, process boundary review, queue and state review, CLI-to-CLI orchestration review, and approval gate analysis.

# When not to use

Do not use this skill to implement IPC code directly, launch orchestration services, or bypass existing approval gates.

# Tool expectations

Read source, docs, tests, and plans. Propose risks, tests, and patches only unless the user separately approves implementation.

# Workflow

1. Identify orchestration boundaries, actors, queues, commands, and state stores.
2. Trace where approvals are required, recorded, and enforced.
3. Check for raw command injection, ambiguous executable text, stale state reuse, and cross-lane mutation risks.
4. Review tests and validation coverage for orchestration failure modes.
5. Produce a prioritized review with approval-gated remediation proposals.

# Expected output

Return: reviewed components, trust boundaries, findings by severity, missing tests, recommended patches, approval gates, residual risk, and next action.

# Guardrails

Treat executable text and planner-generated commands as untrusted until structured and approved. Keep review separate from implementation.

# Validation

Confirm every finding identifies a boundary, source file, state artifact, or test gap.
