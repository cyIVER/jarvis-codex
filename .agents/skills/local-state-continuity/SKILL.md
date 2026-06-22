---
name: local-state-continuity
description: Standardize read-only inspection and summarization of Jarvis local state, plans, reports, and blackboard-style files when resuming work or reconciling state, plans, reports, and continuity artifacts. Do not use for durable global memory writes.
---

# Purpose

Standardize how Jarvis local state, plans, reports, and blackboard-style files are inspected and summarized across sessions.

# When to use

Use this skill when resuming Jarvis work, reconciling `state/`, `plans/`, reports, local continuity files, or blackboard-style coordination artifacts.

# When not to use

Do not use this skill for durable global memory writes, unrelated repository summaries, or speculative state reconstruction without local evidence.

# Tool expectations

Use read-only inspection. Propose memory facts when useful, but do not store them or alter durable memory without explicit approval.

# Workflow

1. Locate relevant local state, plan, report, and continuity files.
2. Identify the latest authoritative artifact for the current task.
3. Separate active decisions, pending approvals, completed work, and stale notes.
4. Summarize continuity in a compact handoff format.
5. Propose durable memory candidates separately from local state findings.

# Expected output

Return: files inspected, current state summary, active decisions, pending approvals, stale or conflicting artifacts, proposed memory candidates, residual risk, and next action.

# Guardrails

Do not promote local notes to durable memory automatically. Do not overwrite or clean state files under this skill.

# Validation

Confirm every state claim is linked to a local artifact or marked as an inference.
