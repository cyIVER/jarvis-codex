---
name: approval-handoff-briefing
description: Produce approval-ready handoff briefs with gates, risks, commands, expected outputs, and verification steps before edits, commands, workflows, or agent fanout. Use when user approval is needed for non-trivial or mutating Jarvis work, not for trivial read-only status checks.
---

# Purpose

Produce approval-ready handoff briefs that make proposed actions, risks, gates, commands, and expected outputs clear before execution.

# When to use

Use this skill before asking the user to approve edits, mutating commands, workflow runs, service launches, installs, migrations, git mutation, or agent fanout.

# When not to use

Do not use this skill for trivial one-command read-only status checks or already-approved narrow edits.

# Tool expectations

Operate read-only and format outputs. Do not execute the proposed mutating command as part of the handoff.

# Workflow

1. State the decision needed from the user.
2. List proposed actions with exact paths and commands where applicable.
3. Identify preconditions, expected outputs, risks, and rollback or inspection notes.
4. Separate independent approval items so they can be accepted or rejected one by one.
5. Include verification steps that should run after approval.

# Expected output

Return: decision requested, scope, proposed commands or edits, approval gates, risks, expected outputs, rollback or inspection notes, verification, and independent approval items.

# Guardrails

Do not bundle unrelated approvals. Do not hide mutating behavior inside broad commands. Keep the brief actionable and specific.

# Validation

Confirm every proposed mutation has an explicit approval gate and a matching verification step.
