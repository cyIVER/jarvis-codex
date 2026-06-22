---
name: worktrunk-lane-governance
description: Govern Jarvis Worktrunk branch and worktree lane planning without mutating git state. Use for branch or worktree lane planning, lane assignment, cleanup policy, and agent-lane split proposals; do not use to execute wt, merge, rebase, reset, clean, delete worktrees, or push.
---

# Purpose

Govern Jarvis Worktrunk lane planning while keeping git and worktree state unchanged.

# When to use

Use this skill for branch and worktree lane planning, lane assignment, cleanup policy, parallel agent lane split, and approval-gated command proposals.

# When not to use

Do not use this skill to execute `wt`, merge, rebase, delete worktrees, reset, clean, push, or otherwise mutate git state.

# Tool expectations

Use read-only git inspection only unless the user explicitly approves a mutating command. Acceptable read-only checks include `git status`, `git branch`, and `git worktree list`.

# Workflow

1. Inspect current branch and worktree state with read-only commands.
2. Identify active lanes, conflicts, stale branches, and ownership boundaries.
3. Propose a lane split with disjoint file or module ownership.
4. List any cleanup or mutation commands as approval-gated proposals only.
5. Define verification for each lane before execution.

# Expected output

Return: current lane state, proposed lanes, file or module ownership, blocked lanes, approval-gated commands, verification plan, residual risk, and next action.

# Guardrails

Do not run mutation commands under this skill. Keep generated command lists explicit, ordered, and approval-gated.

# Validation

Confirm that proposed lanes do not overlap unnecessarily and that every mutating command is labeled as not yet executed.
