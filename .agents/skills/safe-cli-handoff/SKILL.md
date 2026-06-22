---
name: safe-cli-handoff
description: Prepare safe command handoffs with preconditions, approval boundaries, rollback or inspection notes, and verification before running local Jarvis commands that may write, install, start services, or modify git. Do not use for purely read-only rg, sed, ls, or git status.
---

# Purpose

Prepare safe command handoffs before local Jarvis commands that may write, install, start services, or modify git state.

# When to use

Use this skill before running mutating Jarvis commands, workflow scripts, installs, migrations, service launches, git mutation, or commands that create reports outside already-approved paths.

# When not to use

Do not use this skill for purely read-only `rg`, `sed`, `ls`, `find`, `cat`, or `git status` checks.

# Tool expectations

Do not execute commands through this skill. Generate handoff text with exact commands, preconditions, approval boundaries, and verification.

# Workflow

1. Classify the command as read-only, report-writing, source-writing, service-starting, install, migration, or git-mutating.
2. List preconditions and current-state checks.
3. State the exact command and working directory.
4. Identify expected outputs, possible side effects, and inspection or rollback notes.
5. Define post-command verification.

# Expected output

Return: command classification, preconditions, exact command, approval required, expected outputs, side effects, inspection or rollback notes, verification, and next action.

# Guardrails

Do not convert a handoff into execution. Avoid vague command templates when a precise command is needed for approval.

# Validation

Confirm every non-read-only command has explicit approval language and post-run verification.
