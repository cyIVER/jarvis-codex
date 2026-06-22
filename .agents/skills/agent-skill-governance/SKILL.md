---
name: agent-skill-governance
description: Govern Jarvis agent and skill routing, local overrides, project-local Codex policy, pack alignment, least-privilege reviews, and skill-load pressure analysis. Use for Jarvis agent standardization and skill governance, not general skill creation outside Jarvis.
---

# Purpose

Govern Jarvis agent and skill routing, local overrides, and least-privilege policy without changing global behavior by default.

# When to use

Use this skill for Jarvis agent standardization, skill pressure analysis, pack alignment, project-local Codex policy, least-privilege review, and repo-local agent or skill governance.

# When not to use

Do not use this skill for general skill creation outside Jarvis, plugin activation, global skill disabling, or writable worker enablement without explicit approval.

# Tool expectations

Read config, agent TOML, pack manifests, and skill files. Propose changes first unless implementation has been explicitly approved.

# Workflow

1. Inventory active project-local and relevant global agent or skill files.
2. Classify each item by role, permission level, and routing scope.
3. Identify which controls are enforceable by TOML and which are instruction-level only.
4. Keep project-local overrides narrow and avoid global churn.
5. Produce approval-separated recommendations with validation steps.

# Expected output

Return: inspected files, governance classification, enforceable controls, instruction-level controls, recommended changes, approval items, validation, residual risk, and next action.

# Guardrails

Do not invent unsupported TOML fields. Do not globally disable skills, activate extracted catalogs, or change sandbox modes from read-only to writable unless explicitly approved.

# Validation

Confirm each proposed field is supported or clearly marked as instruction-level policy.
